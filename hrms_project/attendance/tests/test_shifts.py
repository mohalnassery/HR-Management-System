from datetime import datetime, date, time, timedelta
from django.test import TestCase
from django.contrib.auth.models import User
from django.utils import timezone

from employees.models import Employee, Department
from attendance.models import Shift, ShiftAssignment
from attendance.services import ShiftService

class ShiftTests(TestCase):
    def setUp(self):
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
            start_time=time(8, 0),
            end_time=time(17, 0),
            break_duration=60,
            grace_period=15
        )
        
        self.night_shift = Shift.objects.create(
            name='Night Shift',
            shift_type='NIGHT',
            start_time=time(20, 0),
            end_time=time(5, 0),
            break_duration=45,
            grace_period=15,
            is_night_shift=True
        )

    def test_shift_creation(self):
        """Test shift creation with various parameters"""
        self.assertEqual(self.day_shift.name, 'Day Shift')
        self.assertEqual(self.day_shift.break_duration, 60)
        self.assertFalse(self.day_shift.is_night_shift)
        
        self.assertEqual(self.night_shift.name, 'Night Shift')
        self.assertTrue(self.night_shift.is_night_shift)

    def test_shift_assignment(self):
        """Test assigning shifts to employees"""
        # Create permanent assignment
        assignment = ShiftService.assign_shift(
            employee=self.employee,
            shift=self.day_shift,
            start_date=date.today(),
            end_date=None,
            created_by=self.user
        )
        
        self.assertTrue(assignment.is_active)
        self.assertIsNone(assignment.end_date)
        
        # Get current shift
        current_shift = ShiftService.get_employee_current_shift(self.employee)
        self.assertEqual(current_shift, self.day_shift)
        
        # Test temporary assignment
        end_date = date.today() + timedelta(days=30)
        temp_assignment = ShiftService.assign_shift(
            employee=self.employee,
            shift=self.night_shift,
            start_date=date.today(),
            end_date=end_date,
            created_by=self.user
        )
        
        # Previous assignment should be inactive
        assignment.refresh_from_db()
        self.assertFalse(assignment.is_active)
        
        # New assignment should be active
        self.assertTrue(temp_assignment.is_active)
        self.assertEqual(temp_assignment.end_date, end_date)

    def test_bulk_shift_assignment(self):
        """Test bulk assignment of shifts"""
        # Create more test employees
        employees = []
        for i in range(3):
            emp = Employee.objects.create(
                employee_number=f'EMP00{i+2}',
                first_name=f'Test{i+2}',
                last_name='Employee',
                department=self.department
            )
            employees.append(emp)
        
        # Bulk assign shift
        employee_ids = [emp.id for emp in employees]
        created_count = ShiftService.bulk_assign_shift(
            employee_ids=employee_ids,
            shift=self.day_shift,
            start_date=date.today(),
            end_date=None,
            created_by=self.user
        )
        
        self.assertEqual(created_count, len(employees))
        
        # Verify assignments
        for emp in employees:
            current_shift = ShiftService.get_employee_current_shift(emp)
            self.assertEqual(current_shift, self.day_shift)

    def test_shift_timing_validation(self):
        """Test shift timing validation"""
        # Test invalid shift times
        with self.assertRaises(ValueError):
            Shift.objects.create(
                name='Invalid Shift',
                shift_type='REGULAR',
                start_time=time(9, 0),
                end_time=time(9, 0),  # Same as start time
                break_duration=60
            )

    def test_shift_history(self):
        """Test employee shift history tracking"""
        # Create multiple assignments
        assignments = []
        for i in range(3):
            start_date = date.today() - timedelta(days=i*30)
            end_date = start_date + timedelta(days=29) if i > 0 else None
            assignment = ShiftService.assign_shift(
                employee=self.employee,
                shift=self.day_shift if i % 2 == 0 else self.night_shift,
                start_date=start_date,
                end_date=end_date,
                created_by=self.user
            )
            assignments.append(assignment)
        
        # Get shift history
        history = ShiftService.get_employee_shift_history(self.employee)
        
        self.assertEqual(len(history), 3)
        self.assertTrue(history[0]['is_active'])  # Most recent should be active
        self.assertEqual(history[0]['shift_name'], self.day_shift.name)

    def test_department_shifts(self):
        """Test getting department shift assignments"""
        # Create multiple employees with different shifts
        employees = []
        for i in range(4):
            emp = Employee.objects.create(
                employee_number=f'EMP00{i+2}',
                first_name=f'Test{i+2}',
                last_name='Employee',
                department=self.department
            )
            employees.append(emp)
            
            # Assign shifts alternating between day and night
            shift = self.day_shift if i % 2 == 0 else self.night_shift
            ShiftService.assign_shift(
                employee=emp,
                shift=shift,
                start_date=date.today(),
                end_date=None,
                created_by=self.user
            )
        
        # Get department shifts
        dept_shifts = ShiftService.get_department_shifts(self.department.id)
        
        self.assertEqual(len(dept_shifts), 2)  # Should have both shifts
        self.assertTrue(self.day_shift.name in dept_shifts)
        self.assertTrue(self.night_shift.name in dept_shifts)
        
        # Each shift should have 2 employees
        for shift_name, employees in dept_shifts.items():
            self.assertEqual(len(employees), 2)
