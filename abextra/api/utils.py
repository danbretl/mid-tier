from django.conf import settings

from sorl.thumbnail import get_thumbnail

def get_iphone_thumb(my_file):
    return get_thumbnail(my_file, **settings.IPHONE_THUMB_OPTIONS)
