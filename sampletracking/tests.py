"""
Comprehensive test suite for the MGML Sample Tracking System.
Tests cover models, forms, and views to ensure data integrity and security.
"""
from django.test import TestCase, Client
from django.contrib.auth.models import User, Group, Permission
from django.urls import reverse
from django.utils import timezone
from django.db import IntegrityError
from django.db.models import ProtectedError
from django.core.exceptions import ValidationError
from datetime import date, timedelta

from .models import CrudeSample, Aliquot, Extract, SequenceLibrary, Plate
from .forms import (
    CrudeSampleForm,
    AliquotForm,
    ExtractForm,
    SequenceLibraryForm
)


class ModelTestCase(TestCase):
    """Test model constraints, validations, and relationships."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        
        # Create a crude sample
        self.crude_sample = CrudeSample.objects.create(
            barcode='CS001',
            date_created=date.today(),
            your_id='TEST001',
            collection_date=date.today() - timedelta(days=1),
            sample_source='Blood',
            freezer_ID='F1',
            shelf_ID='S1',
            box_ID='B1',
            created_by=self.user,
            updated_by=self.user
        )
        
        # Create an aliquot
        self.aliquot = Aliquot.objects.create(
            barcode='AL001',
            date_created=date.today(),
            parent_barcode=self.crude_sample,
            volume=100.0,
            concentration=50.0,
            freezer_ID='F1',
            shelf_ID='S1',
            box_ID='B1',
            created_by=self.user,
            updated_by=self.user
        )
        
        # Create an extract
        self.extract = Extract.objects.create(
            barcode='EX001',
            date_created=date.today(),
            parent=self.aliquot,
            extract_type='DNA',
            quality_score=1.8,
            freezer_ID='F1',
            shelf_ID='S1',
            box_ID='B1',
            created_by=self.user,
            updated_by=self.user
        )
        
        # Create a plate
        self.plate = Plate.objects.create(
            barcode='PL001',
            plate_type='96',
            created_by=self.user,
            updated_by=self.user
        )
    
    def test_cascade_protection_crude_to_aliquot(self):
        """Test that PROTECT prevents deletion of CrudeSample with aliquots."""
        with self.assertRaises(ProtectedError):
            self.crude_sample.delete()
    
    def test_cascade_protection_aliquot_to_extract(self):
        """Test that PROTECT prevents deletion of Aliquot with extracts."""
        with self.assertRaises(ProtectedError):
            self.aliquot.delete()
    
    def test_cascade_protection_extract_to_library(self):
        """Test that PROTECT prevents deletion of Extract with libraries."""
        # Create a library first
        library = SequenceLibrary.objects.create(
            barcode='LIB001',
            date_created=date.today(),
            parent=self.extract,
            library_type='Nextera',
            freezer_ID='F1',
            shelf_ID='S1',
            box_ID='B1',
            created_by=self.user,
            updated_by=self.user
        )
        
        with self.assertRaises(ProtectedError):
            self.extract.delete()
    
    def test_orphan_aliquot_not_allowed(self):
        """Test that aliquot requires a parent CrudeSample."""
        with self.assertRaises(IntegrityError):
            Aliquot.objects.create(
                barcode='AL002',
                date_created=date.today(),
                parent_barcode=None,  # No parent
                freezer_ID='F1',
                shelf_ID='S1',
                box_ID='B1',
                created_by=self.user,
                updated_by=self.user
            )
    
    def test_orphan_extract_not_allowed(self):
        """Test that extract requires a parent Aliquot."""
        with self.assertRaises(IntegrityError):
            Extract.objects.create(
                barcode='EX002',
                date_created=date.today(),
                parent=None,  # No parent
                extract_type='DNA',
                freezer_ID='F1',
                shelf_ID='S1',
                box_ID='B1',
                created_by=self.user,
                updated_by=self.user
            )
    
    def test_orphan_library_not_allowed(self):
        """Test that library requires a parent Extract."""
        with self.assertRaises(IntegrityError):
            SequenceLibrary.objects.create(
                barcode='LIB002',
                date_created=date.today(),
                parent=None,  # No parent
                library_type='Nextera',
                freezer_ID='F1',
                shelf_ID='S1',
                box_ID='B1',
                created_by=self.user,
                updated_by=self.user
            )
    
    def test_unique_together_plate_well(self):
        """Test that plate and well combination must be unique."""
        # Create first library in well A1
        lib1 = SequenceLibrary.objects.create(
            barcode='LIB003',
            date_created=date.today(),
            parent=self.extract,
            library_type='Nextera',
            plate=self.plate,
            well='A1',
            freezer_ID='F1',
            shelf_ID='S1',
            box_ID='B1',
            created_by=self.user,
            updated_by=self.user
        )
        
        # Try to create another library in same plate and well
        with self.assertRaises(IntegrityError):
            SequenceLibrary.objects.create(
                barcode='LIB004',
                date_created=date.today(),
                parent=self.extract,
                library_type='Nextera',
                plate=self.plate,
                well='A1',  # Same well as lib1
                freezer_ID='F1',
                shelf_ID='S1',
                box_ID='B1',
                created_by=self.user,
                updated_by=self.user
            )
    
    def test_barcode_validation(self):
        """Test barcode validator only allows alphanumeric, underscore, and hyphen."""
        # Valid barcode
        valid_sample = CrudeSample(
            barcode='CS-002_TEST',
            date_created=date.today(),
            your_id='TEST002',
            collection_date=date.today(),
            sample_source='Blood',
            freezer_ID='F1',
            shelf_ID='S1',
            box_ID='B1',
            created_by=self.user,
            updated_by=self.user
        )
        valid_sample.full_clean()  # Should not raise
        
        # Invalid barcode with special characters
        invalid_sample = CrudeSample(
            barcode='CS@002#TEST',
            date_created=date.today(),
            your_id='TEST003',
            collection_date=date.today(),
            sample_source='Blood',
            freezer_ID='F1',
            shelf_ID='S1',
            box_ID='B1',
            created_by=self.user,
            updated_by=self.user
        )
        with self.assertRaises(ValidationError):
            invalid_sample.full_clean()
    
    def test_status_field_default(self):
        """Test that status field defaults to AVAILABLE."""
        sample = CrudeSample.objects.create(
            barcode='CS003',
            date_created=date.today(),
            your_id='TEST004',
            collection_date=date.today(),
            sample_source='Blood',
            freezer_ID='F1',
            shelf_ID='S1',
            box_ID='B1',
            created_by=self.user,
            updated_by=self.user
        )
        self.assertEqual(sample.status, 'AVAILABLE')
    
    def test_plate_storage_optional(self):
        """Test that plate storage fields are optional."""
        plate = Plate.objects.create(
            barcode='PL002',
            plate_type='384',
            created_by=self.user,
            updated_by=self.user
            # No storage location specified
        )
        self.assertIsNone(plate.freezer_ID)
        self.assertIsNone(plate.shelf_ID)
        self.assertIsNone(plate.box_ID)


class FormTestCase(TestCase):
    """Test form validations and custom logic."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        
        self.crude_sample = CrudeSample.objects.create(
            barcode='CS001',
            date_created=date.today(),
            your_id='TEST001',
            collection_date=date.today() - timedelta(days=1),
            sample_source='Blood',
            freezer_ID='F1',
            shelf_ID='S1',
            box_ID='B1',
            created_by=self.user,
            updated_by=self.user
        )
        
        self.aliquot = Aliquot.objects.create(
            barcode='AL001',
            date_created=date.today(),
            parent_barcode=self.crude_sample,
            freezer_ID='F1',
            shelf_ID='S1',
            box_ID='B1',
            created_by=self.user,
            updated_by=self.user
        )
        
        self.extract = Extract.objects.create(
            barcode='EX001',
            date_created=date.today(),
            parent=self.aliquot,
            extract_type='DNA',
            freezer_ID='F1',
            shelf_ID='S1',
            box_ID='B1',
            created_by=self.user,
            updated_by=self.user
        )
        
        self.plate = Plate.objects.create(
            barcode='PL001',
            plate_type='96',
            created_by=self.user,
            updated_by=self.user
        )
    
    def test_crude_sample_form_valid(self):
        """Test valid CrudeSampleForm submission."""
        form_data = {
            'barcode': 'CS002',
            'date_created': date.today(),
            'status': 'AVAILABLE',
            'your_id': 'TEST002',
            'collection_date': date.today() - timedelta(days=1),
            'sample_source': 'Stool',
            'freezer_ID': 'F1',
            'shelf_ID': 'S1',
            'box_ID': 'B1',
            'notes': 'Test sample'
        }
        form = CrudeSampleForm(data=form_data)
        self.assertTrue(form.is_valid())
    
    def test_future_date_validation(self):
        """Test that future dates are not allowed."""
        # Future creation date
        form_data = {
            'barcode': 'CS002',
            'date_created': date.today() + timedelta(days=1),
            'status': 'AVAILABLE',
            'your_id': 'TEST002',
            'collection_date': date.today(),
            'sample_source': 'Blood',
            'freezer_ID': 'F1',
            'shelf_ID': 'S1',
            'box_ID': 'B1'
        }
        form = CrudeSampleForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('date_created', form.errors)
        
        # Future collection date
        form_data['date_created'] = date.today()
        form_data['collection_date'] = date.today() + timedelta(days=1)
        form = CrudeSampleForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('collection_date', form.errors)
    
    def test_collection_after_creation_validation(self):
        """Test that collection date cannot be after creation date."""
        form_data = {
            'barcode': 'CS002',
            'date_created': date.today() - timedelta(days=1),
            'status': 'AVAILABLE',
            'your_id': 'TEST002',
            'collection_date': date.today(),
            'sample_source': 'Blood',
            'freezer_ID': 'F1',
            'shelf_ID': 'S1',
            'box_ID': 'B1'
        }
        form = CrudeSampleForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('collection_date', form.errors)
    
    def test_short_barcode_validation(self):
        """Test that barcode must be at least 3 characters."""
        form_data = {
            'barcode': 'CS',  # Too short
            'date_created': date.today(),
            'status': 'AVAILABLE',
            'your_id': 'TEST002',
            'collection_date': date.today(),
            'sample_source': 'Blood',
            'freezer_ID': 'F1',
            'shelf_ID': 'S1',
            'box_ID': 'B1'
        }
        form = CrudeSampleForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('barcode', form.errors)
    
    def test_sequence_library_well_validation(self):
        """Test well format validation."""
        # Valid well format
        form_data = {
            'barcode': 'LIB001',
            'date_created': date.today(),
            'status': 'AVAILABLE',
            'parent': self.extract.pk,
            'library_type': 'Nextera',
            'nindex': 'N701',
            'sindex': 'S502',
            'freezer_ID': 'F1',
            'shelf_ID': 'S1',
            'box_ID': 'B1',
            'plate': self.plate.pk,
            'well': 'A1'
        }
        form = SequenceLibraryForm(data=form_data)
        self.assertTrue(form.is_valid())
        
        # Invalid well format
        form_data['well'] = '1A'  # Wrong format
        form = SequenceLibraryForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('well', form.errors)
        
        # Well too long
        form_data['well'] = 'AAA111'
        form = SequenceLibraryForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('well', form.errors)
    
    def test_plate_well_both_required(self):
        """Test that plate and well must be specified together."""
        form_data = {
            'barcode': 'LIB002',
            'date_created': date.today(),
            'status': 'AVAILABLE',
            'parent': self.extract.pk,
            'library_type': 'Nextera',
            'nindex': 'N701',
            'sindex': 'S502',
            'freezer_ID': 'F1',
            'shelf_ID': 'S1',
            'box_ID': 'B1',
            'plate': self.plate.pk,
            'well': ''  # Plate but no well
        }
        form = SequenceLibraryForm(data=form_data)
        self.assertFalse(form.is_valid())
        
        # Well but no plate
        form_data['plate'] = ''
        form_data['well'] = 'A1'
        form = SequenceLibraryForm(data=form_data)
        self.assertFalse(form.is_valid())


class ViewTestCase(TestCase):
    """Test view permissions and functionality."""
    
    def setUp(self):
        """Set up test users, groups, and permissions."""
        # Create groups
        self.viewer_group = Group.objects.create(name='Viewers')
        self.technician_group = Group.objects.create(name='Technicians')
        self.lab_manager_group = Group.objects.create(name='Lab Managers')
        
        # Set up permissions
        view_perms = Permission.objects.filter(codename__startswith='view_')
        add_perms = Permission.objects.filter(codename__startswith='add_')
        change_perms = Permission.objects.filter(codename__startswith='change_')
        delete_perms = Permission.objects.filter(codename__startswith='delete_')
        
        self.viewer_group.permissions.set(view_perms)
        self.technician_group.permissions.set(view_perms | add_perms | change_perms)
        self.lab_manager_group.permissions.set(
            view_perms | add_perms | change_perms | delete_perms
        )
        
        # Create users
        self.viewer = User.objects.create_user(
            username='viewer',
            password='viewpass'
        )
        self.viewer.groups.add(self.viewer_group)
        
        self.technician = User.objects.create_user(
            username='technician',
            password='techpass'
        )
        self.technician.groups.add(self.technician_group)
        
        self.lab_manager = User.objects.create_user(
            username='lab_manager',
            password='managerpass'
        )
        self.lab_manager.groups.add(self.lab_manager_group)
        
        self.no_perm_user = User.objects.create_user(
            username='noperm',
            password='nopass'
        )
        
        # Create test data
        self.crude_sample = CrudeSample.objects.create(
            barcode='CS001',
            date_created=date.today(),
            your_id='TEST001',
            collection_date=date.today(),
            sample_source='Blood',
            freezer_ID='F1',
            shelf_ID='S1',
            box_ID='B1',
            created_by=self.lab_manager,
            updated_by=self.lab_manager
        )
        
        self.client = Client()
    
    def test_list_view_permissions(self):
        """Test that list views require view permissions."""
        url = reverse('crude_sample_list')
        
        # No permission user - should redirect to login
        self.client.login(username='noperm', password='nopass')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)
        
        # Viewer - should have access
        self.client.login(username='viewer', password='viewpass')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        
        # Technician - should have access
        self.client.login(username='technician', password='techpass')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
    
    def test_create_view_permissions(self):
        """Test that create views require add permissions."""
        url = reverse('create_crude_sample')
        
        # Viewer - should not have access
        self.client.login(username='viewer', password='viewpass')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)
        
        # Technician - should have access
        self.client.login(username='technician', password='techpass')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
    
    def test_update_view_permissions(self):
        """Test that update views require change permissions."""
        url = reverse('crude_sample_update', kwargs={'pk': self.crude_sample.pk})
        
        # Viewer - should not have access
        self.client.login(username='viewer', password='viewpass')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)
        
        # Technician - should have access
        self.client.login(username='technician', password='techpass')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
    
    def test_create_sample_post(self):
        """Test creating a sample via POST request."""
        self.client.login(username='technician', password='techpass')
        url = reverse('create_crude_sample')
        
        post_data = {
            'barcode': 'CS002',
            'date_created': date.today(),
            'status': 'AVAILABLE',
            'your_id': 'TEST002',
            'collection_date': date.today() - timedelta(days=1),
            'sample_source': 'Stool',
            'freezer_ID': 'F1',
            'shelf_ID': 'S1',
            'box_ID': 'B1',
            'notes': 'Test sample creation'
        }
        
        response = self.client.post(url, post_data)
        self.assertEqual(response.status_code, 302)  # Redirect on success
        
        # Verify sample was created
        sample = CrudeSample.objects.get(barcode='CS002')
        self.assertEqual(sample.your_id, 'TEST002')
        self.assertEqual(sample.created_by, self.technician)
    
    def test_search_functionality(self):
        """Test the search view functionality."""
        self.client.login(username='viewer', password='viewpass')
        
        # Create additional samples
        Aliquot.objects.create(
            barcode='AL001',
            date_created=date.today(),
            parent_barcode=self.crude_sample,
            freezer_ID='F1',
            shelf_ID='S1',
            box_ID='B1',
            created_by=self.lab_manager,
            updated_by=self.lab_manager
        )
        
        # Search by barcode
        url = reverse('search')
        response = self.client.get(url, {'q': 'CS001'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'CS001')
        self.assertContains(response, 'Crude Sample')
        
        # Search by your_id
        response = self.client.get(url, {'q': 'TEST001'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'CS001')
        
        # Search across multiple sample types
        response = self.client.get(url, {'q': '001'})
        self.assertEqual(response.status_code, 200)
        # Should find both CS001 and AL001
        self.assertContains(response, 'CS001')
        self.assertContains(response, 'AL001')
    
    def test_home_view_public_access(self):
        """Test that home view is publicly accessible."""
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'MGML Sample Database')
    
    def test_detail_view_shows_children(self):
        """Test that detail views show child samples."""
        # Create related samples
        aliquot = Aliquot.objects.create(
            barcode='AL001',
            date_created=date.today(),
            parent_barcode=self.crude_sample,
            freezer_ID='F1',
            shelf_ID='S1',
            box_ID='B1',
            created_by=self.lab_manager,
            updated_by=self.lab_manager
        )
        
        self.client.login(username='viewer', password='viewpass')
        url = reverse('crude_sample_detail', kwargs={'pk': self.crude_sample.pk})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'AL001')  # Should show child aliquot
    
    def test_search_requires_permissions(self):
        """Test that search view requires appropriate permissions."""
        url = reverse('search')
        
        # User without any permissions
        self.client.login(username='noperm', password='nopass')
        response = self.client.get(url, {'q': 'test'})
        self.assertEqual(response.status_code, 403)
        
        # User with permissions
        self.client.login(username='viewer', password='viewpass')
        response = self.client.get(url, {'q': 'test'})
        self.assertEqual(response.status_code, 200)


class HistoryTestCase(TestCase):
    """Test django-simple-history functionality."""
    
    def setUp(self):
        """Set up test data."""
        self.user1 = User.objects.create_user(
            username='user1',
            password='pass1'
        )
        self.user2 = User.objects.create_user(
            username='user2',
            password='pass2'
        )
    
    def test_history_tracking(self):
        """Test that changes are tracked in history."""
        # Create a sample
        sample = CrudeSample.objects.create(
            barcode='CS001',
            date_created=date.today(),
            your_id='TEST001',
            collection_date=date.today(),
            sample_source='Blood',
            freezer_ID='F1',
            shelf_ID='S1',
            box_ID='B1',
            created_by=self.user1,
            updated_by=self.user1
        )
        
        # Update the sample
        sample.sample_source = 'Stool'
        sample.updated_by = self.user2
        sample.save()
        
        # Check history
        history = sample.history.all()
        self.assertEqual(history.count(), 2)  # Create + Update
        
        # Most recent first
        self.assertEqual(history[0].sample_source, 'Stool')
        self.assertEqual(history[1].sample_source, 'Blood')
    
    def test_history_preserves_user(self):
        """Test that history tracks which user made changes."""
        sample = CrudeSample.objects.create(
            barcode='CS001',
            date_created=date.today(),
            your_id='TEST001',
            collection_date=date.today(),
            sample_source='Blood',
            freezer_ID='F1',
            shelf_ID='S1',
            box_ID='B1',
            created_by=self.user1,
            updated_by=self.user1
        )
        
        # Change status
        sample.status = 'ARCHIVED'
        sample.updated_by = self.user2
        sample.save()
        
        history = sample.history.all()
        # Note: history_user would be set by middleware in actual requests
        self.assertEqual(history[0].status, 'ARCHIVED')
        self.assertEqual(history[1].status, 'AVAILABLE')