# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Deleting field 'EventSummary.date_range'
        db.delete_column('events_eventsummary', 'date_range')

        # Deleting field 'EventSummary.place'
        db.delete_column('events_eventsummary', 'place')

        # Deleting field 'EventSummary.time'
        db.delete_column('events_eventsummary', 'time')

        # Deleting field 'EventSummary.price_range'
        db.delete_column('events_eventsummary', 'price_range')

        # Deleting field 'EventSummary.title'
        db.delete_column('events_eventsummary', 'title')

        # Deleting field 'EventSummary.concrete_category'
        db.delete_column('events_eventsummary', 'concrete_category_id')

        # Adding field 'EventSummary.event'
        db.add_column('events_eventsummary', 'event', self.gf('django.db.models.fields.related.OneToOneField')(default=0, to=orm['events.Event'], unique=True), keep_default=False)

        # Adding field 'EventSummary.occurrence_count'
        db.add_column('events_eventsummary', 'occurrence_count', self.gf('django.db.models.fields.IntegerField')(default=0), keep_default=False)

        # Adding field 'EventSummary.start_date_earliest'
        db.add_column('events_eventsummary', 'start_date_earliest', self.gf('django.db.models.fields.DateField')(default=datetime.date(2011, 4, 7)), keep_default=False)

        # Adding field 'EventSummary.start_date_latest'
        db.add_column('events_eventsummary', 'start_date_latest', self.gf('django.db.models.fields.DateField')(null=True, blank=True), keep_default=False)

        # Adding field 'EventSummary.start_date_distinct_count'
        db.add_column('events_eventsummary', 'start_date_distinct_count', self.gf('django.db.models.fields.IntegerField')(default=0), keep_default=False)

        # Adding field 'EventSummary.start_time_earliest'
        db.add_column('events_eventsummary', 'start_time_earliest', self.gf('django.db.models.fields.TimeField')(null=True, blank=True), keep_default=False)

        # Adding field 'EventSummary.start_time_latest'
        db.add_column('events_eventsummary', 'start_time_latest', self.gf('django.db.models.fields.TimeField')(null=True, blank=True), keep_default=False)

        # Adding field 'EventSummary.start_time_distinct_count'
        db.add_column('events_eventsummary', 'start_time_distinct_count', self.gf('django.db.models.fields.IntegerField')(default=0), keep_default=False)

        # Adding field 'EventSummary.price_quantity_min'
        db.add_column('events_eventsummary', 'price_quantity_min', self.gf('django.db.models.fields.FloatField')(null=True), keep_default=False)

        # Adding field 'EventSummary.price_quantity_max'
        db.add_column('events_eventsummary', 'price_quantity_max', self.gf('django.db.models.fields.FloatField')(null=True), keep_default=False)

        # Adding field 'EventSummary.place_title'
        db.add_column('events_eventsummary', 'place_title', self.gf('django.db.models.fields.CharField')(default='', max_length=255, blank=True), keep_default=False)

        # Adding field 'EventSummary.place_address'
        db.add_column('events_eventsummary', 'place_address', self.gf('django.db.models.fields.CharField')(default='', max_length=200, blank=True), keep_default=False)

        # Adding field 'EventSummary.place_distinct_count'
        db.add_column('events_eventsummary', 'place_distinct_count', self.gf('django.db.models.fields.IntegerField')(default=0), keep_default=False)

        # Deleting field 'Event.summary'
        db.delete_column('events_event', 'summary_id')


    def backwards(self, orm):
        
        # Adding field 'EventSummary.date_range'
        db.add_column('events_eventsummary', 'date_range', self.gf('django.db.models.fields.CharField')(default='', max_length=25, blank=True), keep_default=False)

        # Adding field 'EventSummary.place'
        db.add_column('events_eventsummary', 'place', self.gf('django.db.models.fields.CharField')(default='', max_length=200, blank=True), keep_default=False)

        # Adding field 'EventSummary.time'
        db.add_column('events_eventsummary', 'time', self.gf('django.db.models.fields.CharField')(default='', max_length=25, blank=True), keep_default=False)

        # Adding field 'EventSummary.price_range'
        db.add_column('events_eventsummary', 'price_range', self.gf('django.db.models.fields.CharField')(default='', max_length=25, blank=True), keep_default=False)

        # User chose to not deal with backwards NULL issues for 'EventSummary.title'
        raise RuntimeError("Cannot reverse this migration. 'EventSummary.title' and its values cannot be restored.")

        # User chose to not deal with backwards NULL issues for 'EventSummary.concrete_category'
        raise RuntimeError("Cannot reverse this migration. 'EventSummary.concrete_category' and its values cannot be restored.")

        # Deleting field 'EventSummary.event'
        db.delete_column('events_eventsummary', 'event_id')

        # Deleting field 'EventSummary.occurrence_count'
        db.delete_column('events_eventsummary', 'occurrence_count')

        # Deleting field 'EventSummary.start_date_earliest'
        db.delete_column('events_eventsummary', 'start_date_earliest')

        # Deleting field 'EventSummary.start_date_latest'
        db.delete_column('events_eventsummary', 'start_date_latest')

        # Deleting field 'EventSummary.start_date_distinct_count'
        db.delete_column('events_eventsummary', 'start_date_distinct_count')

        # Deleting field 'EventSummary.start_time_earliest'
        db.delete_column('events_eventsummary', 'start_time_earliest')

        # Deleting field 'EventSummary.start_time_latest'
        db.delete_column('events_eventsummary', 'start_time_latest')

        # Deleting field 'EventSummary.start_time_distinct_count'
        db.delete_column('events_eventsummary', 'start_time_distinct_count')

        # Deleting field 'EventSummary.price_quantity_min'
        db.delete_column('events_eventsummary', 'price_quantity_min')

        # Deleting field 'EventSummary.price_quantity_max'
        db.delete_column('events_eventsummary', 'price_quantity_max')

        # Deleting field 'EventSummary.place_title'
        db.delete_column('events_eventsummary', 'place_title')

        # Deleting field 'EventSummary.place_address'
        db.delete_column('events_eventsummary', 'place_address')

        # Deleting field 'EventSummary.place_distinct_count'
        db.delete_column('events_eventsummary', 'place_distinct_count')

        # Adding field 'Event.summary'
        db.add_column('events_event', 'summary', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['events.EventSummary'], unique=True, null=True), keep_default=False)


    models = {
        'auth.group': {
            'Meta': {'object_name': 'Group'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'})
        },
        'auth.permission': {
            'Meta': {'ordering': "('content_type__app_label', 'content_type__model', 'codename')", 'unique_together': "(('content_type', 'codename'),)", 'object_name': 'Permission'},
            'codename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        'auth.user': {
            'Meta': {'object_name': 'User'},
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Group']", 'symmetrical': 'False', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'})
        },
        'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'events.category': {
            'Meta': {'object_name': 'Category'},
            'association_coefficient': ('django.db.models.fields.FloatField', [], {'default': '0'}),
            'category_type': ('django.db.models.fields.CharField', [], {'max_length': '1'}),
            'color': ('django.db.models.fields.CharField', [], {'max_length': '7', 'blank': 'True'}),
            'icon': ('sorl.thumbnail.fields.ImageField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_associative': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'parent': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'subcategories'", 'null': 'True', 'to': "orm['events.Category']"}),
            'slug': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'max_length': '50', 'db_index': 'True'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'events.event': {
            'Meta': {'object_name': 'Event'},
            'categories': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'events_abstract'", 'symmetrical': 'False', 'to': "orm['events.Category']"}),
            'concrete_category': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'events_concrete'", 'to': "orm['events.Category']"}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'image': ('sorl.thumbnail.fields.ImageField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'image_url': ('django.db.models.fields.URLField', [], {'max_length': '300', 'blank': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'slug': ('django.db.models.fields.SlugField', [], {'max_length': '50', 'db_index': 'True'}),
            'submitted_by': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']", 'null': 'True', 'blank': 'True'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'url': ('django.db.models.fields.URLField', [], {'max_length': '300'}),
            'video_url': ('django.db.models.fields.URLField', [], {'max_length': '200', 'blank': 'True'}),
            'xid': ('django.db.models.fields.CharField', [], {'max_length': '200', 'blank': 'True'})
        },
        'events.eventsummary': {
            'Meta': {'object_name': 'EventSummary'},
            'event': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['events.Event']", 'unique': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'occurrence_count': ('django.db.models.fields.IntegerField', [], {}),
            'place_address': ('django.db.models.fields.CharField', [], {'max_length': '200', 'blank': 'True'}),
            'place_distinct_count': ('django.db.models.fields.IntegerField', [], {}),
            'place_title': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'price_quantity_max': ('django.db.models.fields.FloatField', [], {'null': 'True'}),
            'price_quantity_min': ('django.db.models.fields.FloatField', [], {'null': 'True'}),
            'start_date_distinct_count': ('django.db.models.fields.IntegerField', [], {}),
            'start_date_earliest': ('django.db.models.fields.DateField', [], {}),
            'start_date_latest': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'start_time_distinct_count': ('django.db.models.fields.IntegerField', [], {}),
            'start_time_earliest': ('django.db.models.fields.TimeField', [], {'null': 'True', 'blank': 'True'}),
            'start_time_latest': ('django.db.models.fields.TimeField', [], {'null': 'True', 'blank': 'True'})
        },
        'events.occurrence': {
            'Meta': {'object_name': 'Occurrence'},
            'end_date': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'end_time': ('django.db.models.fields.TimeField', [], {'null': 'True', 'blank': 'True'}),
            'event': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'occurrences'", 'to': "orm['events.Event']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_all_day': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'one_off_place': ('django.db.models.fields.CharField', [], {'max_length': '200', 'blank': 'True'}),
            'place': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'occurrences'", 'to': "orm['places.Place']"}),
            'start_date': ('django.db.models.fields.DateField', [], {}),
            'start_time': ('django.db.models.fields.TimeField', [], {'null': 'True', 'blank': 'True'})
        },
        'places.city': {
            'Meta': {'ordering': "('state', 'city')", 'unique_together': "(('city', 'state'),)", 'object_name': 'City'},
            'city': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'slug': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'max_length': '50', 'db_index': 'True'}),
            'state': ('django.contrib.localflavor.us.models.USStateField', [], {'max_length': '2'})
        },
        'places.place': {
            'Meta': {'ordering': "('title',)", 'object_name': 'Place'},
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
            'Meta': {'ordering': "('address',)", 'object_name': 'Point'},
            'address': ('django.db.models.fields.CharField', [], {'max_length': '200', 'blank': 'True'}),
            'city': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['places.City']"}),
            'country': ('django.db.models.fields.CharField', [], {'max_length': '100', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'latitude': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'longitude': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'zip': ('django.db.models.fields.CharField', [], {'max_length': '10', 'blank': 'True'})
        }
    }

    complete_apps = ['events']
