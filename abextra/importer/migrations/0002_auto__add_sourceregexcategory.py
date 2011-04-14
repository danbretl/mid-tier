# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding model 'SourceRegexCategory'
        db.create_table('importer_sourceregexcategory', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('source', self.gf('django.db.models.fields.related.ForeignKey')(related_name='source_regex_categories', to=orm['events.Source'])),
            ('regex', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('category', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='source_regex_categories', null=True, to=orm['events.Category'])),
        ))
        db.send_create_signal('importer', ['SourceRegexCategory'])


    def backwards(self, orm):
        
        # Deleting model 'SourceRegexCategory'
        db.delete_table('importer_sourceregexcategory')


    models = {
        'events.category': {
            'Meta': {'ordering': "['title']", 'object_name': 'Category'},
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
        'events.source': {
            'Meta': {'object_name': 'Source'},
            'default_abstract_categories': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'sources_with_default_abstract'", 'symmetrical': 'False', 'to': "orm['events.Category']"}),
            'default_concrete_category': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'sources_with_default_concrete'", 'to': "orm['events.Category']"}),
            'domain': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '50'})
        },
        'importer.externalcategory': {
            'Meta': {'unique_together': "(('name', 'source'),)", 'object_name': 'ExternalCategory'},
            'category': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'external_categories'", 'null': 'True', 'to': "orm['events.Category']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'source': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'external_categories'", 'to': "orm['events.Source']"}),
            'xid': ('django.db.models.fields.CharField', [], {'max_length': '300'})
        },
        'importer.sourceregexcategory': {
            'Meta': {'object_name': 'SourceRegexCategory'},
            'category': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'source_regex_categories'", 'null': 'True', 'to': "orm['events.Category']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'regex': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'source': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'source_regex_categories'", 'to': "orm['events.Source']"})
        }
    }

    complete_apps = ['importer']
