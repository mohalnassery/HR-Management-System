from datetime import date, datetime, timedelta
from django.test import TestCase, override_settings
from django.core.cache import cache
from django.contrib.auth.models import User
from django.utils import timezone

from employees.models import Employee, Department
from attendance.models import Shift, ShiftAssignment, RamadanPeriod
from attendance.cache import (
    ShiftCache, RamadanCache, AttendanceMetricsCache,
    invalidate_employee_caches, invalidate_department_caches,
    warm_employee_caches
)

@override_settings(CACHES={
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
    }
})
class CacheTests(TestCase):
    def setUp(self):
        # Clear cache before each test
        cache.clear()
        
        # Create test user
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass'
        )
        
        # Create test department
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
        
        # Create test shift
        self.shift = Shift.objects.create(
            name='Day Shift',
            shift_type='REGULAR',
            start_time='09:00',
            end_time='17:00',
            break_duration=60,
            grace_period=15
        )
        
        # Create shift assignment
        self.assignment = ShiftAssignment.objects.create(
            employee=self.employee,
            shift=self.shift,
            start_date=date.today(),
            created_by=self.user
        )
        
        # Create Ramadan period
        self.ramadan_period = RamadanPeriod.objects.create(
            year=2025,
            start_date=date(2025, 3, 1),
            end_date=date(2025, 3, 30),
            is_active=True
        )

    def test_shift_cache(self):
        """Test shift caching functionality"""
        # Test employee shift caching
        shift_data = {
            'id': self.shift.id,
            'name': self.shift.name,
            'start_time': self.shift.start_time,
            'end_time': self.shift.end_time
        }
        
        # Set cache
        ShiftCache.set_employee_shift(self.employee.id, shift_data)
        
        # Get from cache
        cached_shift = ShiftCache.get_employee_shift(self.employee.id)
        self.assertEqual(cached_shift['id'], self.shift.id)
        
        # Clear cache
        ShiftCache.clear_employee_shift(self.employee.id)
        self.assertIsNone(ShiftCache.get_employee_shift(self.employee.id))
        
        # Test department shifts caching
        dept_shifts = {
            'Day Shift': [{
                'employee_id': self.employee.id,
                'employee_name': str(self.employee)
            }]
        }
        
        ShiftCache.set_department_shifts(self.department.id, dept_shifts)
        cached_dept_shifts = ShiftCache.get_department_shifts(self.department.id)
        self.assertEqual(
            cached_dept_shifts['Day Shift'][0]['employee_id'],
            self.employee.id
        )

    def test_ramadan_cache(self):
        """Test Ramadan period caching"""
        target_date = date(2025, 3, 15)
        period_data = {
            'id': self.ramadan_period.id,
            'start_date': self.ramadan_period.start_date,
            'end_date': self.ramadan_period.end_date
        }
        
        # Set cache
        RamadanCache.set_active_period(target_date, period_data)
        
        # Get from cache
        cached_period = RamadanCache.get_active_period(target_date)
        self.assertEqual(cached_period['id'], self.ramadan_period.id)
        
        # Clear specific date
        RamadanCache.clear_active_period(target_date)
        self.assertIsNone(RamadanCache.get_active_period(target_date))
        
        # Test clear all periods
        RamadanCache.set_active_period(target_date, period_data)
        RamadanCache.clear_all_periods()
        self.assertIsNone(RamadanCache.get_active_period(target_date))

    def test_attendance_metrics_cache(self):
        """Test attendance metrics caching"""
        today = date.today().isoformat()
        metrics_data = {
            'total': 10,
            'present': 8,
            'absent': 2,
            'late': 1
        }
        
        # Test without department
        AttendanceMetricsCache.set_metrics(today, metrics_data)
        cached_metrics = AttendanceMetricsCache.get_metrics(today)
        self.assertEqual(cached_metrics['total'], 10)
        
        # Test with department
        dept_metrics = {**metrics_data, 'department_id': self.department.id}
        AttendanceMetricsCache.set_metrics(today, dept_metrics, self.department.id)
        cached_dept_metrics = AttendanceMetricsCache.get_metrics(today, self.department.id)
        self.assertEqual(cached_dept_metrics['department_id'], self.department.id)
        
        # Test clear metrics
        AttendanceMetricsCache.clear_metrics(today, self.department.id)
        self.assertIsNone(
            AttendanceMetricsCache.get_metrics(today, self.department.id)
        )

    def test_cache_invalidation(self):
        """Test cache invalidation functions"""
        # Setup test data
        shift_data = {'id': self.shift.id, 'name': self.shift.name}
        metrics_data = {'total': 10, 'present': 8}
        today = date.today()
        
        # Set various caches
        ShiftCache.set_employee_shift(self.employee.id, shift_data)
        AttendanceMetricsCache.set_metrics(
            today.isoformat(),
            metrics_data,
            self.department.id
        )
        
        # Test employee cache invalidation
        invalidate_employee_caches(self.employee.id)
        self.assertIsNone(ShiftCache.get_employee_shift(self.employee.id))
        
        # Test department cache invalidation
        ShiftCache.set_department_shifts(self.department.id, {'shifts': []})
        invalidate_department_caches(self.department.id)
        self.assertIsNone(ShiftCache.get_department_shifts(self.department.id))
        self.assertIsNone(
            AttendanceMetricsCache.get_metrics(
                today.isoformat(),
                self.department.id
            )
        )

    def test_cache_warming(self):
        """Test cache warming functionality"""
        # Clear any existing cache
        ShiftCache.clear_employee_shift(self.employee.id)
        
        # Warm the cache
        warm_employee_caches(self.employee.id)
        
        # Check if cache was warmed
        cached_shift = ShiftCache.get_employee_shift(self.employee.id)
        self.assertIsNotNone(cached_shift)
        
        # Verify cached data
        self.assertEqual(cached_shift['id'], self.shift.id)
