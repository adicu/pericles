import settings
from gdata.calendar.client import CalendarClient, CalendarEventQuery
from datetime import datetime, timedelta
from mailsnake import MailSnake

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

def parse_timestamp(ts):
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
    event_dict = {}

    event_dict['title'] = event.title.text
    
    start_time, start_set = parse_timestamp(event.when[0].start)
    end_time, end_set = parse_timestamp(event.when[0].end)
    event_dict['start_date'] = start_time.strftime(settings.DATE_FORMAT)
    event_dict['start_time'] = start_time.strftime(settings.TIME_FORMAT)
    event_dict['end_date'] = end_time.strftime(settings.DATE_FORMAT)
    event_dict['end_time'] = end_time.strftime(settings.TIME_FORMAT) 
    event_dict['location'] = event.where[0].value
    event_dict['description'] = event.content.text
    
    if event_dict['start_date'] != event_dict['end_date']:
        dif_dates = True
    else:
        dif_dates = False
    if dif_dates:
        if start_set and end_set:
            template = unicode(settings.EVENT_HTML_TEMPLATE_WITH_ALL) if html else unicode(settings.EVENT_TEXT_TEMPLATE_WITH_ALL)
        else:
            template = unicode(settings.EVENT_HTML_TEMPLATE_NO_TIMES) if html else unicode(settings.EVENT_TEXT_TEMPLATE_NO_TIMES)
    else:
        template = unicode(settings.EVENT_HTML_TEMPLATE_DEFAULT) if html else unicode(settings.EVENT_TEXT_TEMPLATE_DEFAULT)
            
    return template.format(**event_dict)

def get_events():
    client = CalendarClient(source='adicu-pericles-v1')
    client.ClientLogin(settings.GCAL_USERNAME, 
                       settings.GCAL_PASSWORD, 
                       client.source)

    uri = "https://www.google.com/calendar/feeds/" + settings.GCAL_ID + \
                "/private/full"

    start_date = datetime.today()
    end_date = start_date + timedelta(weeks=1)

    query = CalendarEventQuery()
    query.start_min = start_date.strftime('%Y-%m-%d')
    query.start_max = end_date.strftime('%Y-%m-%d')

    return client.GetCalendarEventFeed(uri=uri, q=query)

def gen_blurb(html=True):
    if html:
        return u'<h3>Hey ADI</h3></br><p>Have a good week</p>'
    else:
        return u'Hey ADI\n Have a good week'

def gen_email_text():
    feed = get_events()
    text = u'\n\n'.join([event_text(event, False) 
                        for event in reversed(feed.entry)])
    html = u'\n\n'.join([event_text(event, True) 
                        for event in reversed(feed.entry)])
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
