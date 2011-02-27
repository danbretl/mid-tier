# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding model 'Source'
        db.create_table('preprocess_source', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(unique=True, max_length=50)),
            ('domain', self.gf('django.db.models.fields.CharField')(max_length=100)),
        ))
        db.send_create_signal('preprocess', ['Source'])

        # Adding model 'ExternalCategory'
        db.create_table('preprocess_externalcategory', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('xid', self.gf('django.db.models.fields.CharField')(max_length=300)),
            ('source', self.gf('django.db.models.fields.related.ForeignKey')(related_name='external_categories', to=orm['preprocess.Source'])),
            ('category', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='external_categories', null=True, to=orm['events.Category'])),
        ))
        db.send_create_signal('preprocess', ['ExternalCategory'])

        # Adding unique constraint on 'ExternalCategory', fields ['name', 'source']
        db.create_unique('preprocess_externalcategory', ['name', 'source_id'])


    def backwards(self, orm):
        
        # Removing unique constraint on 'ExternalCategory', fields ['name', 'source']
        db.delete_unique('preprocess_externalcategory', ['name', 'source_id'])

        # Deleting model 'Source'
        db.delete_table('preprocess_source')

        # Deleting model 'ExternalCategory'
        db.delete_table('preprocess_externalcategory')


    models = {
        'events.category': {
            'Meta': {'object_name': 'Category'},
            'association_coefficient': ('django.db.models.fields.FloatField', [], {'default': '0'}),
            'category_type': ('django.db.models.fields.CharField', [], {'max_length': '1'}),
            'color': ('django.db.models.fields.CharField', [], {'max_length': '7', 'blank': 'True'}),
            'icon': ('django.db.models.fields.files.ImageField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'icon_height': ('django.db.models.fields.PositiveSmallIntegerField', [], {'null': 'True', 'blank': 'True'}),
            'icon_width': ('django.db.models.fields.PositiveSmallIntegerField', [], {'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_associative': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'parent': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'subcategories'", 'null': 'True', 'to': "orm['events.Category']"}),
            'slug': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'max_length': '50', 'db_index': 'True'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'preprocess.costs': {
            'Meta': {'object_name': 'Costs', 'db_table': "u'costs'", 'managed': 'False'},
            'id': ('django.db.models.fields.IntegerField', [], {'primary_key': 'True'}),
            'occurrence': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'costs'", 'to': "orm['preprocess.Occurrences']"}),
            'price': ('django.db.models.fields.CharField', [], {'max_length': '300', 'blank': 'True'}),
            'remark': ('django.db.models.fields.CharField', [], {'max_length': '300', 'blank': 'True'})
        },
        'preprocess.events': {
            'Meta': {'object_name': 'Events', 'db_table': "u'events'", 'managed': 'False'},
            'description': ('django.db.models.fields.CharField', [], {'max_length': '27000', 'blank': 'True'}),
            'id': ('django.db.models.fields.IntegerField', [], {'primary_key': 'True'}),
            'image_url': ('django.db.models.fields.CharField', [], {'max_length': '1800', 'blank': 'True'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '1800', 'blank': 'True'}),
            'url': ('django.db.models.fields.CharField', [], {'max_length': '1800', 'blank': 'True'}),
            'video_url': ('django.db.models.fields.CharField', [], {'max_length': '1800', 'blank': 'True'}),
            'xid': ('django.db.models.fields.CharField', [], {'max_length': '300', 'blank': 'True'})
        },
        'preprocess.externalcategory': {
            'Meta': {'unique_together': "(('name', 'source'),)", 'object_name': 'ExternalCategory'},
            'category': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'external_categories'", 'null': 'True', 'to': "orm['events.Category']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'source': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'external_categories'", 'to': "orm['preprocess.Source']"}),
            'xid': ('django.db.models.fields.CharField', [], {'max_length': '300'})
        },
        'preprocess.occurrences': {
            'Meta': {'object_name': 'Occurrences', 'db_table': "u'occurrences'", 'managed': 'False'},
            'end_date': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'end_time': ('django.db.models.fields.TimeField', [], {'blank': 'True'}),
            'event': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'occurrences'", 'to': "orm['preprocess.Events']"}),
            'id': ('django.db.models.fields.IntegerField', [], {'primary_key': 'True'}),
            'location': ('django.db.models.fields.CharField', [], {'max_length': '1800', 'blank': 'True'}),
            'start_date': ('django.db.models.fields.DateField', [], {}),
            'start_time': ('django.db.models.fields.TimeField', [], {'blank': 'True'}),
            'timestamp': ('django.db.models.fields.DateTimeField', [], {})
        },
        'preprocess.scrapedevent': {
            'Meta': {'object_name': 'ScrapedEvent', 'db_table': "u'scraped_events_vw'", 'managed': 'False'},
            'cost': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'db_column': "'Cost'", 'blank': 'True'}),
            'description': ('django.db.models.fields.CharField', [], {'max_length': '9000', 'db_column': "'Description'", 'blank': 'True'}),
            'email': ('django.db.models.fields.CharField', [], {'max_length': '150', 'db_column': "'Email'", 'blank': 'True'}),
            'endtime': ('django.db.models.fields.TimeField', [], {'db_column': "'EndTime'"}),
            'eventdate': ('django.db.models.fields.DateField', [], {'null': 'True', 'db_column': "'EventDate'", 'blank': 'True'}),
            'eventhighlight': ('django.db.models.fields.CharField', [], {'max_length': '150', 'db_column': "'EventHighlight'", 'blank': 'True'}),
            'eventorganizer': ('django.db.models.fields.CharField', [], {'max_length': '150', 'db_column': "'EventOrganizer'", 'blank': 'True'}),
            'externalid': ('django.db.models.fields.CharField', [], {'max_length': '90', 'db_column': "'ExternalID'", 'blank': 'True'}),
            'imageurl': ('django.db.models.fields.CharField', [], {'max_length': '600', 'db_column': "'ImageURL'", 'blank': 'True'}),
            'internalid': ('django.db.models.fields.IntegerField', [], {'primary_key': 'True', 'db_column': "'InternalID'"}),
            'last_modified': ('django.db.models.fields.DateTimeField', [], {'db_column': "'Last_Modified'"}),
            'location': ('django.db.models.fields.CharField', [], {'max_length': '600', 'db_column': "'Location'", 'blank': 'True'}),
            'phone': ('django.db.models.fields.CharField', [], {'max_length': '45', 'db_column': "'Phone'", 'blank': 'True'}),
            'starttime': ('django.db.models.fields.TimeField', [], {'db_column': "'StartTime'"}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '600', 'db_column': "'Title'", 'blank': 'True'}),
            'url': ('django.db.models.fields.CharField', [], {'max_length': '600', 'db_column': "'URL'", 'blank': 'True'}),
            'videourl': ('django.db.models.fields.CharField', [], {'max_length': '600', 'db_column': "'VideoURL'", 'blank': 'True'})
        },
        'preprocess.source': {
            'Meta': {'object_name': 'Source'},
            'domain': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '50'})
        }
    }

    complete_apps = ['preprocess']
