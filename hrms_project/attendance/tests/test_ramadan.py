from datetime import datetime, date, time, timedelta
from django.test import TestCase
from django.contrib.auth.models import User
from django.utils import timezone

from employees.models import Employee, Department
from attendance.models import Shift, RamadanPeriod
from attendance.services import ShiftService, RamadanService

class RamadanTests(TestCase):
    def setUp(self):
        # Create test shift
        self.shift = Shift.objects.create(
            name='Regular Shift',
            shift_type='REGULAR',
            start_time=time(8, 0),
            end_time=time(17, 0),
            break_duration=60,
            grace_period=15
        )
        
        # Create test Ramadan period
        self.current_year = timezone.now().year
        self.ramadan_start = date(self.current_year, 3, 1)
        self.ramadan_end = date(self.current_year, 3, 30)
        
        self.ramadan_period = RamadanPeriod.objects.create(
            year=self.current_year,
            start_date=self.ramadan_start,
            end_date=self.ramadan_end,
            is_active=True
        )

    def test_ramadan_period_creation(self):
        """Test Ramadan period creation and validation"""
        # Test valid period
        period = RamadanService.create_period(
            year=self.current_year + 1,
            start_date=date(self.current_year + 1, 2, 15),
            end_date=date(self.current_year + 1, 3, 15)
        )
        self.assertTrue(period.is_active)
        self.assertEqual(period.year, self.current_year + 1)
        
        # Test invalid year
        with self.assertRaises(ValueError):
            RamadanService.create_period(
                year=self.current_year + 1,
                start_date=date(self.current_year, 2, 15),  # Different year
                end_date=date(self.current_year + 1, 3, 15)
            )
        
        # Test invalid duration
        with self.assertRaises(ValueError):
            RamadanService.create_period(
                year=self.current_year + 1,
                start_date=date(self.current_year + 1, 2, 15),
                end_date=date(self.current_year + 1, 4, 15)  # Too long
            )

    def test_overlapping_periods(self):
        """Test prevention of overlapping Ramadan periods"""
        # Try to create overlapping period
        with self.assertRaises(ValueError):
            RamadanService.create_period(
                year=self.current_year,
                start_date=date(self.current_year, 3, 15),  # Overlaps with existing period
                end_date=date(self.current_year, 4, 15)
            )

    def test_ramadan_shift_timing(self):
        """Test shift timing adjustments during Ramadan"""
        # Test during Ramadan period
        ramadan_date = self.ramadan_start + timedelta(days=5)
        timing = RamadanService.get_ramadan_shift_timing(self.shift, ramadan_date)
        
        self.assertIsNotNone(timing)
        self.assertEqual(timing['start_time'], self.shift.start_time)
        # End time should be 2 hours earlier
        expected_end = (
            datetime.combine(date.today(), self.shift.end_time) - timedelta(hours=2)
        ).time()
        self.assertEqual(timing['end_time'], expected_end)
        
        # Test outside Ramadan period
        non_ramadan_date = self.ramadan_end + timedelta(days=5)
        timing = RamadanService.get_ramadan_shift_timing(self.shift, non_ramadan_date)
        self.assertIsNone(timing)

    def test_active_period_detection(self):
        """Test finding active Ramadan period for a date"""
        # Test during Ramadan
        ramadan_date = self.ramadan_start + timedelta(days=5)
        active_period = RamadanService.get_active_period(ramadan_date)
        self.assertEqual(active_period, self.ramadan_period)
        
        # Test outside Ramadan
        non_ramadan_date = self.ramadan_end + timedelta(days=5)
        active_period = RamadanService.get_active_period(non_ramadan_date)
        self.assertIsNone(active_period)
        
        # Test with inactive period
        self.ramadan_period.is_active = False
        self.ramadan_period.save()
        active_period = RamadanService.get_active_period(ramadan_date)
        self.assertIsNone(active_period)

    def test_working_hours_calculation(self):
        """Test working hours adjustment during Ramadan"""
        normal_hours = 8.0
        
        # Test Ramadan hours
        ramadan_hours = RamadanService.calculate_working_hours(
            normal_hours=normal_hours,
            is_ramadan=True
        )
        self.assertEqual(ramadan_hours, 6.0)  # 2 hours less
        
        # Test non-Ramadan hours
        regular_hours = RamadanService.calculate_working_hours(
            normal_hours=normal_hours,
            is_ramadan=False
        )
        self.assertEqual(regular_hours, normal_hours)
        
        # Test minimum hours
        short_hours = RamadanService.calculate_working_hours(
            normal_hours=5.0,
            is_ramadan=True
        )
        self.assertEqual(short_hours, 4.0)  # Minimum allowed

    def test_period_validation(self):
        """Test comprehensive period date validation"""
        # Test same year requirement
        with self.assertRaises(ValueError):
            RamadanService.validate_period_dates(
                start_date=date(2024, 12, 31),
                end_date=date(2025, 1, 30),
                year=2024
            )
        
        # Test duration limits
        with self.assertRaises(ValueError):
            RamadanService.validate_period_dates(
                start_date=date(2024, 3, 1),
                end_date=date(2024, 4, 15),  # Too long
                year=2024
            )
        
        # Test valid period
        result = RamadanService.validate_period_dates(
            start_date=date(2024, 3, 1),
            end_date=date(2024, 3, 29),
            year=2024
        )
        self.assertTrue(result)

    def test_period_update(self):
        """Test updating existing Ramadan period"""
        new_start = date(self.current_year, 4, 1)
        new_end = date(self.current_year, 4, 29)
        
        updated_period = RamadanService.update_period(
            period_id=self.ramadan_period.id,
            year=self.current_year,
            start_date=new_start,
            end_date=new_end,
            is_active=True
        )
        
        self.assertEqual(updated_period.start_date, new_start)
        self.assertEqual(updated_period.end_date, new_end)
        self.assertTrue(updated_period.is_active)

    def test_period_listing(self):
        """Test retrieving Ramadan period lists"""
        # Create additional period
        RamadanPeriod.objects.create(
            year=self.current_year + 1,
            start_date=date(self.current_year + 1, 2, 15),
            end_date=date(self.current_year + 1, 3, 15),
            is_active=False
        )
        
        # Test active only
        active_periods = RamadanService.get_all_periods(include_inactive=False)
        self.assertEqual(len(active_periods), 1)
        
        # Test including inactive
        all_periods = RamadanService.get_all_periods(include_inactive=True)
        self.assertEqual(len(all_periods), 2)
        
        # Check sorting
        self.assertGreater(all_periods[0]['year'], all_periods[1]['year'])
