from django.utils.translation import ugettext_lazy as _
from livesettings import ConfigurationGroup, PositiveIntegerValue, config_register

EVENT_GROUP = ConfigurationGroup('EVENTS',
    _('Event module settings'),
    ordering = 0
)

config_register(
    PositiveIntegerValue(EVENT_GROUP, 'FEATURED_EVENT_ID',
        description=_("Featured Event"),
        help_text=_("Primary key of the featured event"),
        default=1
    )
)
