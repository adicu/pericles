import argparse
import httplib2
from datetime import datetime, timedelta

import settings

from mailsnake import MailSnake

import gflags
from oauth2client.file import Storage
from oauth2client.client import OAuth2WebServerFlow
from oauth2client.tools import run_flow
from oauth2client import tools
from apiclient.discovery import build

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

def toTimeString(dateTime):
    # formatting example: 2011-06-03T10:00:00-07:00

    month = str(dateTime.month)
    if len(month) == 1:
        month = '0' + month

    day = str(dateTime.day)
    if len(day) == 1:
        day = '0' + day

    return str(dateTime.year) + '-' + month + '-' + day + 'T00:00:00-05:00'

def fromTimeString(ts):
    if 'T' in ts:
        daystr, timestr = tuple(ts.split('T'))
    else:
        daystr = ts
        timestr = None
    year, month, day = tuple([int(part) for part in daystr.split('-')])
    if timestr:
        hour, minute = tuple([int(part) for part in timestr.split(':')[:2]])
    else:
        return datetime(year, month, day), False
    return datetime(year, month, day, hour, minute), True

def event_text(event, html=True):
    ''' convert event from Google format to Mailchimp format '''

    event_data = {}
    event_data['title'] = event['summary']
    
    start_time, start_set = fromTimeString(event['start']['dateTime'])
    end_time, end_set = fromTimeString(event['end']['dateTime'])
    event_data['start_date'] = start_time.strftime(settings.DATE_FORMAT)
    event_data['start_time'] = start_time.strftime(settings.TIME_FORMAT)
    event_data['end_date'] = end_time.strftime(settings.DATE_FORMAT)
    event_data['end_time'] = end_time.strftime(settings.TIME_FORMAT)

    event_data['location'] = event.get('location', 'TBA')
    event_data['description'] = event.get('description', 'No description')
    
    if event_data['start_date'] != event_data['end_date']:
        if start_set and end_set:
            template = unicode(settings.EVENT_HTML_TEMPLATE_WITH_ALL) if html \
                    else unicode(settings.EVENT_TEXT_TEMPLATE_WITH_ALL)
        else:
            template = unicode(settings.EVENT_HTML_TEMPLATE_NO_TIMES) if html \
                    else unicode(settings.EVENT_TEXT_TEMPLATE_NO_TIMES)
    else:
        template = unicode(settings.EVENT_HTML_TEMPLATE_DEFAULT) if html \
                else unicode(settings.EVENT_TEXT_TEMPLATE_DEFAULT)
            
    return template.format(**event_data)

def get_events():
    parser = argparse.ArgumentParser(parents=[tools.argparser])
    FLAGS = parser.parse_args()

    FLOW = OAuth2WebServerFlow(client_id=settings.GCAL_CLIENT_ID,
            client_secret=settings.GCAL_CLIENT_SECRET,
            scope='https://www.googleapis.com/auth/calendar')
    storage = Storage(settings.CREDENTIALS_PATH)
    run_flow(FLOW, storage, FLAGS)
    credentials = storage.get()
    http = credentials.authorize(httplib2.Http())
    service = build('calendar', 'v3', http=http)

    response = service.events().list(
            calendarId = settings.GCAL_ID,
            timeMin = toTimeString(datetime.now()),
            timeMax = toTimeString(datetime.now() + timedelta(weeks=2)),
            singleEvents = True,
            orderBy = 'startTime').execute()
    return response["items"]

def gen_blurb(html=True):
    if html:
        return u'<h3>Hey ADI</h3></br><p>Have a good week</p>'
    else:
        return u'Hey ADI\n Have a good week'

def gen_email_text():
    feed = get_events()
    text = u'\n\n'.join([event_text(event, False) 
                        for event in feed])
    html = u'\n\n'.join([event_text(event, True) 
                        for event in feed])
    return gen_blurb(True)+ html, gen_blurb(False) + text

def create_campaign(html, text):
    mc = MailSnake(settings.MC_API_KEY)
    options = {
        "subject" : datetime.today().strftime(settings.SUBJECT_TEMPLATE),
        "from_email" : settings.MC_EMAIL,
        "from_name" : settings.MC_FROM_NAME,
        "to_name" : settings.MC_TO_NAME,
        "template_id" : find_template(settings.MC_TEMPLATE_NAME),
        "list_id" : find_list(settings.MC_LIST_NAME)
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
