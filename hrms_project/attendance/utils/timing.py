from datetime import datetime, date, time, timedelta
from typing import Optional, Tuple, Dict, Any
from django.utils import timezone

def calculate_time_difference(start: time, end: time) -> int:
    """
    Calculate minutes between two time objects, handling overnight shifts
    
    Args:
        start: Start time
        end: End time
        
    Returns:
        Number of minutes between times
    """
    start_dt = datetime.combine(date.today(), start)
    end_dt = datetime.combine(date.today(), end)
    
    # Handle overnight shifts
    if end < start:
        end_dt += timedelta(days=1)
        
    return int((end_dt - start_dt).total_seconds() / 60)

def is_within_grace_period(
    actual_time: time,
    expected_time: time,
    grace_minutes: int
) -> bool:
    """
    Check if actual time is within grace period of expected time
    
    Args:
        actual_time: The actual time to check
        expected_time: The expected time
        grace_minutes: Number of grace period minutes
        
    Returns:
        True if within grace period, False otherwise
    """
    actual_dt = datetime.combine(date.today(), actual_time)
    expected_dt = datetime.combine(date.today(), expected_time)
    grace_delta = timedelta(minutes=grace_minutes)
    
    return actual_dt <= (expected_dt + grace_delta)

def calculate_late_minutes(
    actual_time: time,
    expected_time: time,
    grace_minutes: int = 0
) -> int:
    """
    Calculate minutes late, considering grace period
    
    Args:
        actual_time: Actual time of arrival
        expected_time: Expected arrival time
        grace_minutes: Grace period in minutes
        
    Returns:
        Number of minutes late (0 if not late)
    """
    if is_within_grace_period(actual_time, expected_time, grace_minutes):
        return 0
        
    actual_dt = datetime.combine(date.today(), actual_time)
    expected_dt = datetime.combine(date.today(), expected_time)
    
    return int((actual_dt - expected_dt).total_seconds() / 60)

def calculate_early_departure(
    actual_time: time,
    expected_time: time
) -> int:
    """
    Calculate minutes of early departure
    
    Args:
        actual_time: Actual departure time
        expected_time: Expected departure time
        
    Returns:
        Number of minutes left early (0 if not early)
    """
    actual_dt = datetime.combine(date.today(), actual_time)
    expected_dt = datetime.combine(date.today(), expected_time)
    
    if actual_dt >= expected_dt:
        return 0
        
    return int((expected_dt - actual_dt).total_seconds() / 60)

def calculate_work_duration(
    in_time: time,
    out_time: time,
    break_minutes: int = 0
) -> int:
    """
    Calculate total working minutes, excluding break time
    
    Args:
        in_time: Time in
        out_time: Time out
        break_minutes: Break duration in minutes
        
    Returns:
        Total working minutes
    """
    total_minutes = calculate_time_difference(in_time, out_time)
    return max(0, total_minutes - break_minutes)

def adjust_ramadan_timing(
    normal_start: time,
    normal_end: time,
    reduction_hours: int = 2
) -> Tuple[time, time]:
    """
    Adjust shift timing for Ramadan
    
    Args:
        normal_start: Regular start time
        normal_end: Regular end time
        reduction_hours: Hours to reduce by
        
    Returns:
        Tuple of (adjusted_start, adjusted_end)
    """
    # Keep start time same, reduce end time
    end_dt = datetime.combine(date.today(), normal_end)
    adjusted_end = (end_dt - timedelta(hours=reduction_hours)).time()
    
    return (normal_start, adjusted_end)

def parse_time_string(time_str: str) -> Optional[time]:
    """
    Parse time string in various formats
    
    Args:
        time_str: Time string to parse
        
    Returns:
        time object or None if invalid
    """
    formats = [
        '%H:%M',        # 24-hour (14:30)
        '%I:%M %p',     # 12-hour with AM/PM (02:30 PM)
        '%H:%M:%S',     # 24-hour with seconds
        '%I:%M:%S %p'   # 12-hour with seconds and AM/PM
    ]
    
    for fmt in formats:
        try:
            return datetime.strptime(time_str, fmt).time()
        except ValueError:
            continue
            
    return None

def format_minutes_as_hours(minutes: int) -> str:
    """
    Format minutes as hours and minutes string
    
    Args:
        minutes: Number of minutes
        
    Returns:
        Formatted string (e.g., "2h 30m")
    """
    hours = minutes // 60
    remaining_minutes = minutes % 60
    
    if hours == 0:
        return f"{remaining_minutes}m"
    elif remaining_minutes == 0:
        return f"{hours}h"
    else:
        return f"{hours}h {remaining_minutes}m"

def is_night_shift(start: time, end: time) -> bool:
    """
    Check if shift timing indicates a night shift
    
    Args:
        start: Shift start time
        end: Shift end time
        
    Returns:
        True if night shift, False otherwise
    """
    # Consider night shift if:
    # 1. End time is before start time (crosses midnight)
    # 2. Start time is after 6 PM (18:00)
    return end < start or start >= time(18, 0)

def get_shift_period(
    date_to_check: date,
    start: time,
    end: time
) -> Tuple[datetime, datetime]:
    """
    Get actual datetime period for a shift on a given date
    
    Args:
        date_to_check: Date of the shift
        start: Shift start time
        end: Shift end time
        
    Returns:
        Tuple of (period_start, period_end) datetimes
    """
    period_start = datetime.combine(date_to_check, start)
    period_end = datetime.combine(date_to_check, end)
    
    # Handle overnight shifts
    if end < start:
        period_end += timedelta(days=1)
        
    return (period_start, period_end)

def is_time_in_shift(
    check_time: datetime,
    shift_start: time,
    shift_end: time,
    grace_minutes: int = 0
) -> bool:
    """
    Check if a given datetime falls within shift hours
    
    Args:
        check_time: Datetime to check
        shift_start: Shift start time
        shift_end: Shift end time
        grace_minutes: Grace period in minutes
        
    Returns:
        True if time falls within shift period, False otherwise
    """
    shift_date = check_time.date()
    period_start, period_end = get_shift_period(shift_date, shift_start, shift_end)
    
    # Add grace period
    period_start -= timedelta(minutes=grace_minutes)
    period_end += timedelta(minutes=grace_minutes)
    
    return period_start <= check_time <= period_end
