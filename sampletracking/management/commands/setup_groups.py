"""
Management command to set up default user groups and permissions for the sample tracking system.
"""
from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from sampletracking.models import CrudeSample, Aliquot, Extract, SequenceLibrary, Plate


class Command(BaseCommand):
    help = 'Set up default user groups and permissions for the sample tracking system'

    def handle(self, *args, **options):
        # Create groups
        sample_collector_group, _ = Group.objects.get_or_create(name='Sample Collectors')
        technician_group, _ = Group.objects.get_or_create(name='Technicians')
        lab_manager_group, _ = Group.objects.get_or_create(name='Lab Managers')
        viewer_group, _ = Group.objects.get_or_create(name='Viewers')
        
        self.stdout.write(self.style.SUCCESS('Created/verified user groups'))
        
        # Get content types for our models
        models = [CrudeSample, Aliquot, Extract, SequenceLibrary, Plate]
        
        # Define permissions for each group
        # Sample Collectors can only add and view CrudeSamples
        sample_collector_permissions = []
        ct = ContentType.objects.get_for_model(CrudeSample)
        sample_collector_permissions.extend([
            Permission.objects.get(codename='add_crudesample', content_type=ct),
            Permission.objects.get(codename='view_crudesample', content_type=ct)
        ])
        
        # Viewers can only view samples
        viewer_permissions = []
        for model in models:
            ct = ContentType.objects.get_for_model(model)
            view_perm = Permission.objects.get(
                codename=f'view_{model.__name__.lower()}',
                content_type=ct
            )
            viewer_permissions.append(view_perm)
        
        # Technicians can view, add, and change samples (but not delete)
        technician_permissions = viewer_permissions.copy()
        for model in models:
            ct = ContentType.objects.get_for_model(model)
            add_perm = Permission.objects.get(
                codename=f'add_{model.__name__.lower()}',
                content_type=ct
            )
            change_perm = Permission.objects.get(
                codename=f'change_{model.__name__.lower()}',
                content_type=ct
            )
            technician_permissions.extend([add_perm, change_perm])
        
        # Lab Managers have full permissions (including delete)
        lab_manager_permissions = technician_permissions.copy()
        for model in models:
            ct = ContentType.objects.get_for_model(model)
            delete_perm = Permission.objects.get(
                codename=f'delete_{model.__name__.lower()}',
                content_type=ct
            )
            lab_manager_permissions.append(delete_perm)
        
        # Clear existing permissions and assign new ones
        sample_collector_group.permissions.clear()
        sample_collector_group.permissions.set(sample_collector_permissions)
        self.stdout.write(self.style.SUCCESS(f'Assigned {len(sample_collector_permissions)} permissions to Sample Collectors group'))
        
        viewer_group.permissions.clear()
        viewer_group.permissions.set(viewer_permissions)
        self.stdout.write(self.style.SUCCESS(f'Assigned {len(viewer_permissions)} permissions to Viewers group'))
        
        technician_group.permissions.clear()
        technician_group.permissions.set(technician_permissions)
        self.stdout.write(self.style.SUCCESS(f'Assigned {len(technician_permissions)} permissions to Technicians group'))
        
        lab_manager_group.permissions.clear()
        lab_manager_group.permissions.set(lab_manager_permissions)
        self.stdout.write(self.style.SUCCESS(f'Assigned {len(lab_manager_permissions)} permissions to Lab Managers group'))
        
        # Also add admin interface permissions for Lab Managers
        admin_permissions = Permission.objects.filter(
            content_type__app_label='sampletracking',
            codename__contains='view_historical'
        )
        lab_manager_group.permissions.add(*admin_permissions)
        
        self.stdout.write(self.style.SUCCESS('\nPermission Summary:'))
        self.stdout.write(self.style.SUCCESS('- Sample Collectors: Can only register new crude samples'))
        self.stdout.write(self.style.SUCCESS('- Viewers: Can only view samples'))
        self.stdout.write(self.style.SUCCESS('- Technicians: Can view, add, and modify samples'))
        self.stdout.write(self.style.SUCCESS('- Lab Managers: Full access including delete and history'))
        
        self.stdout.write(self.style.SUCCESS('\nGroups and permissions set up successfully!'))
        self.stdout.write(self.style.WARNING('\nNote: You still need to assign users to these groups through the Django admin interface.'))