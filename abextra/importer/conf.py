import os
from django.conf import settings

def get_import_image_dir(source_name):
    """return the full path to raw imported images"""
    return os.path.join(
        settings.IMPORT_ROOT_DIR,
        settings.IMPORT_DIRS[source_name],
        settings.IMPORT_IMAGE_DIRS.get(source_name, settings.IMPORT_IMAGE_DIR_DEFAULT)
    )
