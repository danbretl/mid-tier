from django.utils.translation import ugettext_lazy as _
from livesettings import ConfigurationGroup, PositiveIntegerValue, config_register

ALPHA_GROUP = ConfigurationGroup('ALPHA',
    _('Alpha module settings'),
    ordering = 0
)

config_register(
    PositiveIntegerValue(ALPHA_GROUP, 'APP_DIST_ID',
        description=_("Current Application Distribution Id"),
        help_text=_("Primary key of the application distribution wrapper"),
        default=1
    )
)
