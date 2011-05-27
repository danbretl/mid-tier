"""
see http://vobject.skyhouseconsulting.com/usage.html
test validity of ical here: http://icalvalid.cloudapp.net/Default.aspx
"""
import vobject
import urllib
import settings

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
        event = Event.objects.get(title=title)
        if not event:
            event = Event()
            event.title = title
        return event

    def save_model(self, model, dictionary):
        model_obj = model()
        for key in dictionary:
            model_obj.__setattr__(key, dictionary[key])
        return model

    def handle_image(self, image_url):
        """
        Given a url, saves an image and returns the path to that image.
        """
        pass

    def insert_location_info(self, location_string, delim1=self.address_delim,
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
        return insert_location_dict(self, param_dict)

    def insert_location_dict(self,  param_dict):
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
                event.description = description
            self.insert_attachments(event, vevent.contents['attach'])
