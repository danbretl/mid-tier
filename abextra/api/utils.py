from django.conf import settings

from sorl.thumbnail import get_thumbnail

def get_iphone_thumb(my_file, **options):
    return get_thumbnail(my_file,
        geometry_string=settings.IPHONE_THUMB_GEOMETRY, **options
    )
