# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding model 'ConditionalCategory'
        db.create_table('importer_conditionalcategory', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('conditional_concrete_category', self.gf('django.db.models.fields.related.ForeignKey')(related_name='conditional_concrete_category', to=orm['events.Category'])),
            ('regex', self.gf('django.db.models.fields.CharField')(max_length=100)),
        ))
        db.send_create_signal('importer', ['ConditionalCategory'])

        # Adding M2M table for field resulting_categories on 'ConditionalCategory'
        db.create_table('importer_conditionalcategory_resulting_categories', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('conditionalcategory', models.ForeignKey(orm['importer.conditionalcategory'], null=False)),
            ('category', models.ForeignKey(orm['events.category'], null=False))
        ))
        db.create_unique('importer_conditionalcategory_resulting_categories', ['conditionalcategory_id', 'category_id'])

        # Deleting field 'RegexCategory.category'
        db.delete_column('importer_regexcategory', 'category_id')

        # Deleting field 'RegexCategory.source'
        db.delete_column('importer_regexcategory', 'source_id')

        # Adding M2M table for field sources on 'RegexCategory'
        db.create_table('importer_regexcategory_sources', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('regexcategory', models.ForeignKey(orm['importer.regexcategory'], null=False)),
            ('source', models.ForeignKey(orm['events.source'], null=False))
        ))
        db.create_unique('importer_regexcategory_sources', ['regexcategory_id', 'source_id'])

        # Adding M2M table for field category on 'RegexCategory'
        db.create_table('importer_regexcategory_category', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('regexcategory', models.ForeignKey(orm['importer.regexcategory'], null=False)),
            ('category', models.ForeignKey(orm['events.category'], null=False))
        ))
        db.create_unique('importer_regexcategory_category', ['regexcategory_id', 'category_id'])

        # Changing field 'RegexCategory.model_type'
        db.alter_column('importer_regexcategory', 'model_type', self.gf('django.db.models.fields.CharField')(default='R', max_length=5))


    def backwards(self, orm):
        
        # Deleting model 'ConditionalCategory'
        db.delete_table('importer_conditionalcategory')

        # Removing M2M table for field resulting_categories on 'ConditionalCategory'
        db.delete_table('importer_conditionalcategory_resulting_categories')

        # Adding field 'RegexCategory.category'
        db.add_column('importer_regexcategory', 'category', self.gf('django.db.models.fields.related.ForeignKey')(related_name='source_regex_categories', null=True, to=orm['events.Category'], blank=True), keep_default=False)

        # Adding field 'RegexCategory.source'
        db.add_column('importer_regexcategory', 'source', self.gf('django.db.models.fields.related.ForeignKey')(default=1, related_name='source_regex_categories', to=orm['events.Source']), keep_default=False)

        # Removing M2M table for field sources on 'RegexCategory'
        db.delete_table('importer_regexcategory_sources')

        # Removing M2M table for field category on 'RegexCategory'
        db.delete_table('importer_regexcategory_category')

        # Changing field 'RegexCategory.model_type'
        db.alter_column('importer_regexcategory', 'model_type', self.gf('django.db.models.fields.CharField')(max_length=50, null=True))


    models = {
        'events.category': {
            'Meta': {'object_name': 'Category'},
            'association_coefficient': ('django.db.models.fields.FloatField', [], {'default': '0'}),
            'button_icon': ('sorl.thumbnail.fields.ImageField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'category_type': ('django.db.models.fields.CharField', [], {'max_length': '1'}),
            'color': ('django.db.models.fields.CharField', [], {'max_length': '7', 'blank': 'True'}),
            'icon': ('sorl.thumbnail.fields.ImageField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'image': ('sorl.thumbnail.fields.ImageField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'is_associative': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'parent': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'subcategories'", 'null': 'True', 'to': "orm['events.Category']"}),
            'slug': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'max_length': '50', 'db_index': 'True'}),
            'small_icon': ('sorl.thumbnail.fields.ImageField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'thumb': ('sorl.thumbnail.fields.ImageField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
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
        'importer.conditionalcategory': {
            'Meta': {'object_name': 'ConditionalCategory'},
            'conditional_concrete_category': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'conditional_concrete_category'", 'to': "orm['events.Category']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'regex': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'resulting_categories': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['events.Category']", 'symmetrical': 'False'})
        },
        'importer.externalcategory': {
            'Meta': {'object_name': 'ExternalCategory'},
            'abstract_categories': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'to': "orm['events.Category']", 'null': 'True', 'blank': 'True'}),
            'concrete_category': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'externalcategory_concrete_set'", 'null': 'True', 'to': "orm['events.Category']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'source': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['events.Source']"}),
            'xid': ('django.db.models.fields.CharField', [], {'max_length': '300'})
        },
        'importer.regexcategory': {
            'Meta': {'object_name': 'RegexCategory'},
            'category': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'to': "orm['events.Category']", 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model_type': ('django.db.models.fields.CharField', [], {'max_length': '5'}),
            'regex': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'sources': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['events.Source']", 'symmetrical': 'False'})
        }
    }

    complete_apps = ['importer']
