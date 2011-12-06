"""
API stress test using FunkLoad
"""

import time
import urllib
import unittest
from funkload.FunkLoadTestCase import FunkLoadTestCase

from utils import build_url
from api.conf import TEST_CONSUMER_SECRET, TEST_CONSUMER_KEY

class CategoryStressTest(FunkLoadTestCase):
    """Simple stress test on lightweight category endpoint"""
    endpoint = 'category' 

    def setUp(self):
        self.server_url = self.conf_get('main', 'url')
        self.encoded_params = '?'
        self.encoded_params += urllib.urlencode({'consumer_key': TEST_CONSUMER_KEY,
                                            'consumer_secret': TEST_CONSUMER_SECRET,
                                            'udid': '6AAD4638-7E07-5A5C-A676-3D16E4AFFAF3',
                                            'format': 'json'
        })

    def test_get(self):
        """ Hit some endpoint nb_times"""

        nb_time = self.conf_getInt('test_get', 'nb_time')
        url = self.server_url + build_url(self.endpoint) + self.encoded_params
        for i in range(nb_time):
            self.get(url, description='Getting endpoint %s, iteration %i of %i' %
                    (self.endpoint, i, nb_time))

if __name__ in ('main', '__main__'):
    unittest.main()
