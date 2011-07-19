# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding model 'ConditionalCategoryModel'
        db.create_table('importer_conditionalcategorymodel', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('conditional_category', self.gf('django.db.models.fields.related.ForeignKey')(default=None, related_name='conditional_category', null=True, blank=True, to=orm['events.Category'])),
            ('regex', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('category', self.gf('django.db.models.fields.related.ForeignKey')(related_name='classified_category', to=orm['events.Category'])),
        ))
        db.send_create_signal('importer', ['ConditionalCategoryModel'])


    def backwards(self, orm):
        
        # Deleting model 'ConditionalCategoryModel'
        db.delete_table('importer_conditionalcategorymodel')


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
            'popularity_score': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'slug': ('django.db.models.fields.SlugField', [], {'max_length': '50', 'db_index': 'True'}),
            'submitted_by': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']", 'null': 'True', 'blank': 'True'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'url': ('django.db.models.fields.URLField', [], {'max_length': '300'}),
            'video_url': ('django.db.models.fields.URLField', [], {'max_length': '200', 'blank': 'True'}),
            'xid': ('django.db.models.fields.CharField', [], {'max_length': '200', 'blank': 'True'})
        },
        'events.source': {
            'Meta': {'object_name': 'Source'},
            'default_abstract_categories': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'sources_with_default_abstract'", 'symmetrical': 'False', 'to': "orm['events.Category']"}),
            'default_concrete_category': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'sources_with_default_concrete'", 'to': "orm['events.Category']"}),
            'domain': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '50'})
        },
        'importer.conditionalcategorymodel': {
            'Meta': {'object_name': 'ConditionalCategoryModel'},
            'category': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'classified_category'", 'to': "orm['events.Category']"}),
            'conditional_category': ('django.db.models.fields.related.ForeignKey', [], {'default': 'None', 'related_name': "'conditional_category'", 'null': 'True', 'blank': 'True', 'to': "orm['events.Category']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'regex': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'importer.eventexternalcats': {
            'Meta': {'unique_together': "(('external_category', 'event'),)", 'object_name': 'EventExternalCats'},
            'event': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'event_external_cat'", 'to': "orm['events.Event']"}),
            'external_category': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'event_external_cat'", 'to': "orm['importer.ExternalCategory']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
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
            'source': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'source_regex_categories'", 'null': 'True', 'to': "orm['events.Source']"})
        }
    }

    complete_apps = ['importer']
