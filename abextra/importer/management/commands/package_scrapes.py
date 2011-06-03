"""
Author: Vikas Menon
"""

from django.core.management.base import NoArgsCommand
from django.conf import settings
import tarfile
from datetime import datetime
import os

class Command(NoArgsCommand):
    help = 'Generates a tar.gz package of a scrapy crawl'

    def handle_noargs(self, **options):
        file_name = datetime.now().strftime('scrape-%m.%d.%y-%H.%M.%S.tar.gz')
        images_folder = settings.SCRAPE_IMAGES_PATH
        tar = tarfile.open(file_name, 'w:gz')
        files_list = os.listdir(images_folder)
        for file_to_tar in files_list:
            tar.add(os.path.join(images_folder, file_to_tar),
                    'SCRAPE_IMAGES_PATH/' + file_to_tar)
        tar.add(settings.SCRAPE_FEED_PATH, 'SCRAPE_FEED_PATH')
        tar.close()

