"""
Author: Vikas Menon
"""

from django.core.management.base import LabelCommand
import tarfile
import tempfile
import settings_local
import shutil
from importer.parsers.event import EventParser
from importer.consumer import ScrapeFeedConsumer

class Command(LabelCommand):
    help = 'Unpacks and optionall loads a packaged scrape into local DB'

    def handle_label(self, label, **options):
        self.unpack_load_data_temp(label)

    def unpack_load_data_temp(self, label):
        temp_dir = tempfile.mkdtemp()
        tar = tarfile.open(label)
        tar.extractall(temp_dir)
        settings_local.SCRAPE_FEED_PATH = temp_dir + '/SCRAPE_FEED_PATH'
        settings_local.SCRAPE_IMAGES_PATH = temp_dir + '/full/'
        consumer = ScrapeFeedConsumer()
        parser = EventParser()
        for event in consumer.events():
            parser.parse(event)
        #delete temporary directory
        shutil.rmtree(temp_dir)



