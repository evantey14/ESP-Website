# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import DataMigration
from django.db import models

import collections
import re

class Migration(DataMigration):
    def canonicalize_names(self, all_resources):
        """Do some basic combining of resources with similar names.

        Returns a dict of name -> set of resources that should be represented
        by it.  Not intended to be super-smart, just do some basic combining of
        obvious things.
        """
        canonical_names = collections.defaultdict(set)
        for res in all_resources:
            canonical_names[res.name].add(res)
        for name in canonical_names.keys():
            new_name = None
            if ' ' in name:
                with_dashes = name.replace(' ', '-')
                without_spaces = name.replace(' ', '')
                if with_dashes in canonical_names:
                    new_name = with_dashes
                elif without_spaces in canonical_names:
                    new_name = without_spaces
            if new_name:
                canonical_names[new_name] |= canonical_names[name]
                del canonical_names[name]
        return canonical_names

    def forwards(self, orm):
        "Write your forwards methods here."
        # Note: Don't use "from appname.models import ModelName". 
        # Use orm.ModelName to refer to models in this application,
        # and orm['appname.ModelName'] for models in other applications.
        all_resources = orm.Resource.objects.filter(res_type__name='Classroom')
        canonical_names = self.canonicalize_names(all_resources)
        for name, resources in canonical_names.iteritems():
            # Take the newest (highest id) capacity as correct, and create the
            # resource
            new_cap = sorted(list(resources), key=lambda r: -r.id)[0].num_students
            location = orm.Location(name=name, capacity=new_cap)
            location.save()
            for resource in resources:
                # mark it as the location corresponding to the old resource
                # groups.  don't delete the resources for now, we'll do that
                # in a separate migration.
                resource.res_group.location = location
                resource.res_group.save()

                resource.event.available_locations.add(location)

                scheduled_sections = orm['program.ClassSection'].objects.filter(
                    resourceassignment__resource=resource)
                # Not sure why there would be more than one section scheduled
                # in one Resource, but just in case...
                for section in scheduled_sections:
                    section.locations.add(location)

    def backwards(self, orm):
        "Write your backwards methods here."
        orm.Location.objects.all().delete()

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
        'cal.event': {
            'Meta': {'object_name': 'Event'},
            'available_locations': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['resources.Location']", 'symmetrical': 'False', 'blank': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {}),
            'end': ('django.db.models.fields.DateTimeField', [], {}),
            'event_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['cal.EventType']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '80'}),
            'priority': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'program': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['program.Program']", 'null': 'True', 'blank': 'True'}),
            'short_description': ('django.db.models.fields.TextField', [], {}),
            'start': ('django.db.models.fields.DateTimeField', [], {})
        },
        'cal.eventtype': {
            'Meta': {'object_name': 'EventType'},
            'description': ('django.db.models.fields.TextField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
        },
        'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'datatree.datatree': {
            'Meta': {'unique_together': "(('name', 'parent'),)", 'object_name': 'DataTree'},
            'friendly_name': ('django.db.models.fields.TextField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'lock_table': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '64'}),
            'parent': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'child_set'", 'null': 'True', 'to': "orm['datatree.DataTree']"}),
            'range_correct': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'rangeend': ('django.db.models.fields.IntegerField', [], {}),
            'rangestart': ('django.db.models.fields.IntegerField', [], {}),
            'uri': ('django.db.models.fields.CharField', [], {'max_length': '1024'}),
            'uri_correct': ('django.db.models.fields.BooleanField', [], {'default': 'False'})
        },
        'program.classcategories': {
            'Meta': {'object_name': 'ClassCategories'},
            'category': ('django.db.models.fields.TextField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'seq': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'symbol': ('django.db.models.fields.CharField', [], {'default': "'?'", 'max_length': '1'})
        },
        'program.classflagtype': {
            'Meta': {'ordering': "['seq']", 'object_name': 'ClassFlagType'},
            'color': ('django.db.models.fields.CharField', [], {'max_length': '20', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255'}),
            'seq': ('django.db.models.fields.SmallIntegerField', [], {'default': '0'}),
            'show_in_dashboard': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'show_in_scheduler': ('django.db.models.fields.BooleanField', [], {'default': 'False'})
        },
        'program.classsection': {
            'Meta': {'ordering': "['id']", 'object_name': 'ClassSection'},
            'checklist_progress': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['program.ProgramCheckItem']", 'symmetrical': 'False', 'blank': 'True'}),
            'duration': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '5', 'decimal_places': '2', 'blank': 'True'}),
            'enrolled_students': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'locations': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['resources.Location']", 'symmetrical': 'False', 'blank': 'True'}),
            'max_class_capacity': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'meeting_times': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "'meeting_times'", 'blank': 'True', 'to': "orm['cal.Event']"}),
            'parent_class': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'sections'", 'to': "orm['program.ClassSubject']"}),
            'registration_status': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'registrations': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.User']", 'through': "orm['program.StudentRegistration']", 'symmetrical': 'False'}),
            'status': ('django.db.models.fields.IntegerField', [], {'default': '0'})
        },
        'program.classsizerange': {
            'Meta': {'object_name': 'ClassSizeRange'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'program': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['program.Program']", 'null': 'True', 'blank': 'True'}),
            'range_max': ('django.db.models.fields.IntegerField', [], {}),
            'range_min': ('django.db.models.fields.IntegerField', [], {})
        },
        'program.classsubject': {
            'Meta': {'object_name': 'ClassSubject', 'db_table': "'program_class'"},
            'allow_lateness': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'allowable_class_size_ranges': ('django.db.models.fields.related.ManyToManyField', [], {'blank': 'True', 'related_name': "'classsubject_allowedsizes'", 'null': 'True', 'symmetrical': 'False', 'to': "orm['program.ClassSizeRange']"}),
            'category': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'cls'", 'to': "orm['program.ClassCategories']"}),
            'checklist_progress': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['program.ProgramCheckItem']", 'symmetrical': 'False', 'blank': 'True'}),
            'class_info': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'class_size_max': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'class_size_min': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'class_size_optimal': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'custom_form_data': ('esp.utils.fields.JSONField', [], {'null': 'True', 'blank': 'True'}),
            'directors_notes': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'duration': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '5', 'decimal_places': '2', 'blank': 'True'}),
            'grade_max': ('django.db.models.fields.IntegerField', [], {}),
            'grade_min': ('django.db.models.fields.IntegerField', [], {}),
            'hardness_rating': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'meeting_times': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['cal.Event']", 'symmetrical': 'False', 'blank': 'True'}),
            'message_for_directors': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'optimal_class_size_range': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['program.ClassSizeRange']", 'null': 'True', 'blank': 'True'}),
            'parent_program': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['program.Program']"}),
            'prereqs': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'purchase_requests': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'requested_room': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'requested_special_resources': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'schedule': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'session_count': ('django.db.models.fields.IntegerField', [], {'default': '1'}),
            'status': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'teachers': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.User']", 'symmetrical': 'False'}),
            'title': ('django.db.models.fields.TextField', [], {})
        },
        'program.program': {
            'Meta': {'object_name': 'Program'},
            'class_categories': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['program.ClassCategories']", 'symmetrical': 'False'}),
            'director_cc_email': ('django.db.models.fields.EmailField', [], {'default': "''", 'max_length': '75', 'blank': 'True'}),
            'director_confidential_email': ('django.db.models.fields.EmailField', [], {'default': "''", 'max_length': '75', 'blank': 'True'}),
            'director_email': ('django.db.models.fields.EmailField', [], {'max_length': '75'}),
            'flag_types': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['program.ClassFlagType']", 'symmetrical': 'False', 'blank': 'True'}),
            'grade_max': ('django.db.models.fields.IntegerField', [], {}),
            'grade_min': ('django.db.models.fields.IntegerField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '80'}),
            'program_allow_waitlist': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'program_modules': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['program.ProgramModule']", 'symmetrical': 'False'}),
            'program_size_max': ('django.db.models.fields.IntegerField', [], {'null': 'True'}),
            'url': ('django.db.models.fields.CharField', [], {'max_length': '80'})
        },
        'program.programcheckitem': {
            'Meta': {'ordering': "('seq',)", 'object_name': 'ProgramCheckItem'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'program': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'checkitems'", 'to': "orm['program.Program']"}),
            'seq': ('django.db.models.fields.PositiveIntegerField', [], {'blank': 'True'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '512'})
        },
        'program.programmodule': {
            'Meta': {'object_name': 'ProgramModule'},
            'admin_title': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'handler': ('django.db.models.fields.CharField', [], {'max_length': '32'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'inline_template': ('django.db.models.fields.CharField', [], {'max_length': '32', 'null': 'True', 'blank': 'True'}),
            'link_title': ('django.db.models.fields.CharField', [], {'max_length': '64', 'null': 'True', 'blank': 'True'}),
            'module_type': ('django.db.models.fields.CharField', [], {'max_length': '32'}),
            'required': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'seq': ('django.db.models.fields.IntegerField', [], {})
        },
        'program.registrationtype': {
            'Meta': {'unique_together': "(('name', 'category'),)", 'object_name': 'RegistrationType'},
            'category': ('django.db.models.fields.CharField', [], {'max_length': '32'}),
            'description': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'displayName': ('django.db.models.fields.CharField', [], {'max_length': '32', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '32'})
        },
        'program.studentregistration': {
            'Meta': {'object_name': 'StudentRegistration'},
            'end_date': ('django.db.models.fields.DateTimeField', [], {'default': 'None', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'relationship': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['program.RegistrationType']"}),
            'section': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['program.ClassSection']"}),
            'start_date': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'null': 'True', 'blank': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"})
        },
        'qsdmedia.media': {
            'Meta': {'object_name': 'Media'},
            'file_extension': ('django.db.models.fields.TextField', [], {'max_length': '16', 'null': 'True', 'blank': 'True'}),
            'file_name': ('django.db.models.fields.TextField', [], {'max_length': '256', 'null': 'True', 'blank': 'True'}),
            'format': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'friendly_name': ('django.db.models.fields.TextField', [], {}),
            'hashed_name': ('django.db.models.fields.TextField', [], {'max_length': '256', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'mime_type': ('django.db.models.fields.CharField', [], {'max_length': '256', 'null': 'True', 'blank': 'True'}),
            'owner_id': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True', 'blank': 'True'}),
            'owner_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']", 'null': 'True', 'blank': 'True'}),
            'size': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'target_file': ('django.db.models.fields.files.FileField', [], {'max_length': '100'})
        },
        'resources.location': {
            'Meta': {'object_name': 'Location'},
            'admin_notes': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'capacity': ('django.db.models.fields.IntegerField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'student_notes': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'teacher_notes': ('django.db.models.fields.TextField', [], {'blank': 'True'})
        },
        'resources.resource': {
            'Meta': {'object_name': 'Resource'},
            'event': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['cal.Event']"}),
            'group_id': ('django.db.models.fields.IntegerField', [], {'default': '-1'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_unique': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '80'}),
            'num_students': ('django.db.models.fields.IntegerField', [], {'default': '-1', 'blank': 'True'}),
            'res_group': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['resources.ResourceGroup']", 'null': 'True', 'blank': 'True'}),
            'res_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['resources.ResourceType']", 'on_delete': 'models.PROTECT'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']", 'null': 'True', 'blank': 'True'})
        },
        'resources.resourceassignment': {
            'Meta': {'object_name': 'ResourceAssignment'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'lock_level': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'resource': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['resources.Resource']"}),
            'target': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['program.ClassSection']", 'null': 'True'}),
            'target_subj': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['program.ClassSubject']", 'null': 'True'})
        },
        'resources.resourcegroup': {
            'Meta': {'object_name': 'ResourceGroup'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'location': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['resources.Location']", 'null': 'True'})
        },
        'resources.resourcerequest': {
            'Meta': {'object_name': 'ResourceRequest'},
            'desired_value': ('django.db.models.fields.TextField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'res_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['resources.ResourceType']", 'on_delete': 'models.PROTECT'}),
            'target': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['program.ClassSection']", 'null': 'True'}),
            'target_subj': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['program.ClassSubject']", 'null': 'True'})
        },
        'resources.resourcetype': {
            'Meta': {'object_name': 'ResourceType'},
            'attributes_pickled': ('django.db.models.fields.TextField', [], {'default': '"Don\'t care"', 'blank': 'True'}),
            'autocreated': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'consumable': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'description': ('django.db.models.fields.TextField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '40'}),
            'only_one': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'priority_default': ('django.db.models.fields.IntegerField', [], {'default': '-1'}),
            'program': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['program.Program']", 'null': 'True', 'blank': 'True'})
        }
    }

    complete_apps = ['resources']
    symmetrical = True