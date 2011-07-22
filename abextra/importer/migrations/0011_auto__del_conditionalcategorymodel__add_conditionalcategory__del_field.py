# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Deleting model 'ConditionalCategoryModel'
        db.delete_table('importer_conditionalcategorymodel')

        # Adding model 'ConditionalCategory'
        db.create_table('importer_conditionalcategory', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('conditional_category', self.gf('django.db.models.fields.related.ForeignKey')(default=None, related_name='_conditional_category', null=True, blank=True, to=orm['events.Category'])),
            ('regex', self.gf('django.db.models.fields.CharField')(max_length=100)),
        ))
        db.send_create_signal('importer', ['ConditionalCategory'])

        # Adding M2M table for field category on 'ConditionalCategory'
        db.create_table('importer_conditionalcategory_category', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('conditionalcategory', models.ForeignKey(orm['importer.conditionalcategory'], null=False)),
            ('category', models.ForeignKey(orm['events.category'], null=False))
        ))
        db.create_unique('importer_conditionalcategory_category', ['conditionalcategory_id', 'category_id'])

        # Deleting field 'RegexCategory.category'
        db.delete_column('importer_regexcategory', 'category_id')

        # Adding M2M table for field category on 'RegexCategory'
        db.create_table('importer_regexcategory_category', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('regexcategory', models.ForeignKey(orm['importer.regexcategory'], null=False)),
            ('category', models.ForeignKey(orm['events.category'], null=False))
        ))
        db.create_unique('importer_regexcategory_category', ['regexcategory_id', 'category_id'])


    def backwards(self, orm):
        
        # Adding model 'ConditionalCategoryModel'
        db.create_table('importer_conditionalcategorymodel', (
            ('category', self.gf('django.db.models.fields.related.ForeignKey')(related_name='classified_category', to=orm['events.Category'])),
            ('regex', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('conditional_category', self.gf('django.db.models.fields.related.ForeignKey')(default=None, related_name='conditional_category', null=True, to=orm['events.Category'], blank=True)),
        ))
        db.send_create_signal('importer', ['ConditionalCategoryModel'])

        # Deleting model 'ConditionalCategory'
        db.delete_table('importer_conditionalcategory')

        # Removing M2M table for field category on 'ConditionalCategory'
        db.delete_table('importer_conditionalcategory_category')

        # Adding field 'RegexCategory.category'
        db.add_column('importer_regexcategory', 'category', self.gf('django.db.models.fields.related.ForeignKey')(related_name='source_regex_categories', null=True, to=orm['events.Category'], blank=True), keep_default=False)

        # Removing M2M table for field category on 'RegexCategory'
        db.delete_table('importer_regexcategory_category')


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
            'category': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['events.Category']", 'symmetrical': 'False'}),
            'conditional_category': ('django.db.models.fields.related.ForeignKey', [], {'default': 'None', 'related_name': "'_conditional_category'", 'null': 'True', 'blank': 'True', 'to': "orm['events.Category']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'regex': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'importer.externalcategory': {
            'Meta': {'object_name': 'ExternalCategory'},
            'abstract_categories': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'to': "orm['events.Category']", 'null': 'True', 'blank': 'True'}),
            'concrete_category': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'_external_conc_category'", 'null': 'True', 'to': "orm['events.Category']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'source': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['events.Source']"}),
            'xid': ('django.db.models.fields.CharField', [], {'max_length': '300'})
        },
        'importer.regexcategory': {
            'Meta': {'object_name': 'RegexCategory'},
            'category': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'to': "orm['events.Category']", 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model_type': ('django.db.models.fields.CharField', [], {'max_length': '50', 'null': 'True', 'blank': 'True'}),
            'regex': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'source': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['events.Source']", 'null': 'True', 'blank': 'True'})
        }
    }

    complete_apps = ['importer']
