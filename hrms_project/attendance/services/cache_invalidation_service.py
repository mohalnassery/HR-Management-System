from datetime import date, timedelta
from typing import Optional, List, Set
from django.core.cache import cache
from django.utils import timezone

from ..cache import RamadanCache

class CacheInvalidationService:
    """Service for handling cache invalidation operations"""

    @staticmethod
    def clear_employee_shift_cache(employee_id: int) -> None:
        """Clear employee shift cache"""
        cache_key = f'employee_shift_{employee_id}'
        cache.delete(cache_key)

    @staticmethod
    def clear_shift_statistics_cache(shift_id: int) -> None:
        """Clear shift statistics cache"""
        cache_key = f'shift_statistics_{shift_id}'
        cache.delete(cache_key)

    @staticmethod
    def clear_ramadan_period_cache(start_date: date, end_date: date) -> None:
        """
        Clear Ramadan period cache for a date range.
        Uses pattern-based deletion if available, falls back to iterative deletion.
        """
        if hasattr(cache, 'delete_pattern'):
            # For cache backends that support pattern deletion (e.g., Redis)
            cache.delete_pattern('ramadan_period_*')
        else:
            # Fallback to iterative deletion
            current_date = start_date
            while current_date <= end_date:
                RamadanCache.clear_active_period(current_date)
                current_date += timedelta(days=1)

    @staticmethod
    def clear_employee_schedule_cache(
        employee_id: int,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        days_before: int = 7,
        days_after: int = 30
    ) -> None:
        """
        Clear employee schedule cache for a date range.
        If no dates provided, clears for default range around current date.
        """
        if not start_date:
            start_date = timezone.now().date() - timedelta(days=days_before)
        if not end_date:
            end_date = timezone.now().date() + timedelta(days=days_after)

        current_date = start_date
        while current_date <= end_date:
            key = f'employee_schedule_{employee_id}_{current_date}_{current_date}'
            cache.delete(key)
            current_date += timedelta(days=1)

    @staticmethod
    def clear_department_caches(department_ids: Set[int]) -> None:
        """Clear all caches related to departments"""
        for dept_id in department_ids:
            if dept_id:
                # Clear department shifts
                cache_key = f'department_shifts_{dept_id}'
                cache.delete(cache_key)

                # Clear department metrics
                today = timezone.now().date()
                for days in range(-30, 1):  # Past month
                    target_date = today + timedelta(days=days)
                    cache_key = f'attendance_metrics_{target_date.isoformat()}_{dept_id}'
                    cache.delete(cache_key)

    @classmethod
    def invalidate_shift_related_caches(
        cls,
        employee_ids: List[int],
        shift_id: Optional[int] = None,
        department_ids: Optional[Set[int]] = None
    ) -> None:
        """
        Invalidate all caches related to shift changes.
        
        Args:
            employee_ids: List of affected employee IDs
            shift_id: Optional shift ID if shift-specific caches need clearing
            department_ids: Optional set of department IDs to clear
        """
        # Clear shift statistics if provided
        if shift_id:
            cls.clear_shift_statistics_cache(shift_id)

        # Clear employee-specific caches
        for employee_id in employee_ids:
            cls.clear_employee_shift_cache(employee_id)
            cls.clear_employee_schedule_cache(employee_id)

        # Clear department caches if provided
        if department_ids:
            cls.clear_department_caches(department_ids)

    @classmethod
    def invalidate_ramadan_related_caches(
        cls,
        start_date: date,
        end_date: date,
        affected_employees: Optional[List[int]] = None
    ) -> None:
        """
        Invalidate all caches related to Ramadan period changes.
        
        Args:
            start_date: Start date of affected period
            end_date: End date of affected period
            affected_employees: Optional list of affected employee IDs
        """
        # Clear Ramadan period cache
        cls.clear_ramadan_period_cache(start_date, end_date)

        # Clear affected employee caches if provided
        if affected_employees:
            for employee_id in affected_employees:
                cls.clear_employee_shift_cache(employee_id)
                cls.clear_employee_schedule_cache(
                    employee_id,
                    start_date=start_date,
                    end_date=end_date
                )