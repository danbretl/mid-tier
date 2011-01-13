# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding model 'PlaceType'
        db.create_table('place_types', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('title', self.gf('django.db.models.fields.CharField')(unique=True, max_length=100)),
            ('slug', self.gf('django.db.models.fields.SlugField')(unique=True, max_length=50, db_index=True)),
        ))
        db.send_create_signal('places', ['PlaceType'])

        # Adding model 'City'
        db.create_table('place_cities', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('city', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('state', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('slug', self.gf('django.db.models.fields.SlugField')(unique=True, max_length=50, db_index=True)),
        ))
        db.send_create_signal('places', ['City'])

        # Adding unique constraint on 'City', fields ['city', 'state']
        db.create_unique('place_cities', ['city', 'state'])

        # Adding model 'Point'
        db.create_table('place_points', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('latitude', self.gf('django.db.models.fields.FloatField')(null=True, blank=True)),
            ('longitude', self.gf('django.db.models.fields.FloatField')(null=True, blank=True)),
            ('address', self.gf('django.db.models.fields.CharField')(max_length=200, blank=True)),
            ('city', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['places.City'])),
            ('zip', self.gf('django.db.models.fields.CharField')(max_length=10, blank=True)),
            ('country', self.gf('django.db.models.fields.CharField')(max_length=100, blank=True)),
        ))
        db.send_create_signal('places', ['Point'])

        # Adding model 'Place'
        db.create_table('places', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('point', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['places.Point'])),
            ('prefix', self.gf('django.db.models.fields.CharField')(max_length=20, blank=True)),
            ('title', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('slug', self.gf('django.db.models.fields.SlugField')(max_length=50, db_index=True)),
            ('nickname', self.gf('django.db.models.fields.CharField')(max_length=100, blank=True)),
            ('unit', self.gf('django.db.models.fields.CharField')(max_length=100, blank=True)),
            ('phone', self.gf('django.contrib.localflavor.us.models.PhoneNumberField')(max_length=20, blank=True)),
            ('url', self.gf('django.db.models.fields.URLField')(max_length=200, blank=True)),
            ('email', self.gf('django.db.models.fields.EmailField')(max_length=75, blank=True)),
            ('description', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('status', self.gf('django.db.models.fields.IntegerField')(default=1)),
            ('created', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('modified', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
        ))
        db.send_create_signal('places', ['Place'])

        # Adding M2M table for field place_types on 'Place'
        db.create_table('places_place_types', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('place', models.ForeignKey(orm['places.place'], null=False)),
            ('placetype', models.ForeignKey(orm['places.placetype'], null=False))
        ))
        db.create_unique('places_place_types', ['place_id', 'placetype_id'])


    def backwards(self, orm):
        
        # Removing unique constraint on 'City', fields ['city', 'state']
        db.delete_unique('place_cities', ['city', 'state'])

        # Deleting model 'PlaceType'
        db.delete_table('place_types')

        # Deleting model 'City'
        db.delete_table('place_cities')

        # Deleting model 'Point'
        db.delete_table('place_points')

        # Deleting model 'Place'
        db.delete_table('places')

        # Removing M2M table for field place_types on 'Place'
        db.delete_table('places_place_types')


    models = {
        'places.city': {
            'Meta': {'ordering': "('state', 'city')", 'unique_together': "(('city', 'state'),)", 'object_name': 'City', 'db_table': "'place_cities'"},
            'city': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'slug': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'max_length': '50', 'db_index': 'True'}),
            'state': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'places.place': {
            'Meta': {'ordering': "('title',)", 'object_name': 'Place', 'db_table': "'places'"},
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
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
            'Meta': {'object_name': 'PlaceType', 'db_table': "'place_types'"},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'slug': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'max_length': '50', 'db_index': 'True'}),
            'title': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '100'})
        },
        'places.point': {
            'Meta': {'ordering': "('address',)", 'object_name': 'Point', 'db_table': "'place_points'"},
            'address': ('django.db.models.fields.CharField', [], {'max_length': '200', 'blank': 'True'}),
            'city': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['places.City']"}),
            'country': ('django.db.models.fields.CharField', [], {'max_length': '100', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'latitude': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'longitude': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'zip': ('django.db.models.fields.CharField', [], {'max_length': '10', 'blank': 'True'})
        }
    }

    complete_apps = ['places']
