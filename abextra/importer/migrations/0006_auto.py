# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding M2M table for field abstract_categories on 'ExternalCategory'
        db.create_table('importer_externalcategory_abstract_categories', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('externalcategory', models.ForeignKey(orm['importer.externalcategory'], null=False)),
            ('category', models.ForeignKey(orm['events.category'], null=False))
        ))
        db.create_unique('importer_externalcategory_abstract_categories', ['externalcategory_id', 'category_id'])


    def backwards(self, orm):
        
        # Removing M2M table for field abstract_categories on 'ExternalCategory'
        db.delete_table('importer_externalcategory_abstract_categories')


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
            'Meta': {'object_name': 'ExternalCategory'},
            'abstract_categories': ('django.db.models.fields.related.ManyToManyField', [], {'blank': 'True', 'related_name': "'external_abstract_categories'", 'null': 'True', 'symmetrical': 'False', 'to': "orm['events.Category']"}),
            'concrete_category': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'external_concrete_category'", 'null': 'True', 'to': "orm['events.Category']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'source': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'external_concrete_category'", 'to': "orm['events.Source']"}),
            'xid': ('django.db.models.fields.CharField', [], {'max_length': '300'})
        },
        'importer.regexcategory': {
            'Meta': {'object_name': 'RegexCategory'},
            'category': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'source_regex_categories'", 'null': 'True', 'to': "orm['events.Category']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model_type': ('django.db.models.fields.CharField', [], {'max_length': '50', 'null': 'True', 'blank': 'True'}),
            'regex': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'source': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'source_regex_categories'", 'to': "orm['events.Source']"})
        }
    }

    complete_apps = ['importer']
