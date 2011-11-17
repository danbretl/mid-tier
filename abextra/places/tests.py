from django.contrib.gis import geos
from django.core.exceptions import ValidationError
from django.test import TestCase
from places.models import City
from places.forms import PointImportForm
from django_dynamic_fixture import get, new

class CityTest(TestCase):
    def setUp(self):
        self.data = dict(city='New York', state='NY')

    def test_autoslug(self):
        city = City.objects.create(**self.data)
        self.assertEquals('new-york-ny', city.slug, 'Unexpected slug value')

    def test_uniqueness(self):
        City(**self.data).save()
        city = City(**self.data)
        self.assertRaises(ValidationError, city.validate_unique)

class PointTest(TestCase):
    def setUp(self):
        self.data = dict()

    def test_uniqueness(self):


class PointImportFormTest(TestCase):

    def setUp(self):
        city = get(City, city='Queens', state='NY')
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
