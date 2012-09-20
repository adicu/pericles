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

def parse_timestamp(ts):
    daystr, timestr = tuple(ts.split('T'))
    year, month, day = tuple([int(part) for part in daystr.split('-')])
    hour, minute = tuple([int(part) for part in timestr.split(':')[:2]])
    
    return datetime(year, month, day, hour, minute)

def event_text(event):
    event_dict = {}

    event_dict['title'] = event.title.text

    start_time = parse_timestamp(event.when[0].start)
    end_time = parse_timestamp(event.when[0].end)

    event_dict['date'] = start_time.strftime(settings.DATE_FORMAT)
    event_dict['start'] = start_time.strftime(settings.TIME_FORMAT)
    event_dict['end'] = end_time.strftime(settings.TIME_FORMAT)

    event_dict['location'] = event.where[0].value

    event_dict['description'] = event.content.text

    return settings.EVENT_TEMPLATE.format(**event_dict)


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

def gen_email_text():
    feed = get_events()
    text = '\n\n'.join([event_text(event) for event in reversed(feed.entry)])
    return text

def create_campaign(text):
    mc = MailSnake(settings.MC_API_KEY)
    print "Creating campaign using content\n%s" % text
    options = {
        "list_id" : settings.MC_LIST_ID,
        "subject" : datetime.today().strftime(settings.SUBJECT_TEMPLATE),
        "from_email" : settings.MC_EMAIL,
        "from_name" : settings.MC_FROM_NAME,
        "to_name" : settings.MC_TO_NAME,
        "template_id" : find_template(settings.MC_TEMPLATE_NAME)
    }
    section_name = 'html_' + settings.MC_TEMPLATE_SECTION
    content = {section_name : text}
    return mc.campaignCreate(type='regular', content=content, options=options)

if __name__ == '__main__':
    cid = create_campaign(gen_email_text())
    print "Created new campaign %s" % cid
