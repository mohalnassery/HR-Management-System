import os
from datetime import date, timedelta
from django.test import TestCase, override_settings
from django.core.management import call_command
from django.contrib.auth.models import User
from django.utils import timezone
from django.core.cache import cache
from io import StringIO

from employees.models import Employee, Department
from attendance.models import Shift, ShiftAssignment, RamadanPeriod
from attendance.cache import ShiftCache, RamadanCache

@override_settings(CACHES={
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
    }
})
class CleanupShiftsTest(TestCase):
    def setUp(self):
        # Clear cache
        cache.clear()
        
        # Create test user
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass'
        )
        
        # Create department
        self.department = Department.objects.create(
            name='Test Department'
        )
        
        # Create test employee
        self.employee = Employee.objects.create(
            employee_number='EMP001',
            first_name='Test',
            last_name='Employee',
            department=self.department
        )
        
        # Create test shifts
        self.day_shift = Shift.objects.create(
            name='Day Shift',
            shift_type='REGULAR',
            start_time='09:00',
            end_time='17:00',
            break_duration=60
        )
        
        self.night_shift = Shift.objects.create(
            name='Night Shift',
            shift_type='NIGHT',
            start_time='22:00',
            end_time='06:00',
            break_duration=60
        )
        
        # Create assignments
        self.old_assignment = ShiftAssignment.objects.create(
            employee=self.employee,
            shift=self.day_shift,
            start_date=date.today() - timedelta(days=100),
            end_date=date.today() - timedelta(days=95),
            is_active=False,
            created_by=self.user
        )
        
        self.current_assignment = ShiftAssignment.objects.create(
            employee=self.employee,
            shift=self.night_shift,
            start_date=date.today(),
            created_by=self.user,
            is_active=True
        )
        
        # Create Ramadan periods
        self.old_ramadan = RamadanPeriod.objects.create(
            year=2023,
            start_date=date(2023, 3, 22),
            end_date=date(2023, 4, 20),
            is_active=False
        )
        
        self.current_ramadan = RamadanPeriod.objects.create(
            year=2025,
            start_date=date(2025, 3, 1),
            end_date=date(2025, 3, 30),
            is_active=True
        )

    def test_cleanup_old_assignments(self):
        """Test cleanup of old shift assignments"""
        out = StringIO()
        call_command('cleanup_shifts', '--force', stdout=out)
        
        # Old assignment should be deleted
        self.assertFalse(
            ShiftAssignment.objects.filter(id=self.old_assignment.id).exists()
        )
        
        # Current assignment should remain
        self.assertTrue(
            ShiftAssignment.objects.filter(id=self.current_assignment.id).exists()
        )
        
        # Check output
        output = out.getvalue()
        self.assertIn('Found 1 old shift assignments', output)

    def test_cleanup_ramadan_periods(self):
        """Test cleanup of old Ramadan periods"""
        out = StringIO()
        call_command('cleanup_shifts', '--force', stdout=out)
        
        # Old period should be deleted
        self.assertFalse(
            RamadanPeriod.objects.filter(id=self.old_ramadan.id).exists()
        )
        
        # Current period should remain
        self.assertTrue(
            RamadanPeriod.objects.filter(id=self.current_ramadan.id).exists()
        )
        
        # Check output
        output = out.getvalue()
        self.assertIn('Found 1 old Ramadan periods', output)

    def test_cleanup_orphaned_shifts(self):
        """Test cleanup of orphaned shifts"""
        # Create orphaned shift
        orphaned_shift = Shift.objects.create(
            name='Orphaned Shift',
            shift_type='REGULAR',
            start_time='10:00',
            end_time='18:00'
        )
        
        out = StringIO()
        call_command('cleanup_shifts', '--force', stdout=out)
        
        # Orphaned shift should be deleted
        self.assertFalse(
            Shift.objects.filter(id=orphaned_shift.id).exists()
        )
        
        # Used shifts should remain
        self.assertTrue(
            Shift.objects.filter(id=self.day_shift.id).exists()
        )
        
        # Check output
        output = out.getvalue()
        self.assertIn('Found 1 orphaned shifts', output)

    def test_cleanup_duplicate_assignments(self):
        """Test cleanup of duplicate active assignments"""
        # Create duplicate active assignment
        duplicate = ShiftAssignment.objects.create(
            employee=self.employee,
            shift=self.day_shift,
            start_date=date.today() + timedelta(days=1),
            created_by=self.user,
            is_active=True
        )
        
        out = StringIO()
        call_command('cleanup_shifts', '--force', stdout=out)
        
        # Check only one active assignment remains
        active_count = ShiftAssignment.objects.filter(
            employee=self.employee,
            is_active=True
        ).count()
        self.assertEqual(active_count, 1)
        
        # Most recent should be active
        duplicate.refresh_from_db()
        self.assertTrue(duplicate.is_active)
        
        self.current_assignment.refresh_from_db()
        self.assertFalse(self.current_assignment.is_active)
        
        # Check output
        output = out.getvalue()
        self.assertIn('Found 1 employees with multiple active assignments', output)

    def test_dry_run(self):
        """Test dry run option"""
        initial_assignment_count = ShiftAssignment.objects.count()
        
        out = StringIO()
        call_command('cleanup_shifts', '--dry-run', stdout=out)
        
        # No data should be deleted
        self.assertEqual(
            ShiftAssignment.objects.count(),
            initial_assignment_count
        )
        
        # Check output
        output = out.getvalue()
        self.assertIn('DRY RUN - No data will be deleted', output)

    def test_archiving(self):
        """Test data archiving"""
        out = StringIO()
        call_command('cleanup_shifts', '--force', '--archive', stdout=out)
        
        # Check archive files were created
        files = os.listdir('.')
        archive_files = [f for f in files if f.startswith(('shift_assignments_archive_', 'ramadan_periods_archive_'))]
        
        self.assertTrue(any(f.startswith('shift_assignments_archive_') for f in archive_files))
        self.assertTrue(any(f.startswith('ramadan_periods_archive_') for f in archive_files))
        
        # Clean up archive files
        for f in archive_files:
            os.remove(f)

    def test_cache_clearing(self):
        """Test cache clearing during cleanup"""
        # Set some cache data
        ShiftCache.set_employee_shift(self.employee.id, {'shift_id': self.day_shift.id})
        RamadanCache.set_active_period(date.today(), {'id': self.current_ramadan.id})
        
        # Run cleanup
        call_command('cleanup_shifts', '--force')
        
        # Cache should be cleared
        self.assertIsNone(ShiftCache.get_employee_shift(self.employee.id))
        self.assertIsNone(RamadanCache.get_active_period(date.today()))

    def tearDown(self):
        # Clean up any archive files
        files = os.listdir('.')
        archive_files = [f for f in files if f.startswith(('shift_assignments_archive_', 'ramadan_periods_archive_'))]
        for f in archive_files:
            os.remove(f)
