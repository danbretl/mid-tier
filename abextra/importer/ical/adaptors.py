from importer.adaptors import BaseAdaptor
from events.forms import OccurrenceImportForm

# ========
# = Base =
# ========

class ICalBaseAdaptor(BaseAdaptor):
    source_name = 'iCal'

# ==========
# = Events =
# ==========

class OccurrenceAdaptor(ICalBaseAdaptor):
    model_form = OccurrenceImportForm

    def adapt_form_data_many(self, vobject):
        for vevent in vobject.contents['vevent']:
            form_data = {
                'start_date': vevent.dtstart.value.date(),
                'start_time': vevent.dtstart.value.time(),
                'end_date': vevent.dtend.value.date(),
                'end_time': vevent.dtend.value.time(),
                'is_all_day': None,
            }
            yield form_data

