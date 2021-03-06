import boto
import sys, os
from boto.s3.key import Key

from django.core.management.base import NoArgsCommand
from django.conf import settings

class Command(NoArgsCommand):
    help = 'Loads scraped object generated by scrapy'

    def handle_noargs(self, **options):
        bucket_name = 'kwiqet'

        # connect to the bucket
        conn = boto.connect_s3(
            settings.AWS_ACCESS_KEY_ID, settings.AWS_SECRET_ACCESS_KEY
        )
        bucket = conn.get_bucket(bucket_name)

        # go through the list of files
        for l in bucket:
            keyString = str(l.key).partition('scrapes/')[-1]
            # check if file exists locally, if not: download it
            path = os.path.join(settings.SCRAPE_FEED_PATH, keyString)
            if not os.path.exists(path):
                # create necessary dirs
                dirname = os.path.dirname(path)
                if not os.path.exists(dirname):
                    os.makedirs(dirname)

                # copy the s3 contents
                print path
                l.get_contents_to_filename(path)
