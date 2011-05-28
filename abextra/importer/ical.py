"""
see http://vobject.skyhouseconsulting.com/usage.html
test validity of ical here: http://icalvalid.cloudapp.net/Default.aspx
"""
import vobject
import urllib
import settings
from importer.parsers.locations import PlaceParser
from events.models import Event, Occurrence

class Parser:
    def __init__(self, file, delim='::'):
        if file:
            self.parsedCal = vobject.readOne(file)
        self.address_delim = delim
        self.place_parser = PlaceParser()
        #self.forward_weeks = settings.forward_weeks

    def insert_attachments(self, event, attachments):
        """
        Check if there are any attachments
        Assign attachments to different params (video, img) based on format.
        """
        if not attachments:
            return
        pass

    def get_event_from_title(self, title):
        """
        Checks if an event with the same title already exists in the DB
        If such an event does not exist, return a new event.
        Input : title
        Output: Event object (either existing or new)
        """
        events = Event.objects.filter(title=title)
        event = None
        if not event:
            event = Event()
            event.title = title
        elif len(events) > 1:
            #raise error
            pass
        else:
            event = events[0]

        return event

    def get_occurrence_from_title_date_time(self, event, date, time,
                                            enddate, endtime):
        """
        Incorporate use of enddate and endtime as well.
        They are currently unused.
        """
        occurrences = Occurrence.objects.get(event=event, start_date=date,
                                            start_time=time)
        if not occurrences:
            occurrence = Ocurrence()
            occurrence.start_date = date
            occurrence.start_time = time
            occurrence.event  = event
            return occurrence
        elif len(occurrences) > 1:
            # Validate if information is correct
            # else raise error
            pass
        else:
            #TODO: Validate all other information.
            return occurrences[0]

    def save_model(self, model, dictionary):
        model_obj = model()
        for key in dictionary:
            model_obj.__setattr__(key, dictionary[key])
        return model

    def handle_image(self, image_url):
        """
        Given a url, saves an image and returns the path to that image.
        """
        return

    def insert_location_info(self, location_string, delim1='::',
                             delim2='='):
        """
        #FIXME: How about reusing existing code instead of this?
        WHAT: Given a location string from an iCalendar file, convert location
        into a format usable by kwiqet.
        The function returns a Place object
        HOW:
        This function checks if the objects already exist in the DB
        If they do not exist, objects get created.
        Otherwise, existing objects are utilized.
        """
        params = location_string.split(delim1)
        param_values = [(vals.split(delim2)) for vals in params]
        param_dict = dict([(key.lower(), val) for key, val in param_values])
        return self.insert_location_dict(param_dict)

    def insert_location_dict(self,  param_dict):
        """
        Input: Dictionary of keys that represent location parameters and their
               values
        Output: Tuple(Bool, Place) where Bool indicates if the Place was created
                and stored into the Database
        """
        return self.place_parser.parse(param_dict)

    def store_ocurrence_info(self, event, recurrence_string, location,
                             start_datetime, end_datetime):
        """
        Based on recurrence information, generates occurrences that repeat
        over a time period of forward_weeks which is defined in settings.
        See:
        1) http://www.kanzaki.com/docs/ical/rrule.html
        2) http://www.kanzaki.com/docs/ical/rdate.html
        3) http://www.kanzaki.com/docs/ical/exrule.html
        4) http://www.kanzaki.com/docs/ical/exdate.html

        ver 0.1: Ignoring recurrence string
        """
        start_date = start_datetime.date()
        start_time = start_datetime.time()
        end_date = end_datetime.date()
        end_time = end.datetime.time()
        occurrence = self.get_occurrence_from_title_date_time(event, start_date,
                                                              start_time,
                                                              end_date,
                                                              end_time)
        occurrence.save()

    def get_events(self):
        """
        Returns all events that are listed inside an iCalendar feed.
        """
        for vevent in self.parsedCal.contents['vevent']:
            title = vevent.summary.value      # this is a string
            event = self.get_event_from_title(title)
            self.insert_location_info(vevent.location.value)
            start_datetime = vevent.dtstart.value # this is a date time obj
            end_datetime =  vevent.dtend.value
            self.store_occurrence_info(event, recurrence_string, location,
                                       start_datetime, end_datetime)
            description = vevent.description.value
            if description:
                event.description = incoming

            self.insert_attachments(event, vevent.contents['attach'])
