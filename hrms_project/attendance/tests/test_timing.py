from datetime import datetime, date, time, timedelta
from django.test import TestCase
from attendance.utils.timing import (
    calculate_time_difference,
    is_within_grace_period,
    calculate_late_minutes,
    calculate_early_departure,
    calculate_work_duration,
    adjust_ramadan_timing,
    parse_time_string,
    format_minutes_as_hours,
    is_night_shift,
    get_shift_period,
    is_time_in_shift
)

class TimingUtilsTests(TestCase):
    def test_calculate_time_difference(self):
        """Test time difference calculation"""
        # Regular case
        start = time(9, 0)
        end = time(17, 0)
        self.assertEqual(calculate_time_difference(start, end), 480)  # 8 hours
        
        # Overnight shift
        start = time(22, 0)
        end = time(6, 0)
        self.assertEqual(calculate_time_difference(start, end), 480)  # 8 hours
        
        # Same time
        start = end = time(9, 0)
        self.assertEqual(calculate_time_difference(start, end), 0)

    def test_grace_period(self):
        """Test grace period checks"""
        expected = time(9, 0)
        
        # Within grace period
        actual = time(9, 10)
        self.assertTrue(is_within_grace_period(actual, expected, 15))
        
        # Outside grace period
        actual = time(9, 20)
        self.assertFalse(is_within_grace_period(actual, expected, 15))
        
        # Exact match
        self.assertTrue(is_within_grace_period(expected, expected, 0))

    def test_late_minutes_calculation(self):
        """Test late minutes calculation"""
        expected = time(9, 0)
        grace = 10
        
        # Not late (within grace)
        actual = time(9, 5)
        self.assertEqual(calculate_late_minutes(actual, expected, grace), 0)
        
        # Late
        actual = time(9, 30)
        self.assertEqual(calculate_late_minutes(actual, expected, grace), 30)
        
        # Very late
        actual = time(10, 0)
        self.assertEqual(calculate_late_minutes(actual, expected, grace), 60)

    def test_early_departure(self):
        """Test early departure calculation"""
        expected = time(17, 0)
        
        # Not early
        actual = time(17, 30)
        self.assertEqual(calculate_early_departure(actual, expected), 0)
        
        # Early
        actual = time(16, 30)
        self.assertEqual(calculate_early_departure(actual, expected), 30)
        
        # Very early
        actual = time(15, 0)
        self.assertEqual(calculate_early_departure(actual, expected), 120)

    def test_work_duration(self):
        """Test work duration calculation"""
        # Regular day
        in_time = time(9, 0)
        out_time = time(17, 0)
        self.assertEqual(calculate_work_duration(in_time, out_time), 480)  # 8 hours
        
        # With break
        self.assertEqual(calculate_work_duration(in_time, out_time, 60), 420)  # 7 hours
        
        # Overnight shift
        in_time = time(22, 0)
        out_time = time(6, 0)
        self.assertEqual(calculate_work_duration(in_time, out_time), 480)  # 8 hours

    def test_ramadan_timing(self):
        """Test Ramadan timing adjustments"""
        start = time(8, 0)
        end = time(17, 0)
        
        adjusted_start, adjusted_end = adjust_ramadan_timing(start, end)
        
        # Start time should remain same
        self.assertEqual(adjusted_start, start)
        # End time should be 2 hours earlier
        self.assertEqual(adjusted_end, time(15, 0))
        
        # Test with different reduction
        _, adjusted_end = adjust_ramadan_timing(start, end, reduction_hours=3)
        self.assertEqual(adjusted_end, time(14, 0))

    def test_time_string_parsing(self):
        """Test time string parsing"""
        # 24-hour format
        self.assertEqual(parse_time_string('14:30'), time(14, 30))
        
        # 12-hour format
        self.assertEqual(parse_time_string('02:30 PM'), time(14, 30))
        
        # With seconds
        self.assertEqual(parse_time_string('14:30:00'), time(14, 30))
        
        # Invalid format
        self.assertIsNone(parse_time_string('invalid'))

    def test_minutes_formatting(self):
        """Test minutes to hours formatting"""
        # Only minutes
        self.assertEqual(format_minutes_as_hours(45), '45m')
        
        # Only hours
        self.assertEqual(format_minutes_as_hours(120), '2h')
        
        # Hours and minutes
        self.assertEqual(format_minutes_as_hours(150), '2h 30m')
        
        # Zero
        self.assertEqual(format_minutes_as_hours(0), '0m')

    def test_night_shift_detection(self):
        """Test night shift detection"""
        # Regular day shift
        self.assertFalse(is_night_shift(time(9, 0), time(17, 0)))
        
        # Night shift crossing midnight
        self.assertTrue(is_night_shift(time(22, 0), time(6, 0)))
        
        # Evening shift
        self.assertTrue(is_night_shift(time(18, 0), time(2, 0)))

    def test_shift_period(self):
        """Test shift period calculation"""
        check_date = date(2025, 1, 1)
        
        # Regular day shift
        start, end = get_shift_period(
            check_date,
            time(9, 0),
            time(17, 0)
        )
        self.assertEqual(start.date(), check_date)
        self.assertEqual(end.date(), check_date)
        
        # Night shift
        start, end = get_shift_period(
            check_date,
            time(22, 0),
            time(6, 0)
        )
        self.assertEqual(start.date(), check_date)
        self.assertEqual(end.date(), check_date + timedelta(days=1))

    def test_time_in_shift(self):
        """Test time in shift checking"""
        shift_start = time(9, 0)
        shift_end = time(17, 0)
        check_date = date(2025, 1, 1)
        
        # Within shift
        check_time = datetime.combine(check_date, time(12, 0))
        self.assertTrue(is_time_in_shift(check_time, shift_start, shift_end))
        
        # Outside shift
        check_time = datetime.combine(check_date, time(8, 0))
        self.assertFalse(is_time_in_shift(check_time, shift_start, shift_end))
        
        # Within grace period
        check_time = datetime.combine(check_date, time(9, 10))
        self.assertTrue(is_time_in_shift(check_time, shift_start, shift_end, grace_minutes=15))
