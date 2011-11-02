from django.contrib.gis import geos
from django.test import TestCase
from places.models import City
from places.forms import PointImportForm

class PointImportFormTest(TestCase):

    def setUp(self):
        city, created = City.objects.get_or_create(city='Queens', state='NY')
        self.base_data = dict(
            city=city.id,
            address='Broadway and 42nd St.',
            country='US'
        )

    def test_geometry_geocode(self):
        lat, lon = 40.758224, -73.917404
        data = dict(self.base_data, **dict(latitude=str(lat), longitude=str(lon)))
        form = PointImportForm(data=data)
        self.assertTrue(form.is_valid(), 'Form invalid')
        point = form.save()
        self.assertTrue(point.id, 'Point not properly persisted')
        self.assertEqual(geos.Point(lon, lat), point.geometry, 'Unexpected point geometry')
        self.assertEqual('11103', point.zip, 'Incorrect zipcode reverse geocode')
