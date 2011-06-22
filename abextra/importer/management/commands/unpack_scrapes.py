"""
Author: Vikas Menon
"""

from django.core.management.base import LabelCommand
import tarfile
import tempfile
import os
from django.conf import settings
import shutil
from importer.parsers.event import EventParser
from importer.consumer import ScrapeFeedConsumer

class Command(LabelCommand):
    help = 'Unpacks and optionally loads a packaged scrape into local DB'

    def handle_label(self, label, **options):
        self.unpack_load_data_temp(label)

    def unpack_load_data_temp(self, label):
        temp_dir = tempfile.mkdtemp()
        tar = tarfile.open(label)
        tar.extractall(temp_dir)
        settings.SCRAPE_FEED_PATH = temp_dir + '/SCRAPE_FEED_PATH'
        settings.SCRAPE_IMAGES_PATH = os.path.join(temp_dir,
                                                   'SCRAPE_IMAGES_PATH')
        consumer = ScrapeFeedConsumer()
        parser = EventParser()
        for event in consumer.events():
            parser.parse(event)
        #delete temporary directory
        shutil.rmtree(temp_dir)



