from datetime import date, datetime, timedelta
from typing import Optional, Dict, Any, List
from django.core.cache import cache
from django.db.models import QuerySet
from django.conf import settings

# Cache keys and timeouts
CACHE_KEYS = {
    'employee_shift': 'employee_shift_{}',  # Employee's current shift
    'ramadan_period': 'ramadan_period_{}',  # Active Ramadan period for date
    'department_shifts': 'department_shifts_{}',  # Department's shift assignments
    'employee_schedule': 'employee_schedule_{}_{}_{}',  # Employee's schedule for date range
    'shift_statistics': 'shift_statistics_{}',  # Statistics for shift
    'attendance_metrics': 'attendance_metrics_{}_{}',  # Daily attendance metrics
}

CACHE_TIMEOUTS = {
    'employee_shift': 60 * 60,  # 1 hour
    'ramadan_period': 60 * 60 * 24,  # 24 hours
    'department_shifts': 60 * 30,  # 30 minutes
    'employee_schedule': 60 * 15,  # 15 minutes
    'shift_statistics': 60 * 60,  # 1 hour
    'attendance_metrics': 60 * 60 * 12,  # 12 hours
}

def get_employee_shift_cache_key(employee_id: int) -> str:
    """Generate cache key for employee's current shift"""
    return CACHE_KEYS['employee_shift'].format(employee_id)

def get_ramadan_period_cache_key(target_date: date) -> str:
    """Generate cache key for Ramadan period"""
    return CACHE_KEYS['ramadan_period'].format(target_date.isoformat())

def get_department_shifts_cache_key(department_id: int) -> str:
    """Generate cache key for department shifts"""
    return CACHE_KEYS['department_shifts'].format(department_id)

def get_employee_schedule_cache_key(employee_id: int, start_date: date, end_date: date) -> str:
    """Generate cache key for employee schedule"""
    return CACHE_KEYS['employee_schedule'].format(
        employee_id,
        start_date.isoformat(),
        end_date.isoformat()
    )

def get_shift_statistics_cache_key(shift_id: int) -> str:
    """Generate cache key for shift statistics"""
    return CACHE_KEYS['shift_statistics'].format(shift_id)

def get_attendance_metrics_cache_key(date_str: str, department_id: Optional[int] = None) -> str:
    """Generate cache key for attendance metrics"""
    return CACHE_KEYS['attendance_metrics'].format(date_str, department_id or 'all')

class ShiftCache:
    """Cache manager for shift-related data"""
    
    @staticmethod
    def get_employee_shift(employee_id: int) -> Optional[Dict[str, Any]]:
        """Get employee's current shift from cache"""
        key = get_employee_shift_cache_key(employee_id)
        return cache.get(key)

    @staticmethod
    def set_employee_shift(employee_id: int, shift_data: Dict[str, Any]) -> None:
        """Cache employee's current shift"""
        key = get_employee_shift_cache_key(employee_id)
        cache.set(key, shift_data, CACHE_TIMEOUTS['employee_shift'])

    @staticmethod
    def clear_employee_shift(employee_id: int) -> None:
        """Clear employee's shift cache"""
        key = get_employee_shift_cache_key(employee_id)
        cache.delete(key)

    @staticmethod
    def get_department_shifts(department_id: int) -> Optional[Dict[str, List[Dict[str, Any]]]]:
        """Get department shifts from cache"""
        key = get_department_shifts_cache_key(department_id)
        return cache.get(key)

    @staticmethod
    def set_department_shifts(department_id: int, shifts_data: Dict[str, List[Dict[str, Any]]]) -> None:
        """Cache department shifts"""
        key = get_department_shifts_cache_key(department_id)
        cache.set(key, shifts_data, CACHE_TIMEOUTS['department_shifts'])

    @staticmethod
    def clear_department_shifts(department_id: int) -> None:
        """Clear department shifts cache"""
        key = get_department_shifts_cache_key(department_id)
        cache.delete(key)

class RamadanCache:
    """Cache manager for Ramadan period data"""
    
    @staticmethod
    def get_active_period(target_date: date) -> Optional[Dict[str, Any]]:
        """Get active Ramadan period from cache"""
        key = get_ramadan_period_cache_key(target_date)
        return cache.get(key)

    @staticmethod
    def set_active_period(target_date: date, period_data: Dict[str, Any]) -> None:
        """Cache active Ramadan period"""
        key = get_ramadan_period_cache_key(target_date)
        cache.set(key, period_data, CACHE_TIMEOUTS['ramadan_period'])

    @staticmethod
    def clear_active_period(target_date: date) -> None:
        """Clear Ramadan period cache"""
        key = get_ramadan_period_cache_key(target_date)
        cache.delete(key)

    @staticmethod
    def clear_all_periods() -> None:
        """Clear all Ramadan period caches"""
        cache.delete_pattern('ramadan_period_*')

class AttendanceMetricsCache:
    """Cache manager for attendance metrics"""
    
    @staticmethod
    def get_metrics(date_str: str, department_id: Optional[int] = None) -> Optional[Dict[str, Any]]:
        """Get attendance metrics from cache"""
        key = get_attendance_metrics_cache_key(date_str, department_id)
        return cache.get(key)

    @staticmethod
    def set_metrics(
        date_str: str,
        metrics_data: Dict[str, Any],
        department_id: Optional[int] = None
    ) -> None:
        """Cache attendance metrics"""
        key = get_attendance_metrics_cache_key(date_str, department_id)
        cache.set(key, metrics_data, CACHE_TIMEOUTS['attendance_metrics'])

    @staticmethod
    def clear_metrics(date_str: str, department_id: Optional[int] = None) -> None:
        """Clear attendance metrics cache"""
        key = get_attendance_metrics_cache_key(date_str, department_id)
        cache.delete(key)

def invalidate_employee_caches(employee_id: int) -> None:
    """Invalidate all caches related to an employee"""
    # Clear shift cache
    ShiftCache.clear_employee_shift(employee_id)
    
    # Clear schedule caches for recent dates
    today = date.today()
    for days in range(-7, 30):  # Past week to next month
        target_date = today + timedelta(days=days)
        key = get_employee_schedule_cache_key(
            employee_id,
            target_date,
            target_date
        )
        cache.delete(key)

def invalidate_department_caches(department_id: int) -> None:
    """Invalidate all caches related to a department"""
    # Clear department shifts
    ShiftCache.clear_department_shifts(department_id)
    
    # Clear department metrics
    today = date.today()
    for days in range(-30, 1):  # Past month
        target_date = today + timedelta(days=days)
        AttendanceMetricsCache.clear_metrics(
            target_date.isoformat(),
            department_id
        )

def warm_employee_caches(employee_id: int) -> None:
    """Pre-warm commonly accessed employee caches"""
    from attendance.services import ShiftService
    
    # Warm up current shift
    current_shift = ShiftService.get_employee_current_shift(employee_id)
    if current_shift:
        ShiftCache.set_employee_shift(employee_id, current_shift)
