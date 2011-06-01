"""
see http://vobject.skyhouseconsulting.com/usage.html
test validity of ical here: http://icalvalid.cloudapp.net/Default.aspx
"""
import vobject
import urllib
import settings
from importer.parsers.event import EventParser
from events.models import Event, Occurrence, Source

class DictObj(dict):
    """
    Consider moving this to a more general place.
    This class allows to make our dictionary objects compatible
    with existing ScrapeFeedConsumer objects.
    """
    def __getattr__(self, name):
        try:
            return self.__getitem__(name)
        except KeyError:
            raise AttributeError

class Parser:
    def __init__(self, file_path=None, delim='::'):
        """
        Initialize parser from an iCal file.
        """
        if file_path:
            ical_file_handle = open(file_path)
            self.parsedCal = vobject.readOne(ical_file_handle)
        self.address_delim = delim
        self.event_parser = EventParser()
        # especiall for recurring events in ical.
        #self.forward_weeks = settings.forward_weeks

    def extract_location_info(self, location_string, delim1='::',
                             delim2='='):
        """
        Given a location string from an iCalendar file, convert location
        into a format usable by kwiqet.
        The function returns a dictionary
        HOW:
        This function checks if the objects already exist in the DB
        If they do not exist, objects get created.
        Otherwise, existing objects are utilized.
        """
        params = location_string.split(delim1)
        param_values = [(vals.split(delim2)) for vals in params]
        return dict([(key.lower(), val) for key, val in param_values])

    def insert_event_dict(self, param_dict):
        """
        Given any dictionary representing an event as input; create or update
        all existing information about the event.
        Input: Dictionary of keys that represent event parameters and their
               values
        Output: Tuple(Bool, event) where Bool indicates if the event was created
                and stored into the Database

        """
        occ_dict = param_dict.get('occurrences')
        if occ_dict:
            param_dict['occurrences'] = [DictObj(occ) for occ in occ_dict]
        else:
            param_dict['occurrences'] = []
        return self.event_parser.parse(DictObj(param_dict))

    def extract_info(self, vevent):
        """
        Extracts all pieces of information from a vevent object.
        Input: vevent object
        Ouput: A dictionary containing event, occurrence and location info.
        """
        raw_event = DictObj()
        raw_occurrence = DictObj()
        raw_event['title'] = vevent.summary.value
        raw_event['description'] = vevent.description.value
        #FIXME: Identify URL
        raw_event['url'] = 'www.google.com'
        #FIXME: Better mechanism for identifyng source ical
        raw_event['source'] = Source.objects.get(name='iCal')
        #FIXME: Identify images and video links.
        attachments = vevent.contents['attach']
        #FIXME: Identify better mechanism for prices
        raw_occurrence['prices'] = []
        raw_occurrence['start_time'] = vevent.dtstart.value.time()
        raw_occurrence['start_date'] = vevent.dtstart.value.date()
        raw_occurrence['end_date'] = vevent.dtend.value.date()
        raw_occurrence['end_time'] = vevent.dtend.value.time()
        #NOTE: Location does not need be a DictObj
        location = self.extract_location_info(vevent.location.value)
        raw_occurrence['location'] = location
        raw_event['occurrences'] = [raw_occurrence]
        return raw_event

    def get_events(self):
        """
        Returns all events that are listed inside an iCalendar feed.
        This will automatically create, update and delete existing events and
        any related information in the calendar. The update is performed only
        forward_weeks into the future.
        """
        events = []
        for vevent in self.parsedCal.contents['vevent']:
            event_dict = self.extract_info(vevent)
            success, event = self.insert_event_dict(event_dict)
            events.append(event)
        return events
