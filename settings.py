from sensitive import *

# There are message templates for html and text, which vary based on the number of times available

CREDENTIALS_PATH = "credentials.txt"

EVENT_TEMPLATE = {}
EVENT_TEMPLATE['HTML_TITLE'] = "<h3><a href=\"{url}\">{title}</a></h3>\n"
EVENT_TEMPLATE['TEXT_TITLE'] = "{title}\n"
EVENT_TEMPLATE['HTML_START_DATE'] = "<h4>{start_date}"
EVENT_TEMPLATE['TEXT_START_DATE'] = "{start_date}"
EVENT_TEMPLATE['START_TIME'] = "{start_time}"
EVENT_TEMPLATE['END_DATE'] = "{end_date}"
EVENT_TEMPLATE['END_TIME'] = "{end_time}"
EVENT_TEMPLATE['HTML_LOC'] = " at {location}</h4>\n"
EVENT_TEMPLATE['HTML_DESC'] = "<p>{description}</p>"
EVENT_TEMPLATE['TEXT_LOC'] = " at {location}\n"
EVENT_TEMPLATE['TEXT_DESC'] = "{description}"

EVENT_HTML_TEMPLATE_WITH_ALL = (EVENT_TEMPLATE['HTML_TITLE'] + EVENT_TEMPLATE['HTML_START_DATE'] \
        + ", " + EVENT_TEMPLATE['START_TIME'] + " &mdash; " + EVENT_TEMPLATE['END_DATE'] + ", " \
        + EVENT_TEMPLATE['END_TIME'] + EVENT_TEMPLATE['HTML_LOC']+ EVENT_TEMPLATE['HTML_DESC'])

EVENT_HTML_TEMPLATE_DEFAULT = (EVENT_TEMPLATE['HTML_TITLE'] + EVENT_TEMPLATE['HTML_START_DATE'] \
        + ", " +  EVENT_TEMPLATE['START_TIME'] + " &mdash; " + EVENT_TEMPLATE['END_TIME'] \
        + EVENT_TEMPLATE['HTML_LOC'] + EVENT_TEMPLATE['HTML_DESC'])

EVENT_TEXT_TEMPLATE_DEFAULT = EVENT_TEMPLATE['TEXT_TITLE'] + EVENT_TEMPLATE['TEXT_START_DATE'] \
        + ", " + EVENT_TEMPLATE['START_TIME'] + " &mdash; " + EVENT_TEMPLATE['END_TIME'] \
        + EVENT_TEMPLATE['TEXT_LOC'] + EVENT_TEMPLATE['TEXT_DESC']

EVENT_TEXT_TEMPLATE_WITH_ALL = (EVENT_TEMPLATE['TEXT_TITLE'] + EVENT_TEMPLATE['TEXT_START_DATE'] \
        + ", " + EVENT_TEMPLATE['START_TIME'] +  " &mdash; " + EVENT_TEMPLATE['END_DATE'] \
        + ", " + EVENT_TEMPLATE['END_TIME'] + EVENT_TEMPLATE['TEXT_LOC'] + EVENT_TEMPLATE['TEXT_DESC'])

SUBJECT_TEMPLATE = "ADI Newsletter %-m/%-d/%Y"

DATE_FORMAT = '%A, %-m/%-d'
TIME_FORMAT = '%-I:%M %p'

