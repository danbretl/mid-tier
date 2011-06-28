import boto
import sys, os
from boto.s3.key import Key

LOCAL_PATH = 'scrapes/'
AWS_ACCESS_KEY_ID = 'AKIAIZT6EDXBGOQARBPA'
AWS_SECRET_ACCESS_KEY = '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'

bucket_name = 'kwiqet'
# connect to the bucket
conn = boto.connect_s3(AWS_ACCESS_KEY_ID,
                AWS_SECRET_ACCESS_KEY)
bucket = conn.get_bucket(bucket_name)
# go through the list of files
for l in bucket:
  keyString = str(l.key)
  # check if file exists locally, if not: download it
  if not os.path.exists(LOCAL_PATH+keyString):
    l.get_contents_to_filename(LOCAL_PATH+keyString)
