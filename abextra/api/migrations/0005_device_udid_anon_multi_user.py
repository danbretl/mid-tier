# encoding: utf-8
import datetime
from south.db import db
from south.v2 import DataMigration
from django.db import models
from api.models import DeviceUdidManager

class Migration(DataMigration):

    def create_anonymous_user(self, orm):
        username_anonymous = DeviceUdidManager().generate_username_unique()
        user_anonymous = orm['auth.User'].objects.create(
            username=username_anonymous, password='!'
        )
        # add to proper user group
        group = orm['auth.Group'].objects.get(name='device_user_anonymous')
        user_anonymous.groups.add(group)
        return user_anonymous

    def forwards(self, orm):
        "Write your forwards methods here."
        for device_udid in orm.DeviceUdid.objects.all():
            user = device_udid.user
            # anonymous users
            if user.username.startswith('udid_'):
                device_udid.user_anonymous = device_udid.user
                device_udid.save()
            else:
                device_udid.user_anonymous = self.create_anonymous_user(orm)
                device_udid.save()
                device_udid.users.add(user)

    def backwards(self, orm):
        "Write your backwards methods here."
        for device_udid in orm.DeviceUdid.objects.all():
            device_udid.user = device_udid.user_anonymous
            device_udid.save()

    models = {
        'api.consumer': {
            'Meta': {'object_name': 'Consumer'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'key': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '18'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '20'}),
            'secret': ('django.db.models.fields.CharField', [], {'max_length': '40'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'consumers_tasty'", 'to': "orm['auth.User']"})
        },
        'api.deviceudid': {
            'Meta': {'object_name': 'DeviceUdid'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'udid': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '40'}),
            'user': ('django.db.models.fields.related.OneToOneField', [], {'related_name': "'device_udid'", 'unique': 'True', 'to': "orm['auth.User']"}),
            'user_anonymous': ('django.db.models.fields.related.OneToOneField', [], {'blank': 'True', 'related_name': "'device_udid_anonymous'", 'unique': 'True', 'null': 'True', 'to': "orm['auth.User']"}),
            'users': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'device_udids'", 'symmetrical': 'False', 'to': "orm['auth.User']"})
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

    complete_apps = ['api']
