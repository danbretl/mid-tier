"""Django settings for abextra project."""
import os

DEBUG = False
TEMPLATE_DEBUG = DEBUG

ADMINS = (
    ('Pavel Katsev', 'pkatsev@abextratech.com'),
    ('Rabi Alam', 'ralam@abextratech.com'),
)
MANAGERS = ADMINS

# db connections and credentials should be defined in higher-level settings
DATABASES = {
    'default': {
        'ENGINE': 'django.contrib.gis.db.backends.postgis',
        'NAME': 'kwiqet',
        'HOST': '',                     # Set to empty string for localhost.
        'PORT': '',                     # Set to empty string for default.
        'TEST_CHARSET': 'utf8',
    },
}

# FIXME this router breaks tests during fixture loading, don't really need it right now
# FIXME hence, this ugly face hack
# if all(map(lambda cmd: not cmd in sys.argv, ('migrate', 'schemamigration', 'datamigration'))):
#     # custom db routers
#     DATABASE_ROUTERS = ['preprocess.routers.PreprocessRouter']

# don't run south migrations to setup test dbs
SOUTH_TESTS_MIGRATE = False

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# On Unix systems, a value of None will cause Django to use the same
# timezone as the operating system.
# If running in a Windows environment this must be set to the same as your
# system time zone.
TIME_ZONE = 'America/New_York'

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

# Convenience variable for absolute path definitions to the project
PROJECT_ROOT = os.path.dirname(__file__)

# Absolute filesystem path to the directory that will hold user-uploaded files.
# Example: "/home/media/media.lawrence.com/"
MEDIA_ROOT = os.path.join(PROJECT_ROOT, 'media/')

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash if there is a path component (optional in other cases).
# Examples: "http://media.lawrence.com", "http://example.com/media/"
MEDIA_URL = '/site_media/media/'

# URL to use when referring to static files located in STATIC_ROOT.
# Example: "/site_media/static/" or "http://static.example.com/"
STATIC_ROOT = os.path.join(PROJECT_ROOT, 'static_root/')

# URL to use when referring to static files located in STATIC_ROOT.
# Example: "/site_media/static/" or "http://static.example.com/"
STATIC_URL = '/site_media/static/'

STATICFILES_DIRS = (
    os.path.join(PROJECT_ROOT, 'static/'),
)

# URL prefix for admin media -- CSS, JavaScript and images. Make sure to use a
# trailing slash.
# Examples: "http://foo.com/media/", "/media/".
ADMIN_MEDIA_PREFIX = STATIC_URL + 'admin/'

# URL that handles the autocomplete's required front-end resources
AUTOCOMPLETE_MEDIA_PREFIX = '/static/autocomplete/media/'

# Make this unique, and don't share it with anybody.
SECRET_KEY = '3xh0mi2n)pvri!l^-8-@-xkjn^uc#q!79!yfdc-@qe&!4e4_em'

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    # ('django.template.loaders.cached.Loader',
    #     (
            'django.template.loaders.filesystem.Loader',
            'django.template.loaders.app_directories.Loader',
            'django.template.loaders.eggs.Loader',
    #     )
    # ),
)

TEMPLATE_DIRS = (
    os.path.join(PROJECT_ROOT, 'templates'),
    # Put strings here, like "/home/html/django_templates"
    # Don't forget to use absolute paths, not relative paths.
)

AUTHENTICATION_BACKENDS = (
    'userena.backends.UserenaAuthenticationBackend',
    'guardian.backends.ObjectPermissionBackend',
    'django.contrib.auth.backends.ModelBackend',
)

AUTH_PROFILE_MODULE = 'accounts.UserProfile'

ANONYMOUS_USER_ID = -1

LOGIN_REDIRECT_URL = '/alpha/accounts/%(username)s/'
LOGIN_URL = '/alpha/accounts/signin/'
LOGOUT_URL = '/alpha/accounts/signout/'

USERENA_SIGNIN_REDIRECT_URL = LOGIN_REDIRECT_URL
USERENA_DEFAULT_PRIVACY = 'closed'
USERENA_WITHOUT_USERNAMES = True
USERENA_MUGSHOT_SIZE = 50

MIDDLEWARE_CLASSES = (
    'django.middleware.gzip.GZipMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
)

ROOT_URLCONF = 'abextra.urls'

FIXTURE_DIRS = (
    os.path.join(PROJECT_ROOT, 'fixtures'),
)

INSTALLED_APPS = (
    'django.contrib.auth',          # authentication
    'django.contrib.contenttypes',  # content types
    'django.contrib.sessions',      # sessions
    'django.contrib.sites',         # sites
    'django.contrib.messages',      # user messages
    'django.contrib.admin',         # admin
    'django.contrib.admindocs',     # admin documentation
    'django.contrib.comments',      # comments
    'django.contrib.staticfiles',   # statics
    'django.contrib.gis',           # gis

    'fabtastic',                    # deployments
    'fixture_magic',                # additional fixture commands
    'gunicorn',                     # gunicorn | app server
    'livesettings',                 # live settings ;)
    'sorl.thumbnail',               # thumbnails
    'south',                        # migrations managements
    'tastypie',                     # new api assistance
    'userena',                      # accounts and registration
    'guardian',                     # object level permissions  | userena dep
    'easy_thumbnails',              # thumbnails                | userena dep

    'voting',                       # django voting     | voice dep
    'gravatar',                     # django gravatar   | voice dep
    'djangovoice',                  # feedback and issue tracking

    'accounts',                     # ABEX user profile extensions
    'alphasignup',                  # ABEX simple web front for Alpha signup
    'api',                          # ABEX API models, resources and utils
    'behavior',                     # ABEX behavior | user actions
    'core',                         # ABEX core
    'events',                       # ABEX events
    'importer',                     # ABEX part of the scrape pipeline
    'learning',                     # ABEX machine learning | recommendations
    'places',                       # ABEX places | helps normalize places
    'preprocess',                   # ABEX data preprocessing | scrape->django
    'prices',                       # ABEX prices
    'pundit',                       # ABEX categorization of events
)

# ===========
# = Logging =
# ===========
LOGGING = {
    'version': 1,
    # 'disable_existing_loggers': True,
    'formatters': {
        'verbose': {
            'format': '%(levelname)s %(asctime)s %(module)s %(process)d %(thread)d %(message)s'
        },
        'simple': {
            'format': '%(levelname)s %(name)s %(message)s'
        },
    },
    'handlers': {
        'console':{
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'simple'
        },
        'mail_admins': {
            'level': 'ERROR',
            'class': 'django.utils.log.AdminEmailHandler',
        },
        'null': {
            'level': 'DEBUG',
            'class': 'django.utils.log.NullHandler',
        },
        'file':{
            'level' : 'INFO',
            'class' : 'logging.FileHandler',
            'filename': 'kwiqet.log'}
    },
    'loggers': {
        'django': {
             'handlers': ['console'],
             # 'propagate': True,
             'level': 'DEBUG',
        },
        # 'django.request': {
        #     'handlers': ['console'],
        #     'level': 'DEBUG',
        #     'propagate': False,
        # },
        'keyedcache': {
            'handlers': ['console'],
            'level': 'DEBUG',
        },
        'consumer.scrape': {
            'handlers': ['console'],
            'level': 'DEBUG',
        },
        'api.test' : {
            'handlers': ['console'],
            'level': 'DEBUG',
        },
        'importer.adaptor': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
        },
        'importer.api.eventful.utils': {
            'handlers': ['console'],
            'level': 'INFO',
        },
        'importer.api.eventful.paginator': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
        },
        'importer.api.eventful.consumer': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
        },
        'importer.api.eventful.client': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
        },
        'importer.api.eventful.adaptor': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
        },
    }
}

# ===============
# = Keyed Cache =
# ===============
CACHE_PREFIX = str(SITE_ID)
CACHE_TIMEOUT = 60              # 1 minute

# ==============================
# = Kwiqet specific settings =
# ==============================
IPHONE_THUMB_OPTIONS = {
    'geometry_string': '640x360',
    # 'reflection_amount': 0.2,
    # 'reflection_opacity': 0.8
}

# ==========
# = Import =
# ==========
IMPORT_ROOT_DIR = '/tmp/kwiqet_import'
IMPORT_IMAGE_DIR_DEFAULT = 'images'
IMPORT_IMAGE_MIN_DIMS = {'width': 320, 'height': 180}

