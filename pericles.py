import argparse
import httplib2
from datetime import datetime, timedelta
import requests
import json
import fileinput
import logging
import sys

from sensitive import *
import settings

from bson import json_util

from mailsnake import MailSnake

import gspread

from oauth2client.client import OAuth2WebServerFlow
from oauth2client import tools
from oauth2client.file import Storage

def find_template(name):
    mc = MailSnake(settings.MC_API_KEY)
    templates = mc.templates()['user']

    for temp in templates:
        if temp['name'] == name:
            return temp['id']

    return 0

def find_list(name):
    mc = MailSnake(settings.MC_API_KEY)
    lists = mc.lists(filters = {"list_name": name})

    if lists['total'] == 0:
        return 0

    return lists['data'][0]['id']

def fromTimeString(dts):
    if dts == '':
        return ''

    [ds, ts] = dts.split(' ')
    [month, day, year] = map(int, ds.split('/'))
    [hour, minute, second] = map(int, ts.split(':'))
    return datetime(year, month, day, hour, minute)

def fromDateString(ds):
    if ds == '':
        return ''

    [month, day, year] = map(int, ds.split('/'))
    return datetime(year, month, day)

def event_text(event, html=True):

    event_data = {}
    event_data['title'] = event['title']
    event_data['url'] = event.get('facebook_url', 'http://www.adicu.com')

    start_time = event['start_datetime']
    end_time = event['end_datetime']
    if start_time != '':
        event_data['start_date'] = start_time.strftime(settings.DATE_FORMAT)
        event_data['start_time'] = start_time.strftime(settings.TIME_FORMAT)
    if end_time != '':
        event_data['end_date'] = end_time.strftime(settings.DATE_FORMAT)
        event_data['end_time'] = end_time.strftime(settings.TIME_FORMAT)

    event_data['location'] = event.get('location', 'TBA')
    event_data['description'] = event.get('long_description')
    event_data['subtitle']  = event.get('subtitle', '')

    if start_time == '' or end_time == '':
        template = unicode(settings.EVENT_HTML_TEMPLATE_CUSTOM_SUB) if html \
                else unicode(settings.EVENT_TEXT_TEMPLATE_CUSTOM_SUB)
    elif event_data['start_date'] != event_data['end_date']:
        template = unicode(settings.EVENT_HTML_TEMPLATE_WITH_ALL) if html \
                else unicode(settings.EVENT_TEXT_TEMPLATE_WITH_ALL)
    else:
        template = unicode(settings.EVENT_HTML_TEMPLATE_DEFAULT) if html \
                else unicode(settings.EVENT_TEXT_TEMPLATE_DEFAULT)

    return template.format(**event_data)

def get_credentials():
    storage = Storage('credentials.txt')
    credentials = storage.get()

    if credentials is None or credentials.invalid:
        flow = OAuth2WebServerFlow(client_id=settings.GCAL_CLIENT_ID,
                                   client_secret=settings.GCAL_CLIENT_SECRET,
                                   scope='https://spreadsheets.google.com/feeds')
        parser = argparse.ArgumentParser(parents=[tools.argparser])
        flags = parser.parse_args()

        credentials = tools.run_flow(flow, storage, flags)

    return credentials

def recordToEvent(record):
    event = { 'title': record['Name of Event']
            , 'facebook_url': record['Link to Event']
            , 'start_datetime': fromTimeString(record['Start Time'])
            , 'end_datetime': fromTimeString(record['End Time'])
            , 'location': record.get('Location of Event', 'TBA')
            , 'subtitle': record.get('Custom Subtitle', '')
            , 'long_description': record['Blurb']
            , 'include_date': fromDateString(record['Include Date']) }
    return event

def isThisWeek(event):
    now = datetime.now()
    day = (now.weekday() + 1) % 7   # make Sunday be first day of week
    sunday = now - timedelta(days=day, hours=now.hour, minutes=now.minute)
    # in the form the include date is mandatory for the script
    if not event['include_date']:
      return False
    return sunday <= event['include_date'] < sunday + timedelta(days=10)

def get_sheets_events():
    gc = gspread.authorize(get_credentials())
    # sheets = gc.openall()
    # sheet = gc.open('ADI Community Events 16')
    try:
      sheet = gc.open_by_key('18cy2TtUXtrl2DPz89SJuCi7_Ggp7uBdWtaPcsoOsuaM')
    except gspread.exceptions.HTTPError:
      logging.warning("Cannot access Google Drive. Retry one more time in 10 seconds to access it.")
      time.sleep(10)

    isValidRecord = lambda r: 'Name of Event' in r and r['Name of Event'] != ''
    records = filter(isValidRecord, sheet.sheet1.get_all_records())
    events = map(recordToEvent, records)

    return filter(isThisWeek, events)

def get_events():
    r = requests.get('https://adicu.com/admin/api/events/this_week')
    eventum_events = json.loads(r.text, object_hook=json_util.object_hook)['data']
    eventum_events.sort(key=lambda e: e['start_datetime'])

    sheets_events = get_sheets_events()
    sheets_events.sort(key=lambda e: e['include_date']
            if e['start_datetime'] == '' else e['start_datetime'])

    return eventum_events, sheets_events

def gen_blurb(html=True):
    blurb_text = ''
    with open(sys.argv[1]) as f:
      lines = f.readlines()

    for line in lines:
      blurb_text += str(line)

    if html:
        return u'<h3>Hey ADI,</h3><p>' + blurb_text + '</p><br/>'
    else:
        return u'Hey ADI,\n' + blurb_text

def gen_seperator(html=True):
    seperator_text = '-- In The Community --'
    if html:
        return u'<br/><h4>' + seperator_text + '</h4><br/>'
    else:
        return u'\n' + seperator_text + '\n'

def gen_events(events, html=True):
    return u'\n\n'.join([event_text(event, html)
                        for event in events])

def gen_email_text():
    adi, community = get_events()
    adi_html = gen_events(adi, True)
    adi_text = gen_events(adi, False)
    community_html = gen_seperator(True) + gen_events(community, True) \
            if len(community) > 0 else ''
    community_text = gen_seperator(False) + gen_events(community, False) \
            if len(community) > 0 else ''

    html = gen_blurb(True) + adi_html + community_html
    text = gen_blurb(False) + adi_text + community_text

    return html, text

def create_campaign(html, text):
    mc = MailSnake(settings.MC_API_KEY)
    options = {
        'subject' : datetime.today().strftime(settings.SUBJECT_TEMPLATE),
        'from_email' : settings.MC_EMAIL,
        'from_name' : settings.MC_FROM_NAME,
        'to_name' : settings.MC_TO_NAME,
        'template_id' : find_template(settings.MC_TEMPLATE_NAME),
        'list_id' : find_list(settings.MC_LIST_NAME)
    }
    section_name = 'html_' + settings.MC_TEMPLATE_SECTION
    content = {section_name: html, "text": text}
    cid = mc.campaignCreate(type='regular', content=content, options=options)

    return cid

def campaign_info(cid):
    mc = MailSnake(settings.MC_API_KEY)
    campaigns = mc.campaigns(filters = {"campaign_id": cid})

    if campaigns['total'] == 0:
        return 0

    webid = campaigns['data'][0]['web_id']
    title = campaigns['data'][0]['title']

    region = settings.MC_API_KEY.split('-')[1]

    url = "https://%s.admin.mailchimp.com/campaigns/show?id=%d" % (region, webid)

    return title, url

if __name__ == '__main__':
    cid = create_campaign(*gen_email_text())
    title, url = campaign_info(cid)
    print "Created new campaign %s. Edit it at %s." % (title, url)
