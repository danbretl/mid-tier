# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding model 'Consumer'
        db.create_table('newapi_consumer', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(unique=True, max_length=20)),
            ('key', self.gf('django.db.models.fields.CharField')(unique=True, max_length=18)),
            ('secret', self.gf('django.db.models.fields.CharField')(max_length=40)),
            ('is_active', self.gf('django.db.models.fields.BooleanField')(default=False)),
        ))
        db.send_create_signal('newapi', ['Consumer'])


    def backwards(self, orm):
        
        # Deleting model 'Consumer'
        db.delete_table('newapi_consumer')


    models = {
        'newapi.consumer': {
            'Meta': {'object_name': 'Consumer'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'key': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '18'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '20'}),
            'secret': ('django.db.models.fields.CharField', [], {'max_length': '40'})
        }
    }

    complete_apps = ['newapi']
