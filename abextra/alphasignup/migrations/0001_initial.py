# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding model 'AlphaQuestionnaire'
        db.create_table('alphasignup_alphaquestionnaire', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('device_platform', self.gf('django.db.models.fields.CharField')(max_length=1)),
            ('zip', self.gf('django.db.models.fields.CharField')(max_length=10, blank=True)),
            ('is_usage_info_ok', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('is_mobile_planner', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('is_app_dev', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('year_of_birth', self.gf('django.db.models.fields.IntegerField')()),
            ('profile', self.gf('django.db.models.fields.related.OneToOneField')(related_name='alpha_questionnaire', unique=True, to=orm['accounts.UserProfile'])),
        ))
        db.send_create_signal('alphasignup', ['AlphaQuestionnaire'])

        # Adding model 'AppDistribution'
        db.create_table('alphasignup_appdistribution', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('version', self.gf('django.db.models.fields.CharField')(max_length=20)),
            ('archive', self.gf('django.db.models.fields.files.FileField')(max_length=100)),
        ))
        db.send_create_signal('alphasignup', ['AppDistribution'])


    def backwards(self, orm):
        
        # Deleting model 'AlphaQuestionnaire'
        db.delete_table('alphasignup_alphaquestionnaire')

        # Deleting model 'AppDistribution'
        db.delete_table('alphasignup_appdistribution')


    models = {
        'accounts.userprofile': {
            'Meta': {'object_name': 'UserProfile'},
            'alpha_status': ('django.db.models.fields.CharField', [], {'max_length': '1', 'null': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'mugshot': ('django.db.models.fields.files.ImageField', [], {'max_length': '100', 'blank': 'True'}),
            'privacy': ('django.db.models.fields.CharField', [], {'default': "'closed'", 'max_length': '15'}),
            'user': ('django.db.models.fields.related.OneToOneField', [], {'related_name': "'profile'", 'unique': 'True', 'to': "orm['auth.User']"})
        },
        'alphasignup.alphaquestionnaire': {
            'Meta': {'object_name': 'AlphaQuestionnaire'},
            'device_platform': ('django.db.models.fields.CharField', [], {'max_length': '1'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_app_dev': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_mobile_planner': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_usage_info_ok': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'profile': ('django.db.models.fields.related.OneToOneField', [], {'related_name': "'alpha_questionnaire'", 'unique': 'True', 'to': "orm['accounts.UserProfile']"}),
            'year_of_birth': ('django.db.models.fields.IntegerField', [], {}),
            'zip': ('django.db.models.fields.CharField', [], {'max_length': '10', 'blank': 'True'})
        },
        'alphasignup.appdistribution': {
            'Meta': {'object_name': 'AppDistribution'},
            'archive': ('django.db.models.fields.files.FileField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'version': ('django.db.models.fields.CharField', [], {'max_length': '20'})
        },
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
        }
    }

    complete_apps = ['alphasignup']
