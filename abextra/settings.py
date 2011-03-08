# Django settings for abextra project.

# try to load local.settings used to override common settings
try:
    import settings_local
except ImportError:
    settings_local = None
    print u'File settings_local.py is not found. Continuing with production settings.'

ADMINS = (
    ('Pavel Katsev', 'pkatsev@abextratech.com'),
)
MANAGERS = ADMINS

DB_USER = getattr(settings_local, 'DB_USER', 'abex_dev')
DB_PASSWD = getattr(settings_local, 'DB_PASSWD', 'abex113')
DB_HOST = getattr(settings_local, 'DB_HOST', 'localhost')
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'abexmid',
        'USER': DB_USER,
        'PASSWORD': DB_PASSWD,
        'HOST': DB_HOST,                        # Set to empty string for localhost.
        'PORT': '',                             # Set to empty string for default.
    },
    'scrape': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'scrape',
        'USER': DB_USER,
        'PASSWORD': DB_PASSWD,
        'HOST': DB_HOST,                        # Set to empty string for localhost.
        'PORT': '',                             # Set to empty string for default.
    }
}

# don't run south migrations to setup test dbs
SOUTH_TESTS_MIGRATE = False

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# On Unix systems, a value of None will cause Django to use the same
# timezone as the operating system.
# If running in a Windows environment this must be set to the same as your
# system time zone.
TIME_ZONE = 'America/Chicago'

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'en-us'

SITE_ID = 1

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True

# If you set this to False, Django will not format dates, numbers and
# calendars according to the current locale
USE_L10N = True

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash if there is a path component (optional in other cases).
# Examples: "http://media.lawrence.com", "http://example.com/media/"
MEDIA_URL = '/static/'

# URL prefix for admin media -- CSS, JavaScript and images. Make sure to use a
# trailing slash.
# Examples: "http://foo.com/media/", "/media/".
ADMIN_MEDIA_PREFIX = '/media/'

# Make this unique, and don't share it with anybody.
SECRET_KEY = '3xh0mi2n)pvri!l^-8-@-xkjn^uc#q!79!yfdc-@qe&!4e4_em'

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    ('django.template.loaders.cached.Loader', (
        'django.template.loaders.filesystem.Loader',
        'django.template.loaders.app_directories.Loader',
        #     'django.template.loaders.eggs.Loader',
    )),
)

MIDDLEWARE_CLASSES = (
    'django.middleware.gzip.GZipMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    # 'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
)

ROOT_URLCONF = 'abextra.urls'

TEMPLATE_DIRS = (
    'templates',
    # Put strings here, like "/home/html/django_templates" or "C:/www/django/templates".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
)

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.messages',
    'django.contrib.admin',
    # 'django.contrib.admindocs',   # admin documentation
    'south',                        # migrations managements
    'registration',                 # user registration app
    'piston',                       # api assistance
    'behavior',                     # ABEX behavior | user actions
    'core',                         # ABEX core
    'events',                       # ABEX events
    'learning',                     # ABEX machine learning | recommendations
    'places',                       # ABEX places | helps normalize places
    'preprocess',                   # ABEX data preprocessing | scrape->django
    'prices',                       # ABEX prices
)

#########################
######### DEBUG #########
#########################

# assume that if local settings are present, that we're in dev debug mode
# TODO clearly needs refactoring, this belongs directly in the settings_local
DEBUG = bool(settings_local)
TEMPLATE_DEBUG = DEBUG
if TEMPLATE_DEBUG:
    # MIDDLEWARE_CLASSES += ('debug_toolbar.middleware.DebugToolbarMiddleware',)
    INSTALLED_APPS += ('debug_toolbar',)
    INTERNAL_IPS = ('127.0.0.1',)
    DEBUG_TOOLBAR_PANELS = (
        'debug_toolbar.panels.version.VersionDebugPanel',
        # 'debug_toolbar.panels.timer.TimerDebugPanel',
        # 'debug_toolbar.panels.settings_vars.SettingsVarsDebugPanel',
        # 'debug_toolbar.panels.headers.HeaderDebugPanel',
        # 'debug_toolbar.panels.request_vars.RequestVarsDebugPanel',
        # 'debug_toolbar.panels.template.TemplateDebugPanel',
        # 'debug_toolbar.panels.sql.SQLDebugPanel',
        # 'debug_toolbar.panels.signals.SignalDebugPanel',
        # 'debug_toolbar.panels.logger.LoggingPanel',
    )

import os
PROJECT_ROOT = os.path.dirname(__file__)
FIXTURE_DIRS = (
    os.path.join(PROJECT_ROOT,'fixtures'),
)

# Absolute filesystem path to the directory that will hold user-uploaded files.
# Example: "/home/media/media.lawrence.com/"
MEDIA_ROOT = os.path.join(PROJECT_ROOT, 'static')
STATIC_DOC_ROOT = MEDIA_ROOT


AUTOCOMPLETE_MEDIA_PREFIX = '/static/autocomplete/media/'

# FIXME this router breakes tests during fixture loading, don't really need it right now
# FIXME hence, this ugly face hack
# import sys
# if all(map(lambda cmd: not cmd in sys.argv, ('migrate', 'schemamigration', 'datamigration'))):
#     # custom db routers
#     DATABASE_ROUTERS = ['preprocess.routers.PreprocessRouter']
