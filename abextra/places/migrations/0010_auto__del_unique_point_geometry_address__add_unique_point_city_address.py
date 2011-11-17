# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Removing unique constraint on 'City', fields ['slug']
        db.delete_unique('places_city', ['slug'])

        # Removing unique constraint on 'Point', fields ['geometry', 'address']
        db.delete_unique('places_point', ['geometry', 'address'])

        # Adding unique constraint on 'Point', fields ['city', 'address']
        db.create_unique('places_point', ['city_id', 'address'])

        # Changing field 'City.city'
        db.alter_column('places_city', 'city', self.gf('django.db.models.fields.CharField')(max_length=47))

        # Changing field 'City.slug'
        db.alter_column('places_city', 'slug', self.gf('autoslug.fields.AutoSlugField')(unique_with=(), max_length=50, populate_from=None))


    def backwards(self, orm):
        
        # Removing unique constraint on 'Point', fields ['city', 'address']
        db.delete_unique('places_point', ['city_id', 'address'])

        # Adding unique constraint on 'Point', fields ['geometry', 'address']
        db.create_unique('places_point', ['geometry', 'address'])

        # Changing field 'City.city'
        db.alter_column('places_city', 'city', self.gf('django.db.models.fields.CharField')(max_length=100))

        # Changing field 'City.slug'
        db.alter_column('places_city', 'slug', self.gf('django.db.models.fields.SlugField')(max_length=50, unique=True))

        # Adding unique constraint on 'City', fields ['slug']
        db.create_unique('places_city', ['slug'])


    models = {
        'places.city': {
            'Meta': {'unique_together': "(('city', 'state'),)", 'object_name': 'City'},
            'city': ('django.db.models.fields.CharField', [], {'max_length': '47'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'slug': ('autoslug.fields.AutoSlugField', [], {'unique_with': '()', 'max_length': '50', 'populate_from': 'None', 'db_index': 'True'}),
            'state': ('django.contrib.localflavor.us.models.USStateField', [], {'max_length': '2'})
        },
        'places.place': {
            'Meta': {'ordering': "('title',)", 'unique_together': "(('point', 'title'),)", 'object_name': 'Place'},
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'image': ('sorl.thumbnail.fields.ImageField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'image_url': ('django.db.models.fields.URLField', [], {'max_length': '200', 'blank': 'True'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'nickname': ('django.db.models.fields.CharField', [], {'max_length': '100', 'blank': 'True'}),
            'phone': ('django.contrib.localflavor.us.models.PhoneNumberField', [], {'max_length': '20', 'blank': 'True'}),
            'place_types': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['places.PlaceType']", 'symmetrical': 'False', 'blank': 'True'}),
            'point': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['places.Point']"}),
            'prefix': ('django.db.models.fields.CharField', [], {'max_length': '20', 'blank': 'True'}),
            'slug': ('django.db.models.fields.SlugField', [], {'max_length': '50', 'db_index': 'True'}),
            'status': ('django.db.models.fields.IntegerField', [], {'default': '1'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'unit': ('django.db.models.fields.CharField', [], {'max_length': '100', 'blank': 'True'}),
            'url': ('django.db.models.fields.URLField', [], {'max_length': '200', 'blank': 'True'})
        },
        'places.placetype': {
            'Meta': {'object_name': 'PlaceType'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'slug': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'max_length': '50', 'db_index': 'True'}),
            'title': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '100'})
        },
        'places.point': {
            'Meta': {'ordering': "('address',)", 'unique_together': "(('address', 'city'),)", 'object_name': 'Point'},
            'address': ('django.db.models.fields.CharField', [], {'max_length': '200', 'blank': 'True'}),
            'city': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['places.City']"}),
            'country': ('django.db.models.fields.CharField', [], {'max_length': '100', 'blank': 'True'}),
            'geometry': ('django.contrib.gis.db.models.fields.PointField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'zip': ('django.db.models.fields.CharField', [], {'max_length': '10', 'blank': 'True'})
        }
    }

    complete_apps = ['places']
