from datetime import date, datetime, timedelta
from typing import Optional, Dict, Any, List, TypeVar, Generic, Union
from django.core.cache import cache
from django.db.models import QuerySet
from django.conf import settings

# Cache configuration
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

def generate_cache_key(key_name: str, *args) -> str:
    """
    Centralized cache key generation function.
    
    Args:
        key_name: Name of the cache key template from CACHE_KEYS
        *args: Arguments to format into the key template
        
    Returns:
        Formatted cache key string
    
    Raises:
        KeyError: If key_name is not found in CACHE_KEYS
    """
    if key_name not in CACHE_KEYS:
        raise KeyError(f"Unknown cache key name: {key_name}")
    
    # Format date objects to ISO format
    formatted_args = [
        arg.isoformat() if isinstance(arg, date) else arg
        for arg in args
    ]
    
    return CACHE_KEYS[key_name].format(*formatted_args)

T = TypeVar('T')

class CacheManager(Generic[T]):
    """
    Base cache manager class providing generic cache operations.
    
    Type Parameters:
        T: The type of data being cached
    """
    
    def __init__(self, key_name: str, timeout_key: str):
        """
        Initialize cache manager with key configuration.
        
        Args:
            key_name: Name of the cache key template from CACHE_KEYS
            timeout_key: Name of the timeout from CACHE_TIMEOUTS
        """
        self.key_name = key_name
        self.timeout = CACHE_TIMEOUTS[timeout_key]
    
    def get_key(self, *args) -> str:
        """Generate cache key for given arguments"""
        return generate_cache_key(self.key_name, *args)
    
    def get(self, *args) -> Optional[T]:
        """Get cached data"""
        key = self.get_key(*args)
        return cache.get(key)
    
    def set(self, data: T, *args) -> None:
        """Set cache data"""
        key = self.get_key(*args)
        cache.set(key, data, self.timeout)
    
    def clear(self, *args) -> None:
        """Clear cached data"""
        key = self.get_key(*args)
        cache.delete(key)
    
    def clear_pattern(self, pattern: str) -> None:
        """
        Clear all cache keys matching a pattern.
        Note: Implementation depends on cache backend capabilities.
        Falls back to no-op if pattern deletion is not supported.
        """
        if hasattr(cache, 'delete_pattern'):
            # For cache backends that support pattern deletion (e.g., Redis)
            cache.delete_pattern(pattern)

class ShiftCache:
    """Cache manager for shift-related data"""
    
    _employee_shift = CacheManager[Dict[str, Any]]('employee_shift', 'employee_shift')
    _department_shifts = CacheManager[Dict[str, List[Dict[str, Any]]]]('department_shifts', 'department_shifts')
    
    @classmethod
    def get_employee_shift(cls, employee_id: int) -> Optional[Dict[str, Any]]:
        """Get employee's current shift from cache"""
        return cls._employee_shift.get(employee_id)
    
    @classmethod
    def set_employee_shift(cls, employee_id: int, shift_data: Dict[str, Any]) -> None:
        """Cache employee's current shift"""
        cls._employee_shift.set(shift_data, employee_id)
    
    @classmethod
    def clear_employee_shift(cls, employee_id: int) -> None:
        """Clear employee's shift cache"""
        cls._employee_shift.clear(employee_id)
    
    @classmethod
    def get_department_shifts(cls, department_id: int) -> Optional[Dict[str, List[Dict[str, Any]]]]:
        """Get department shifts from cache"""
        return cls._department_shifts.get(department_id)
    
    @classmethod
    def set_department_shifts(cls, department_id: int, shifts_data: Dict[str, List[Dict[str, Any]]]) -> None:
        """Cache department shifts"""
        cls._department_shifts.set(shifts_data, department_id)
    
    @classmethod
    def clear_department_shifts(cls, department_id: int) -> None:
        """Clear department shifts cache"""
        cls._department_shifts.clear(department_id)

class RamadanCache:
    """Cache manager for Ramadan period data"""
    
    _period = CacheManager[Dict[str, Any]]('ramadan_period', 'ramadan_period')
    
    @classmethod
    def get_active_period(cls, target_date: date) -> Optional[Dict[str, Any]]:
        """Get active Ramadan period from cache"""
        return cls._period.get(target_date)
    
    @classmethod
    def set_active_period(cls, target_date: date, period_data: Dict[str, Any]) -> None:
        """Cache active Ramadan period"""
        cls._period.set(period_data, target_date)
    
    @classmethod
    def clear_active_period(cls, target_date: date) -> None:
        """Clear Ramadan period cache"""
        cls._period.clear(target_date)
    
    @classmethod
    def clear_all_periods(cls) -> None:
        """Clear all Ramadan period caches"""
        # Try to use pattern deletion if supported
        cls._period.clear_pattern('ramadan_period_*')
        
        # Fallback to iterative deletion if pattern deletion is not supported
        if not hasattr(cache, 'delete_pattern'):
            current_date = date.today()
            year_start = date(current_date.year, 1, 1)
            year_end = date(current_date.year, 12, 31)
            
            current = year_start
            while current <= year_end:
                cls.clear_active_period(current)
                current += timedelta(days=1)

class AttendanceMetricsCache:
    """Cache manager for attendance metrics"""
    
    _metrics = CacheManager[Dict[str, Any]]('attendance_metrics', 'attendance_metrics')
    
    @classmethod
    def get_metrics(cls, date_str: str, department_id: Optional[int] = None) -> Optional[Dict[str, Any]]:
        """Get attendance metrics from cache"""
        return cls._metrics.get(date_str, department_id or 'all')
    
    @classmethod
    def set_metrics(
        cls,
        date_str: str,
        metrics_data: Dict[str, Any],
        department_id: Optional[int] = None
    ) -> None:
        """Cache attendance metrics"""
        cls._metrics.set(metrics_data, date_str, department_id or 'all')
    
    @classmethod
    def clear_metrics(cls, date_str: str, department_id: Optional[int] = None) -> None:
        """Clear attendance metrics cache"""
        cls._metrics.clear(date_str, department_id or 'all')

def invalidate_employee_caches(employee_id: int) -> None:
    """Invalidate all caches related to an employee"""
    # Clear shift cache
    ShiftCache.clear_employee_shift(employee_id)
    
    # Clear schedule caches for recent dates
    today = date.today()
    schedule_cache = CacheManager[Any]('employee_schedule', 'employee_schedule')
    
    for days in range(-7, 30):  # Past week to next month
        target_date = today + timedelta(days=days)
        schedule_cache.clear(employee_id, target_date, target_date)

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
