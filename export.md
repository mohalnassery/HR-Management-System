### hrms_project\attendance\__init__.py
```
default_app_config = 'attendance.apps.AttendanceConfig'

"""
Attendance App

This Django app provides attendance and leave management functionality including:
- Daily attendance tracking with Friday rules
- Leave management with various leave types
- Holiday management with recurring holidays
- Calendar views for attendance, leaves, and holidays
"""

```

### hrms_project\attendance\admin.py
```
from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe

from .models import (
    Shift, ShiftAssignment, RamadanPeriod, AttendanceRecord, 
    AttendanceLog, Leave, LeaveType, Holiday
)

@admin.register(Shift)
class ShiftAdmin(admin.ModelAdmin):
    list_display = ('name', 'shift_type', 'timing_display', 'is_night_shift', 'grace_period', 'is_active')
    list_filter = ('shift_type', 'is_night_shift', 'is_active')
    search_fields = ('name', 'description')
    ordering = ('name',)
    
    def timing_display(self, obj):
        return f"{obj.start_time.strftime('%I:%M %p')} - {obj.end_time.strftime('%I:%M %p')}"
    timing_display.short_description = 'Timing'

@admin.register(ShiftAssignment)
class ShiftAssignmentAdmin(admin.ModelAdmin):
    list_display = ('employee_link', 'shift_link', 'period_display', 'is_active', 'created_by', 'created_at')
    list_filter = ('is_active', 'shift', 'created_at')
    search_fields = ('employee__first_name', 'employee__last_name', 'employee__employee_number', 'shift__name')
    ordering = ('-created_at',)
    raw_id_fields = ('employee', 'shift')
    
    def employee_link(self, obj):
        url = reverse('admin:employees_employee_change', args=[obj.employee.id])
        return format_html('<a href="{}">{}</a>', url, obj.employee)
    employee_link.short_description = 'Employee'
    
    def shift_link(self, obj):
        url = reverse('admin:attendance_shift_change', args=[obj.shift.id])
        return format_html('<a href="{}">{}</a>', url, obj.shift.name)
    shift_link.short_description = 'Shift'
    
    def period_display(self, obj):
        if obj.end_date:
            return f"{obj.start_date.strftime('%b %d, %Y')} - {obj.end_date.strftime('%b %d, %Y')}"
        return f"From {obj.start_date.strftime('%b %d, %Y')} (Permanent)"
    period_display.short_description = 'Period'

@admin.register(RamadanPeriod)
class RamadanPeriodAdmin(admin.ModelAdmin):
    list_display = ('year', 'start_date', 'end_date', 'duration_display', 'is_active')
    list_filter = ('year', 'is_active')
    search_fields = ('year',)
    ordering = ('-year',)
    
    def duration_display(self, obj):
        if obj.start_date and obj.end_date:
            duration = (obj.end_date - obj.start_date).days + 1
            return f"{duration} days"
        return "Not set"
    duration_display.short_description = 'Duration'

@admin.register(AttendanceLog)
class AttendanceLogAdmin(admin.ModelAdmin):
    list_display = ('employee_link', 'date', 'time_display', 'status_display', 'source')
    list_filter = ('date', 'source', 'status', 'is_active')  
    search_fields = ('employee__first_name', 'employee__last_name', 'employee__employee_number')
    date_hierarchy = 'date'
    ordering = ('-date', 'employee__first_name')
    raw_id_fields = ('employee',)

    def employee_link(self, obj):
        url = reverse('admin:employees_employee_change', args=[obj.employee.id])
        return format_html('<a href="{}">{}</a>', url, obj.employee)
    employee_link.short_description = 'Employee'

    def time_display(self, obj):
        if obj.first_in_time and obj.last_out_time:
            return f"{obj.first_in_time.strftime('%I:%M %p')} - {obj.last_out_time.strftime('%I:%M %p')}"
        return "No time records"
    time_display.short_description = 'Timing'

    def status_display(self, obj):
        status_colors = {
            'present': 'green',
            'absent': 'red',
            'late': 'orange',
            'leave': 'blue',
            'holiday': 'purple'
        }
        color = status_colors.get(obj.status, 'gray')
        return format_html(
            '<span style="color: {};">{}</span>',
            color,
            obj.get_status_display()
        )
    status_display.short_description = 'Status'

@admin.register(AttendanceRecord)
class AttendanceRecordAdmin(admin.ModelAdmin):
    list_display = ('employee_link', 'timestamp', 'event_point', 'device_name')  
    list_filter = ('event_point', 'timestamp')  
    search_fields = ('employee__first_name', 'employee__last_name', 'employee__employee_number', 'device_name')
    date_hierarchy = 'timestamp'
    ordering = ('-timestamp',)
    raw_id_fields = ('employee',)

    def employee_link(self, obj):
        url = reverse('admin:employees_employee_change', args=[obj.employee.id])
        return format_html('<a href="{}">{}</a>', url, obj.employee)
    employee_link.short_description = 'Employee'

@admin.register(Leave)
class LeaveAdmin(admin.ModelAdmin):
    list_display = ('employee_link', 'leave_type', 'period_display', 'duration', 'status', 'created_at')  
    list_filter = ('status', 'leave_type', 'created_at')
    search_fields = ('employee__first_name', 'employee__last_name', 'employee__employee_number')
    date_hierarchy = 'start_date'
    ordering = ('-created_at',)
    raw_id_fields = ('employee',)

    def employee_link(self, obj):
        url = reverse('admin:employees_employee_change', args=[obj.employee.id])
        return format_html('<a href="{}">{}</a>', url, obj.employee)
    employee_link.short_description = 'Employee'

    def period_display(self, obj):
        return f"{obj.start_date.strftime('%b %d, %Y')} - {obj.end_date.strftime('%b %d, %Y')}"
    period_display.short_description = 'Period'

@admin.register(LeaveType)
class LeaveTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'days_allowed', 'is_paid', 'is_active')
    list_filter = ('is_paid', 'is_active')
    search_fields = ('name', 'code')
    ordering = ('name',)

@admin.register(Holiday)
class HolidayAdmin(admin.ModelAdmin):
    list_display = ('name', 'date', 'is_recurring', 'is_active')
    list_filter = ('is_recurring', 'is_active')
    search_fields = ('name',)
    date_hierarchy = 'date'
    ordering = ('-date',)

```

### hrms_project\attendance\apps.py
```
from django.apps import AppConfig
from django.db.models.signals import post_save, post_delete


class AttendanceConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'attendance'
    verbose_name = 'Attendance Management'

    def ready(self):
        """
        Connect signal handlers when the app is ready
        """
        # Import signal handlers
        from . import signals

        # Attendance Record Signals
        # post_save.connect(signals.process_attendance_record, sender='attendance.AttendanceRecord')
        post_delete.connect(signals.cleanup_attendance_record, sender='attendance.AttendanceRecord')

        # Leave Request Signals
        post_save.connect(signals.process_leave_request, sender='attendance.Leave')
        post_delete.connect(signals.cleanup_leave_request, sender='attendance.Leave')
        
        # Holiday Signals
        post_save.connect(signals.process_holiday, sender='attendance.Holiday')
        post_delete.connect(signals.cleanup_holiday, sender='attendance.Holiday')

        # Leave Type Signals
        post_save.connect(signals.create_leave_balances, sender='attendance.LeaveType')

        # Initialize periodic tasks
        try:
            from django.conf import settings
            from .tasks import (
                process_monthly_leave_accruals,
                process_leave_year_reset,
                process_friday_attendance,
                process_recurring_holidays
            )
            
            # Schedule periodic tasks if Celery is configured
            if hasattr(settings, 'CELERY_BEAT_SCHEDULE'):
                settings.CELERY_BEAT_SCHEDULE.update({
                    'process-monthly-leave-accruals': {
                        'task': 'attendance.tasks.process_monthly_leave_accruals',
                        'schedule': 60 * 60 * 24,  # Daily at midnight (will only run on 1st day of month)
                    },
                    'process-leave-year-reset': {
                        'task': 'attendance.tasks.process_leave_year_reset',
                        'schedule': 60 * 60 * 24,  # Daily at midnight (will only run on Jan 1st)
                    },
                    'process-friday-attendance': {
                        'task': 'attendance.tasks.process_friday_attendance',
                        'schedule': 60 * 60 * 24,  # Daily at midnight (will only run on Fridays)
                    },
                    'process-recurring-holidays': {
                        'task': 'attendance.tasks.process_recurring_holidays',
                        'schedule': 60 * 60 * 24,  # Daily at midnight (will only run on Dec 1st)
                    },
                })
        except ImportError:
            # Celery not installed or configured, skip task scheduling
            pass

        # Load and register custom template tags
        from django.template.backends.django import get_installed_libraries
        get_installed_libraries()

```

### hrms_project\attendance\cache.py
```
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

```

### hrms_project\attendance\management\commands\__init__.py
```
"""
Management commands for attendance app.

Available commands:
- reset_annual_leave: Reset annual leave balances for all employees
- generate_holidays: Generate holidays for next year based on recurring holidays
"""

```

### hrms_project\attendance\management\commands\cleanup_shifts.py
```
import logging
from datetime import datetime, date, timedelta
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone
from django.db.models import Q, Count
from django.contrib.auth.models import User

from attendance.models import (
    Shift, ShiftAssignment, RamadanPeriod, AttendanceLog
)
from attendance.cache import (
    ShiftCache, RamadanCache, invalidate_department_caches,
    invalidate_employee_caches
)

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Cleanup and maintenance of shift-related data'

    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            type=int,
            default=90,
            help='Number of days to keep in history (default: 90)'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be deleted without actually deleting'
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force cleanup without confirmation'
        )
        parser.add_argument(
            '--archive',
            action='store_true',
            help='Archive data instead of deleting'
        )

    def handle(self, *args, **options):
        try:
            days = options['days']
            dry_run = options['dry_run']
            force = options['force']
            archive = options['archive']
            
            cutoff_date = timezone.now().date() - timedelta(days=days)
            
            self.stdout.write(
                self.style.WARNING(
                    f'\nStarting shift data cleanup for data older than {cutoff_date}'
                )
            )
            
            if dry_run:
                self.stdout.write(
                    self.style.WARNING('DRY RUN - No data will be deleted')
                )
            
            # Confirm unless --force is used
            if not dry_run and not force:
                confirm = input(
                    '\nThis will permanently delete old shift data. '
                    'Are you sure? [y/N]: '
                )
                if confirm.lower() != 'y':
                    self.stdout.write('Operation cancelled.')
                    return
            
            with transaction.atomic():
                # Clean up expired shift assignments
                self.cleanup_shift_assignments(cutoff_date, dry_run, archive)
                
                # Clean up old Ramadan periods
                self.cleanup_ramadan_periods(cutoff_date, dry_run, archive)
                
                # Clean up orphaned shifts
                self.cleanup_orphaned_shifts(dry_run)
                
                # Clean up duplicate assignments
                self.cleanup_duplicate_assignments(dry_run)
                
                if not dry_run:
                    # Clear relevant caches
                    self.clear_caches()
            
            self.stdout.write(self.style.SUCCESS('\nCleanup completed successfully'))
            
        except Exception as e:
            self.stderr.write(
                self.style.ERROR(f'Error during cleanup: {str(e)}')
            )
            logger.error('Error in cleanup_shifts command', exc_info=True)

    def cleanup_shift_assignments(self, cutoff_date, dry_run, archive):
        """Clean up old shift assignments"""
        old_assignments = ShiftAssignment.objects.filter(
            end_date__lt=cutoff_date,
            is_active=False
        )
        
        count = old_assignments.count()
        self.stdout.write(f'\nFound {count} old shift assignments')
        
        if not dry_run:
            if archive:
                # Archive assignments before deleting
                self.archive_assignments(old_assignments)
            
            # Delete assignments
            old_assignments.delete()
            self.stdout.write(f'Deleted {count} old assignments')

    def cleanup_ramadan_periods(self, cutoff_date, dry_run, archive):
        """Clean up old Ramadan periods"""
        old_periods = RamadanPeriod.objects.filter(
            end_date__lt=cutoff_date,
            is_active=False
        )
        
        count = old_periods.count()
        self.stdout.write(f'\nFound {count} old Ramadan periods')
        
        if not dry_run:
            if archive:
                # Archive periods before deleting
                self.archive_ramadan_periods(old_periods)
            
            # Delete periods
            old_periods.delete()
            self.stdout.write(f'Deleted {count} old periods')

    def cleanup_orphaned_shifts(self, dry_run):
        """Clean up shifts with no assignments"""
        orphaned_shifts = Shift.objects.filter(
            shiftassignment__isnull=True
        )
        
        count = orphaned_shifts.count()
        self.stdout.write(f'\nFound {count} orphaned shifts')
        
        if not dry_run:
            orphaned_shifts.delete()
            self.stdout.write(f'Deleted {count} orphaned shifts')

    def cleanup_duplicate_assignments(self, dry_run):
        """Clean up duplicate active assignments for employees"""
        duplicates = ShiftAssignment.objects.filter(
            is_active=True
        ).values(
            'employee'
        ).annotate(
            count=Count('id')
        ).filter(
            count__gt=1
        )
        
        count = len(duplicates)
        self.stdout.write(f'\nFound {count} employees with multiple active assignments')
        
        if not dry_run:
            for dup in duplicates:
                # Keep only the most recent assignment
                assignments = ShiftAssignment.objects.filter(
                    employee_id=dup['employee'],
                    is_active=True
                ).order_by('-created_at')
                
                # Deactivate all but the most recent
                assignments.exclude(id=assignments[0].id).update(is_active=False)
            
            self.stdout.write(f'Fixed {count} duplicate assignments')

    def archive_assignments(self, assignments):
        """Archive shift assignments to file"""
        timestamp = timezone.now().strftime('%Y%m%d_%H%M%S')
        filename = f'shift_assignments_archive_{timestamp}.csv'
        
        with open(filename, 'w') as f:
            # Write header
            f.write('employee_id,shift_id,start_date,end_date,created_at\n')
            
            # Write data
            for assignment in assignments:
                f.write(
                    f'{assignment.employee_id},{assignment.shift_id},'
                    f'{assignment.start_date},{assignment.end_date},'
                    f'{assignment.created_at}\n'
                )
        
        self.stdout.write(f'Archived assignments to {filename}')

    def archive_ramadan_periods(self, periods):
        """Archive Ramadan periods to file"""
        timestamp = timezone.now().strftime('%Y%m%d_%H%M%S')
        filename = f'ramadan_periods_archive_{timestamp}.csv'
        
        with open(filename, 'w') as f:
            # Write header
            f.write('year,start_date,end_date,is_active\n')
            
            # Write data
            for period in periods:
                f.write(
                    f'{period.year},{period.start_date},'
                    f'{period.end_date},{period.is_active}\n'
                )
        
        self.stdout.write(f'Archived Ramadan periods to {filename}')

    def clear_caches(self):
        """Clear all related caches"""
        RamadanCache.clear_all_periods()
        
        # Clear department caches
        departments = set(ShiftAssignment.objects.values_list(
            'employee__department_id',
            flat=True
        ))
        for dept_id in departments:
            if dept_id:
                invalidate_department_caches(dept_id)
        
        self.stdout.write('Cleared relevant caches')

```

### hrms_project\attendance\management\commands\generate_holidays.py
```
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db import transaction
from attendance.models import Holiday
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Generate holidays for next year based on recurring holidays'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Run without making changes to see what would happen',
        )
        parser.add_argument(
            '--year',
            type=int,
            help='Specify year to generate (defaults to next year)',
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force generation even if not December',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        force = options['force']
        target_year = options['year'] or timezone.now().year + 1
        current_month = timezone.now().month

        # Check if it's December or force flag is set
        if current_month != 12 and not force:
            self.stdout.write(
                self.style.WARNING(
                    'Holiday generation should be run in December. '
                    'Use --force to override.'
                )
            )
            return

        self.stdout.write(
            self.style.SUCCESS(f'Starting holiday generation for year {target_year}')
        )
        if dry_run:
            self.stdout.write(
                self.style.WARNING('DRY RUN - no changes will be made')
            )

        try:
            with transaction.atomic():
                # Get all recurring holidays
                recurring_holidays = Holiday.objects.filter(
                    is_recurring=True,
                    is_active=True
                )

                self.stdout.write(
                    f'Found {recurring_holidays.count()} recurring holidays'
                )

                holidays_created = 0
                holidays_skipped = 0

                # Process each recurring holiday
                for holiday in recurring_holidays:
                    # Create date for target year
                    try:
                        new_date = holiday.date.replace(year=target_year)
                        
                        # Check if holiday already exists
                        existing = Holiday.objects.filter(
                            date=new_date,
                            name=holiday.name
                        ).exists()
                        
                        if existing:
                            self.stdout.write(
                                f'  Skipping {holiday.name} - already exists on {new_date}'
                            )
                            holidays_skipped += 1
                            continue

                        # Create new holiday instance
                        if not dry_run:
                            new_holiday = Holiday.objects.create(
                                date=new_date,
                                name=holiday.name,
                                description=holiday.description,
                                holiday_type=holiday.holiday_type,
                                is_paid=holiday.is_paid,
                                is_recurring=False  # New instance is not recurring
                            )
                            
                            # Copy department associations if any
                            if holiday.applicable_departments.exists():
                                new_holiday.applicable_departments.set(
                                    holiday.applicable_departments.all()
                                )

                        self.stdout.write(
                            f'  Created {holiday.name} on {new_date}'
                        )
                        holidays_created += 1

                    except Exception as e:
                        logger.error(
                            f'Error processing holiday {holiday.name}: {str(e)}'
                        )
                        if not dry_run:
                            raise

                if dry_run:
                    transaction.set_rollback(True)
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'Dry run completed - would create {holidays_created} '
                            f'holidays ({holidays_skipped} skipped)'
                        )
                    )
                else:
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'Successfully created {holidays_created} holidays '
                            f'({holidays_skipped} skipped)'
                        )
                    )

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error generating holidays: {str(e)}')
            )
            logger.error(f'Holiday generation failed: {str(e)}')
            raise

```

### hrms_project\attendance\management\commands\generate_report.py
```
import logging
from django.core.management.base import BaseCommand
from django.template.loader import render_to_string
from django.utils import timezone
from django.db.models import Count, Avg, Q, Sum, F, ExpressionWrapper, fields
from django.db.models.functions import ExtractHour, ExtractMinute
from datetime import datetime, timedelta
from attendance.models import AttendanceLog, Leave, LeaveType, LeaveBalance
from employees.models import Employee, Department
import os
import csv
from io import StringIO
import json

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Generate attendance and leave reports for specified period'

    def add_arguments(self, parser):
        parser.add_argument(
            '--report-type',
            type=str,
            choices=['daily', 'weekly', 'monthly', 'custom'],
            default='monthly',
            help='Type of report to generate'
        )
        parser.add_argument(
            '--start-date',
            type=str,
            help='Start date for custom report (YYYY-MM-DD)'
        )
        parser.add_argument(
            '--end-date',
            type=str,
            help='End date for custom report (YYYY-MM-DD)'
        )
        parser.add_argument(
            '--department',
            type=int,
            help='Department ID to filter report'
        )
        parser.add_argument(
            '--employee',
            type=int,
            help='Employee ID to generate individual report'
        )
        parser.add_argument(
            '--format',
            type=str,
            choices=['html', 'csv', 'json'],
            default='html',
            help='Output format for the report'
        )
        parser.add_argument(
            '--output-dir',
            type=str,
            help='Directory to save report files'
        )

    def handle(self, *args, **options):
        report_type = options['report_type']
        format_type = options['format']
        output_dir = options.get('output_dir') or 'reports'

        # Ensure output directory exists
        os.makedirs(output_dir, exist_ok=True)

        # Calculate date range
        end_date = timezone.now().date()
        if report_type == 'daily':
            start_date = end_date
        elif report_type == 'weekly':
            start_date = end_date - timedelta(days=7)
        elif report_type == 'monthly':
            start_date = end_date.replace(day=1)
        else:  # custom
            try:
                start_date = datetime.strptime(options['start_date'], '%Y-%m-%d').date()
                end_date = datetime.strptime(options['end_date'], '%Y-%m-%d').date()
            except (ValueError, TypeError):
                self.stderr.write('Invalid date format. Use YYYY-MM-DD')
                return

        # Get filters
        department_id = options.get('department')
        employee_id = options.get('employee')

        try:
            # Generate reports based on scope
            if employee_id:
                self._generate_employee_report(
                    employee_id, start_date, end_date, format_type, output_dir
                )
            elif department_id:
                self._generate_department_report(
                    department_id, start_date, end_date, format_type, output_dir
                )
            else:
                self._generate_organization_report(
                    start_date, end_date, format_type, output_dir
                )

            self.stdout.write(self.style.SUCCESS(
                f'Successfully generated {report_type} report(s) in {format_type} format'
            ))

        except Exception as e:
            logger.error(f'Error generating report: {str(e)}')
            self.stderr.write(f'Error generating report: {str(e)}')
            raise

    def _generate_employee_report(self, employee_id, start_date, end_date, format_type, output_dir):
        """Generate detailed report for a single employee"""
        employee = Employee.objects.get(id=employee_id)
        
        # Get attendance logs
        attendance_logs = AttendanceLog.objects.filter(
            employee=employee,
            date__range=[start_date, end_date]
        ).order_by('date')

        # Calculate attendance statistics
        total_days = (end_date - start_date).days + 1
        present_days = attendance_logs.filter(first_in_time__isnull=False).count()
        absent_days = attendance_logs.filter(first_in_time__isnull=True).count()
        late_days = attendance_logs.filter(is_late=True).count()

        # Calculate average arrival and departure times
        avg_arrival = attendance_logs.exclude(
            first_in_time__isnull=True
        ).annotate(
            hour=ExtractHour('first_in_time'),
            minute=ExtractMinute('first_in_time')
        ).aggregate(
            avg_hour=Avg('hour'),
            avg_minute=Avg('minute')
        )

        # Get leave information
        leaves = Leave.objects.filter(
            employee=employee,
            start_date__lte=end_date,
            end_date__gte=start_date
        ).select_related('leave_type')

        # Get leave balances
        leave_balances = LeaveBalance.objects.filter(
            employee=employee,
            is_active=True
        ).select_related('leave_type')

        report_data = {
            'employee': employee,
            'period': {
                'start_date': start_date,
                'end_date': end_date,
                'total_days': total_days
            },
            'attendance': {
                'present_days': present_days,
                'absent_days': absent_days,
                'late_days': late_days,
                'attendance_rate': (present_days / total_days * 100) if total_days > 0 else 0,
                'avg_arrival_time': (
                    f"{int(avg_arrival['avg_hour'] or 0):02d}:"
                    f"{int(avg_arrival['avg_minute'] or 0):02d}"
                ),
                'logs': attendance_logs
            },
            'leaves': leaves,
            'leave_balances': leave_balances,
            'generated_at': timezone.now()
        }

        # Generate report in specified format
        filename = f"employee_report_{employee.employee_number}_{start_date}_{end_date}"
        self._save_report(report_data, format_type, filename, output_dir, 'employee_report.html')

    def _generate_department_report(self, department_id, start_date, end_date, format_type, output_dir):
        """Generate summary report for a department"""
        department = Department.objects.get(id=department_id)
        employees = Employee.objects.filter(department=department, is_active=True)

        # Calculate department statistics
        total_days = (end_date - start_date).days + 1
        attendance_stats = AttendanceLog.objects.filter(
            employee__department=department,
            date__range=[start_date, end_date]
        ).aggregate(
            total_present=Count('id', filter=Q(first_in_time__isnull=False)),
            total_absent=Count('id', filter=Q(first_in_time__isnull=True)),
            total_late=Count('id', filter=Q(is_late=True))
        )

        # Calculate leave statistics
        leave_stats = Leave.objects.filter(
            employee__department=department,
            start_date__lte=end_date,
            end_date__gte=start_date,
            status='approved'
        ).values('leave_type__name').annotate(
            total_days=Count('id'),
            total_employees=Count('employee', distinct=True)
        )

        report_data = {
            'department': department,
            'period': {
                'start_date': start_date,
                'end_date': end_date,
                'total_days': total_days
            },
            'statistics': {
                'total_employees': employees.count(),
                'present_rate': (attendance_stats['total_present'] / (total_days * employees.count()) * 100) if employees.count() > 0 else 0,
                'absent_rate': (attendance_stats['total_absent'] / (total_days * employees.count()) * 100) if employees.count() > 0 else 0,
                'late_rate': (attendance_stats['total_late'] / attendance_stats['total_present'] * 100) if attendance_stats['total_present'] > 0 else 0,
            },
            'attendance': attendance_stats,
            'leave_stats': leave_stats,
            'employees': employees,
            'generated_at': timezone.now()
        }

        # Generate report in specified format
        filename = f"department_report_{department.code}_{start_date}_{end_date}"
        self._save_report(report_data, format_type, filename, output_dir, 'department_report.html')

    def _generate_organization_report(self, start_date, end_date, format_type, output_dir):
        """Generate overall organization attendance and leave report"""
        departments = Department.objects.all()
        total_days = (end_date - start_date).days + 1

        # Overall statistics
        org_stats = AttendanceLog.objects.filter(
            date__range=[start_date, end_date]
        ).aggregate(
            total_present=Count('id', filter=Q(first_in_time__isnull=False)),
            total_absent=Count('id', filter=Q(first_in_time__isnull=True)),
            total_late=Count('id', filter=Q(is_late=True))
        )

        # Department-wise statistics
        dept_stats = []
        for dept in departments:
            stats = AttendanceLog.objects.filter(
                employee__department=dept,
                date__range=[start_date, end_date]
            ).aggregate(
                present=Count('id', filter=Q(first_in_time__isnull=False)),
                absent=Count('id', filter=Q(first_in_time__isnull=True)),
                late=Count('id', filter=Q(is_late=True))
            )
            dept_stats.append({
                'department': dept,
                'stats': stats
            })

        # Leave type statistics
        leave_stats = Leave.objects.filter(
            start_date__lte=end_date,
            end_date__gte=start_date,
            status='approved'
        ).values('leave_type__name').annotate(
            total_days=Count('id'),
            total_employees=Count('employee', distinct=True)
        )

        report_data = {
            'period': {
                'start_date': start_date,
                'end_date': end_date,
                'total_days': total_days
            },
            'organization': {
                'total_departments': departments.count(),
                'total_employees': Employee.objects.filter(is_active=True).count(),
                'stats': org_stats
            },
            'department_stats': dept_stats,
            'leave_stats': leave_stats,
            'generated_at': timezone.now()
        }

        # Generate report in specified format
        filename = f"organization_report_{start_date}_{end_date}"
        self._save_report(report_data, format_type, filename, output_dir, 'organization_report.html')

    def _save_report(self, data, format_type, filename, output_dir, template_name):
        """Save report in specified format"""
        if format_type == 'html':
            content = render_to_string(f'attendance/reports/{template_name}', data)
            filepath = os.path.join(output_dir, f'{filename}.html')
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)

        elif format_type == 'csv':
            filepath = os.path.join(output_dir, f'{filename}.csv')
            with open(filepath, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                self._write_csv_data(writer, data)

        elif format_type == 'json':
            filepath = os.path.join(output_dir, f'{filename}.json')
            with open(filepath, 'w', encoding='utf-8') as f:
                # Convert datetime objects to string format
                json.dump(self._prepare_json_data(data), f, indent=2, default=str)

    def _write_csv_data(self, writer, data):
        """Convert report data to CSV format"""
        # Write header
        writer.writerow(['Report Generated:', data['generated_at'].strftime('%Y-%m-%d %H:%M:%S')])
        writer.writerow(['Period:', f"{data['period']['start_date']} to {data['period']['end_date']}"])
        writer.writerow([])

        # Write statistics
        if 'statistics' in data:
            writer.writerow(['Statistics'])
            for key, value in data['statistics'].items():
                writer.writerow([key.replace('_', ' ').title(), f"{value:.2f}%"])
            writer.writerow([])

        # Write attendance data if available
        if 'attendance' in data and isinstance(data['attendance'], dict):
            writer.writerow(['Attendance Summary'])
            for key, value in data['attendance'].items():
                writer.writerow([key.replace('_', ' ').title(), value])

    def _prepare_json_data(self, data):
        """Prepare data for JSON serialization"""
        # Convert model instances to dictionaries
        if isinstance(data, dict):
            return {k: self._prepare_json_data(v) for k, v in data.items()}
        elif hasattr(data, '_meta'):  # Django model instance
            return {
                field.name: getattr(data, field.name)
                for field in data._meta.fields
            }
        elif isinstance(data, (list, tuple)):
            return [self._prepare_json_data(item) for item in data]
        return data

```

### hrms_project\attendance\management\commands\import_attendance.py
```
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from django.db import transaction
from employees.models import Employee
from attendance.models import AttendanceRecord
import pandas as pd
import logging
from datetime import datetime
import pytz

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Import attendance records from machine export file (Excel/CSV)'

    def add_arguments(self, parser):
        parser.add_argument('file_path', type=str, help='Path to the input file')
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Run without making changes to see what would happen',
        )
        parser.add_argument(
            '--format',
            choices=['excel', 'csv'],
            default='excel',
            help='Input file format (default: excel)',
        )
        parser.add_argument(
            '--timezone',
            default='Asia/Riyadh',
            help='Timezone for timestamps (default: Asia/Riyadh)',
        )
        parser.add_argument(
            '--skip-rows',
            type=int,
            default=0,
            help='Number of header rows to skip',
        )

    def handle(self, *args, **options):
        file_path = options['file_path']
        dry_run = options['dry_run']
        file_format = options['format']
        tz = pytz.timezone(options['timezone'])
        skip_rows = options['skip_rows']

        self.stdout.write(
            self.style.SUCCESS(f'Starting attendance import from {file_path}')
        )
        if dry_run:
            self.stdout.write(
                self.style.WARNING('DRY RUN - no changes will be made')
            )

        try:
            # Read the file
            if file_format == 'excel':
                df = pd.read_excel(file_path, skiprows=skip_rows)
            else:
                df = pd.read_csv(file_path, skiprows=skip_rows)

            # Expected columns with possible variations
            employee_id_cols = ['Personnel ID', 'Employee ID', 'ID', 'Badge']
            timestamp_cols = ['Date And Time', 'DateTime', 'Timestamp', 'Time']
            device_cols = ['Device Name', 'Device', 'Terminal']
            event_cols = ['Event Point', 'Event', 'Type']

            # Find actual column names in the file
            employee_id_col = next((col for col in employee_id_cols if col in df.columns), None)
            timestamp_col = next((col for col in timestamp_cols if col in df.columns), None)
            device_col = next((col for col in device_cols if col in df.columns), None)
            event_col = next((col for col in event_cols if col in df.columns), None)

            if not all([employee_id_col, timestamp_col]):
                raise CommandError('Required columns not found in the file')

            records_created = 0
            duplicates = 0
            errors = 0

            with transaction.atomic():
                for _, row in df.iterrows():
                    try:
                        # Get employee
                        employee_number = str(row[employee_id_col]).strip()
                        try:
                            employee = Employee.objects.get(employee_number=employee_number)
                        except Employee.DoesNotExist:
                            self.stdout.write(
                                self.style.WARNING(
                                    f'Employee not found: {employee_number}'
                                )
                            )
                            errors += 1
                            continue

                        # Parse timestamp
                        try:
                            timestamp = pd.to_datetime(row[timestamp_col])
                            timestamp = tz.localize(timestamp.replace(tzinfo=None))
                        except Exception as e:
                            self.stdout.write(
                                self.style.ERROR(
                                    f'Invalid timestamp for {employee_number}: {str(e)}'
                                )
                            )
                            errors += 1
                            continue

                        # Check for duplicate record
                        if AttendanceRecord.objects.filter(
                            employee=employee,
                            timestamp=timestamp,
                            is_active=True
                        ).exists():
                            duplicates += 1
                            continue

                        # Create attendance record
                        if not dry_run:
                            record = AttendanceRecord.objects.create(
                                employee=employee,
                                timestamp=timestamp,
                                device_name=row.get(device_col, ''),
                                event_point=row.get(event_col, ''),
                                source='import'
                            )
                            records_created += 1

                    except Exception as e:
                        self.stdout.write(
                            self.style.ERROR(f'Error processing row: {str(e)}')
                        )
                        logger.error(f'Import error: {str(e)}', exc_info=True)
                        errors += 1
                        if not dry_run:
                            raise

                if dry_run:
                    transaction.set_rollback(True)
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'Dry run completed - would create {records_created} records\n'
                            f'Duplicates: {duplicates}\n'
                            f'Errors: {errors}'
                        )
                    )
                else:
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'Successfully created {records_created} records\n'
                            f'Duplicates: {duplicates}\n'
                            f'Errors: {errors}'
                        )
                    )

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error importing attendance records: {str(e)}')
            )
            logger.error(f'Attendance import failed: {str(e)}', exc_info=True)
            raise CommandError(str(e))

```

### hrms_project\attendance\management\commands\init_leave_types.py
```
from django.core.management.base import BaseCommand
from django.db import transaction
from attendance.models import LeaveType
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Initialize default leave types with standard configurations'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force creation even if leave types exist',
        )

    def handle(self, *args, **options):
        force = options['force']

        # Check if leave types already exist
        if LeaveType.objects.exists() and not force:
            self.stdout.write(
                self.style.WARNING(
                    'Leave types already exist. Use --force to reinitialize.'
                )
            )
            return

        try:
            with transaction.atomic():
                # Define default leave types
                leave_types = [
                    {
                        'code': 'EMERG',
                        'name': 'Emergency Leave',
                        'description': 'For emergency situations requiring immediate leave',
                        'default_days': 15,
                        'accrual_type': 'fixed',
                        'requires_document': False,
                        'reset_period': 'yearly',
                        'allow_carryover': False,
                        'gender_specific': 'A',  # All genders
                        'is_paid': True,
                    },
                    {
                        'code': 'ANNUAL',
                        'name': 'Annual Leave',
                        'description': 'Standard annual leave accrued based on working days',
                        'default_days': 0,  # Accrued at 2.5 days per 30 worked days
                        'accrual_type': 'periodic',
                        'accrual_rate': 2.5,
                        'accrual_period': 30,
                        'requires_document': False,
                        'reset_period': 'yearly',
                        'allow_carryover': True,
                        'max_carryover': 30,
                        'gender_specific': 'A',
                    },
                    {
                        'code': 'SICK_REG',
                        'name': 'Sick Leave (Regular)',
                        'description': 'Regular sick leave with three tiers',
                        'default_days': 15,  # Tier 1
                        'accrual_type': 'fixed',
                        'requires_document': True,
                        'reset_period': 'yearly',
                        'allow_carryover': False,
                        'gender_specific': 'A',
                        'is_paid': True,
                        'has_tiers': True,
                        'tier_2_days': 20,  # Half paid
                        'tier_3_days': 20,  # Unpaid
                    },
                    {
                        'code': 'INJURY',
                        'name': 'Injury Leave',
                        'description': 'Leave for work-related injuries',
                        'default_days': 365,  # Unlimited but set to 1 year for tracking
                        'accrual_type': 'fixed',
                        'requires_document': True,
                        'reset_period': 'never',
                        'allow_carryover': True,
                        'gender_specific': 'A',
                        'is_paid': True,
                    },
                    {
                        'code': 'MATERNITY',
                        'name': 'Maternity Leave',
                        'description': 'Maternity leave for female employees',
                        'default_days': 60,
                        'accrual_type': 'fixed',
                        'requires_document': True,
                        'reset_period': 'never',
                        'allow_carryover': False,
                        'gender_specific': 'F',
                        'is_paid': True,
                    },
                    {
                        'code': 'PATERNITY',
                        'name': 'Paternity Leave',
                        'description': 'Paternity leave for male employees',
                        'default_days': 1,
                        'accrual_type': 'fixed',
                        'requires_document': True,
                        'reset_period': 'never',
                        'allow_carryover': False,
                        'gender_specific': 'M',
                        'is_paid': True,
                    },
                    {
                        'code': 'MARRIAGE',
                        'name': 'Marriage Leave',
                        'description': 'Leave for employee marriage',
                        'default_days': 3,
                        'accrual_type': 'fixed',
                        'requires_document': True,
                        'reset_period': 'never',
                        'allow_carryover': False,
                        'gender_specific': 'A',
                        'is_paid': True,
                    },
                    {
                        'code': 'DEATH',
                        'name': 'Relative Death Leave',
                        'description': 'Leave for death of immediate family member',
                        'default_days': 3,
                        'accrual_type': 'fixed',
                        'requires_document': True,
                        'reset_period': 'never',
                        'allow_carryover': False,
                        'gender_specific': 'A',
                        'is_paid': True,
                    },
                    {
                        'code': 'PERM',
                        'name': 'Permission Leave',
                        'description': 'Short permission leave (tracked in hours)',
                        'default_days': 8,  # 8 hours = 1 day
                        'accrual_type': 'fixed',
                        'requires_document': False,
                        'reset_period': 'monthly',
                        'allow_carryover': False,
                        'gender_specific': 'A',
                        'is_paid': True,
                        'unit_type': 'hours',
                    },
                ]

                for leave_type_data in leave_types:
                    leave_type = LeaveType.objects.create(**leave_type_data)
                    self.stdout.write(
                        f'Created leave type: {leave_type.name}'
                    )

                self.stdout.write(
                    self.style.SUCCESS(
                        f'Successfully initialized {len(leave_types)} leave types'
                    )
                )

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error initializing leave types: {str(e)}')
            )
            logger.error(f'Leave type initialization failed: {str(e)}')
            raise

```

### hrms_project\attendance\management\commands\init_ramadan_periods.py
```
import logging
from datetime import date
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from attendance.models import RamadanPeriod

logger = logging.getLogger(__name__)

# Sample Ramadan periods for the next few years
# Dates are approximate and should be adjusted based on actual calendar
SAMPLE_PERIODS = [
    {
        'year': 2024,
        'start_date': date(2024, 3, 11),
        'end_date': date(2024, 4, 9),
        'is_active': True,
    },
    {
        'year': 2025,
        'start_date': date(2025, 3, 1),
        'end_date': date(2025, 3, 30),
        'is_active': False,
    },
    {
        'year': 2026,
        'start_date': date(2026, 2, 18),
        'end_date': date(2026, 3, 19),
        'is_active': False,
    }
]

class Command(BaseCommand):
    help = 'Initialize sample Ramadan periods in the system'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force recreation of Ramadan periods even if they exist',
        )

    def handle(self, *args, **options):
        try:
            with transaction.atomic():
                created_count = 0
                updated_count = 0
                skipped_count = 0

                for period_data in SAMPLE_PERIODS:
                    year = period_data['year']

                    if options['force']:
                        # Update or create
                        period, created = RamadanPeriod.objects.update_or_create(
                            year=year,
                            defaults={
                                **period_data,
                                'created_at': timezone.now(),
                                'updated_at': timezone.now()
                            }
                        )
                        if created:
                            created_count += 1
                            self.stdout.write(
                                self.style.SUCCESS(f'Created Ramadan period for {year}')
                            )
                        else:
                            updated_count += 1
                            self.stdout.write(
                                self.style.WARNING(f'Updated Ramadan period for {year}')
                            )
                    else:
                        # Only create if doesn't exist
                        if not RamadanPeriod.objects.filter(year=year).exists():
                            RamadanPeriod.objects.create(
                                **period_data,
                                created_at=timezone.now(),
                                updated_at=timezone.now()
                            )
                            created_count += 1
                            self.stdout.write(
                                self.style.SUCCESS(f'Created Ramadan period for {year}')
                            )
                        else:
                            skipped_count += 1
                            self.stdout.write(
                                self.style.WARNING(f'Skipped existing period for {year}')
                            )

                # Print summary
                self.stdout.write('\nSummary:')
                self.stdout.write(f'Created: {created_count}')
                if options['force']:
                    self.stdout.write(f'Updated: {updated_count}')
                else:
                    self.stdout.write(f'Skipped: {skipped_count}')
                self.stdout.write(
                    self.style.SUCCESS('Successfully initialized Ramadan periods')
                )

        except Exception as e:
            self.stderr.write(
                self.style.ERROR(f'Error initializing Ramadan periods: {str(e)}')
            )
            logger.error('Error in init_ramadan_periods command', exc_info=True)

    def validate_period(self, start_date, end_date):
        """Validate Ramadan period dates"""
        if end_date < start_date:
            raise ValueError("End date cannot be before start date")

        duration = (end_date - start_date).days + 1
        if duration < 28 or duration > 31:
            raise ValueError(f"Invalid duration: {duration} days")

        if start_date.year != end_date.year:
            raise ValueError("Start and end dates must be in the same year")

        return True

```

### hrms_project\attendance\management\commands\init_shift_types.py
```
import logging
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone
from datetime import time

from attendance.models import Shift

logger = logging.getLogger(__name__)

DEFAULT_SHIFTS = [
    {
        'name': 'Regular Day Shift',
        'shift_type': 'REGULAR',
        'start_time': time(8, 0),  # 8:00 AM
        'end_time': time(17, 0),   # 5:00 PM
        'break_duration': 60,      # 1 hour lunch break
        'grace_period': 15,        # 15 minutes grace period
        'description': 'Standard working hours from 8 AM to 5 PM'
    },
    {
        'name': 'Night Shift',
        'shift_type': 'NIGHT',
        'start_time': time(20, 0),  # 8:00 PM
        'end_time': time(5, 0),     # 5:00 AM next day
        'break_duration': 45,       # 45 minutes break
        'grace_period': 15,
        'is_night_shift': True,
        'description': 'Night shift from 8 PM to 5 AM'
    },
    {
        'name': 'Morning Shift',
        'shift_type': 'REGULAR',
        'start_time': time(6, 0),   # 6:00 AM
        'end_time': time(14, 0),    # 2:00 PM
        'break_duration': 30,       # 30 minutes break
        'grace_period': 10,
        'description': 'Early morning shift from 6 AM to 2 PM'
    },
    {
        'name': 'Evening Shift',
        'shift_type': 'REGULAR',
        'start_time': time(14, 0),  # 2:00 PM
        'end_time': time(22, 0),    # 10:00 PM
        'break_duration': 45,       # 45 minutes break
        'grace_period': 15,
        'description': 'Evening shift from 2 PM to 10 PM'
    },
    {
        'name': 'Flexible Hours',
        'shift_type': 'FLEXIBLE',
        'start_time': time(7, 0),   # 7:00 AM
        'end_time': time(19, 0),    # 7:00 PM
        'break_duration': 60,
        'grace_period': 30,         # Longer grace period for flexible hours
        'description': 'Flexible working hours between 7 AM and 7 PM'
    },
    {
        'name': 'Split Shift',
        'shift_type': 'SPLIT',
        'start_time': time(9, 0),   # 9:00 AM
        'end_time': time(20, 0),    # 8:00 PM
        'break_duration': 180,      # 3 hours break
        'grace_period': 15,
        'description': 'Split shift with extended break in between'
    },
    {
        'name': 'Ramadan Shift',
        'shift_type': 'RAMADAN',
        'start_time': time(9, 0),   # 9:00 AM
        'end_time': time(15, 0),    # 3:00 PM
        'break_duration': 0,        # No break during Ramadan hours
        'grace_period': 15,
        'description': 'Reduced hours during Ramadan'
    }
]

class Command(BaseCommand):
    help = 'Initialize default shift types in the system'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force recreation of shift types even if they exist',
        )

    def handle(self, *args, **options):
        try:
            with transaction.atomic():
                created_count = 0
                updated_count = 0
                skipped_count = 0

                for shift_data in DEFAULT_SHIFTS:
                    shift_name = shift_data['name']
                    
                    if options['force']:
                        # Update or create
                        shift, created = Shift.objects.update_or_create(
                            name=shift_name,
                            defaults={
                                **shift_data,
                                'created_at': timezone.now(),
                                'updated_at': timezone.now()
                            }
                        )
                        if created:
                            created_count += 1
                            self.stdout.write(
                                self.style.SUCCESS(f'Created shift: {shift_name}')
                            )
                        else:
                            updated_count += 1
                            self.stdout.write(
                                self.style.WARNING(f'Updated shift: {shift_name}')
                            )
                    else:
                        # Only create if doesn't exist
                        if not Shift.objects.filter(name=shift_name).exists():
                            Shift.objects.create(
                                **shift_data,
                                created_at=timezone.now(),
                                updated_at=timezone.now()
                            )
                            created_count += 1
                            self.stdout.write(
                                self.style.SUCCESS(f'Created shift: {shift_name}')
                            )
                        else:
                            skipped_count += 1
                            self.stdout.write(
                                self.style.WARNING(f'Skipped existing shift: {shift_name}')
                            )

                # Print summary
                self.stdout.write('\nSummary:')
                self.stdout.write(f'Created: {created_count}')
                if options['force']:
                    self.stdout.write(f'Updated: {updated_count}')
                else:
                    self.stdout.write(f'Skipped: {skipped_count}')
                self.stdout.write(
                    self.style.SUCCESS('Successfully initialized shift types')
                )

        except Exception as e:
            self.stderr.write(
                self.style.ERROR(f'Error initializing shift types: {str(e)}')
            )
            logger.error('Error in init_shift_types command', exc_info=True)

```

### hrms_project\attendance\management\commands\recalculate_leave_balance.py
```
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from django.db import transaction
from django.db.models import Count, Q
from employees.models import Employee
from attendance.models import (
    AttendanceLog, Leave, LeaveType, LeaveBalance
)
from attendance.services import LeaveBalanceService
import logging
from datetime import datetime, date, timedelta
from calendar import monthrange

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Recalculate leave balances based on attendance records'

    def add_arguments(self, parser):
        parser.add_argument(
            '--start-date',
            type=str,
            help='Start date (YYYY-MM-DD)',
        )
        parser.add_argument(
            '--end-date',
            type=str,
            help='End date (YYYY-MM-DD)',
        )
        parser.add_argument(
            '--month',
            type=int,
            help='Month (1-12) - alternative to start/end dates',
        )
        parser.add_argument(
            '--year',
            type=int,
            help='Year for processing',
        )
        parser.add_argument(
            '--employee',
            type=int,
            help='Employee ID to process',
        )
        parser.add_argument(
            '--leave-type',
            help='Leave type code to process (e.g., ANNUAL)',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Run without making changes to see what would happen',
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force update even if balances exist',
        )

    def handle(self, *args, **options):
        # Process date range
        if options['month']:
            year = options['year'] or timezone.now().year
            month = options['month']
            _, last_day = monthrange(year, month)
            start_date = date(year, month, 1)
            end_date = date(year, month, last_day)
        else:
            try:
                start_date = datetime.strptime(options['start_date'], '%Y-%m-%d').date()
                end_date = datetime.strptime(options['end_date'], '%Y-%m-%d').date()
            except (TypeError, ValueError):
                raise CommandError('Invalid date format. Use YYYY-MM-DD')

        dry_run = options['dry_run']
        force = options['force']

        self.stdout.write(
            self.style.SUCCESS(
                f'Starting leave balance recalculation '
                f'({start_date} to {end_date})'
            )
        )

        try:
            with transaction.atomic():
                # Get employees to process
                employees = Employee.objects.filter(is_active=True)
                if options['employee']:
                    employees = employees.filter(id=options['employee'])

                # Get leave types to process
                leave_types = LeaveType.objects.filter(
                    is_active=True,
                    accrual_type='periodic'
                )
                if options['leave_type']:
                    leave_types = leave_types.filter(
                        code=options['leave_type'].upper()
                    )

                if not employees.exists():
                    raise CommandError('No employees found')
                if not leave_types.exists():
                    raise CommandError('No leave types found')

                for employee in employees:
                    self.stdout.write(
                        f'\nProcessing {employee.get_full_name()}:'
                    )

                    for leave_type in leave_types:
                        self.stdout.write(
                            f'  Leave Type: {leave_type.name}'
                        )

                        # Get attendance records
                        attendance_logs = AttendanceLog.objects.filter(
                            employee=employee,
                            date__range=(start_date, end_date),
                            is_active=True,
                            source__in=['system', 'manual', 'friday_rule']
                        ).exclude(
                            Q(status='leave') | Q(status='holiday')
                        )

                        # Calculate new accrual
                        worked_days = attendance_logs.filter(
                            Q(status='present') | 
                            (Q(source='friday_rule') & Q(status__in=['present', 'half']))
                        ).count()

                        accrual = (worked_days / leave_type.accrual_period) * leave_type.accrual_rate
                        current_period = f"{start_date.year}-{start_date.month:02d}"

                        # Get or create balance record
                        try:
                            balance = LeaveBalance.objects.get(
                                employee=employee,
                                leave_type=leave_type,
                                period=current_period,
                                is_active=True
                            )

                            if not force:
                                self.stdout.write(
                                    self.style.WARNING(
                                        f'    Balance already exists. '
                                        f'Use --force to update'
                                    )
                                )
                                continue

                        except LeaveBalance.DoesNotExist:
                            if not dry_run:
                                balance = LeaveBalance.objects.create(
                                    employee=employee,
                                    leave_type=leave_type,
                                    period=current_period,
                                    total_days=0,
                                    available_days=0
                                )

                        # Calculate leaves taken
                        leaves_taken = Leave.objects.filter(
                            employee=employee,
                            leave_type=leave_type,
                            start_date__gte=start_date,
                            end_date__lte=end_date,
                            status='approved',
                            is_active=True
                        ).aggregate(
                            total_days=models.Sum('duration')
                        )['total_days'] or 0

                        # Update balance
                        if not dry_run:
                            old_total = balance.total_days
                            old_available = balance.available_days
                            
                            balance.total_days = accrual
                            balance.available_days = max(0, accrual - leaves_taken)
                            balance.last_calculated = timezone.now()
                            balance.save()

                        self.stdout.write(
                            f'    Worked Days: {worked_days}\n'
                            f'    Accrual: {accrual:.2f}\n'
                            f'    Leaves Taken: {leaves_taken}\n'
                            f'    Old Balance: {old_total:.2f} '
                            f'({old_available:.2f} available)\n'
                            f'    New Balance: {accrual:.2f} '
                            f'({max(0, accrual - leaves_taken):.2f} available)'
                        )

                if dry_run:
                    transaction.set_rollback(True)
                    self.stdout.write(
                        self.style.SUCCESS('Dry run completed successfully')
                    )
                else:
                    self.stdout.write(
                        self.style.SUCCESS('Leave balances recalculated successfully')
                    )

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error recalculating leave balances: {str(e)}')
            )
            logger.error(f'Leave balance recalculation failed: {str(e)}', exc_info=True)
            raise CommandError(str(e))

```

### hrms_project\attendance\management\commands\reset_annual_leave.py
```
import logging
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone
from django.db.models import F
from attendance.models import LeaveType, LeaveBalance, LeaveTransaction
from employees.models import Employee

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Reset leave balances for fixed-allowance leave types at the start of a new year'

    def add_arguments(self, parser):
        parser.add_argument(
            '--year',
            type=int,
            help='Specify year to reset balances for (defaults to current year)'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Simulate the reset without making actual changes'
        )

    def handle(self, *args, **options):
        year = options.get('year') or timezone.now().year
        dry_run = options.get('dry_run', False)

        if dry_run:
            self.stdout.write(self.style.WARNING('Running in dry-run mode - no changes will be made'))

        try:
            with transaction.atomic():
                # Get all active employees
                employees = Employee.objects.filter(is_active=True)
                self.stdout.write(f'Found {employees.count()} active employees')

                # Get leave types that need annual reset
                leave_types = LeaveType.objects.filter(
                    is_active=True,
                    rules__accrual_type='FIXED',
                    rules__reset_period='YEARLY'
                ).select_related('rules')

                self.stdout.write(f'Found {leave_types.count()} leave types to reset')

                balances_reset = 0
                balances_archived = 0

                for leave_type in leave_types:
                    self.stdout.write(f'\nProcessing {leave_type.name}:')
                    allowed_days = leave_type.rules.days_allowed

                    for employee in employees:
                        # Get current balance
                        try:
                            current_balance = LeaveBalance.objects.get(
                                employee=employee,
                                leave_type=leave_type
                            )

                            # Archive old balance if it exists and has transactions
                            if LeaveTransaction.objects.filter(
                                leave_balance=current_balance,
                                transaction_date__year=year-1
                            ).exists():
                                if not dry_run:
                                    LeaveBalance.objects.create(
                                        employee=employee,
                                        leave_type=leave_type,
                                        year=year-1,
                                        initial_balance=current_balance.initial_balance,
                                        current_balance=current_balance.current_balance,
                                        is_archived=True
                                    )
                                balances_archived += 1

                            # Reset balance to allowed days
                            if not dry_run:
                                current_balance.initial_balance = allowed_days
                                current_balance.current_balance = allowed_days
                                current_balance.year = year
                                current_balance.last_reset = timezone.now()
                                current_balance.save()

                                # Create reset transaction
                                LeaveTransaction.objects.create(
                                    leave_balance=current_balance,
                                    transaction_type='RESET',
                                    days=allowed_days,
                                    balance_after=allowed_days,
                                    description=f'Annual reset for {year}',
                                    transaction_date=timezone.now()
                                )
                            balances_reset += 1

                        except LeaveBalance.DoesNotExist:
                            # Create new balance if it doesn't exist
                            if not dry_run:
                                balance = LeaveBalance.objects.create(
                                    employee=employee,
                                    leave_type=leave_type,
                                    year=year,
                                    initial_balance=allowed_days,
                                    current_balance=allowed_days,
                                    last_reset=timezone.now()
                                )
                                LeaveTransaction.objects.create(
                                    leave_balance=balance,
                                    transaction_type='INITIAL',
                                    days=allowed_days,
                                    balance_after=allowed_days,
                                    description=f'Initial balance for {year}',
                                    transaction_date=timezone.now()
                                )
                            balances_reset += 1

                if not dry_run:
                    transaction.commit()
                    self.stdout.write(self.style.SUCCESS(
                        f'\nSuccessfully reset {balances_reset} balances and archived {balances_archived} old balances'
                    ))
                else:
                    self.stdout.write(self.style.WARNING(
                        f'\nDry run complete: Would reset {balances_reset} balances and archive {balances_archived} old balances'
                    ))

        except Exception as e:
            logger.error(f'Error resetting leave balances: {str(e)}')
            self.stdout.write(self.style.ERROR(f'Error resetting leave balances: {str(e)}'))
            if not dry_run:
                transaction.rollback()
            raise

    def _log_employee_balance(self, employee, leave_type, old_balance, new_balance):
        """Helper to log balance changes for auditing"""
        logger.info(
            f'Employee: {employee.employee_number} - {employee.get_full_name()}\n'
            f'Leave Type: {leave_type.name}\n'
            f'Old Balance: {old_balance}\n'
            f'New Balance: {new_balance}\n'
            f'Timestamp: {timezone.now()}\n'
            f'{"-"*50}'
        )

```

### hrms_project\attendance\management\commands\year_end_processing.py
```
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from django.db import transaction
from django.core.management import call_command
import logging
from datetime import datetime, date

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Perform end-of-year processing tasks for attendance management'

    def add_arguments(self, parser):
        parser.add_argument(
            '--year',
            type=int,
            help='Year to process (defaults to current year)',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Run without making changes to see what would happen',
        )
        parser.add_argument(
            '--skip-reset',
            action='store_true',
            help='Skip leave balance reset',
        )
        parser.add_argument(
            '--skip-holidays',
            action='store_true',
            help='Skip holiday generation',
        )
        parser.add_argument(
            '--skip-archive',
            action='store_true',
            help='Skip record archiving',
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force processing even if not December',
        )

    def handle(self, *args, **options):
        year = options['year'] or timezone.now().year
        dry_run = options['dry_run']
        skip_reset = options['skip_reset']
        skip_holidays = options['skip_holidays']
        skip_archive = options['skip_archive']
        force = options['force']

        # Check if it's December or force flag is set
        if timezone.now().month != 12 and not force:
            self.stdout.write(
                self.style.WARNING(
                    'Year-end processing should be run in December. '
                    'Use --force to override.'
                )
            )
            return

        try:
            with transaction.atomic():
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Starting year-end processing for {year}'
                    )
                )

                if not skip_reset:
                    self.stdout.write('Resetting leave balances...')
                    try:
                        if not dry_run:
                            call_command('reset_annual_leave', year=year + 1)
                        self.stdout.write('Leave balances reset complete')
                    except Exception as e:
                        self.stdout.write(
                            self.style.ERROR(f'Error resetting leave balances: {str(e)}')
                        )
                        raise

                if not skip_holidays:
                    self.stdout.write('Generating holidays for next year...')
                    try:
                        if not dry_run:
                            call_command('generate_holidays', year=year + 1, force=True)
                        self.stdout.write('Holiday generation complete')
                    except Exception as e:
                        self.stdout.write(
                            self.style.ERROR(f'Error generating holidays: {str(e)}')
                        )
                        raise

                if not skip_archive:
                    self.stdout.write('Archiving old records...')
                    try:
                        if not dry_run:
                            self._archive_old_records(year)
                        self.stdout.write('Record archiving complete')
                    except Exception as e:
                        self.stdout.write(
                            self.style.ERROR(f'Error archiving records: {str(e)}')
                        )
                        raise

                # Generate year-end reports
                self.stdout.write('Generating year-end reports...')
                try:
                    if not dry_run:
                        self._generate_year_end_reports(year)
                    self.stdout.write('Report generation complete')
                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(f'Error generating reports: {str(e)}')
                    )
                    raise

                if dry_run:
                    transaction.set_rollback(True)
                    self.stdout.write(
                        self.style.SUCCESS('Dry run completed successfully')
                    )
                else:
                    self.stdout.write(
                        self.style.SUCCESS('Year-end processing completed successfully')
                    )

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Year-end processing failed: {str(e)}')
            )
            logger.error(f'Year-end processing failed: {str(e)}', exc_info=True)
            raise CommandError(str(e))

    def _archive_old_records(self, year):
        """Archive old attendance records and logs"""
        from attendance.models import (
            AttendanceRecord, AttendanceLog, Leave, 
            LeaveBalance, Holiday
        )
        
        year_start = date(year, 1, 1)
        year_end = date(year, 12, 31)

        # Archive attendance records
        AttendanceRecord.objects.filter(
            timestamp__year=year,
            is_active=True
        ).update(
            is_active=False,
            archived_at=timezone.now()
        )

        # Archive attendance logs
        AttendanceLog.objects.filter(
            date__year=year,
            is_active=True
        ).update(
            is_active=False,
            archived_at=timezone.now()
        )

        # Archive completed leaves
        Leave.objects.filter(
            end_date__year=year,
            status__in=['approved', 'rejected', 'cancelled'],
            is_active=True
        ).update(
            is_active=False,
            archived_at=timezone.now()
        )

        # Archive old leave balances
        LeaveBalance.objects.filter(
            year=year,
            is_active=True
        ).update(
            is_active=False,
            archived_at=timezone.now()
        )

        # Archive past holidays
        Holiday.objects.filter(
            date__year=year,
            is_recurring=False,
            is_active=True
        ).update(
            is_active=False,
            archived_at=timezone.now()
        )

    def _generate_year_end_reports(self, year):
        """Generate comprehensive year-end reports"""
        from employees.models import Department

        # Generate overall attendance report
        call_command('generate_report', 
            year=year,
            format='excel',
            output=f'reports/year_end_{year}/attendance_summary_{year}.xlsx'
        )

        # Generate department-wise reports
        departments = Department.objects.filter(is_active=True)
        for dept in departments:
            call_command('generate_report',
                year=year,
                department=dept.id,
                format='excel',
                output=f'reports/year_end_{year}/attendance_{dept.code}_{year}.xlsx'
            )

        # Generate leave balance report
        call_command('generate_report',
            year=year,
            format='excel',
            type='leave_balance',
            output=f'reports/year_end_{year}/leave_balance_{year}.xlsx'
        )

        # Generate holiday report
        call_command('generate_report',
            year=year,
            format='excel',
            type='holiday',
            output=f'reports/year_end_{year}/holidays_{year}.xlsx'
        )

```

### hrms_project\attendance\migrations\0001_initial.py
```
# Generated by Django 4.2.9 on 2025-02-04 00:30

from django.conf import settings
import django.core.validators
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('employees', '0009_alter_employeeoffence_details_and_more'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [

        migrations.CreateModel(
            name='Leave',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('start_date', models.DateField()),
                ('end_date', models.DateField()),
                ('duration', models.DecimalField(decimal_places=2, help_text='Duration in days', max_digits=4)),
                ('start_half', models.BooleanField(default=False, help_text='True if starting with half day')),
                ('end_half', models.BooleanField(default=False, help_text='True if ending with half day')),
                ('reason', models.TextField()),
                ('status', models.CharField(choices=[('draft', 'Draft'), ('pending', 'Pending Approval'), ('approved', 'Approved'), ('rejected', 'Rejected'), ('cancelled', 'Cancelled')], default='draft', max_length=20)),
                ('submitted_at', models.DateTimeField(blank=True, null=True)),
                ('approved_at', models.DateTimeField(blank=True, null=True)),
                ('rejection_reason', models.TextField(blank=True)),
                ('cancellation_reason', models.TextField(blank=True)),
                ('is_active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('approved_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='approved_leaves', to=settings.AUTH_USER_MODEL)),
                ('employee', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='leaves', to='employees.employee')),
            ],
        ),
        migrations.CreateModel(
            name='LeaveType',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('code', models.CharField(max_length=20, unique=True)),
                ('category', models.CharField(choices=[('REGULAR', 'Regular Leave'), ('SPECIAL', 'Special Leave'), ('MEDICAL', 'Medical Leave')], max_length=20)),
                ('description', models.TextField(blank=True)),
                ('days_allowed', models.PositiveIntegerField(help_text='Number of days allowed per period')),
                ('is_paid', models.BooleanField(default=True)),
                ('requires_document', models.BooleanField(default=False)),
                ('gender_specific', models.CharField(choices=[('M', 'Male Only'), ('F', 'Female Only'), ('A', 'All')], default='A', max_length=1)),
                ('accrual_enabled', models.BooleanField(default=False)),
                ('accrual_days', models.DecimalField(blank=True, decimal_places=2, help_text='Days accrued per month/period', max_digits=4, null=True)),
                ('accrual_period', models.CharField(blank=True, choices=[('MONTHLY', 'Monthly'), ('WORKED', 'Per Worked Days')], max_length=10, null=True)),
                ('reset_period', models.CharField(choices=[('YEARLY', 'Yearly'), ('NEVER', 'Never Reset'), ('EVENT', 'Per Event')], default='YEARLY', max_length=10)),
                ('is_active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'ordering': ['name'],
            },
        ),
        migrations.CreateModel(
            name='Shift',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('start_time', models.TimeField()),
                ('end_time', models.TimeField()),
                ('is_night_shift', models.BooleanField(default=False)),
                ('is_active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'ordering': ['start_time'],
            },
        ),
        migrations.CreateModel(
            name='LeaveDocument',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('document', models.FileField(upload_to='leave_documents/%Y/%m/', validators=[django.core.validators.FileExtensionValidator(allowed_extensions=['pdf', 'jpg', 'jpeg', 'png'])])),
                ('document_type', models.CharField(max_length=50)),
                ('notes', models.TextField(blank=True)),
                ('uploaded_at', models.DateTimeField(auto_now_add=True)),
                ('leave', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='documents', to='attendance.leave')),
            ],
        ),
        migrations.CreateModel(
            name='LeaveActivity',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('action', models.CharField(max_length=50)),
                ('details', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('actor', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
                ('leave', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='activities', to='attendance.leave')),
            ],
            options={
                'verbose_name_plural': 'Leave activities',
                'ordering': ['-created_at'],
            },
        ),
        migrations.AddField(
            model_name='leave',
            name='leave_type',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='leave_requests', to='attendance.leavetype'),
        ),
        migrations.CreateModel(
            name='Holiday',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('date', models.DateField()),
                ('holiday_type', models.CharField(choices=[('PUBLIC', 'Public Holiday'), ('COMPANY', 'Company Holiday'), ('OPTIONAL', 'Optional Holiday')], default='PUBLIC', max_length=20)),
                ('is_recurring', models.BooleanField(default=False, help_text='If True, holiday repeats every year')),
                ('description', models.TextField(blank=True)),
                ('is_paid', models.BooleanField(default=True)),
                ('is_active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('applicable_departments', models.ManyToManyField(blank=True, related_name='holidays', to='employees.department')),
                ('created_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-date'],
            },
        ),
        migrations.CreateModel(
            name='AttendanceLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateField()),
                ('first_in_time', models.TimeField()),
                ('last_out_time', models.TimeField()),
                ('source', models.CharField(choices=[('system', 'System'), ('manual', 'Manual')], default='system', max_length=20)),
                ('is_active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('created_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='created_attendance_logs', to=settings.AUTH_USER_MODEL)),
                ('employee', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='attendance_logs', to='employees.employee')),
                ('shift', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='attendance.shift')),
            ],
            options={
                'ordering': ['-date'],
                'unique_together': {('employee', 'date')},
            },
        ),
        migrations.CreateModel(
            name='AttendanceEdit',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('original_first_in', models.TimeField()),
                ('original_last_out', models.TimeField()),
                ('edited_first_in', models.TimeField()),
                ('edited_last_out', models.TimeField()),
                ('edit_timestamp', models.DateTimeField(auto_now_add=True)),
                ('edit_reason', models.TextField()),
                ('is_active', models.BooleanField(default=True)),
                ('attendance_log', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='edits', to='attendance.attendancelog')),
                ('edited_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-edit_timestamp'],
            },
        ),
        migrations.CreateModel(
            name='LeaveBalance',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('total_days', models.DecimalField(decimal_places=2, default=0, max_digits=6)),
                ('used_days', models.DecimalField(decimal_places=2, default=0, max_digits=6)),
                ('pending_days', models.DecimalField(decimal_places=2, default=0, max_digits=6)),
                ('last_accrual_date', models.DateField(blank=True, null=True)),
                ('last_reset_date', models.DateField(blank=True, null=True)),
                ('valid_until', models.DateField(blank=True, null=True)),
                ('is_active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('employee', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='leave_balances', to='employees.employee')),
                ('leave_type', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='employee_balances', to='attendance.leavetype')),
            ],
            options={
                'ordering': ['employee', 'leave_type'],
                'unique_together': {('employee', 'leave_type')},
            },
        ),
        migrations.CreateModel(
            name='AttendanceRecord',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('timestamp', models.DateTimeField()),
                ('device_name', models.CharField(max_length=100)),
                ('event_point', models.CharField(max_length=100)),
                ('verify_type', models.CharField(max_length=50)),
                ('event_description', models.TextField(blank=True, null=True)),
                ('remarks', models.TextField(blank=True, null=True)),
                ('is_active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('employee', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='attendance_records', to='employees.employee')),
            ],
            options={
                'ordering': ['-timestamp'],
                'unique_together': {('employee', 'timestamp')},
            },
        ),
    ]

```

### hrms_project\attendance\migrations\0002_initial_leave_types.py
```
from django.db import migrations

def create_leave_types(apps, schema_editor):
    LeaveType = apps.get_model('attendance', 'LeaveType')

    leave_types = [
        # Emergency Leave
        {
            'name': 'Emergency Leave',
            'code': 'EMERG',
            'category': 'REGULAR',
            'description': 'Emergency leave up to 15 days per year',
            'days_allowed': 15,
            'is_paid': True,
            'requires_document': False,
            'gender_specific': 'A',
            'accrual_enabled': False,
            'reset_period': 'YEARLY'
        },
        # Annual Leave
        {
            'name': 'Annual Leave',
            'code': 'ANNUAL',
            'category': 'REGULAR',
            'description': 'Annual leave accrued at 2.5 days per 30 working days',
            'days_allowed': 30,
            'is_paid': True,
            'requires_document': False,
            'gender_specific': 'A',
            'accrual_enabled': True,
            'accrual_days': 2.5,
            'accrual_period': 'WORKED',
            'reset_period': 'YEARLY'
        },
        # Half Day Leave
        {
            'name': 'Half Day Leave',
            'code': 'HALF',
            'category': 'REGULAR',
            'description': 'Half day leave deducted from annual leave balance',
            'days_allowed': 0,  # Deducted from annual leave
            'is_paid': True,
            'requires_document': False,
            'gender_specific': 'A',
            'accrual_enabled': False,
            'reset_period': 'NEVER'
        },
        # Permission Leave
        {
            'name': 'Permission Leave',
            'code': 'PERM',
            'category': 'REGULAR',
            'description': 'Short permission tracked in hours (8 hours = 1 day)',
            'days_allowed': 3,
            'is_paid': True,
            'requires_document': False,
            'gender_specific': 'A',
            'accrual_enabled': False,
            'reset_period': 'YEARLY'
        },
        # Regular Sick Leave - Tier 1
        {
            'name': 'Sick Leave - Tier 1',
            'code': 'SICK1',
            'category': 'MEDICAL',
            'description': 'First 15 days of sick leave (fully paid)',
            'days_allowed': 15,
            'is_paid': True,
            'requires_document': True,
            'gender_specific': 'A',
            'accrual_enabled': False,
            'reset_period': 'YEARLY'
        },
        # Regular Sick Leave - Tier 2
        {
            'name': 'Sick Leave - Tier 2',
            'code': 'SICK2',
            'category': 'MEDICAL',
            'description': 'Next 20 days of sick leave (half paid)',
            'days_allowed': 20,
            'is_paid': True,
            'requires_document': True,
            'gender_specific': 'A',
            'accrual_enabled': False,
            'reset_period': 'YEARLY'
        },
        # Regular Sick Leave - Tier 3
        {
            'name': 'Sick Leave - Tier 3',
            'code': 'SICK3',
            'category': 'MEDICAL',
            'description': 'Final 20 days of sick leave (unpaid)',
            'days_allowed': 20,
            'is_paid': False,
            'requires_document': True,
            'gender_specific': 'A',
            'accrual_enabled': False,
            'reset_period': 'YEARLY'
        },
        # Injury Leave
        {
            'name': 'Injury Leave',
            'code': 'INJURY',
            'category': 'MEDICAL',
            'description': 'Unlimited paid leave for work-related injuries',
            'days_allowed': 0,  # Unlimited
            'is_paid': True,
            'requires_document': True,
            'gender_specific': 'A',
            'accrual_enabled': False,
            'reset_period': 'EVENT'
        },
        # Relative Death Leave
        {
            'name': 'Relative Death Leave',
            'code': 'DEATH',
            'category': 'SPECIAL',
            'description': '3 days paid leave per death event',
            'days_allowed': 3,
            'is_paid': True,
            'requires_document': True,
            'gender_specific': 'A',
            'accrual_enabled': False,
            'reset_period': 'EVENT'
        },
        # Maternity Leave
        {
            'name': 'Maternity Leave',
            'code': 'MATER',
            'category': 'SPECIAL',
            'description': '60 days paid leave for childbirth',
            'days_allowed': 60,
            'is_paid': True,
            'requires_document': True,
            'gender_specific': 'F',
            'accrual_enabled': False,
            'reset_period': 'EVENT'
        },
        # Paternity Leave
        {
            'name': 'Paternity Leave',
            'code': 'PATER',
            'category': 'SPECIAL',
            'description': '1 day paid leave for childbirth',
            'days_allowed': 1,
            'is_paid': True,
            'requires_document': True,
            'gender_specific': 'M',
            'accrual_enabled': False,
            'reset_period': 'EVENT'
        },
        # Marriage Leave
        {
            'name': 'Marriage Leave',
            'code': 'MARR',
            'category': 'SPECIAL',
            'description': '3 days paid leave per marriage event',
            'days_allowed': 3,
            'is_paid': True,
            'requires_document': True,
            'gender_specific': 'A',
            'accrual_enabled': False,
            'reset_period': 'EVENT'
        },
    ]

    for leave_type in leave_types:
        LeaveType.objects.create(**leave_type)

def remove_leave_types(apps, schema_editor):
    LeaveType = apps.get_model('attendance', 'LeaveType')
    LeaveType.objects.all().delete()

class Migration(migrations.Migration):
    dependencies = [
        ('attendance', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(create_leave_types, remove_leave_types),
    ]

```

### hrms_project\attendance\migrations\0003_leaverule.py
```
# Generated by Django 4.2.9 on 2025-02-04 07:32

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('attendance', '0002_initial_leave_types'),
    ]

    operations = [
        migrations.CreateModel(
            name='LeaveRule',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('code', models.CharField(max_length=50, unique=True)),
                ('description', models.TextField(blank=True)),
                ('days_allowed', models.DecimalField(decimal_places=2, max_digits=5)),
                ('is_paid', models.BooleanField(default=True)),
                ('requires_approval', models.BooleanField(default=True)),
                ('requires_documentation', models.BooleanField(default=False)),
                ('documentation_info', models.TextField(blank=True, help_text='What documents are required')),
                ('reset_frequency', models.CharField(choices=[('never', 'Never'), ('annually', 'Annually'), ('monthly', 'Monthly'), ('per_event', 'Per Event')], default='annually', max_length=20)),
                ('gender_specific', models.CharField(choices=[('M', 'Male Only'), ('F', 'Female Only'), ('A', 'All')], default='A', max_length=1)),
                ('min_service_months', models.PositiveIntegerField(default=0)),
                ('max_days_per_request', models.PositiveIntegerField(blank=True, null=True)),
                ('min_days_per_request', models.DecimalField(decimal_places=2, default=0.5, max_digits=4)),
                ('notice_days_required', models.PositiveIntegerField(default=0)),
                ('is_active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'ordering': ['name'],
            },
        ),
    ]

```

### hrms_project\attendance\migrations\0004_attendancelog_early_departure_and_more.py
```
# Generated by Django 4.2.9 on 2025-02-08 07:21

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('attendance', '0003_leaverule'),
    ]

    operations = [
        migrations.AddField(
            model_name='attendancelog',
            name='early_departure',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='attendancelog',
            name='early_minutes',
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AddField(
            model_name='attendancelog',
            name='is_late',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='attendancelog',
            name='late_minutes',
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AddField(
            model_name='attendancelog',
            name='status',
            field=models.CharField(choices=[('present', 'Present'), ('absent', 'Absent'), ('late', 'Late'), ('leave', 'Leave'), ('holiday', 'Holiday')], default='absent', max_length=20),
        ),
        migrations.AddField(
            model_name='attendancelog',
            name='total_work_minutes',
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AlterField(
            model_name='attendancelog',
            name='first_in_time',
            field=models.TimeField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='attendancelog',
            name='last_out_time',
            field=models.TimeField(blank=True, null=True),
        ),
    ]

```

### hrms_project\attendance\migrations\0006_add_shift_management.py
```
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('employees', '0010_employee_user'),
        ('attendance', '0004_attendancelog_early_departure_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='shift',
            name='shift_type',
            field=models.CharField(
                choices=[
                    ('DEFAULT', 'Default Shift (7AM-4PM)'),
                    ('CLEANER', 'Cleaner Shift (6AM-3PM)'),
                    ('NIGHT', 'Night Shift'),
                    ('OPEN', 'Open Shift'),
                ],
                default='DEFAULT',
                max_length=20
            ),
        ),
        migrations.AddField(
            model_name='shift',
            name='grace_period',
            field=models.PositiveIntegerField(
                default=15,
                help_text='Grace period in minutes'
            ),
        ),
        migrations.AddField(
            model_name='shift',
            name='break_duration',
            field=models.PositiveIntegerField(
                default=60,
                help_text='Break duration in minutes'
            ),
        ),
        migrations.CreateModel(
            name='RamadanPeriod',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('year', models.IntegerField()),
                ('start_date', models.DateField()),
                ('end_date', models.DateField()),
                ('is_active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name': 'Ramadan Period',
                'verbose_name_plural': 'Ramadan Periods',
                'ordering': ['-year'],
            },
        ),
        migrations.CreateModel(
            name='ShiftAssignment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('start_date', models.DateField(help_text='Start date of shift assignment')),
                ('end_date', models.DateField(blank=True, help_text='End date of shift assignment (null = permanent)', null=True)),
                ('is_active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('created_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='created_shift_assignments', to='auth.user')),
                ('employee', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='shift_assignments', to='employees.employee')),
                ('shift', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='assignments', to='attendance.shift')),
            ],
            options={
                'verbose_name': 'Shift Assignment',
                'verbose_name_plural': 'Shift Assignments',
                'ordering': ['-start_date'],
            },
        ),
    ]

```

### hrms_project\attendance\migrations\0007_alter_shiftassignment_created_by.py
```
# Generated by Django 4.2.9 on 2025-02-10 09:01

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('attendance', '0006_add_shift_management'),
    ]

    operations = [
        migrations.AlterField(
            model_name='shiftassignment',
            name='created_by',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='created_shift_assignments', to=settings.AUTH_USER_MODEL),
        ),
    ]

```

### hrms_project\attendance\migrations\__init__.py
```

```

### hrms_project\attendance\models.py
```
from django.db import models
from django.conf import settings
from employees.models import Employee
from django.core.exceptions import ValidationError
from django.core.validators import FileExtensionValidator
from django.utils import timezone

class RamadanPeriod(models.Model):
    """Defines Ramadan periods for different years"""
    year = models.IntegerField()
    start_date = models.DateField()
    end_date = models.DateField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-year']
        verbose_name = 'Ramadan Period'
        verbose_name_plural = 'Ramadan Periods'

    def __str__(self):
        return f"Ramadan {self.year} ({self.start_date} to {self.end_date})"

    def clean(self):
        if self.start_date and self.end_date:
            if self.start_date > self.end_date:
                raise ValidationError("End date cannot be before start date")
            if self.start_date.year != self.year or self.end_date.year != self.year:
                raise ValidationError("Dates must be within the specified year")

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

class Shift(models.Model):
    """Define different types of shifts"""
    SHIFT_TYPES = [
        ('DEFAULT', 'Default Shift (7AM-4PM)'),
        ('CLEANER', 'Cleaner Shift (6AM-3PM)'),
        ('NIGHT', 'Night Shift'),
        ('OPEN', 'Open Shift'),
    ]

    name = models.CharField(max_length=100)
    shift_type = models.CharField(max_length=20, choices=SHIFT_TYPES, default='DEFAULT')
    start_time = models.TimeField()
    end_time = models.TimeField()
    is_night_shift = models.BooleanField(default=False)
    grace_period = models.PositiveIntegerField(
        default=15,
        help_text="Grace period in minutes"
    )
    break_duration = models.PositiveIntegerField(
        default=60,
        help_text="Break duration in minutes"
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} ({self.start_time}-{self.end_time})"

    class Meta:
        ordering = ['start_time']

class ShiftAssignment(models.Model):
    """Track shift assignments for employees"""
    employee = models.ForeignKey(
        'employees.Employee',
        on_delete=models.CASCADE,
        related_name='shift_assignments'
    )
    shift = models.ForeignKey(
        Shift,
        on_delete=models.CASCADE,
        related_name='assignments'
    )
    start_date = models.DateField(help_text="Start date of shift assignment")
    end_date = models.DateField(
        null=True,
        blank=True,
        help_text="End date of shift assignment (null = permanent)"
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_shift_assignments'
    )

    class Meta:
        ordering = ['-start_date']
        verbose_name = 'Shift Assignment'
        verbose_name_plural = 'Shift Assignments'

    def __str__(self):
        end = f" to {self.end_date}" if self.end_date else " (Permanent)"
        return f"{self.employee} - {self.shift.name} from {self.start_date}{end}"

    def clean(self):
        if self.start_date and self.end_date and self.end_date < self.start_date:
            raise ValidationError("End date cannot be before start date")

        # Check for overlapping assignments
        overlapping = ShiftAssignment.objects.filter(
            employee=self.employee,
            is_active=True,
            start_date__lte=self.end_date or timezone.now().date(),
        ).exclude(pk=self.pk)

        if self.end_date:
            overlapping = overlapping.filter(
                models.Q(end_date__isnull=True) |
                models.Q(end_date__gte=self.start_date)
            )
        
        if overlapping.exists():
            raise ValidationError(
                "This assignment overlaps with an existing shift assignment"
            )

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

class AttendanceRecord(models.Model):
    """Raw attendance data from machine"""
    employee = models.ForeignKey(
        Employee,
        on_delete=models.CASCADE,
        related_name='attendance_records'
    )
    timestamp = models.DateTimeField()
    device_name = models.CharField(max_length=100)
    event_point = models.CharField(max_length=100)
    verify_type = models.CharField(max_length=50)
    event_description = models.TextField(blank=True, null=True)
    remarks = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['employee', 'timestamp']
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.employee} - {self.timestamp}"

class AttendanceLog(models.Model):
    """Processed attendance data with first in/last out times"""
    STATUS_CHOICES = [
        ('present', 'Present'),
        ('absent', 'Absent'),
        ('late', 'Late'),
        ('leave', 'Leave'),
        ('holiday', 'Holiday')
    ]

    employee = models.ForeignKey(
        Employee,
        on_delete=models.CASCADE,
        related_name='attendance_logs'
    )
    date = models.DateField()
    first_in_time = models.TimeField(null=True, blank=True)
    last_out_time = models.TimeField(null=True, blank=True)
    shift = models.ForeignKey(
        Shift,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    
    # Status tracking
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='absent'
    )
    is_late = models.BooleanField(default=False)
    late_minutes = models.PositiveIntegerField(default=0)
    early_departure = models.BooleanField(default=False)
    early_minutes = models.PositiveIntegerField(default=0)
    total_work_minutes = models.PositiveIntegerField(default=0)
    source = models.CharField(
        max_length=20,
        choices=[('system', 'System'), ('manual', 'Manual')],
        default='system'
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_attendance_logs'
    )

    class Meta:
        unique_together = ['employee', 'date']
        ordering = ['-date']

    def __str__(self):
        return f"{self.employee} - {self.date}"

class AttendanceEdit(models.Model):
    """Track changes to attendance logs"""
    attendance_log = models.ForeignKey(
        AttendanceLog,
        on_delete=models.CASCADE,
        related_name='edits'
    )
    original_first_in = models.TimeField()
    original_last_out = models.TimeField()
    edited_first_in = models.TimeField()
    edited_last_out = models.TimeField()
    edited_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True
    )
    edit_timestamp = models.DateTimeField(auto_now_add=True)
    edit_reason = models.TextField()
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['-edit_timestamp']

    def __str__(self):
        return f"Edit on {self.attendance_log} at {self.edit_timestamp}"

class LeaveType(models.Model):
    """Define leave types and their rules"""
    CATEGORY_CHOICES = [
        ('REGULAR', 'Regular Leave'),
        ('SPECIAL', 'Special Leave'),
        ('MEDICAL', 'Medical Leave'),
    ]
    
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=20, unique=True)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    description = models.TextField(blank=True)
    
    # Leave allowance configuration
    days_allowed = models.PositiveIntegerField(help_text="Number of days allowed per period")
    is_paid = models.BooleanField(default=True)
    requires_document = models.BooleanField(default=False)
    gender_specific = models.CharField(
        max_length=1, 
        choices=[('M', 'Male Only'), ('F', 'Female Only'), ('A', 'All')],
        default='A'
    )
    
    # Accrual settings
    accrual_enabled = models.BooleanField(default=False)
    accrual_days = models.DecimalField(
        max_digits=4, 
        decimal_places=2, 
        null=True, 
        blank=True,
        help_text="Days accrued per month/period"
    )
    accrual_period = models.CharField(
        max_length=10,
        choices=[('MONTHLY', 'Monthly'), ('WORKED', 'Per Worked Days')],
        null=True,
        blank=True
    )
    
    # Reset configuration
    reset_period = models.CharField(
        max_length=10,
        choices=[
            ('YEARLY', 'Yearly'),
            ('NEVER', 'Never Reset'),
            ('EVENT', 'Per Event')
        ],
        default='YEARLY'
    )
    
    # System fields
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} ({self.code})"
    
    class Meta:
        ordering = ['name']

class LeaveBalance(models.Model):
    """Track leave balances for employees"""
    employee = models.ForeignKey(
        Employee,
        on_delete=models.CASCADE,
        related_name='leave_balances'
    )
    leave_type = models.ForeignKey(
        LeaveType,
        on_delete=models.CASCADE,
        related_name='employee_balances'
    )
    
    total_days = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    used_days = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    pending_days = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    
    last_accrual_date = models.DateField(null=True, blank=True)
    last_reset_date = models.DateField(null=True, blank=True)
    valid_until = models.DateField(null=True, blank=True)
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.employee} - {self.leave_type} Balance"
    
    @property
    def available_days(self):
        """Calculate available days excluding pending requests"""
        return self.total_days - self.used_days - self.pending_days

    class Meta:
        unique_together = ['employee', 'leave_type']
        ordering = ['employee', 'leave_type']

class LeaveRule(models.Model):
    """Defines rules and configurations for different leave types"""
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True)
    days_allowed = models.DecimalField(max_digits=5, decimal_places=2)
    is_paid = models.BooleanField(default=True)
    requires_approval = models.BooleanField(default=True)
    requires_documentation = models.BooleanField(default=False)
    documentation_info = models.TextField(blank=True, help_text="What documents are required")
    reset_frequency = models.CharField(
        max_length=20,
        choices=[
            ('never', 'Never'),
            ('annually', 'Annually'),
            ('monthly', 'Monthly'),
            ('per_event', 'Per Event'),
        ],
        default='annually'
    )
    gender_specific = models.CharField(
        max_length=1,
        choices=[('M', 'Male Only'), ('F', 'Female Only'), ('A', 'All')],
        default='A'
    )
    min_service_months = models.PositiveIntegerField(default=0)
    max_days_per_request = models.PositiveIntegerField(null=True, blank=True)
    min_days_per_request = models.DecimalField(
        max_digits=4, 
        decimal_places=2,
        default=0.5
    )
    notice_days_required = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['name']

class Leave(models.Model):
    """Track leave requests and their status"""
    LEAVE_STATUS = [
        ('draft', 'Draft'),
        ('pending', 'Pending Approval'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('cancelled', 'Cancelled')
    ]

    employee = models.ForeignKey(
        Employee,
        on_delete=models.CASCADE,
        related_name='leaves'
    )
    leave_type = models.ForeignKey(
        LeaveType,
        on_delete=models.PROTECT,
        related_name='leave_requests'
    )
    
    # Request details
    start_date = models.DateField()
    end_date = models.DateField()
    duration = models.DecimalField(
        max_digits=4,
        decimal_places=2,
        help_text="Duration in days"
    )
    start_half = models.BooleanField(
        default=False,
        help_text="True if starting with half day"
    )
    end_half = models.BooleanField(
        default=False,
        help_text="True if ending with half day"
    )
    reason = models.TextField()
    
    # Status tracking
    status = models.CharField(
        max_length=20,
        choices=LEAVE_STATUS,
        default='draft'
    )
    submitted_at = models.DateTimeField(null=True, blank=True)
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='approved_leaves'
    )
    approved_at = models.DateTimeField(null=True, blank=True)
    rejection_reason = models.TextField(blank=True)
    cancellation_reason = models.TextField(blank=True)
    
    # System fields
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.employee} - {self.leave_type} ({self.start_date} to {self.end_date})"

    def clean(self):
        if self.start_date and self.end_date:
            if self.start_date > self.end_date:
                raise ValidationError("End date cannot be before start date")

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

class LeaveDocument(models.Model):
    """Store documents related to leave requests"""
    leave = models.ForeignKey(
        Leave,
        on_delete=models.CASCADE,
        related_name='documents'
    )
    document = models.FileField(
        upload_to='leave_documents/%Y/%m/',
        validators=[
            FileExtensionValidator(
                allowed_extensions=['pdf', 'jpg', 'jpeg', 'png']
            )
        ]
    )
    document_type = models.CharField(max_length=50)
    notes = models.TextField(blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.leave} - {self.document_type}"

class LeaveActivity(models.Model):
    """Track all activities related to leave requests"""
    leave = models.ForeignKey(
        Leave,
        on_delete=models.CASCADE,
        related_name='activities'
    )
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True
    )
    action = models.CharField(max_length=50)
    details = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.leave} - {self.action} by {self.actor}"
    
    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = 'Leave activities'

class Holiday(models.Model):
    """Define holidays and their configurations"""
    HOLIDAY_TYPES = [
        ('PUBLIC', 'Public Holiday'),
        ('COMPANY', 'Company Holiday'),
        ('OPTIONAL', 'Optional Holiday')
    ]
    
    name = models.CharField(max_length=100)
    date = models.DateField()
    holiday_type = models.CharField(
        max_length=20,
        choices=HOLIDAY_TYPES,
        default='PUBLIC'
    )
    is_recurring = models.BooleanField(
        default=False,
        help_text="If True, holiday repeats every year"
    )
    description = models.TextField(blank=True)
    is_paid = models.BooleanField(default=True)
    
    # Specific employee groups this holiday applies to
    applicable_departments = models.ManyToManyField(
        'employees.Department',
        blank=True,
        related_name='holidays'
    )
    
    # System fields
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-date']

    def __str__(self):
        return f"{self.date} - {self.description}"

```

### hrms_project\attendance\schedules.py
```
from celery.schedules import crontab

# Schedule configuration for periodic tasks
SHIFT_SCHEDULES = {
    # Check and deactivate expired shift assignments daily at 00:01 AM
    'update-expired-shifts': {
        'task': 'attendance.tasks.update_expired_shift_assignments',
        'schedule': crontab(hour=0, minute=1),
        'options': {
            'expires': 3600  # Task expires after 1 hour
        }
    },
    
    # Notify about upcoming shift changes daily at 6:00 AM
    'notify-shift-changes': {
        'task': 'attendance.tasks.notify_shift_changes',
        'schedule': crontab(hour=6, minute=0),
        'options': {
            'expires': 3600
        }
    },
    
    # Process Ramadan shift changes daily at 00:05 AM
    'process-ramadan-shifts': {
        'task': 'attendance.tasks.process_ramadan_shift_changes',
        'schedule': crontab(hour=0, minute=5),
        'options': {
            'expires': 3600
        }
    },
    
    # Calculate attendance metrics daily at 1:00 AM
    'calculate-attendance-metrics': {
        'task': 'attendance.tasks.calculate_attendance_metrics',
        'schedule': crontab(hour=1, minute=0),
        'options': {
            'expires': 7200  # Expires after 2 hours
        }
    },
    
    # Check for missing shift assignments weekly on Sunday at 8:00 AM
    'check-missing-shifts': {
        'task': 'attendance.tasks.notify_missing_shift_assignments',
        'schedule': crontab(hour=8, minute=0, day_of_week=0),
        'options': {
            'expires': 3600
        }
    }
}

# Optional overrides for holidays and weekends
SCHEDULE_OVERRIDES = {
    'ignore_dates': [
        # Add specific dates to ignore tasks
        # Format: 'YYYY-MM-DD'
    ],
    'weekend_schedule': {
        # Define different schedules for weekends if needed
        'update-expired-shifts': {
            'schedule': crontab(hour=1, minute=0)  # Run later on weekends
        }
    }
}

# Schedule Groups
SCHEDULE_GROUPS = {
    'critical': [
        'update-expired-shifts',
        'process-ramadan-shifts'
    ],
    'notifications': [
        'notify-shift-changes',
        'notify-missing-shift-assignments'
    ],
    'reports': [
        'calculate-attendance-metrics'
    ]
}

# Retry Settings
RETRY_SETTINGS = {
    'default': {
        'max_retries': 3,
        'interval_start': 0,
        'interval_step': 300,  # 5 minutes
        'interval_max': 3600,  # 1 hour
    },
    'critical': {
        'max_retries': 5,
        'interval_start': 0,
        'interval_step': 180,  # 3 minutes
        'interval_max': 1800,  # 30 minutes
    }
}

# Task Priority Settings
TASK_PRIORITIES = {
    'update-expired-shifts': 'high',
    'process-ramadan-shifts': 'high',
    'notify-shift-changes': 'normal',
    'calculate-attendance-metrics': 'low',
    'notify-missing-shift-assignments': 'normal'
}

# Error Notification Settings
ERROR_NOTIFICATION = {
    'notify_on_error': True,
    'error_recipients': ['hr@example.com', 'tech@example.com'],
    'error_threshold': 3,  # Number of failures before notification
    'error_cooldown': 1800  # 30 minutes between notifications
}

def get_schedule_config():
    """Get complete schedule configuration"""
    return {
        'schedules': SHIFT_SCHEDULES,
        'overrides': SCHEDULE_OVERRIDES,
        'groups': SCHEDULE_GROUPS,
        'retry': RETRY_SETTINGS,
        'priorities': TASK_PRIORITIES,
        'error_handling': ERROR_NOTIFICATION
    }

def get_task_schedule(task_name):
    """Get schedule configuration for a specific task"""
    if task_name in SHIFT_SCHEDULES:
        return {
            'schedule': SHIFT_SCHEDULES[task_name],
            'retry': (
                RETRY_SETTINGS['critical'] 
                if task_name in SCHEDULE_GROUPS['critical']
                else RETRY_SETTINGS['default']
            ),
            'priority': TASK_PRIORITIES.get(task_name, 'normal')
        }
    return None

def is_task_enabled(task_name, date_str=None):
    """Check if a task should run on a given date"""
    if date_str and date_str in SCHEDULE_OVERRIDES['ignore_dates']:
        return False
    return True

```

### hrms_project\attendance\serializers.py
```
from rest_framework import serializers
from .models import (
    Shift, AttendanceRecord, AttendanceLog,
    AttendanceEdit, Leave, Holiday
)
from employees.models import Employee

class ShiftSerializer(serializers.ModelSerializer):
    class Meta:
        model = Shift
        fields = '__all__'

class AttendanceRecordSerializer(serializers.ModelSerializer):
    employee_name = serializers.SerializerMethodField()

    class Meta:
        model = AttendanceRecord
        fields = '__all__'

    def get_employee_name(self, obj):
        return obj.employee.get_full_name()

class AttendanceLogSerializer(serializers.ModelSerializer):
    employee_name = serializers.SerializerMethodField()
    shift_name = serializers.SerializerMethodField()
    employee_id = serializers.SerializerMethodField()
    personnel_id = serializers.SerializerMethodField()

    class Meta:
        model = AttendanceLog
        fields = '__all__'

    def get_employee_name(self, obj):
        return obj.employee.get_full_name() if obj.employee else None

    def get_shift_name(self, obj):
        return obj.shift.name if obj.shift else None

    def get_employee_id(self, obj):
        return obj.employee.id if obj.employee else None

    def get_personnel_id(self, obj):
        return obj.employee.employee_number if obj.employee else None

class AttendanceEditSerializer(serializers.ModelSerializer):
    edited_by_name = serializers.SerializerMethodField()

    class Meta:
        model = AttendanceEdit
        fields = '__all__'

    def get_edited_by_name(self, obj):
        return obj.edited_by.get_full_name() if obj.edited_by else None

class LeaveSerializer(serializers.ModelSerializer):
    employee_name = serializers.SerializerMethodField()
    approved_by_name = serializers.SerializerMethodField()

    class Meta:
        model = Leave
        fields = '__all__'

    def get_employee_name(self, obj):
        return obj.employee.get_full_name()

    def get_approved_by_name(self, obj):
        return obj.approved_by.get_full_name() if obj.approved_by else None

class HolidaySerializer(serializers.ModelSerializer):
    created_by_name = serializers.SerializerMethodField()

    class Meta:
        model = Holiday
        fields = '__all__'

    def get_created_by_name(self, obj):
        return obj.created_by.get_full_name() if obj.created_by else None

class AttendanceUploadSerializer(serializers.Serializer):
    file = serializers.FileField()

class BulkAttendanceCreateSerializer(serializers.Serializer):
    records = serializers.ListField(
        child=serializers.DictField()
    )

    def validate(self, data):
        records = data.get('records', [])
        for record in records:
            if not all(k in record for k in ('employee_id', 'timestamp')):
                raise serializers.ValidationError(
                    "Each record must contain employee_id and timestamp"
                )
        return data

    def create(self, validated_data):
        records = validated_data.get('records', [])
        created_records = []

        for record in records:
            try:
                employee = Employee.objects.get(id=record['employee_id'])
                attendance_record = AttendanceRecord.objects.create(
                    employee=employee,
                    timestamp=record['timestamp'],
                    device_name=record.get('device_name', ''),
                    event_point=record.get('event_point', ''),
                    verify_type=record.get('verify_type', ''),
                    event_description=record.get('event_description', ''),
                    remarks=record.get('remarks', '')
                )
                created_records.append(attendance_record)
            except Employee.DoesNotExist:
                continue

        return created_records
```

### hrms_project\attendance\services\__init__.py
```
from .shift_service import ShiftService
from .ramadan_service import RamadanService
from .attendance_status_service import AttendanceStatusService

__all__ = ['ShiftService', 'RamadanService', 'AttendanceStatusService']
```

### hrms_project\attendance\services\attendance_status_service.py
```
class AttendanceStatusService:
    @staticmethod
    def calculate_status(attendance_log):
        """
        Calculate attendance status based on attendance log
        """
        if attendance_log.is_leave:
            return 'leave'
        elif attendance_log.is_holiday:
            return 'holiday'
        elif not attendance_log.first_in_time:
            return 'absent'
        elif attendance_log.is_late:
            return 'late'
        return 'present'
```

### hrms_project\attendance\services\ramadan_service.py
```
from datetime import date, datetime, timedelta
from typing import Optional, Dict, Any, List

from django.db import transaction
from django.utils import timezone

from ..models import RamadanPeriod

class RamadanService:
    @staticmethod
    def get_active_period(date_to_check: Optional[date] = None) -> Optional[RamadanPeriod]:
        """
        Get the active Ramadan period for a given date
        
        Args:
            date_to_check: The date to check (defaults to today)
            
        Returns:
            RamadanPeriod if date falls within an active period, None otherwise
        """
        if not date_to_check:
            date_to_check = timezone.now().date()
            
        return RamadanPeriod.objects.filter(
            start_date__lte=date_to_check,
            end_date__gte=date_to_check,
            is_active=True
        ).first()

    @staticmethod
    def create_period(year: int, start_date: date, end_date: date) -> RamadanPeriod:
        """
        Create a new Ramadan period
        
        Args:
            year: The year of the Ramadan period
            start_date: Start date of Ramadan
            end_date: End date of Ramadan
            
        Returns:
            The created RamadanPeriod instance
            
        Raises:
            ValueError: If dates are invalid or period overlaps with existing ones
        """
        # Validate year matches dates
        if (start_date.year != year or end_date.year != year):
            raise ValueError("Start and end dates must be within the specified year")
            
        # Check for overlaps
        overlapping = RamadanPeriod.objects.filter(
            start_date__lte=end_date,
            end_date__gte=start_date
        ).exists()
        
        if overlapping:
            raise ValueError("This period overlaps with an existing Ramadan period")
            
        return RamadanPeriod.objects.create(
            year=year,
            start_date=start_date,
            end_date=end_date,
            is_active=True
        )

    @staticmethod
    @transaction.atomic
    def update_period(
        period_id: int,
        year: int,
        start_date: date,
        end_date: date,
        is_active: bool
    ) -> RamadanPeriod:
        """
        Update an existing Ramadan period
        
        Args:
            period_id: ID of the period to update
            year: New year
            start_date: New start date
            end_date: New end date
            is_active: New active status
            
        Returns:
            The updated RamadanPeriod instance
            
        Raises:
            ValueError: If dates are invalid or period overlaps with existing ones
            RamadanPeriod.DoesNotExist: If period_id is invalid
        """
        # Validate year matches dates
        if (start_date.year != year or end_date.year != year):
            raise ValueError("Start and end dates must be within the specified year")
            
        # Check for overlaps with other periods
        overlapping = RamadanPeriod.objects.exclude(
            id=period_id
        ).filter(
            start_date__lte=end_date,
            end_date__gte=start_date
        ).exists()
        
        if overlapping:
            raise ValueError("This period overlaps with an existing Ramadan period")
            
        period = RamadanPeriod.objects.get(id=period_id)
        period.year = year
        period.start_date = start_date
        period.end_date = end_date
        period.is_active = is_active
        period.save()
        
        return period

    @staticmethod
    def get_all_periods(include_inactive: bool = False) -> List[Dict[str, Any]]:
        """
        Get all Ramadan periods with optional filtering
        
        Args:
            include_inactive: Whether to include inactive periods
            
        Returns:
            List of dictionaries containing period details
        """
        queryset = RamadanPeriod.objects.all()
        if not include_inactive:
            queryset = queryset.filter(is_active=True)
            
        return [{
            'id': period.id,
            'year': period.year,
            'start_date': period.start_date,
            'end_date': period.end_date,
            'is_active': period.is_active,
            'duration': (period.end_date - period.start_date).days + 1
        } for period in queryset.order_by('-year')]

    @staticmethod
    def calculate_working_hours(
        normal_hours: float,
        is_ramadan: bool = False
    ) -> float:
        """
        Calculate adjusted working hours for Ramadan
        
        Args:
            normal_hours: Regular working hours
            is_ramadan: Whether the calculation is for Ramadan period
            
        Returns:
            Adjusted working hours
        """
        if not is_ramadan:
            return normal_hours
            
        # Default Ramadan reduction (2 hours less)
        return max(normal_hours - 2, 4)  # Minimum 4 hours

    @staticmethod
    def validate_period_dates(
        start_date: date,
        end_date: date,
        year: int,
        exclude_id: Optional[int] = None
    ) -> bool:
        """
        Validate Ramadan period dates
        
        Args:
            start_date: Proposed start date
            end_date: Proposed end date
            year: Year the period should be in
            exclude_id: Optional ID to exclude from overlap check
            
        Returns:
            True if dates are valid, False otherwise
            
        Raises:
            ValueError with specific error message if validation fails
        """
        # Check year consistency
        if start_date.year != year or end_date.year != year:
            raise ValueError("Start and end dates must be within the specified year")
            
        # Check date order
        if end_date < start_date:
            raise ValueError("End date cannot be before start date")
            
        # Check duration (typical Ramadan is 29-30 days)
        duration = (end_date - start_date).days + 1
        if duration < 28 or duration > 31:
            raise ValueError(f"Duration ({duration} days) seems invalid for Ramadan")
            
        # Check for overlaps
        query = RamadanPeriod.objects.filter(
            start_date__lte=end_date,
            end_date__gte=start_date
        )
        if exclude_id:
            query = query.exclude(id=exclude_id)
            
        if query.exists():
            raise ValueError("This period overlaps with an existing Ramadan period")
            
        return True

```

### hrms_project\attendance\services\shift_service.py
```
from datetime import datetime, date, timedelta
from typing import Optional, List, Dict, Any

from django.db import transaction
from django.db.models import Q
from django.utils import timezone
from django.contrib.auth.models import User

from ..models import Shift, ShiftAssignment, RamadanPeriod
from employees.models import Employee

class ShiftService:
    @staticmethod
    def get_active_shifts():
        """Get all active shifts ordered by start time"""
        return Shift.objects.filter(is_active=True).order_by('start_time')

    @staticmethod
    def get_employee_current_shift(employee: Employee) -> Optional[Shift]:
        """Get an employee's currently active shift"""
        today = timezone.now().date()
        assignment = ShiftAssignment.objects.filter(
            employee=employee,
            start_date__lte=today,
            is_active=True
        ).filter(
            Q(end_date__isnull=True) | Q(end_date__gte=today)
        ).first()
        return assignment.shift if assignment else None

    @staticmethod
    def get_employee_shift_history(employee: Employee) -> List[Dict[str, Any]]:
        """Get complete shift assignment history for an employee"""
        assignments = ShiftAssignment.objects.filter(
            employee=employee
        ).select_related('shift', 'created_by').order_by('-start_date')
        
        return [{
            'shift_name': assignment.shift.name,
            'start_date': assignment.start_date,
            'end_date': assignment.end_date,
            'is_active': assignment.is_active,
            'created_by': assignment.created_by.get_full_name(),
            'created_at': assignment.created_at
        } for assignment in assignments]

    @staticmethod
    @transaction.atomic
    def assign_shift(
        employee: Employee,
        shift: Shift,
        start_date: date,
        end_date: Optional[date],
        created_by: User,
        is_active: bool = True
    ) -> ShiftAssignment:
        """
        Assign a shift to an employee
        
        Args:
            employee: The employee to assign the shift to
            shift: The shift to assign
            start_date: When the assignment starts
            end_date: Optional end date for temporary assignments
            created_by: User creating the assignment
            is_active: Whether the assignment should be active
            
        Returns:
            The created shift assignment
        """
        if is_active:
            # Deactivate any existing active assignments
            ShiftAssignment.objects.filter(
                employee=employee,
                is_active=True
            ).update(is_active=False)
            
        # Create new assignment
        return ShiftAssignment.objects.create(
            employee=employee,
            shift=shift,
            start_date=start_date,
            end_date=end_date,
            created_by=created_by,
            is_active=is_active
        )

    @staticmethod
    def get_ramadan_shift_timing(shift: Shift, date: date) -> Optional[Dict[str, Any]]:
        """
        Get adjusted shift timing if the given date falls in Ramadan period
        
        Args:
            shift: The shift to check
            date: The date to check for Ramadan timing
            
        Returns:
            Dict with adjusted start_time and end_time if in Ramadan, None otherwise
        """
        ramadan_period = RamadanPeriod.objects.filter(
            start_date__lte=date,
            end_date__gte=date,
            is_active=True
        ).first()
        
        if not ramadan_period:
            return None
            
        # Default Ramadan adjustment (reduce by 2 hours)
        start_time = shift.start_time
        end_time = (
            datetime.combine(date, shift.end_time) - timedelta(hours=2)
        ).time()
        
        return {
            'start_time': start_time,
            'end_time': end_time
        }

    @staticmethod
    def filter_assignments(
        department_id: Optional[int] = None,
        shift_id: Optional[int] = None,
        is_active: Optional[bool] = None,
        search_query: Optional[str] = None,
        assignment_type: Optional[str] = None
    ):
        """
        Filter shift assignments based on various criteria
        
        Args:
            department_id: Filter by department
            shift_id: Filter by shift
            is_active: Filter by active status
            search_query: Search employee name or number
            assignment_type: Filter by permanent/temporary
            
        Returns:
            Filtered queryset of ShiftAssignment objects
        """
        queryset = ShiftAssignment.objects.all()
        
        if department_id:
            queryset = queryset.filter(employee__department_id=department_id)
            
        if shift_id:
            queryset = queryset.filter(shift_id=shift_id)
            
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active)
            
        if search_query:
            queryset = queryset.filter(
                Q(employee__first_name__icontains=search_query) |
                Q(employee__last_name__icontains=search_query) |
                Q(employee__employee_number__icontains=search_query)
            )
            
        if assignment_type:
            if assignment_type == 'permanent':
                queryset = queryset.filter(end_date__isnull=True)
            elif assignment_type == 'temporary':
                queryset = queryset.filter(end_date__isnull=False)
                
        return queryset.select_related(
            'employee',
            'employee__department',
            'shift',
            'created_by'
        ).order_by('-created_at')

    @staticmethod
    def get_department_shifts(department_id: int, date: Optional[date] = None) -> Dict[str, List[Dict]]:
        """
        Get all shift assignments for a department grouped by shift
        
        Args:
            department_id: The department to get shifts for
            date: Optional date to check assignments for
            
        Returns:
            Dict with shift names as keys and lists of employees as values
        """
        if not date:
            date = timezone.now().date()
            
        assignments = ShiftAssignment.objects.filter(
            employee__department_id=department_id,
            start_date__lte=date,
            is_active=True
        ).filter(
            Q(end_date__isnull=True) | Q(end_date__gte=date)
        ).select_related('employee', 'shift')
        
        shifts = {}
        for assignment in assignments:
            shift_name = assignment.shift.name
            if shift_name not in shifts:
                shifts[shift_name] = []
                
            shifts[shift_name].append({
                'employee_number': assignment.employee.employee_number,
                'employee_name': assignment.employee.get_full_name(),
                'assignment_id': assignment.id,
                'start_date': assignment.start_date,
                'end_date': assignment.end_date
            })
            
        return shifts

    @staticmethod
    @transaction.atomic
    def bulk_assign_shift(
        employee_ids: List[int],
        shift: Shift,
        start_date: date,
        end_date: Optional[date],
        created_by: User,
        is_active: bool = True
    ) -> int:
        """
        Assign a shift to multiple employees at once
        
        Args:
            employee_ids: List of employee IDs to assign the shift to
            shift: The shift to assign
            start_date: When the assignment starts
            end_date: Optional end date for temporary assignments
            created_by: User creating the assignments
            is_active: Whether the assignments should be active
            
        Returns:
            Number of assignments created
        """
        if is_active:
            # Deactivate existing active assignments for these employees
            ShiftAssignment.objects.filter(
                employee_id__in=employee_ids,
                is_active=True
            ).update(is_active=False)
            
        # Create new assignments
        assignments = [
            ShiftAssignment(
                employee_id=emp_id,
                shift=shift,
                start_date=start_date,
                end_date=end_date,
                created_by=created_by,
                is_active=is_active
            )
            for emp_id in employee_ids
        ]
        
        created = ShiftAssignment.objects.bulk_create(assignments)
        return len(created)

```

### hrms_project\attendance\services.py
```
from django.utils import timezone
from django.db.models import Q, F
from datetime import datetime, timedelta, time
from typing import Optional, List, Dict, Any

from .models import (
    Employee, AttendanceLog, AttendanceRecord,
    Leave, LeaveType, LeaveBalance, Holiday,
    ShiftAssignment, RamadanPeriod
)

class AttendanceStatusService:
    """Service class for determining attendance status"""

    @staticmethod
    def is_ramadan(date: datetime.date, employee: Employee) -> bool:
        """Check if the given date falls within Ramadan period for Muslim employees"""
        if employee.religion != "Muslim":
            return False

        return RamadanPeriod.objects.filter(
            year=date.year,
            start_date__lte=date,
            end_date__gte=date,
            is_active=True
        ).exists()

    @staticmethod
    def get_employee_shift(employee: Employee, date: datetime.date) -> Optional[ShiftAssignment]:
        """Get the active shift assignment for an employee on a given date"""
        return ShiftAssignment.objects.filter(
            employee=employee,
            start_date__lte=date,
            is_active=True
        ).filter(
            Q(end_date__isnull=True) | Q(end_date__gte=date)
        ).first()

    
    @staticmethod
    def calculate_status(attendance_log: AttendanceLog) -> dict:
        """
        Calculate attendance status, late minutes, early departure etc.
        Returns dict with status details
        """
        # Get the shift assignment
        shift_assignment = AttendanceStatusService.get_employee_shift(
            attendance_log.employee, attendance_log.date
        )

        # If no shift assigned, use default shift
        if not shift_assignment:
            shift = attendance_log.shift  # Fallback to the one set in attendance_log
            if not shift:
                return {
                    'status': 'absent',
                    'is_late': False,
                    'late_minutes': 0,
                    'early_departure': False,
                    'early_minutes': 0,
                    'total_work_minutes': 0
                }
        else:
            shift = shift_assignment.shift
            attendance_log.shift = shift  # Update the log with the correct shift

        
        # Check if it's Ramadan for Muslim employees
        is_ramadan_day = AttendanceStatusService.is_ramadan(attendance_log.date, attendance_log.employee)

        # Get shift times
        shift_start = shift.start_time
        shift_end = shift.end_time if not is_ramadan_day else (
            datetime.combine(attendance_log.date, shift_start) + timedelta(hours=6)
        ).time()
        
        # Initialize result
        result = {
            'status': 'absent',
            'is_late': False,
            'late_minutes': 0,
            'early_departure': False,
            'early_minutes': 0,
            'total_work_minutes': 0
        }
        
        # If no check-in/out, mark as absent
        if not attendance_log.first_in_time or not attendance_log.last_out_time:
            return result

        # Apply grace period for lateness
        actual_start = (
            datetime.combine(attendance_log.date, shift_start) + 
            timedelta(minutes=shift.grace_period)
        ).time()

        # Calculate late minutes only if beyond grace period
        if attendance_log.first_in_time > actual_start:
            late_delta = datetime.combine(attendance_log.date, attendance_log.first_in_time) - \
                        datetime.combine(attendance_log.date, shift_start)
            result['is_late'] = True
            result['late_minutes'] = late_delta.seconds // 60
            
        # Calculate early departure
        if attendance_log.last_out_time < shift_end:
            early_delta = datetime.combine(attendance_log.date, shift_end) - \
                         datetime.combine(attendance_log.date, attendance_log.last_out_time)
            result['early_departure'] = True
            result['early_minutes'] = early_delta.seconds // 60
            
        # Calculate total work minutes
        work_delta = datetime.combine(attendance_log.date, attendance_log.last_out_time) - \
                    datetime.combine(attendance_log.date, attendance_log.first_in_time)

        total_minutes = work_delta.seconds // 60

        # Handle break deduction
        if is_ramadan_day:
            # No break deduction during Ramadan
            result['total_work_minutes'] = total_minutes
        else:
            # Always deduct break duration unless it's a custom shift with different break duration
            result['total_work_minutes'] = total_minutes - shift.break_duration
        
        # Determine status
        if result['is_late']:
            result['status'] = 'late'
        else:
            result['status'] = 'present'
            
        return result
    
    @staticmethod
    def update_attendance_status(attendance_log: AttendanceLog):
        """Update attendance log with calculated status"""
        status_details = AttendanceStatusService.calculate_status(attendance_log)
        
        for key, value in status_details.items():
            setattr(attendance_log, key, value)
            
        attendance_log.save()


class FridayRuleService:
    """Service class for handling Friday attendance rules"""

    @staticmethod
    def get_friday_status(employee: Employee, friday_date: datetime.date) -> str:
        """
        Determine Friday attendance status based on Thursday and Saturday attendance.
        
        Rules:
        1. If employee works on both Thursday and Saturday -> Present
        2. If employee is absent on both Thursday and Saturday -> Absent
        3. If employee is present on either Thursday or Saturday -> Present
        """
        # Verify the date is a Friday
        if friday_date.weekday() != 4:  # 4 is Friday
            raise ValueError("Provided date is not a Friday")

        thursday_date = friday_date - timedelta(days=1)
        saturday_date = friday_date + timedelta(days=1)

        # Check Thursday attendance
        thursday_present = AttendanceLog.objects.filter(
            employee=employee,
            date=thursday_date,
            is_active=True,
            first_in_time__isnull=False
        ).exists()

        # Check Saturday attendance
        saturday_present = AttendanceLog.objects.filter(
            employee=employee,
            date=saturday_date,
            is_active=True,
            first_in_time__isnull=False
        ).exists()

        # Apply rules
        if thursday_present and saturday_present:
            return 'present'
        elif not thursday_present and not saturday_present:
            return 'absent'
        else:
            return 'present'

    @staticmethod
    def process_friday_attendance():
        """Process Friday attendance for all employees"""
        today = timezone.now().date()
        if today.weekday() != 4:  # Not Friday
            return

        employees = Employee.objects.filter(is_active=True)
        for employee in employees:
            status = FridayRuleService.get_friday_status(employee, today)
            AttendanceLog.objects.update_or_create(
                employee=employee,
                date=today,
                defaults={
                    'status': status,
                    'source': 'friday_rule'
                }
            )

class LeaveBalanceService:
    """Service class for managing leave balances"""

    @staticmethod
    def calculate_annual_leave_accrual(employee: Employee, period_start: datetime.date, period_end: datetime.date) -> float:
        """
        Calculate annual leave accrual based on worked days.
        Rate: 2.5 days for every 30 working days
        """
        # Count working days (including Fridays that count as worked)
        worked_days = AttendanceLog.objects.filter(
            Q(employee=employee) &
            Q(date__range=(period_start, period_end)) &
            Q(is_active=True) &
            (Q(status='present') | Q(source='friday_rule'))
        ).count()

        # Calculate accrual
        return (worked_days / 30) * 2.5

    @staticmethod
    def update_leave_balances():
        """Update leave balances for all employees"""
        today = timezone.now().date()
        first_of_month = today.replace(day=1)
        
        if today != first_of_month:  # Only run on first day of month
            return

        employees = Employee.objects.filter(is_active=True)
        leave_types = LeaveType.objects.filter(is_active=True)

        for employee in employees:
            for leave_type in leave_types:
                if leave_type.accrual_type == 'annual':
                    # Calculate accrual for previous month
                    last_month_end = first_of_month - timedelta(days=1)
                    last_month_start = last_month_end.replace(day=1)
                    
                    accrual = LeaveBalanceService.calculate_annual_leave_accrual(
                        employee, last_month_start, last_month_end
                    )

                    # Update balance
                    balance, created = LeaveBalance.objects.get_or_create(
                        employee=employee,
                        leave_type=leave_type,
                        is_active=True,
                        defaults={'total_days': 0, 'available_days': 0}
                    )
                    
                    balance.total_days += accrual
                    balance.available_days += accrual
                    balance.save()

class LeaveRequestService:
    """Service class for handling leave requests"""

    @staticmethod
    def validate_leave_request(
        employee: Employee,
        leave_type: LeaveType,
        start_date: datetime.date,
        end_date: datetime.date,
        start_half: bool = False,
        end_half: bool = False
    ) -> Dict[str, Any]:
        """Validate a leave request"""
        if start_date > end_date:
            return {'valid': False, 'error': 'End date cannot be before start date'}

        # Calculate duration
        duration = (end_date - start_date).days + 1
        if start_half:
            duration -= 0.5
        if end_half:
            duration -= 0.5

        # Check balance
        try:
            balance = LeaveBalance.objects.get(
                employee=employee,
                leave_type=leave_type,
                is_active=True
            )
            if duration > balance.available_days:
                return {
                    'valid': False,
                    'error': f'Insufficient leave balance. Available: {balance.available_days} days'
                }
        except LeaveBalance.DoesNotExist:
            return {'valid': False, 'error': 'No leave balance found'}

        # Check for overlapping leaves
        overlapping = Leave.objects.filter(
            employee=employee,
            is_active=True,
            status__in=['pending', 'approved'],
            start_date__lte=end_date,
            end_date__gte=start_date
        ).exists()

        if overlapping:
            return {'valid': False, 'error': 'Leave dates overlap with existing leave'}

        return {
            'valid': True,
            'duration': duration,
            'balance_after': balance.available_days - duration
        }

    @staticmethod
    def create_leave_request(
        employee: Employee,
        leave_type: LeaveType,
        start_date: datetime.date,
        end_date: datetime.date,
        reason: str,
        start_half: bool = False,
        end_half: bool = False,
        documents: List = None
    ) -> Dict[str, Any]:
        """Create a new leave request"""
        validation = LeaveRequestService.validate_leave_request(
            employee, leave_type, start_date, end_date, start_half, end_half
        )

        if not validation['valid']:
            return {'success': False, 'error': validation['error']}

        leave = Leave.objects.create(
            employee=employee,
            leave_type=leave_type,
            start_date=start_date,
            end_date=end_date,
            start_half=start_half,
            end_half=end_half,
            duration=validation['duration'],
            reason=reason,
            status='pending'
        )

        if documents:
            for doc in documents:
                leave.documents.create(document=doc)

        return {'success': True, 'leave_request': leave}

class RecurringHolidayService:
    """Service class for managing recurring holidays"""

    @staticmethod
    def generate_next_year_holidays():
        """Generate holidays for next year based on recurring holidays"""
        # Only run in December
        if timezone.now().month != 12:
            return

        next_year = timezone.now().year + 1
        holidays = Holiday.objects.filter(
            is_recurring=True,
            is_active=True
        )

        for holiday in holidays:
            # Create holiday for next year
            Holiday.objects.get_or_create(
                date=holiday.date.replace(year=next_year),
                defaults={
                    'name': holiday.name,
                    'holiday_type': holiday.holiday_type,
                    'description': holiday.description,
                    'is_paid': holiday.is_paid,
                    'is_recurring': False,  # New instance is not recurring
                }
            )
            
            if holiday.applicable_departments.exists():
                new_holiday = Holiday.objects.get(
                    date=holiday.date.replace(year=next_year)
                )
                new_holiday.applicable_departments.set(
                    holiday.applicable_departments.all()
                )

```

### hrms_project\attendance\signals.py
```
from django.db.models.signals import pre_save, post_save, pre_delete, post_delete
from django.dispatch import receiver
from django.core.cache import cache
from django.utils import timezone
from django.db import transaction

from .models import Shift, ShiftAssignment, RamadanPeriod, AttendanceLog
from .services import ShiftService, RamadanService

from django.core.exceptions import ObjectDoesNotExist
from .models import (
    AttendanceRecord, AttendanceLog, Leave, LeaveType, 
    LeaveBalance, Holiday, Employee
)
from .services import AttendanceStatusService
from datetime import datetime, timedelta

@receiver(pre_save, sender=ShiftAssignment)
def handle_shift_assignment_update(sender, instance, **kwargs):
    """Handle shift assignment changes"""
    if instance.pk:  # Existing assignment
        old_instance = ShiftAssignment.objects.get(pk=instance.pk)
        
        # If making active and wasn't active before
        if instance.is_active and not old_instance.is_active:
            # Deactivate other active assignments for this employee
            ShiftAssignment.objects.filter(
                employee=instance.employee,
                is_active=True
            ).exclude(pk=instance.pk).update(is_active=False)
            
        # Clear employee shift cache
        cache_key = f'employee_shift_{instance.employee_id}'
        cache.delete(cache_key)

@receiver(post_save, sender=ShiftAssignment)
def handle_shift_assignment_create(sender, instance, created, **kwargs):
    """Handle new shift assignments"""
    if created and instance.is_active:
        # Deactivate other active assignments for this employee
        with transaction.atomic():
            ShiftAssignment.objects.filter(
                employee=instance.employee,
                is_active=True
            ).exclude(pk=instance.pk).update(is_active=False)
    
    # Clear employee shift cache
    cache_key = f'employee_shift_{instance.employee_id}'
    cache.delete(cache_key)

@receiver(pre_delete, sender=ShiftAssignment)
def handle_shift_assignment_delete(sender, instance, **kwargs):
    """Handle shift assignment deletion"""
    # Clear employee shift cache
    cache_key = f'employee_shift_{instance.employee_id}'
    cache.delete(cache_key)

@receiver(pre_save, sender=RamadanPeriod)
def validate_ramadan_period(sender, instance, **kwargs):
    """Validate Ramadan period before saving"""
    if instance.pk:
        # Update case
        RamadanService.validate_period_dates(
            start_date=instance.start_date,
            end_date=instance.end_date,
            year=instance.year,
            exclude_id=instance.pk
        )
    else:
        # Create case
        RamadanService.validate_period_dates(
            start_date=instance.start_date,
            end_date=instance.end_date,
            year=instance.year
        )

@receiver(post_save, sender=RamadanPeriod)
def handle_ramadan_period_change(sender, instance, created, **kwargs):
    """Handle Ramadan period changes"""
    # Clear any cached Ramadan period information
    cache.delete_pattern('ramadan_period_*')
    
    if instance.is_active:
        # Deactivate other active periods in the same year
        RamadanPeriod.objects.filter(
            year=instance.year,
            is_active=True
        ).exclude(pk=instance.pk).update(is_active=False)

@receiver(pre_save, sender=Shift)
def validate_shift_timing(sender, instance, **kwargs):
    """Validate shift timing before saving"""
    if instance.start_time == instance.end_time:
        raise ValueError("Start time and end time cannot be the same")
        
    if instance.break_duration < 0 or instance.break_duration > 180:
        raise ValueError("Break duration must be between 0 and 180 minutes")
        
    if instance.grace_period < 0 or instance.grace_period > 60:
        raise ValueError("Grace period must be between 0 and 60 minutes")

@receiver(post_save, sender=Shift)
def handle_shift_changes(sender, instance, created, **kwargs):
    """Handle shift changes"""
    # Clear shift-related caches
    cache.delete_pattern('shift_*')
    
    # If shift is deactivated, deactivate its assignments
    if not instance.is_active:
        ShiftAssignment.objects.filter(
            shift=instance,
            is_active=True
        ).update(is_active=False)

@receiver(pre_save, sender=AttendanceLog)
def calculate_attendance_status(sender, instance, **kwargs):
    """Calculate attendance status based on shift"""
    if not hasattr(instance, 'employee'):
        return
        
    # Get employee's shift for the date
    shift = ShiftService.get_employee_current_shift(instance.employee)
    if not shift:
        return
        
    # Get Ramadan adjusted timing if applicable
    ramadan_timing = RamadanService.get_ramadan_shift_timing(shift, instance.date)
    
    if ramadan_timing:
        shift_start = ramadan_timing['start_time']
        shift_end = ramadan_timing['end_time']
    else:
        shift_start = shift.start_time
        shift_end = shift.end_time
    
    # Calculate late status
    if instance.first_in_time:
        grace_minutes = shift.grace_period
        shift_start_dt = datetime.combine(instance.date, shift_start)
        actual_in_dt = datetime.combine(instance.date, instance.first_in_time)
        
        instance.is_late = actual_in_dt > (shift_start_dt + timedelta(minutes=grace_minutes))
        if instance.is_late:
            instance.late_minutes = int((actual_in_dt - shift_start_dt).total_seconds() / 60)
    
    # Calculate early departure
    if instance.last_out_time:
        shift_end_dt = datetime.combine(instance.date, shift_end)
        actual_out_dt = datetime.combine(instance.date, instance.last_out_time)
        
        instance.early_departure = actual_out_dt < shift_end_dt
        if instance.early_departure:
            instance.early_minutes = int((shift_end_dt - actual_out_dt).total_seconds() / 60)
    
    # Calculate work duration
    if instance.first_in_time and instance.last_out_time:
        total_minutes = int(
            (instance.last_out_time.hour * 60 + instance.last_out_time.minute) -
            (instance.first_in_time.hour * 60 + instance.first_in_time.minute)
        )
        # Subtract break duration
        instance.total_work_minutes = max(0, total_minutes - shift.break_duration)


@receiver(post_save, sender=AttendanceRecord)
def process_attendance_record(sender, instance, created, **kwargs):
    """
    Process attendance record to create or update attendance log
    """
    if not created and not instance.is_active:
        return

    # Get or create attendance log for the day
    date = instance.timestamp.date()
    try:
        log = AttendanceLog.objects.get(
            employee=instance.employee,
            date=date,
            is_active=True
        )
    except AttendanceLog.DoesNotExist:
        log = AttendanceLog(
            employee=instance.employee,
            date=date,
            source='system'
        )

    # Get all active records for the day
    records = AttendanceRecord.objects.filter(
        employee=instance.employee,
        timestamp__date=date,
        is_active=True
    ).order_by('timestamp')

    if records.exists():
        # Update log times and shift
        log.first_in_time = records.first().timestamp.time()
        log.last_out_time = records.last().timestamp.time()
        # Get the shift assignment
        shift_assignment = ShiftService.get_employee_current_shift(instance.employee)
        if shift_assignment:
            log.shift = shift_assignment
        
        # Save initial changes
        log.save()
        
        # Calculate and update status
        AttendanceStatusService.update_attendance_status(log)

@receiver(post_delete, sender=AttendanceRecord)
def cleanup_attendance_record(sender, instance, **kwargs):
    """
    Clean up attendance log when record is deleted
    """
    date = instance.timestamp.date()
    
    try:
        log = AttendanceLog.objects.get(
            employee=instance.employee,
            date=date,
            is_active=True
        )
        
        # Get remaining records for the day
        records = AttendanceRecord.objects.filter(
            employee=instance.employee,
            timestamp__date=date,
            is_active=True
        ).order_by('timestamp')
        
        if not records.exists():
            # No more records, delete log
            log.delete()
        else:
            # Update log times
            log.first_in_time = records.first().timestamp.time()
            log.last_out_time = records.last().timestamp.time()
            log.save()
            
    except AttendanceLog.DoesNotExist:
        pass

@receiver(post_save, sender=Leave)
def process_leave_request(sender, instance, created, **kwargs):
    """
    Process leave request approval/rejection
    """
    if not instance.is_active:
        return

    if instance.status == 'approved':
        # Create attendance logs for leave days
        current_date = instance.start_date
        while current_date <= instance.end_date:
            # Skip if log already exists
            if not AttendanceLog.objects.filter(
                employee=instance.employee,
                date=current_date,
                is_active=True
            ).exists():
                AttendanceLog.objects.create(
                    employee=instance.employee,
                    date=current_date,
                    status='leave',
                    source='leave',
                    leave=instance
                )
            current_date += timedelta(days=1)

        # Update leave balance
        try:
            balance = LeaveBalance.objects.get(
                employee=instance.employee,
                leave_type=instance.leave_type,
                is_active=True
            )
            balance.available_days -= instance.duration
            balance.save()
        except LeaveBalance.DoesNotExist:
            pass

@receiver(post_delete, sender=Leave)
def cleanup_leave_request(sender, instance, **kwargs):
    """
    Clean up attendance logs when leave is deleted
    """
    # Delete attendance logs created for this leave
    AttendanceLog.objects.filter(
        employee=instance.employee,
        date__range=(instance.start_date, instance.end_date),
        source='leave',
        leave=instance,
        is_active=True
    ).delete()

    # Restore leave balance if was approved
    if instance.status == 'approved':
        try:
            balance = LeaveBalance.objects.get(
                employee=instance.employee,
                leave_type=instance.leave_type,
                is_active=True
            )
            balance.available_days += instance.duration
            balance.save()
        except LeaveBalance.DoesNotExist:
            pass

@receiver(post_save, sender=Holiday)
def process_holiday(sender, instance, created, **kwargs):
    """
    Process holiday creation/update
    """
    if not instance.is_active:
        return

    # Create attendance logs for holiday
    employees = Employee.objects.filter(is_active=True)
    if instance.applicable_departments.exists():
        employees = employees.filter(department__in=instance.applicable_departments.all())

    for employee in employees:
        # Skip if log already exists
        if not AttendanceLog.objects.filter(
            employee=employee,
            date=instance.date,
            is_active=True
        ).exists():
            AttendanceLog.objects.create(
                employee=employee,
                date=instance.date,
                status='holiday',
                source='holiday',
                holiday=instance
            )

@receiver(post_delete, sender=Holiday)
def cleanup_holiday(sender, instance, **kwargs):
    """
    Clean up attendance logs when holiday is deleted
    """
    # Delete attendance logs created for this holiday
    AttendanceLog.objects.filter(
        date=instance.date,
        source='holiday',
        holiday=instance,
        is_active=True
    ).delete()

@receiver(post_save, sender=LeaveType)
def create_leave_balances(sender, instance, created, **kwargs):
    """
    Create leave balances for new leave type
    """
    if created and instance.is_active:
        # Create leave balance for all active employees
        employees = Employee.objects.filter(is_active=True)
        balances = []
        
        for employee in employees:
            if not LeaveBalance.objects.filter(
                employee=employee,
                leave_type=instance,
                is_active=True
            ).exists():
                balances.append(LeaveBalance(
                    employee=employee,
                    leave_type=instance,
                    total_days=instance.default_days,
                    available_days=instance.default_days
                ))
        
        if balances:
            LeaveBalance.objects.bulk_create(balances)

```

### hrms_project\attendance\static\attendance\css\attendance.css
```
/* Attendance Calendar */
.calendar-container {
    margin: 20px 0;
    padding: 20px;
    border-radius: 8px;
    background-color: white;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.calendar-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 20px;
}

.calendar-title {
    font-size: 1.5rem;
    font-weight: bold;
    color: #333;
}

.calendar-nav {
    display: flex;
    gap: 10px;
}

.calendar {
    width: 100%;
    border-collapse: collapse;
}

.calendar th {
    padding: 10px;
    text-align: center;
    background-color: #f8f9fa;
    border: 1px solid #dee2e6;
}

.calendar td {
    width: 14.28%;
    padding: 0;
    border: 1px solid #dee2e6;
    position: relative;
}

.calendar td > div {
    min-height: 100px;
    padding: 10px;
}

.calendar .date-number {
    position: absolute;
    top: 5px;
    right: 5px;
    width: 24px;
    height: 24px;
    line-height: 24px;
    text-align: center;
    border-radius: 50%;
}

/* Calendar Status Classes */
.calendar td.weekend {
    background-color: #f8f9fa;
}

.calendar td.today .date-number {
    background-color: #007bff;
    color: white;
}

.calendar td.present {
    background-color: #d4edda;
}

.calendar td.absent {
    background-color: #f8d7da;
}

.calendar td.late {
    background-color: #fff3cd;
}

.calendar td.leave {
    background-color: #cce5ff;
}

.calendar td.holiday {
    background-color: #e2e3e5;
}

/* Attendance Status Badges */
.status-badge {
    display: inline-block;
    padding: 4px 8px;
    border-radius: 4px;
    font-size: 12px;
    font-weight: bold;
    text-transform: uppercase;
}

/* Leave Request Form */
.leave-request-form {
    max-width: 800px;
    margin: 20px auto;
    padding: 20px;
    background-color: white;
    border-radius: 8px;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.leave-balance-summary {
    margin: 20px 0;
    padding: 15px;
    background-color: #f8f9fa;
    border-radius: 4px;
}

.leave-balance-item {
    display: flex;
    justify-content: space-between;
    padding: 10px;
    border-bottom: 1px solid #dee2e6;
}

.leave-balance-item:last-child {
    border-bottom: none;
}

/* Attendance Log Details */
.attendance-detail {
    padding: 20px;
    background-color: white;
    border-radius: 8px;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.time-log {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 10px;
    margin: 5px 0;
    background-color: #f8f9fa;
    border-radius: 4px;
}

.time-log .time {
    font-size: 1.2rem;
    font-weight: bold;
}

.time-log .source {
    font-size: 0.9rem;
    color: #6c757d;
}

/* Monthly Summary */
.attendance-summary {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 15px;
    padding: 15px;
    background-color: #f8f9fa;
    border-radius: 8px;
    margin: 20px 0;
}

.attendance-summary > div {
    padding: 10px;
    background-color: white;
    border-radius: 4px;
    text-align: center;
    box-shadow: 0 1px 3px rgba(0,0,0,0.1);
}

.attendance-summary .present { color: #28a745; }
.attendance-summary .late { color: #ffc107; }
.attendance-summary .absent { color: #dc3545; }
.attendance-summary .leave { color: #17a2b8; }
.attendance-summary .holiday { color: #6c757d; }

/* Holiday List */
.holiday-list {
    list-style: none;
    padding: 0;
}

.holiday-item {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 15px;
    margin: 10px 0;
    background-color: white;
    border-radius: 8px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.1);
}

.holiday-date {
    font-weight: bold;
    color: #495057;
}

.holiday-name {
    flex-grow: 1;
    margin: 0 15px;
}

/* Leave Request List */
.leave-request-list {
    list-style: none;
    padding: 0;
}

.leave-request-item {
    padding: 15px;
    margin: 10px 0;
    background-color: white;
    border-radius: 8px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.1);
}

.leave-request-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 10px;
}

.leave-request-dates {
    font-size: 0.9rem;
    color: #6c757d;
}

/* Status Colors */
.status-pending { color: #ffc107; }
.status-approved { color: #28a745; }
.status-rejected { color: #dc3545; }

/* Responsive Design */
@media (max-width: 768px) {
    .calendar td > div {
        min-height: 60px;
    }
    
    .attendance-summary {
        grid-template-columns: repeat(2, 1fr);
    }
    
    .leave-request-header {
        flex-direction: column;
        align-items: flex-start;
    }
    
    .leave-request-dates {
        margin-top: 5px;
    }
}

@media (max-width: 576px) {
    .calendar-header {
        flex-direction: column;
        gap: 10px;
    }
    
    .attendance-summary {
        grid-template-columns: 1fr;
    }
}

```

### hrms_project\attendance\static\attendance\css\reports.css
```
body {
    font-family: Arial, sans-serif;
    line-height: 1.6;
    color: #333;
    max-width: 1200px;
    margin: 0 auto;
    padding: 20px;
}

.header {
    text-align: center;
    padding: 20px;
    background-color: #f8f9fa;
    border-bottom: 3px solid #007bff;
    margin-bottom: 30px;
}

.department-info {
    background-color: #fff;
    padding: 20px;
    border-radius: 5px;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    margin-bottom: 30px;
}

.info-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
    gap: 20px;
    margin-bottom: 20px;
}

.info-item {
    padding: 10px;
    background-color: #f8f9fa;
    border-radius: 4px;
}

.info-label {
    font-weight: bold;
    color: #495057;
    margin-bottom: 5px;
}

.info-value {
    color: #212529;
}

.stats-container {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 20px;
    margin-bottom: 30px;
}

.stat-card {
    background-color: #fff;
    padding: 20px;
    border-radius: 5px;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    text-align: center;
}

.stat-value {
    font-size: 24px;
    font-weight: bold;
    margin: 10px 0;
}

.stat-label {
    color: #6c757d;
    font-size: 14px;
}

.employee-list {
    margin-bottom: 30px;
}

.table-container {
    overflow-x: auto;
}

table {
    width: 100%;
    border-collapse: collapse;
    margin: 20px 0;
}

th, td {
    padding: 12px;
    text-align: left;
    border-bottom: 1px solid #dee2e6;
}

th {
    background-color: #f8f9fa;
    font-weight: bold;
    color: #495057;
}

tr:hover {
    background-color: #f8f9fa;
}

.chart-container {
    background-color: #fff;
    padding: 20px;
    border-radius: 5px;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    margin-bottom: 30px;
}

.progress-bar {
    height: 8px;
    background-color: #e9ecef;
    border-radius: 4px;
    margin: 10px 0;
    overflow: hidden;
}

.progress-fill {
    height: 100%;
    border-radius: 4px;
    transition: width 0.3s ease;
}

.leave-section {
    margin-bottom: 40px;
}

.trend-indicator {
    display: inline-block;
    margin-left: 5px;
    font-size: 12px;
}

/* Status Colors */
.stat-card.stat-present .stat-value { color: #28a745; }
.stat-card.stat-absent .stat-value { color: #dc3545; }
.stat-card.stat-late .stat-value { color: #ffc107; }
.stat-card.stat-leave .stat-value { color: #17a2b8; }

.trend-up { color: #28a745; }
.trend-down { color: #dc3545; }
.trend-neutral { color: #6c757d; }

/* Status Badges */
.status-badge {
    padding: 4px 8px;
    border-radius: 4px;
    font-size: 12px;
    font-weight: bold;
}

.status-badge.present,
.status-badge.approved { 
    background-color: #d4edda; 
    color: #155724; 
}

.status-badge.absent,
.status-badge.rejected { 
    background-color: #f8d7da; 
    color: #721c24; 
}

.status-badge.late,
.status-badge.pending { 
    background-color: #fff3cd; 
    color: #856404; 
}

.status-badge.leave,
.status-badge.holiday { 
    background-color: #d1ecf1; 
    color: #0c5460; 
}

/* Employee Report Specific */
.employee-info {
    background-color: #fff;
    padding: 20px;
    border-radius: 5px;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    margin-bottom: 30px;
}

.daily-attendance,
.leave-details {
    background-color: #fff;
    padding: 20px;
    border-radius: 5px;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    margin-bottom: 30px;
}

.percent-indicator {
    font-size: 14px;
    color: #6c757d;
    margin-top: 5px;
    text-align: right;
}

.footer {
    text-align: center;
    margin-top: 30px;
    padding-top: 20px;
    border-top: 1px solid #dee2e6;
    color: #6c757d;
    font-size: 12px;
}

/* Print Styles */
@media print {
    body {
        padding: 0;
        background: white;
    }
    
    .header {
        background: white !important;
        color: black !important;
    }
    
    .chart-container,
    .department-info,
    .stat-card {
        break-inside: avoid;
        box-shadow: none;
        border: 1px solid #dee2e6;
    }
    
    table { page-break-inside: auto; }
    tr { page-break-inside: avoid; }
}

```

### hrms_project\attendance\static\attendance\css\shifts.css
```
/* Shift Management Styles */

/* Shift List */
.shift-list {
    margin-bottom: 2rem;
}

.shift-card {
    border: 1px solid #dee2e6;
    border-radius: 0.5rem;
    margin-bottom: 1rem;
    transition: box-shadow 0.3s ease;
}

.shift-card:hover {
    box-shadow: 0 0.125rem 0.25rem rgba(0, 0, 0, 0.075);
}

.shift-header {
    padding: 1rem;
    background-color: #f8f9fa;
    border-bottom: 1px solid #dee2e6;
    border-radius: 0.5rem 0.5rem 0 0;
    display: flex;
    justify-content: space-between;
    align-items: center;
}

.shift-body {
    padding: 1rem;
}

.shift-footer {
    padding: 0.75rem 1rem;
    background-color: #f8f9fa;
    border-top: 1px solid #dee2e6;
    border-radius: 0 0 0.5rem 0.5rem;
}

/* Shift Types */
.shift-type {
    display: inline-block;
    padding: 0.25rem 0.5rem;
    border-radius: 0.25rem;
    font-size: 0.875rem;
    font-weight: 500;
}

.shift-type-regular {
    background-color: #e3f2fd;
    color: #0d47a1;
}

.shift-type-night {
    background-color: #ede7f6;
    color: #4527a0;
}

.shift-type-flexible {
    background-color: #e8f5e9;
    color: #1b5e20;
}

.shift-type-split {
    background-color: #fff3e0;
    color: #e65100;
}

.shift-type-ramadan {
    background-color: #fce4ec;
    color: #880e4f;
}

/* Shift Timing */
.shift-timing {
    display: flex;
    align-items: center;
    margin: 0.5rem 0;
    color: #495057;
}

.shift-timing i {
    margin-right: 0.5rem;
    color: #6c757d;
}

/* Break Duration */
.break-duration {
    color: #6c757d;
    font-size: 0.875rem;
    margin-top: 0.25rem;
}

/* Grace Period */
.grace-period {
    background-color: #fff3cd;
    border: 1px solid #ffeeba;
    color: #856404;
    padding: 0.25rem 0.5rem;
    border-radius: 0.25rem;
    font-size: 0.875rem;
    display: inline-block;
    margin-top: 0.5rem;
}

/* Assignment Section */
.assignment-list {
    margin-top: 1rem;
}

.assignment-item {
    padding: 0.75rem;
    border: 1px solid #dee2e6;
    border-radius: 0.25rem;
    margin-bottom: 0.5rem;
    display: flex;
    justify-content: space-between;
    align-items: center;
}

/* Active/Inactive Status */
.status-badge {
    padding: 0.25rem 0.5rem;
    border-radius: 0.25rem;
    font-size: 0.75rem;
    font-weight: 600;
}

.status-active {
    background-color: #d4edda;
    color: #155724;
}

.status-inactive {
    background-color: #f8d7da;
    color: #721c24;
}

/* Ramadan Period */
.ramadan-period {
    background-color: #fff8e1;
    border: 1px solid #ffecb3;
    border-radius: 0.5rem;
    padding: 1rem;
    margin-bottom: 1rem;
}

.ramadan-dates {
    color: #b71c1c;
    font-weight: 500;
    margin: 0.5rem 0;
}

.ramadan-badge {
    background-color: #ffebee;
    color: #c62828;
    padding: 0.25rem 0.75rem;
    border-radius: 1rem;
    font-size: 0.875rem;
    display: inline-block;
}

/* Assignment Forms */
.assignment-form {
    max-width: 600px;
    margin: 0 auto;
    padding: 1.5rem;
    background-color: #fff;
    border-radius: 0.5rem;
    box-shadow: 0 0.125rem 0.25rem rgba(0, 0, 0, 0.075);
}

.date-range-inputs {
    display: flex;
    gap: 1rem;
    margin-bottom: 1rem;
}

.employee-select {
    margin-bottom: 1.5rem;
}

/* Shift Statistics */
.shift-stats {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 1rem;
    margin: 1rem 0;
}

.stat-card {
    padding: 1rem;
    background-color: #f8f9fa;
    border-radius: 0.5rem;
    text-align: center;
}

.stat-value {
    font-size: 1.5rem;
    font-weight: 600;
    color: #0d6efd;
}

.stat-label {
    color: #6c757d;
    font-size: 0.875rem;
    margin-top: 0.25rem;
}

/* Responsive Design */
@media (max-width: 768px) {
    .shift-header {
        flex-direction: column;
        align-items: flex-start;
    }
    
    .shift-header .btn-group {
        margin-top: 0.5rem;
    }
    
    .shift-stats {
        grid-template-columns: 1fr;
    }
    
    .date-range-inputs {
        flex-direction: column;
        gap: 0.5rem;
    }
}

```

### hrms_project\attendance\static\attendance\js\attendance.js
```
// Initialize calendar and event handlers
document.addEventListener('DOMContentLoaded', function() {
    initializeCalendar();
    initializeLeaveForm();
    initializeAttendanceMarking();
    setupDateRangePicker();
});

// Calendar Functions
function initializeCalendar() {
    const calendarEl = document.getElementById('attendance-calendar');
    if (!calendarEl) return;

    const calendar = new FullCalendar.Calendar(calendarEl, {
        initialView: 'dayGridMonth',
        headerToolbar: {
            left: 'prev,next today',
            center: 'title',
            right: 'dayGridMonth,timeGridWeek,timeGridDay'
        },
        events: '/attendance/api/calendar-events/',
        eventDidMount: function(info) {
            // Add tooltips to events
            const status = info.event.extendedProps.status;
            const timeIn = info.event.extendedProps.first_in || '';
            const timeOut = info.event.extendedProps.last_out || '';
            
            tippy(info.el, {
                content: `
                    <strong>Status:</strong> ${status}<br>
                    <strong>Time In:</strong> ${timeIn}<br>
                    <strong>Time Out:</strong> ${timeOut}
                `,
                allowHTML: true
            });
        },
        eventClick: function(info) {
            showAttendanceDetail(info.event);
        }
    });

    calendar.render();
}

function showAttendanceDetail(event) {
    // Fetch and display attendance details in modal
    fetch(`/attendance/api/logs/${event.id}/details/`)
        .then(response => response.json())
        .then(data => {
            const modal = new bootstrap.Modal(document.getElementById('attendance-detail-modal'));
            document.getElementById('attendance-detail-content').innerHTML = `
                <div class="attendance-detail">
                    <h5>Attendance Details</h5>
                    <div class="detail-row">
                        <strong>Date:</strong> ${data.date}
                    </div>
                    <div class="detail-row">
                        <strong>Status:</strong> ${data.status}
                    </div>
                    <div class="detail-row">
                        <strong>Time In:</strong> ${data.first_in || '-'}
                    </div>
                    <div class="detail-row">
                        <strong>Time Out:</strong> ${data.last_out || '-'}
                    </div>
                    <div class="detail-row">
                        <strong>Source:</strong> ${data.source}
                    </div>
                </div>
            `;
            modal.show();
        })
        .catch(error => console.error('Error:', error));
}

// Leave Request Functions
function initializeLeaveForm() {
    const leaveForm = document.getElementById('leave-request-form');
    if (!leaveForm) return;

    const leaveTypeSelect = document.getElementById('leave_type');
    const startDateInput = document.getElementById('start_date');
    const endDateInput = document.getElementById('end_date');

    // Update leave balance display when type changes
    leaveTypeSelect?.addEventListener('change', function() {
        updateLeaveBalance(this.value);
    });

    // Calculate duration when dates change
    [startDateInput, endDateInput].forEach(input => {
        input?.addEventListener('change', function() {
            if (startDateInput.value && endDateInput.value) {
                calculateLeaveDuration(startDateInput.value, endDateInput.value);
            }
        });
    });

    // Handle form submission
    leaveForm.addEventListener('submit', function(e) {
        e.preventDefault();
        submitLeaveRequest(new FormData(this));
    });
}

function updateLeaveBalance(leaveTypeId) {
    if (!leaveTypeId) return;

    fetch(`/attendance/api/leave-balance/${leaveTypeId}/`)
        .then(response => response.json())
        .then(data => {
            document.getElementById('leave-balance-display').innerHTML = `
                Available: ${data.available_days} days<br>
                Consumed: ${data.consumed_days} days
            `;
        })
        .catch(error => console.error('Error:', error));
}

function calculateLeaveDuration(startDate, endDate) {
    fetch('/attendance/api/calculate-leave-duration/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCsrfToken()
        },
        body: JSON.stringify({ start_date: startDate, end_date: endDate })
    })
    .then(response => response.json())
    .then(data => {
        document.getElementById('duration-display').textContent = 
            `Duration: ${data.duration} days`;
    })
    .catch(error => console.error('Error:', error));
}

function submitLeaveRequest(formData) {
    fetch('/attendance/api/leave-requests/', {
        method: 'POST',
        headers: {
            'X-CSRFToken': getCsrfToken()
        },
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showAlert('success', 'Leave request submitted successfully');
            setTimeout(() => window.location.href = '/attendance/leaves/', 2000);
        } else {
            showAlert('danger', data.error || 'Error submitting leave request');
        }
    })
    .catch(error => {
        showAlert('danger', 'Error submitting leave request');
        console.error('Error:', error);
    });
}

// Attendance Marking Functions
function initializeAttendanceMarking() {
    const markAttendanceForm = document.getElementById('mark-attendance-form');
    if (!markAttendanceForm) return;

    markAttendanceForm.addEventListener('submit', function(e) {
        e.preventDefault();
        submitAttendance(new FormData(this));
    });

    // Initialize employee search typeahead
    const employeeInput = document.getElementById('employee_search');
    if (employeeInput) {
        new Bloodhound({
            datumTokenizer: Bloodhound.tokenizers.obj.whitespace('value'),
            queryTokenizer: Bloodhound.tokenizers.whitespace,
            remote: {
                url: '/attendance/api/search-employees/?q=%QUERY',
                wildcard: '%QUERY'
            }
        });

        $(employeeInput).typeahead(null, {
            name: 'employees',
            display: 'full_name',
            source: employeeEngine
        });
    }
}

function submitAttendance(formData) {
    fetch('/attendance/api/mark-attendance/', {
        method: 'POST',
        headers: {
            'X-CSRFToken': getCsrfToken()
        },
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showAlert('success', 'Attendance marked successfully');
            document.getElementById('mark-attendance-form').reset();
        } else {
            showAlert('danger', data.error || 'Error marking attendance');
        }
    })
    .catch(error => {
        showAlert('danger', 'Error marking attendance');
        console.error('Error:', error);
    });
}

// Utility Functions
function setupDateRangePicker() {
    const dateRangePicker = document.getElementById('date-range');
    if (!dateRangePicker) return;

    $(dateRangePicker).daterangepicker({
        autoUpdateInput: false,
        locale: {
            cancelLabel: 'Clear'
        }
    });

    $(dateRangePicker).on('apply.daterangepicker', function(ev, picker) {
        $(this).val(picker.startDate.format('MM/DD/YYYY') + ' - ' + picker.endDate.format('MM/DD/YYYY'));
        updateDateRange(picker.startDate, picker.endDate);
    });

    $(dateRangePicker).on('cancel.daterangepicker', function(ev, picker) {
        $(this).val('');
    });
}

function showAlert(type, message) {
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type} alert-dismissible fade show`;
    alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
    `;
    
    const alertContainer = document.getElementById('alert-container');
    if (alertContainer) {
        alertContainer.appendChild(alertDiv);
        setTimeout(() => alertDiv.remove(), 5000);
    }
}

function getCsrfToken() {
    return document.querySelector('[name=csrfmiddlewaretoken]').value;
}

// Handle Back Button
window.addEventListener('popstate', function(e) {
    if (e.state && e.state.modal) {
        // Close any open modals when using browser back button
        const modals = document.querySelectorAll('.modal');
        modals.forEach(modal => {
            const modalInstance = bootstrap.Modal.getInstance(modal);
            if (modalInstance) modalInstance.hide();
        });
    }
});

```

### hrms_project\attendance\static\attendance\js\ramadan.js
```
class RamadanPeriodManager {
    constructor() {
        this.deleteId = null;
        this.initializeEventListeners();
    }

    initializeEventListeners() {
        document.addEventListener('DOMContentLoaded', () => {
            // Set current year as default
            const currentYear = new Date().getFullYear();
            const yearInput = document.getElementById('year');
            if (yearInput) {
                yearInput.value = currentYear;
            }
            
            // Add date validation listeners
            ['start_date', 'end_date'].forEach(id => {
                const element = document.getElementById(id);
                if (element) {
                    element.addEventListener('change', () => this.validatePeriod('add'));
                }
            });

            ['edit_start_date', 'edit_end_date'].forEach(id => {
                const element = document.getElementById(id);
                if (element) {
                    element.addEventListener('change', () => this.validatePeriod('edit'));
                }
            });
        });
    }

    validatePeriod(mode) {
        const prefix = mode === 'edit' ? 'edit_' : '';
        const startDate = document.getElementById(`${prefix}start_date`).value;
        const endDate = document.getElementById(`${prefix}end_date`).value;
        const validation = document.getElementById(`${prefix}periodValidation`);
        const message = document.getElementById(`${prefix}validationMessage`);
        
        if (startDate && endDate) {
            const start = new Date(startDate);
            const end = new Date(endDate);
            const days = Math.floor((end - start) / (1000 * 60 * 60 * 24)) + 1;
            
            if (days < 28 || days > 31) {
                validation.classList.remove('d-none', 'alert-info');
                validation.classList.add('alert-warning');
                message.textContent = `Duration (${days} days) seems unusual for Ramadan`;
            } else {
                validation.classList.remove('d-none', 'alert-warning');
                validation.classList.add('alert-info');
                message.textContent = `Duration: ${days} days`;
            }
        }
    }

    async savePeriod() {
        const form = document.getElementById('addPeriodForm');
        const data = {
            year: parseInt(form.querySelector('#year').value),
            start_date: form.querySelector('#start_date').value,
            end_date: form.querySelector('#end_date').value
        };
        
        try {
            const response = await fetch('/attendance/ramadan_period_add/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCookie('csrftoken')
                },
                body: JSON.stringify(data)
            });
            
            const result = await response.json();
            if (response.ok) {
                location.reload();
            } else {
                throw new Error(result.error || 'Error adding Ramadan period');
            }
        } catch (error) {
            alert(error.message);
        }
    }

    async editPeriod(id) {
        try {
            const response = await fetch(`/attendance/ramadan_period_detail/${id}/`);
            const data = await response.json();
            
            // Populate form
            document.getElementById('edit_period_id').value = id;
            document.getElementById('edit_year').value = data.year;
            document.getElementById('edit_start_date').value = data.start_date;
            document.getElementById('edit_end_date').value = data.end_date;
            document.getElementById('edit_is_active').checked = data.is_active;
            
            this.validatePeriod('edit');
            
            // Show modal
            new bootstrap.Modal(document.getElementById('editPeriodModal')).show();
        } catch (error) {
            alert('Error loading period details');
        }
    }

    async updatePeriod() {
        const id = document.getElementById('edit_period_id').value;
        const data = {
            year: parseInt(document.getElementById('edit_year').value),
            start_date: document.getElementById('edit_start_date').value,
            end_date: document.getElementById('edit_end_date').value,
            is_active: document.getElementById('edit_is_active').checked
        };
        
        try {
            const response = await fetch(`/attendance/ramadan_period_detail/${id}/`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCookie('csrftoken')
                },
                body: JSON.stringify(data)
            });
            
            if (response.ok) {
                location.reload();
            } else {
                const result = await response.json();
                throw new Error(result.error || 'Error updating Ramadan period');
            }
        } catch (error) {
            alert(error.message);
        }
    }

    confirmDelete(id) {
        this.deleteId = id;
        new bootstrap.Modal(document.getElementById('deleteModal')).show();
    }

    async deletePeriod() {
        if (!this.deleteId) return;
        
        try {
            const response = await fetch(`/attendance/ramadan_period_detail/${this.deleteId}/`, {
                method: 'DELETE',
                headers: {
                    'X-CSRFToken': this.getCookie('csrftoken')
                }
            });
            
            if (response.ok) {
                location.reload();
            } else {
                throw new Error('Error deleting Ramadan period');
            }
        } catch (error) {
            alert(error.message);
        }
    }

    getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }
}

// Initialize the manager
const ramadanManager = new RamadanPeriodManager();

// Export for global access
window.ramadanManager = ramadanManager;

```

### hrms_project\attendance\tasks.py
```
from datetime import datetime, date, timedelta
import logging

from celery import shared_task
from django.db import transaction
from django.db.models import Q
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string

from .models import (
    ShiftAssignment, AttendanceLog, RamadanPeriod,
    Employee, Leave
)
from .services import ShiftService, RamadanService

logger = logging.getLogger(__name__)

@shared_task
def update_expired_shift_assignments():
    """Deactivate expired shift assignments"""
    today = timezone.now().date()
    
    expired = ShiftAssignment.objects.filter(
        end_date__lt=today,
        is_active=True
    )
    
    updated_count = expired.update(is_active=False)
    logger.info(f"Deactivated {updated_count} expired shift assignments")
    
    return updated_count

@shared_task
def notify_shift_changes():
    """Notify employees of upcoming shift changes"""
    tomorrow = timezone.now().date() + timedelta(days=1)
    
    # Find assignments starting tomorrow
    new_assignments = ShiftAssignment.objects.filter(
        start_date=tomorrow,
        is_active=True
    ).select_related('employee', 'shift')
    
    for assignment in new_assignments:
        try:
            # Check if this is different from current shift
            current_shift = ShiftService.get_employee_current_shift(assignment.employee)
            if current_shift and current_shift != assignment.shift:
                # Prepare email
                context = {
                    'employee': assignment.employee,
                    'old_shift': current_shift,
                    'new_shift': assignment.shift,
                    'start_date': tomorrow
                }
                
                html_message = render_to_string(
                    'attendance/email/shift_change_notification.html',
                    context
                )
                
                # Send email
                send_mail(
                    subject='Shift Change Notification',
                    message='Your shift is changing tomorrow.',
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[assignment.employee.email],
                    html_message=html_message
                )
                
                logger.info(f"Sent shift change notification to {assignment.employee}")
                
        except Exception as e:
            logger.error(f"Error sending shift change notification: {str(e)}")

@shared_task
def process_ramadan_shift_changes():
    """Handle shift adjustments for Ramadan period"""
    today = timezone.now().date()
    
    # Check if today is start or end of Ramadan
    ramadan_start = RamadanPeriod.objects.filter(
        start_date=today,
        is_active=True
    ).first()
    
    ramadan_end = RamadanPeriod.objects.filter(
        end_date=today,
        is_active=True
    ).first()
    
    if ramadan_start:
        logger.info("Processing Ramadan start adjustments")
        # Notify all employees with active shifts
        assignments = ShiftAssignment.objects.filter(
            is_active=True,
            start_date__lte=today
        ).filter(
            Q(end_date__isnull=True) | Q(end_date__gte=today)
        ).select_related('employee', 'shift')
        
        for assignment in assignments:
            try:
                context = {
                    'employee': assignment.employee,
                    'shift': assignment.shift,
                    'ramadan_period': ramadan_start,
                    'adjusted_timing': RamadanService.get_ramadan_shift_timing(
                        assignment.shift, today
                    )
                }
                
                html_message = render_to_string(
                    'attendance/email/ramadan_timing_notification.html',
                    context
                )
                
                send_mail(
                    subject='Ramadan Working Hours Notification',
                    message='Your working hours have been adjusted for Ramadan.',
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[assignment.employee.email],
                    html_message=html_message
                )
                
            except Exception as e:
                logger.error(f"Error sending Ramadan notification: {str(e)}")
    
    elif ramadan_end:
        logger.info("Processing Ramadan end adjustments")
        # Similar notification for end of Ramadan
        assignments = ShiftAssignment.objects.filter(
            is_active=True,
            start_date__lte=today
        ).filter(
            Q(end_date__isnull=True) | Q(end_date__gte=today)
        ).select_related('employee', 'shift')
        
        for assignment in assignments:
            try:
                context = {
                    'employee': assignment.employee,
                    'shift': assignment.shift,
                    'ramadan_period': ramadan_end,
                    'is_end': True
                }
                
                html_message = render_to_string(
                    'attendance/email/ramadan_timing_notification.html',
                    context
                )
                
                send_mail(
                    subject='Regular Working Hours Resume',
                    message='Regular working hours will resume after Ramadan.',
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[assignment.employee.email],
                    html_message=html_message
                )
                
            except Exception as e:
                logger.error(f"Error sending Ramadan end notification: {str(e)}")

@shared_task
def calculate_attendance_metrics(date_str=None):
    """Calculate attendance metrics for a given date"""
    if date_str:
        target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
    else:
        target_date = timezone.now().date() - timedelta(days=1)
    
    logs = AttendanceLog.objects.filter(
        date=target_date
    ).select_related('employee')
    
    metrics = {
        'total': logs.count(),
        'present': 0,
        'absent': 0,
        'late': 0,
        'leave': 0,
        'early_departure': 0
    }
    
    for log in logs:
        if log.is_leave:
            metrics['leave'] += 1
        elif not log.first_in_time:
            metrics['absent'] += 1
        else:
            metrics['present'] += 1
            if log.is_late:
                metrics['late'] += 1
            if log.early_departure:
                metrics['early_departure'] += 1
    
    # Store metrics in cache or database as needed
    logger.info(f"Attendance metrics for {target_date}: {metrics}")
    return metrics

@shared_task
def notify_missing_shift_assignments():
    """Notify HR about employees without active shift assignments"""
    employees = Employee.objects.filter(
        is_active=True
    ).exclude(
        shiftassignment__is_active=True
    )
    
    if employees.exists():
        context = {
            'employees': employees,
            'count': employees.count()
        }
        
        html_message = render_to_string(
            'attendance/email/missing_shift_notification.html',
            context
        )
        
        send_mail(
            subject='Employees Without Shift Assignments',
            message=f'{employees.count()} employees have no active shift assignment.',
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[settings.HR_EMAIL],
            html_message=html_message
        )
        
        logger.info(f"Sent notification for {employees.count()} employees without shifts")
        return employees.count()
    
    return 0

```

### hrms_project\attendance\templates\attendance\attendance_detail.html
```
{% extends 'attendance/base.html' %}
{% load static %}

{% block attendance_content %}
<div class="card">
    <div class="card-header">
        <div class="row align-items-center">
            <div class="col">
                <h5 class="mb-0">Attendance Details</h5>
                <small class="text-muted">Employee: {{ employee_name }} (ID: {{ personnel_id }})</small>
            </div>
            <div class="col-auto">
                <button type="button" class="btn btn-primary" data-bs-toggle="modal" data-bs-target="#addLogModal">
                    <i class="fas fa-plus"></i> Add Log
                </button>
            </div>
        </div>
    </div>
    <div class="card-body">
        <!-- Dashboard Stats -->
        <div class="row mb-4">
            <div class="col-md-3">
                <div class="card bg-light">
                    <div class="card-body text-center">
                        <h6 class="card-title">Status</h6>
                        <p class="card-text h4 mb-0 
                            {% if stats.status == 'Present' %}text-success
                            {% elif stats.status == 'Late' %}text-warning
                            {% else %}text-danger{% endif %}">
                            {{ stats.status }}
                        </p>
                    </div>
                </div>
            </div>
            <div class="col-md-3">
                <div class="card bg-light">
                    <div class="card-body text-center">
                        <h6 class="card-title">Total Hours</h6>
                        <p class="card-text h4 mb-0">{{ stats.total_hours }}</p>
                    </div>
                </div>
            </div>
            <div class="col-md-3">
                <div class="card bg-light">
                    <div class="card-body text-center">
                        <h6 class="card-title">First In</h6>
                        <p class="card-text h4 mb-0 {% if stats.is_late %}text-warning{% endif %}">
                            {{ stats.first_in }}
                        </p>
                    </div>
                </div>
            </div>
            <div class="col-md-3">
                <div class="card bg-light">
                    <div class="card-body text-center">
                        <h6 class="card-title">Last Out</h6>
                        <p class="card-text h4 mb-0">{{ stats.last_out }}</p>
                    </div>
                </div>
            </div>
        </div>

        <!-- Employee and Date Information -->
        <div class="row mb-4">
            <div class="col-md-6">
                <div class="card">
                    <div class="card-body">
                        <h6 class="card-title">Employee Information</h6>
                        <table class="table table-sm">
                            <tr>
                                <th width="150">Department:</th>
                                <td>{{ department }}</td>
                            </tr>
                            <tr>
                                <th>Designation:</th>
                                <td>{{ designation }}</td>
                            </tr>
                        </table>
                    </div>
                </div>
            </div>
            <div class="col-md-6">
                <div class="card">
                    <div class="card-body">
                        <h6 class="card-title">Date Information</h6>
                        <table class="table table-sm">
                            <tr>
                                <th width="150">Date:</th>
                                <td>{{ date }}</td>
                            </tr>
                            <tr>
                                <th>Day:</th>
                                <td>{{ day }}</td>
                            </tr>
                        </table>
                    </div>
                </div>
            </div>
        </div>

        <!-- Attendance Logs Table -->
        <div class="card">
            <div class="card-body">
                <h6 class="card-title">Attendance Logs</h6>
                <div class="table-responsive">
                    <table class="table table-hover" id="logs-table">
                        <thead>
                            <tr>
                                <th>Time</th>
                                <th>Type</th>
                                <th>Source</th>
                                <th>Device</th>
                                <th>Actions</th>
                            </tr>
                        </thead>
                        <tbody id="logs-body">
                            {% for record in records %}
                            <tr {% if record.is_special %}class="table-primary"{% endif %}>
                                <td>{{ record.time }}</td>
                                <td>
                                    <span class="badge {{ record.badge_class }}">
                                        {{ record.type }}{{ record.label }}
                                    </span>
                                </td>
                                <td>{{ record.source }}</td>
                                <td>{{ record.device_name }}</td>
                                <td>
                                    <button class="btn btn-sm btn-outline-primary me-1" onclick="editLog({{ record.id }})">
                                        <i class="fas fa-edit"></i>
                                    </button>
                                    <button class="btn btn-sm btn-outline-danger" onclick="confirmDelete({{ record.id }})">
                                        <i class="fas fa-trash"></i>
                                    </button>
                                </td>
                            </tr>
                            {% empty %}
                            <tr>
                                <td colspan="5" class="text-center">No attendance records found for this date.</td>
                            </tr>
                            {% endfor %}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    </div>
</div>

<!-- Edit Log Modal -->
<div class="modal fade" id="editLogModal" tabindex="-1">
    <div class="modal-dialog">
        <div class="modal-content">
            <div class="modal-header">
                <h5 class="modal-title">Edit Log</h5>
                <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
            </div>
            <div class="modal-body">
                <form id="edit-log-form">
                    <input type="hidden" id="edit-log-id">
                    <div class="mb-3">
                        <label class="form-label">Time</label>
                        <input type="time" class="form-control" id="edit-log-time" required>
                    </div>
                    <div class="mb-3">
                        <label class="form-label">Edit Reason</label>
                        <textarea class="form-control" id="edit-reason" rows="3" required></textarea>
                    </div>
                </form>
            </div>
            <div class="modal-footer">
                <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
                <button type="button" class="btn btn-primary" onclick="saveLogEdit()">Save Changes</button>
            </div>
        </div>
    </div>
</div>

<!-- Add Log Modal -->
<div class="modal fade" id="addLogModal" tabindex="-1">
    <div class="modal-dialog">
        <div class="modal-content">
            <div class="modal-header">
                <h5 class="modal-title">Add New Log</h5>
                <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
            </div>
            <div class="modal-body">
                <form id="add-log-form">
                    <div class="mb-3">
                        <label class="form-label">Time</label>
                        <input type="time" class="form-control" id="add-log-time" required>
                    </div>
                    <div class="mb-3">
                        <label class="form-label">Type</label>
                        <select class="form-select" id="add-log-type" required>
                            <option value="IN">Check In</option>
                            <option value="OUT">Check Out</option>
                        </select>
                    </div>
                    <div class="mb-3">
                        <label class="form-label">Reason</label>
                        <textarea class="form-control" id="add-log-reason" rows="3" required></textarea>
                    </div>
                </form>
            </div>
            <div class="modal-footer">
                <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
                <button type="button" class="btn btn-primary" onclick="addNewLog()">Add Log</button>
            </div>
        </div>
    </div>
</div>

<!-- Delete Confirmation Modal -->
<div class="modal fade" id="deleteLogModal" tabindex="-1">
    <div class="modal-dialog">
        <div class="modal-content">
            <div class="modal-header">
                <h5 class="modal-title">Confirm Delete</h5>
                <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
            </div>
            <div class="modal-body">
                <p>Are you sure you want to delete this log? This action cannot be undone.</p>
                <input type="hidden" id="delete-log-id">
            </div>
            <div class="modal-footer">
                <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
                <button type="button" class="btn btn-danger" onclick="deleteLog()">Delete</button>
            </div>
        </div>
    </div>
</div>

{% csrf_token %}

{% endblock %}

{% block extra_js %}
<script>
let currentPersonnelId = '{{ personnel_id }}';
let currentDate = '{{ date }}';

function editLog(recordId) {
    fetch(`/attendance/api/records/${recordId}/`)
        .then(response => response.json())
        .then(data => {
            document.getElementById('edit-log-id').value = recordId;
            document.getElementById('edit-log-time').value = data.timestamp.split('T')[1].substring(0, 5);
            const modal = new bootstrap.Modal(document.getElementById('editLogModal'));
            modal.show();
        })
        .catch(error => {
            console.error('Error:', error);
            alert('Failed to load log details');
        });
}

function saveLogEdit() {
    const recordId = document.getElementById('edit-log-id').value;
    const time = document.getElementById('edit-log-time').value;
    const reason = document.getElementById('edit-reason').value;

    if (!time || !reason) {
        alert('Please fill in all fields');
        return;
    }

    fetch(`/attendance/api/records/${recordId}/`, {
        method: 'PATCH',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
        },
        body: JSON.stringify({
            time: time,
            reason: reason
        })
    })
    .then(response => {
        if (!response.ok) throw new Error('Failed to update log');
        return response.json();
    })
    .then(() => {
        location.reload();
    })
    .catch(error => {
        console.error('Error:', error);
        alert('Failed to update log');
    });
}

function addNewLog() {
    const time = document.getElementById('add-log-time').value;
    const type = document.getElementById('add-log-type').value;
    const reason = document.getElementById('add-log-reason').value;

    if (!time || !reason) {
        alert('Please fill in all fields');
        return;
    }

    fetch('/attendance/api/records/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
        },
        body: JSON.stringify({
            personnel_id: currentPersonnelId,
            date: currentDate,
            time: time,
            type: type,
            reason: reason
        })
    })
    .then(response => {
        if (!response.ok) throw new Error('Failed to add log');
        return response.json();
    })
    .then(() => {
        location.reload();
    })
    .catch(error => {
        console.error('Error:', error);
        alert('Failed to add log');
    });
}

function confirmDelete(recordId) {
    document.getElementById('delete-log-id').value = recordId;
    const modal = new bootstrap.Modal(document.getElementById('deleteLogModal'));
    modal.show();
}

function deleteLog() {
    const recordId = document.getElementById('delete-log-id').value;

    fetch(`/attendance/api/records/${recordId}/`, {
        method: 'DELETE',
        headers: {
            'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
        }
    })
    .then(response => {
        if (!response.ok) throw new Error('Failed to delete log');
        location.reload();
    })
    .catch(error => {
        console.error('Error:', error);
        alert('Failed to delete log');
    });
}
</script>
{% endblock %}

```

### hrms_project\attendance\templates\attendance\attendance_list.html
```
{% extends 'attendance/base.html' %}
{% load static %}

{% block attendance_content %}
<div class="card">
    <div class="card-header">
        <div class="row align-items-center">
            <div class="col">
                <h5 class="mb-0">Daily Attendance</h5>
            </div>
            <div class="col-auto">
                <a href="{% url 'attendance:upload_attendance' %}" class="btn btn-primary">
                    <i class="fas fa-upload"></i> Upload Attendance
                </a>
            </div>
        </div>
    </div>
    <div class="card-body">
        <!-- Filters -->
        <div class="row mb-3">
            <div class="col-md-3">
                <label class="form-label">Date Range</label>
                <div class="input-group">
                    <input type="date" class="form-control" id="start-date">
                    <span class="input-group-text">to</span>
                    <input type="date" class="form-control" id="end-date">
                </div>
            </div>
            <div class="col-md-3">
                <label class="form-label">Department</label>
                <select class="form-select" id="department-filter">
                    <option value="">All Departments</option>
                    {% for dept in departments %}
                    <option value="{{ dept.id }}">{{ dept.name }}</option>
                    {% endfor %}
                </select>
            </div>
            <div class="col-md-3">
                <label class="form-label">Status</label>
                <select class="form-select" id="status-filter">
                    <option value="">All Status</option>
                    <option value="present">Present</option>
                    <option value="absent">Absent</option>
                    <option value="late">Late</option>
                    <option value="leave">Leave</option>
                </select>
            </div>
            <div class="col-md-3">
                <label class="form-label">Search</label>
                <input type="text" class="form-control" id="search-input" placeholder="Search employees...">
            </div>
        </div>

        <!-- Summary Cards -->
        <div class="row mb-3">
            <div class="col-md-3">
                <div class="card bg-success text-white">
                    <div class="card-body">
                        <h6 class="card-title">Present</h6>
                        <h3 class="card-text" id="present-count">0</h3>
                    </div>
                </div>
            </div>
            <div class="col-md-3">
                <div class="card bg-danger text-white">
                    <div class="card-body">
                        <h6 class="card-title">Absent</h6>
                        <h3 class="card-text" id="absent-count">0</h3>
                    </div>
                </div>
            </div>
            <div class="col-md-3">
                <div class="card bg-warning">
                    <div class="card-body">
                        <h6 class="card-title">Late</h6>
                        <h3 class="card-text" id="late-count">0</h3>
                    </div>
                </div>
            </div>
            <div class="col-md-3">
                <div class="card bg-info text-white">
                    <div class="card-body">
                        <h6 class="card-title">On Leave</h6>
                        <h3 class="card-text" id="leave-count">0</h3>
                    </div>
                </div>
            </div>
        </div>

        <!-- Attendance Table -->
        <div class="table-responsive">
            <table class="table table-striped table-hover" id="attendance-table">
                <thead>
                    <tr>
                        <th>Personnel ID</th>
                        <th>Name</th>
                        <th>Department</th>
                        <th>Date</th>
                        <th>First In</th>
                        <th>Last Out</th>
                        <th>Status</th>
                        <th>Source</th>
                        <th>Actions</th>
                    </tr>
                </thead>
                <tbody id="attendance-logs">
                    <!-- Data will be loaded dynamically -->
                </tbody>
            </table>
        </div>

        <!-- Pagination -->
        <nav aria-label="Page navigation" class="mt-3">
            <ul class="pagination justify-content-center" id="pagination">
                <!-- Pagination will be generated dynamically -->
            </ul>
        </nav>
    </div>
</div>

{% endblock %}

{% block extra_js %}
<script>
document.addEventListener('DOMContentLoaded', function() {
    // Initial load
    fetchAttendanceLogs();

    // Add event listeners for filters
    document.getElementById('start-date').addEventListener('change', () => fetchAttendanceLogs(1));
    document.getElementById('end-date').addEventListener('change', () => fetchAttendanceLogs(1));
    document.getElementById('department-filter').addEventListener('change', () => fetchAttendanceLogs(1));
    document.getElementById('status-filter').addEventListener('change', () => fetchAttendanceLogs(1));
    document.getElementById('search-input').addEventListener('input', debounce(() => fetchAttendanceLogs(1), 500));
});

function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

function fetchAttendanceLogs(page = 1) {
    const params = new URLSearchParams({
        start_date: document.getElementById('start-date').value,
        end_date: document.getElementById('end-date').value,
        department: document.getElementById('department-filter').value,
        status: document.getElementById('status-filter').value,
        search: document.getElementById('search-input').value,
        page: page.toString()
    });

    fetch(`/attendance/api/logs/?${params}`, {
        headers: {
            'Accept': 'application/json',
            'X-Requested-With': 'XMLHttpRequest'
        }
    })
    .then(response => {
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return response.json();
    })
    .then(data => {
        // Update summary counts
        document.getElementById('present-count').textContent = data.summary?.present || 0;
        document.getElementById('absent-count').textContent = data.summary?.absent || 0;
        document.getElementById('late-count').textContent = data.summary?.late || 0;
        document.getElementById('leave-count').textContent = data.summary?.leave || 0;

        // Update table content
        const tbody = document.getElementById('attendance-logs');
        tbody.innerHTML = data.results.map(log => `
            <tr>
                <td>${log.personnel_id || '-'}</td>
                <td>
                    <a href="/employees/${log.employee_id}/" class="text-decoration-none" ${log.employee_id ? '' : 'onclick="return false;"'}>
                        ${log.employee_name}
                    </a>
                </td>
                <td>${log.department || '-'}</td>
                <td id="log-date-${log.id}">${formatDate(log.date)}</td>
                <td>${formatTime(log.first_in_time) || '-'}</td>
                <td>${formatTime(log.last_out_time) || '-'}</td>
                <td>
                    <span class="badge ${getStatusBadgeClass(getStatusText(log))}">
                        ${getStatusText(log)}
                    </span>
                </td>
                <td>${log.source || '-'}</td>
                <td>
                    <button class="btn btn-sm btn-outline-primary" onclick="viewDetails(${log.id}, '${log.personnel_id || ''}')">
                        <i class="fas fa-eye"></i>
                    </button>
                </td>
            </tr>
        `).join('');

        updatePagination(data);
    })
    .catch(error => {
        console.error('Error fetching attendance logs:', error);
        document.getElementById('attendance-logs').innerHTML = `
            <tr>
                <td colspan="9" class="text-center text-danger">
                    Error loading attendance data. Please try again.
                </td>
            </tr>
        `;
    });
}

function formatDate(dateString) {
    const options = { year: 'numeric', month: 'short', day: 'numeric' };
    return new Date(dateString).toLocaleDateString(undefined, options);
}

function formatTime(timeString) {
    if (!timeString) return null;
    const date = new Date(`2000-01-01T${timeString}`);
    return date.toLocaleTimeString(undefined, { 
        hour: '2-digit', 
        minute: '2-digit',
        hour12: true 
    });
}

function getStatusText(log) {
    if (!log.first_in_time) return 'Absent';
    if (log.is_late) return 'Late';
    return 'Present';
}

function getStatusBadgeClass(status) {
    switch (status.toLowerCase()) {
        case 'present':
            return 'bg-success';
        case 'absent':
            return 'bg-danger';
        case 'late':
            return 'bg-warning text-dark';
        case 'leave':
            return 'bg-info';
        default:
            return 'bg-secondary';
    }
}

function updatePagination(data) {
    const pagination = document.getElementById('pagination');
    if (!data.count) {
        pagination.innerHTML = '';
        return;
    }

    // Use the page size from the response or default to 400
    const pageSize = data.results.length || 400;
    const totalPages = Math.ceil(data.count / pageSize);
    const currentPage = parseInt(new URLSearchParams(window.location.search).get('page')) || 1;

    let paginationHtml = '';
    
    // Previous button
    paginationHtml += `
        <li class="page-item ${currentPage === 1 ? 'disabled' : ''}">
            <a class="page-link" href="#" onclick="fetchAttendanceLogs(${currentPage - 1}); return false;">Previous</a>
        </li>
    `;

    // Page numbers
    for (let i = 1; i <= totalPages; i++) {
        if (i === 1 || i === totalPages || (i >= currentPage - 2 && i <= currentPage + 2)) {
            paginationHtml += `
                <li class="page-item ${i === currentPage ? 'active' : ''}">
                    <a class="page-link" href="#" onclick="fetchAttendanceLogs(${i}); return false;">${i}</a>
                </li>
            `;
        } else if (i === currentPage - 3 || i === currentPage + 3) {
            paginationHtml += '<li class="page-item disabled"><span class="page-link">...</span></li>';
        }
    }

    // Next button
    paginationHtml += `
        <li class="page-item ${currentPage === totalPages ? 'disabled' : ''}">
            <a class="page-link" href="#" onclick="fetchAttendanceLogs(${currentPage + 1}); return false;">Next</a>
        </li>
    `;

    pagination.innerHTML = paginationHtml;
}

function viewDetails(logId, personnelId) {
    const date = document.getElementById(`log-date-${logId}`).textContent;
    window.location.href = `{% url 'attendance:attendance_detail' %}?personnel_id=${personnelId}&date=${date}`;
}
</script>
{% endblock %}

```

### hrms_project\attendance\templates\attendance\attendance_report.html
```
{% extends 'attendance/base.html' %}
{% load static %}

{% block attendance_content %}
<div class="card">
    <div class="card-header">
        <h5 class="card-title mb-0">
            <i class="fas fa-chart-bar"></i> Attendance Reports
        </h5>
    </div>
    <div class="card-body">
        <!-- Filters -->
        <div class="row mb-4">
            <div class="col-md-3">
                <label for="department" class="form-label">Department</label>
                <select class="form-select" id="department">
                    <option value="">All Departments</option>
                    {% for dept in departments %}
                    <option value="{{ dept.id }}">{{ dept.name }}</option>
                    {% endfor %}
                </select>
            </div>
            <div class="col-md-3">
                <label for="dateRange" class="form-label">Date Range</label>
                <select class="form-select" id="dateRange">
                    <option value="today">Today</option>
                    <option value="week">This Week</option>
                    <option value="month">This Month</option>
                    <option value="custom">Custom Range</option>
                </select>
            </div>
            <div class="col-md-4" id="customDateRange" style="display: none;">
                <div class="row">
                    <div class="col-6">
                        <label for="startDate" class="form-label">Start Date</label>
                        <input type="date" class="form-control" id="startDate">
                    </div>
                    <div class="col-6">
                        <label for="endDate" class="form-label">End Date</label>
                        <input type="date" class="form-control" id="endDate">
                    </div>
                </div>
            </div>
            <div class="col-md-2 d-flex align-items-end">
                <button class="btn btn-primary w-100" id="generateReport">
                    Generate Report
                </button>
            </div>
        </div>

        <!-- Report Content -->
        <div class="report-content">
            <!-- Summary Cards -->
            <div class="row mb-4">
                <div class="col-md-3">
                    <div class="card bg-primary text-white">
                        <div class="card-body">
                            <h6 class="card-title">Present</h6>
                            <h3 class="card-text" id="presentCount">-</h3>
                        </div>
                    </div>
                </div>
                <div class="col-md-3">
                    <div class="card bg-danger text-white">
                        <div class="card-body">
                            <h6 class="card-title">Absent</h6>
                            <h3 class="card-text" id="absentCount">-</h3>
                        </div>
                    </div>
                </div>
                <div class="col-md-3">
                    <div class="card bg-warning text-white">
                        <div class="card-body">
                            <h6 class="card-title">Late</h6>
                            <h3 class="card-text" id="lateCount">-</h3>
                        </div>
                    </div>
                </div>
                <div class="col-md-3">
                    <div class="card bg-info text-white">
                        <div class="card-body">
                            <h6 class="card-title">On Leave</h6>
                            <h3 class="card-text" id="leaveCount">-</h3>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Charts -->
            <div class="row mb-4">
                <div class="col-md-6">
                    <div class="card">
                        <div class="card-body">
                            <h6 class="card-title">Daily Attendance Trend</h6>
                            <canvas id="attendanceTrendChart"></canvas>
                        </div>
                    </div>
                </div>
                <div class="col-md-6">
                    <div class="card">
                        <div class="card-body">
                            <h6 class="card-title">Department-wise Attendance</h6>
                            <canvas id="departmentChart"></canvas>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Detailed Report Table -->
            <div class="card">
                <div class="card-body">
                    <h6 class="card-title mb-3">Detailed Report</h6>
                    <div class="table-responsive">
                        <table class="table table-striped table-hover" id="reportTable">
                            <thead>
                                <tr>
                                    <th>Employee ID</th>
                                    <th>Name</th>
                                    <th>Department</th>
                                    <th>Present Days</th>
                                    <th>Absent Days</th>
                                    <th>Late Days</th>
                                    <th>Leave Days</th>
                                    <th>Actions</th>
                                </tr>
                            </thead>
                            <tbody>
                                <!-- Data will be populated via JavaScript -->
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>
        </div>
    </div>
</div>
{% endblock %}

{% block extra_js %}
{{ block.super }}
<!-- Chart.js -->
<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
<!-- Custom report JS -->
<script src="{% static 'attendance/js/attendance_report.js' %}"></script>
{% endblock %}

```

### hrms_project\attendance\templates\attendance\base.html
```
{% extends 'core/base.html' %}
{% load static %}

{% block extra_css %}
<!-- FullCalendar CSS -->
<link href='https://cdn.jsdelivr.net/npm/@fullcalendar/core@6.1.10/main.min.css' rel='stylesheet' />
<link href='https://cdn.jsdelivr.net/npm/@fullcalendar/daygrid@6.1.10/main.min.css' rel='stylesheet' />
<!-- Custom attendance CSS -->
<link href="{% static 'attendance/css/attendance.css' %}" rel="stylesheet" />
{% endblock %}

{% block content %}
<div class="container-fluid mt-4">
    <div class="row">
        <!-- Sidebar -->
        <div class="col-md-3 col-lg-2">
            <!-- Daily Attendance Section -->
            <div class="list-group mb-4">
                <div class="list-group-item bg-light fw-bold">
                    <i class="fas fa-clock"></i> Daily Attendance
                </div>
                <a href="{% url 'attendance:attendance_list' %}" 
                   class="list-group-item list-group-item-action {% if request.resolver_match.url_name == 'attendance_list' %}active{% endif %}">
                    <i class="fas fa-list"></i> View Attendance
                </a>
                <a href="{% url 'attendance:mark_attendance' %}"
                   class="list-group-item list-group-item-action {% if request.resolver_match.url_name == 'mark_attendance' %}active{% endif %}">
                    <i class="fas fa-edit"></i> Mark Attendance
                </a>
                <a href="{% url 'attendance:upload_attendance' %}"
                   class="list-group-item list-group-item-action {% if request.resolver_match.url_name == 'upload_attendance' %}active{% endif %}">
                    <i class="fas fa-upload"></i> Upload Attendance
                </a>
                <a href="{% url 'attendance:attendance_report' %}"
                   class="list-group-item list-group-item-action {% if request.resolver_match.url_name == 'attendance_report' %}active{% endif %}">
                    <i class="fas fa-chart-bar"></i> Reports
                </a>
            </div>

            <!-- Holiday Management Section -->
            <div class="list-group mb-4">
                <div class="list-group-item bg-light fw-bold">
                    <i class="fas fa-star"></i> Holiday Management
                </div>
                <a href="{% url 'attendance:holiday_list' %}"
                   class="list-group-item list-group-item-action {% if request.resolver_match.url_name == 'holiday_list' %}active{% endif %}">
                    <i class="fas fa-list"></i> Holiday List
                </a>
                <a href="{% url 'attendance:holiday_create' %}"
                   class="list-group-item list-group-item-action {% if request.resolver_match.url_name == 'holiday_create' %}active{% endif %}">
                    <i class="fas fa-plus"></i> Add Holiday
                </a>
                <a href="{% url 'attendance:recurring_holidays' %}"
                   class="list-group-item list-group-item-action {% if request.resolver_match.url_name == 'recurring_holidays' %}active{% endif %}">
                    <i class="fas fa-redo"></i> Recurring Holidays
                </a>
            </div>

            <!-- Leave Management Section -->
            <div class="list-group mb-4">
                <div class="list-group-item bg-light fw-bold">
                    <i class="fas fa-calendar-minus"></i> Leave Management
                </div>
                <a href="{% url 'attendance:leave_request_list' %}"
                   class="list-group-item list-group-item-action {% if request.resolver_match.url_name == 'leave_request_list' %}active{% endif %}">
                    <i class="fas fa-list"></i> Leave Requests
                </a>
                <a href="{% url 'attendance:leave_request_create' %}"
                   class="list-group-item list-group-item-action {% if request.resolver_match.url_name == 'leave_request_create' %}active{% endif %}">
                    <i class="fas fa-plus"></i> Apply for Leave
                </a>
                <a href="{% url 'attendance:leave_balance' %}"
                   class="list-group-item list-group-item-action {% if request.resolver_match.url_name == 'leave_balance' %}active{% endif %}">
                    <i class="fas fa-balance-scale"></i> Leave Balances
                </a>
                <a href="{% url 'attendance:leave_types' %}"
                   class="list-group-item list-group-item-action {% if request.resolver_match.url_name == 'leave_types' %}active{% endif %}">
                    <i class="fas fa-tags"></i> Leave Types
                </a>
            </div>

            <!-- Calendar Views Section -->
            <div class="list-group mb-4">
                <div class="list-group-item bg-light fw-bold">
                    <i class="fas fa-calendar-alt"></i> Calendar Views
                </div>
                <a href="{% url 'attendance:calendar_month' %}"
                   class="list-group-item list-group-item-action {% if request.resolver_match.url_name == 'calendar_month' %}active{% endif %}">
                    <i class="far fa-calendar"></i> Monthly View
                </a>
                <a href="{% url 'attendance:calendar_week' %}"
                   class="list-group-item list-group-item-action {% if request.resolver_match.url_name == 'calendar_week' %}active{% endif %}">
                    <i class="far fa-calendar-alt"></i> Weekly View
                </a>
                <a href="{% url 'attendance:calendar_department' %}"
                   class="list-group-item list-group-item-action {% if request.resolver_match.url_name == 'calendar_department' %}active{% endif %}">
                    <i class="fas fa-users"></i> Department View
                </a>
            </div>

            <!-- Status Legend -->
            <div class="card mt-3">
                <div class="card-header">
                    <h6 class="mb-0">Status Legend</h6>
                </div>
                <div class="card-body p-2">
                    <div class="d-flex align-items-center mb-2">
                        <div class="status-dot bg-success"></div>
                        <span class="ms-2">Present</span>
                    </div>
                    <div class="d-flex align-items-center mb-2">
                        <div class="status-dot bg-danger"></div>
                        <span class="ms-2">Absent</span>
                    </div>
                    <div class="d-flex align-items-center mb-2">
                        <div class="status-dot bg-warning"></div>
                        <span class="ms-2">Late</span>
                    </div>
                    <div class="d-flex align-items-center mb-2">
                        <div class="status-dot bg-info"></div>
                        <span class="ms-2">Leave</span>
                    </div>
                    <div class="d-flex align-items-center mb-2">
                        <div class="status-dot bg-primary"></div>
                        <span class="ms-2">Holiday</span>
                    </div>
                    <div class="d-flex align-items-center">
                        <div class="status-dot bg-secondary"></div>
                        <span class="ms-2">Friday</span>
                    </div>
                </div>
            </div>
        </div>

        <!-- Main Content -->
        <div class="col-md-9 col-lg-10">
            {% block attendance_content %}{% endblock %}
        </div>
    </div>
</div>
{% endblock %}

{% block extra_js %}
<!-- Bootstrap Bundle with Popper -->
<script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
<!-- jQuery -->
<script src="https://code.jquery.com/jquery-3.6.0.min.js"></script>
<!-- FullCalendar Bundle -->
<script src='https://cdn.jsdelivr.net/npm/@fullcalendar/core@6.1.10/index.global.min.js'></script>
<script src='https://cdn.jsdelivr.net/npm/@fullcalendar/daygrid@6.1.10/index.global.min.js'></script>
<script src='https://cdn.jsdelivr.net/npm/@fullcalendar/interaction@6.1.10/index.global.min.js'></script>
<!-- Custom attendance JS -->
<script src="{% static 'attendance/js/attendance.js' %}"></script>
{% endblock %}

```

### hrms_project\attendance\templates\attendance\calendar.html
```
{% extends 'attendance/base.html' %}
{% load static %}

{% block extra_css %}
{{ block.super }}
<link href="https://cdn.jsdelivr.net/npm/select2@4.1.0-rc.0/dist/css/select2.min.css" rel="stylesheet" />
<style>
.fc-event {
    cursor: pointer;
}

.fc-day-friday {
    background-color: rgba(0,0,0,0.05);
}

.fc-day-today {
    background-color: rgba(0,123,255,0.1) !important;
}

.calendar-legend {
    display: flex;
    gap: 1rem;
    flex-wrap: wrap;
    margin-bottom: 1rem;
}

.legend-item {
    display: flex;
    align-items: center;
    gap: 0.5rem;
}

.legend-color {
    width: 20px;
    height: 20px;
    border-radius: 4px;
}

.tooltip-inner {
    max-width: 300px;
}

#filter-collapse {
    transition: all 0.3s ease-in-out;
}

/* Select2 Custom Styles */
.select2-container--default .select2-selection--single {
    height: 38px;
    border: 1px solid #ced4da;
}

.select2-container--default .select2-selection--single .select2-selection__rendered {
    line-height: 36px;
    padding-left: 12px;
}

.select2-container--default .select2-selection--single .select2-selection__arrow {
    height: 36px;
}
</style>
{% endblock %}

{% block attendance_content %}
<div class="card">
    <div class="card-header">
        <div class="d-flex justify-content-between align-items-center">
            <div class="d-flex align-items-center">
                <h5 class="mb-0 d-inline-block me-2">Attendance Calendar</h5>
                <h6 class="mb-0 me-3" id="calendar-title"></h6>
                <button class="btn btn-link" type="button" data-bs-toggle="collapse" data-bs-target="#filter-collapse">
                    <i class="fas fa-filter"></i> Filters
                </button>
            </div>
            <div class="btn-group ms-auto">
                <button class="btn btn-outline-secondary" id="prev-month">
                    <i class="fas fa-chevron-left"></i>
                </button>
                <button class="btn btn-outline-secondary" id="today">Today</button>
                <button class="btn btn-outline-secondary" id="next-month">
                    <i class="fas fa-chevron-right"></i>
                </button>
            </div>
        </div>
    </div>
    <div class="card-body">
        <!-- Filters -->
        <div class="collapse mb-4" id="filter-collapse">
            <div class="card card-body">
                <div class="row">
                    <div class="col-md-3">
                        <label class="form-label">Department</label>
                        <select class="form-select" id="department-filter">
                            <option value="">All Departments</option>
                            {% for dept in departments %}
                            <option value="{{ dept.id }}">{{ dept.name }}</option>
                            {% endfor %}
                        </select>
                    </div>
                    <div class="col-md-3">
                        <label class="form-label">Employee</label>
                        <select class="form-control" id="employee-filter">
                            <option value="">All Employees</option>
                        </select>
                    </div>
                    <div class="col-md-3">
                        <label class="form-label">View Type</label>
                        <select class="form-select" id="view-type">
                            <option value="dayGridMonth">Month</option>
                            <option value="dayGridWeek">Week</option>
                            <option value="dayGridDay">Day</option>
                        </select>
                    </div>
                    <div class="col-md-3 d-flex align-items-end">
                        <button class="btn btn-primary w-100" id="apply-filters">
                            Apply Filters
                        </button>
                    </div>
                </div>
            </div>
        </div>

        <!-- Calendar Legend -->
        <div class="calendar-legend">
            <div class="legend-item">
                <div class="legend-color bg-success"></div>
                <span>Present</span>
            </div>
            <div class="legend-item">
                <div class="legend-color bg-danger"></div>
                <span>Absent</span>
            </div>
            <div class="legend-item">
                <div class="legend-color bg-warning"></div>
                <span>Late</span>
            </div>
            <div class="legend-item">
                <div class="legend-color bg-info"></div>
                <span>Leave</span>
            </div>
            <div class="legend-item">
                <div class="legend-color bg-primary"></div>
                <span>Holiday</span>
            </div>
            <div class="legend-item">
                <div class="legend-color" style="background-color: rgba(0,0,0,0.05);"></div>
                <span>Friday</span>
            </div>
        </div>

        <!-- Calendar -->
        <div id="calendar"></div>
    </div>
</div>

<!-- Event Detail Modal -->
<div class="modal fade" id="eventModal" tabindex="-1">
    <div class="modal-dialog">
        <div class="modal-content">
            <div class="modal-header">
                <h5 class="modal-title" id="eventTitle">Event Details</h5>
                <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
            </div>
            <div class="modal-body" id="eventDetails">
                <!-- Event details will be loaded here -->
            </div>
            <div class="modal-footer">
                <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Close</button>
            </div>
        </div>
    </div>
</div>
{% endblock %}

{% block extra_js %}
{{ block.super }}
<script src="https://cdn.jsdelivr.net/npm/select2@4.1.0-rc.0/dist/js/select2.min.js"></script>
<script>
document.addEventListener('DOMContentLoaded', function() {
    // Initialize Select2
    $('#employee-filter').select2({
        placeholder: 'Search by ID or Name',
        allowClear: true,
        minimumInputLength: 1,
        ajax: {
            url: '{% url "attendance:search_employees" %}',
            dataType: 'json',
            delay: 250,
            data: function(params) {
                return {
                    q: params.term,
                    department: $('#department-filter').val()
                };
            },
            processResults: function(data) {
                return {
                    results: data.map(function(emp) {
                        return {
                            id: emp.id,
                            text: emp.employee_number + ' - ' + emp.full_name,
                            employee_number: emp.employee_number
                        };
                    })
                };
            },
            cache: true
        }
    });

    // Update search when department changes
    $('#department-filter').on('change', function() {
        $('#employee-filter').val(null).trigger('change');
    });

    var calendarEl = document.getElementById('calendar');
    var calendar = new FullCalendar.Calendar(calendarEl, {
        initialView: 'dayGridMonth',
        headerToolbar: false,
        dayHeaderFormat: { weekday: 'short' },
        firstDay: 0, // Start week on Sunday
        height: 'auto',
        dayCellDidMount: function(info) {
            // Add class to Fridays
            if (info.date.getDay() === 5) { // 5 is Friday
                info.el.classList.add('fc-day-friday');
            }
        },
        eventDidMount: function(info) {
            // Add tooltips
            $(info.el).tooltip({
                title: info.event.extendedProps.tooltip || info.event.title,
                placement: 'top',
                container: 'body'
            });
        },
        eventClick: function(info) {
            showEventDetails(info.event);
        },
        displayEventTime: false, // Hide time from event display
        eventDisplay: 'block', // Display events as blocks
        events: function(info, successCallback, failureCallback) {
            // Get filter values
            const department = $('#department-filter').val();
            const employee = $('#employee-filter').val();
            
            $.ajax({
                url: '{% url "attendance:calendar_events" %}',
                data: {
                    start: info.startStr,
                    end: info.endStr,
                    department: department,
                    employee: employee
                },
                success: function(response) {
                    if (response && Array.isArray(response)) {
                        const events = response.map(event => ({
                            ...event,
                            display: 'block',
                            classNames: [event.color ? `bg-${event.color}` : '']
                        }));
                        successCallback(events);
                    } else {
                        failureCallback('Invalid response format');
                    }
                },
                error: function(xhr, status, error) {
                    console.error('Error loading events:', error);
                    failureCallback('Error loading events');
                }
            });
        }
    });

    calendar.render();

    // Navigation buttons
    $('#prev-month').click(() => {
        calendar.prev();
        calendar.refetchEvents();
    });
    $('#next-month').click(() => {
        calendar.next();
        calendar.refetchEvents();
    });
    $('#today').click(() => {
        calendar.today();
        calendar.refetchEvents();
    });

    // View type change
    $('#view-type').change(function() {
        calendar.changeView($(this).val());
    });

    // Apply filters
    $('#apply-filters').click(function() {
        calendar.refetchEvents();
    });

    // Handle date clicks
    $(document).on('click', '.fc-daygrid-day', function(e) {
        const date = $(this).data('date');
        const employeeId = $('#employee-filter').val();
        
        // Prepare URL for attendance details
        let url = `{% url "attendance:attendance_detail" %}?date=${date}`;
        
        if (employeeId) {
            const empNumber = $('#employee-filter').select2('data')[0]?.employee_number;
            if (empNumber) {
                url += '&personnel_id=' + empNumber;
            }
        }
        
        // Load attendance details in modal
        $('#eventDetails').load(url, function() {
            $('#eventModal').modal('show');
        });
    });

    // Update calendar title
    function updateCalendarTitle() {
        const date = calendar.getDate();
        const title = date.toLocaleString('default', { month: 'long', year: 'numeric' });
        $('#calendar-title').text(title);
    }

    // Initialize calendar with current month
    const today = new Date();
    calendar.gotoDate(today);
    updateCalendarTitle();

    // Update title on navigation
    calendar.on('datesSet', function(info) {
        updateCalendarTitle();
    });

    function showEventDetails(event) {
        const modal = $('#eventModal');
        const title = event.title;
        const details = event.extendedProps;
        
        modal.find('#eventTitle').text(title);
        
        let detailsHtml = '<dl class="row mb-0">';
        
        // Common fields
        if (details.employee) {
            detailsHtml += `
                <dt class="col-sm-4">Employee</dt>
                <dd class="col-sm-8">${details.employee}</dd>
            `;
        }
        
        if (details.department) {
            detailsHtml += `
                <dt class="col-sm-4">Department</dt>
                <dd class="col-sm-8">${details.department}</dd>
            `;
        }
        
        // Attendance specific fields
        if (details.type === 'attendance') {
            detailsHtml += `
                <dt class="col-sm-4">Status</dt>
                <dd class="col-sm-8">
                    <span class="badge bg-${details.status_color}">${details.status}</span>
                </dd>
                <dt class="col-sm-4">Time In</dt>
                <dd class="col-sm-8">${details.time_in || '-'}</dd>
                <dt class="col-sm-4">Time Out</dt>
                <dd class="col-sm-8">${details.time_out || '-'}</dd>
            `;
            
            if (details.status === 'Late') {
                detailsHtml += `
                    <dt class="col-sm-4">Late By</dt>
                    <dd class="col-sm-8">${details.late_by}</dd>
                `;
            }
        }
        
        // Leave specific fields
        if (details.type === 'leave') {
            detailsHtml += `
                <dt class="col-sm-4">Leave Type</dt>
                <dd class="col-sm-8">${details.leave_type}</dd>
                <dt class="col-sm-4">Duration</dt>
                <dd class="col-sm-8">${details.duration} days</dd>
                <dt class="col-sm-4">Status</dt>
                <dd class="col-sm-8">
                    <span class="badge bg-${details.status_color}">${details.status}</span>
                </dd>
            `;
            
            if (details.reason) {
                detailsHtml += `
                    <dt class="col-sm-4">Reason</dt>
                    <dd class="col-sm-8">${details.reason}</dd>
                `;
            }
        }
        
        // Holiday specific fields
        if (details.type === 'holiday') {
            detailsHtml += `
                <dt class="col-sm-4">Holiday Type</dt>
                <dd class="col-sm-8">${details.holiday_type}</dd>
            `;
            
            if (details.description) {
                detailsHtml += `
                    <dt class="col-sm-4">Description</dt>
                    <dd class="col-sm-8">${details.description}</dd>
                `;
            }
        }
        
        detailsHtml += '</dl>';
        
        modal.find('#eventDetails').html(detailsHtml);
        modal.modal('show');
    }

    // Clean up tooltips when events are removed
    calendar.on('eventRemove', function(info) {
        $(info.el).tooltip('dispose');
    });
});
</script>
{% endblock %}

```

### hrms_project\attendance\templates\attendance\email\attendance_reminder.html
```
<!DOCTYPE html>
<html>
<head>
    <style>
        body {
            font-family: Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            padding: 20px;
        }
        .header {
            background-color: #f8f9fa;
            padding: 15px;
            border-bottom: 3px solid #17a2b8;
            margin-bottom: 20px;
        }
        .content {
            background-color: white;
            padding: 20px;
            border-radius: 5px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .reminder-box {
            background-color: #d1ecf1;
            border: 1px solid #bee5eb;
            color: #0c5460;
            padding: 15px;
            border-radius: 4px;
            margin: 15px 0;
        }
        .time-box {
            background-color: #fff3cd;
            border: 1px solid #ffeeba;
            padding: 15px;
            border-radius: 4px;
            margin: 15px 0;
            text-align: center;
        }
        .current-time {
            font-size: 24px;
            font-weight: bold;
            color: #856404;
            margin: 10px 0;
        }
        .schedule-info {
            background-color: #f8f9fa;
            padding: 15px;
            border-radius: 4px;
            margin: 15px 0;
        }
        .info-table {
            width: 100%;
            border-collapse: collapse;
            margin: 15px 0;
        }
        .info-table th,
        .info-table td {
            padding: 10px;
            text-align: left;
            border-bottom: 1px solid #dee2e6;
        }
        .info-table th {
            background-color: #f1f3f5;
            font-weight: bold;
            width: 40%;
        }
        .footer {
            margin-top: 20px;
            padding-top: 20px;
            border-top: 1px solid #eee;
            font-size: 12px;
            color: #666;
        }
        .action-buttons {
            margin: 20px 0;
            text-align: center;
        }
        .btn {
            display: inline-block;
            padding: 10px 20px;
            margin: 0 10px;
            text-decoration: none;
            border-radius: 4px;
            font-weight: bold;
        }
        .btn-primary {
            background-color: #17a2b8;
            color: white;
        }
        .clock-status {
            display: flex;
            justify-content: space-around;
            margin: 20px 0;
            text-align: center;
        }
        .status-item {
            padding: 15px;
            border-radius: 4px;
            min-width: 150px;
        }
        .status-label {
            font-size: 14px;
            color: #666;
            margin-bottom: 5px;
        }
        .status-value {
            font-size: 18px;
            font-weight: bold;
        }
        .status-pending {
            background-color: #fff3cd;
            border: 1px solid #ffeeba;
        }
        .status-completed {
            background-color: #d4edda;
            border: 1px solid #c3e6cb;
        }
        .quick-links {
            background-color: #e9ecef;
            padding: 15px;
            border-radius: 4px;
            margin: 15px 0;
        }
        .quick-links ul {
            list-style: none;
            padding: 0;
            margin: 0;
        }
        .quick-links li {
            margin: 10px 0;
        }
        .quick-links a {
            color: #17a2b8;
            text-decoration: none;
        }
    </style>
</head>
<body>
    <div class="header">
        <h2>Attendance Reminder</h2>
        <p>{{ current_date|date:"l, F j, Y" }}</p>
    </div>

    <div class="content">
        <p>Dear {{ employee.get_full_name }},</p>

        <div class="reminder-box">
            <h3>🕒 Daily Attendance Reminder</h3>
            <p>This is a friendly reminder about your attendance for today.</p>
        </div>

        <div class="time-box">
            <div class="current-time">{{ current_time|time:"h:i A" }}</div>
            <p>Current Time</p>
        </div>

        <div class="clock-status">
            <div class="status-item {% if clock_in_time %}status-completed{% else %}status-pending{% endif %}">
                <div class="status-label">Clock In</div>
                <div class="status-value">
                    {% if clock_in_time %}
                    {{ clock_in_time|time:"h:i A" }}
                    {% else %}
                    Pending
                    {% endif %}
                </div>
            </div>
            <div class="status-item {% if clock_out_time %}status-completed{% else %}status-pending{% endif %}">
                <div class="status-label">Clock Out</div>
                <div class="status-value">
                    {% if clock_out_time %}
                    {{ clock_out_time|time:"h:i A" }}
                    {% else %}
                    Pending
                    {% endif %}
                </div>
            </div>
        </div>

        <div class="schedule-info">
            <h4>Today's Schedule</h4>
            <table class="info-table">
                <tr>
                    <th>Regular Start Time</th>
                    <td>{{ schedule.start_time|time:"h:i A" }}</td>
                </tr>
                <tr>
                    <th>Regular End Time</th>
                    <td>{{ schedule.end_time|time:"h:i A" }}</td>
                </tr>
                <tr>
                    <th>Grace Period</th>
                    <td>{{ grace_period }} minutes</td>
                </tr>
            </table>
        </div>

        {% if missing_action %}
        <div class="action-buttons">
            <a href="{{ portal_link }}" class="btn btn-primary">{{ missing_action }}</a>
        </div>
        {% endif %}

        <div class="quick-links">
            <h4>Quick Links</h4>
            <ul>
                <li><a href="{{ attendance_history_link }}">View Attendance History</a></li>
                <li><a href="{{ request_correction_link }}">Request Attendance Correction</a></li>
                <li><a href="{{ leave_request_link }}">Submit Leave Request</a></li>
                {% if support_link %}
                <li><a href="{{ support_link }}">Technical Support</a></li>
                {% endif %}
            </ul>
        </div>

        {% if notifications %}
        <div class="reminder-box">
            <h4>Important Notifications</h4>
            <ul>
                {% for notification in notifications %}
                <li>{{ notification }}</li>
                {% endfor %}
            </ul>
        </div>
        {% endif %}
    </div>

    <div class="footer">
        <p>This is an automated reminder from the HR Management System.</p>
        <p>For any issues with attendance recording, please contact your supervisor or HR immediately.</p>
        {% if help_desk_contact %}
        <p>Technical Support: {{ help_desk_contact }}</p>
        {% endif %}
    </div>
</body>
</html>

```

### hrms_project\attendance\templates\attendance\email\attendance_warning.html
```
<!DOCTYPE html>
<html>
<head>
    <style>
        body {
            font-family: Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            padding: 20px;
        }
        .header {
            background-color: #f8f9fa;
            padding: 15px;
            border-bottom: 3px solid #dc3545;
            margin-bottom: 20px;
        }
        .content {
            background-color: white;
            padding: 20px;
            border-radius: 5px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .warning-box {
            background-color: #f8d7da;
            border: 1px solid #f5c6cb;
            color: #721c24;
            padding: 15px;
            border-radius: 4px;
            margin: 15px 0;
        }
        .incident-details {
            background-color: #fff3cd;
            border: 1px solid #ffeeba;
            padding: 15px;
            border-radius: 4px;
            margin: 15px 0;
        }
        .incident-table {
            width: 100%;
            border-collapse: collapse;
            margin: 15px 0;
        }
        .incident-table th,
        .incident-table td {
            padding: 10px;
            text-align: left;
            border-bottom: 1px solid #dee2e6;
        }
        .incident-table th {
            background-color: #f8f9fa;
            font-weight: bold;
        }
        .policy-reminder {
            background-color: #e2e3e5;
            padding: 15px;
            border-radius: 4px;
            margin: 15px 0;
        }
        .action-required {
            background-color: #cce5ff;
            border: 1px solid #b8daff;
            padding: 15px;
            border-radius: 4px;
            margin: 15px 0;
        }
        .footer {
            margin-top: 20px;
            padding-top: 20px;
            border-top: 1px solid #eee;
            font-size: 12px;
            color: #666;
        }
    </style>
</head>
<body>
    <div class="header">
        <h2>Attendance Warning Notice</h2>
    </div>

    <div class="content">
        <p>Dear {{ employee.get_full_name }},</p>

        <div class="warning-box">
            <h3>⚠️ Warning: Attendance Policy Violation</h3>
            <p>This notice is to inform you that your attendance record has fallen below company standards.</p>
        </div>

        <div class="incident-details">
            <h4>Violation Details:</h4>
            <table class="incident-table">
                <tr>
                    <th>Type:</th>
                    <td>{{ violation_type }}</td>
                </tr>
                <tr>
                    <th>Period:</th>
                    <td>{{ period }}</td>
                </tr>
                <tr>
                    <th>Incidents:</th>
                    <td>{{ incident_count }}</td>
                </tr>
            </table>

            {% if incidents %}
            <h4>Recent Incidents:</h4>
            <table class="incident-table">
                <thead>
                    <tr>
                        <th>Date</th>
                        <th>Type</th>
                        <th>Details</th>
                    </tr>
                </thead>
                <tbody>
                    {% for incident in incidents %}
                    <tr>
                        <td>{{ incident.date|date:"d/m/Y" }}</td>
                        <td>{{ incident.type }}</td>
                        <td>{{ incident.details }}</td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
            {% endif %}
        </div>

        <div class="policy-reminder">
            <h4>Company Policy Reminder:</h4>
            <ul>
                <li>Regular working hours are from {{ work_hours }}</li>
                <li>Maximum allowed late arrivals per month: {{ max_late_allowed }}</li>
                <li>Maximum allowed unexcused absences per month: {{ max_absences_allowed }}</li>
                <li>Three warnings may result in disciplinary action</li>
            </ul>
        </div>

        <div class="action-required">
            <h4>Required Actions:</h4>
            <ol>
                <li>Please provide an explanation for these incidents to your supervisor within 3 working days</li>
                <li>Schedule a meeting with HR to discuss any underlying issues</li>
                <li>Ensure future compliance with attendance policies</li>
            </ol>
        </div>

        <p>If you are experiencing any issues that affect your attendance, please discuss them with your supervisor or HR. We are here to help and can work together to find appropriate solutions.</p>

        <p>Best regards,<br>
        HR Department</p>
    </div>

    <div class="footer">
        <p>This is an official warning notice. Please acknowledge receipt by replying to this email.</p>
        <p>If you need assistance, please contact HR at {{ hr_email|default:"hr@company.com" }}</p>
        <p>Reference: {{ warning_reference }}<br>
        Notice Date: {{ generated_at|date:"l, F j, Y" }}</p>
        {% if warning_level %}
        <p><strong>Warning Level:</strong> {{ warning_level }} of 3</p>
        {% endif %}
    </div>
</body>
</html>

```

### hrms_project\attendance\templates\attendance\email\leave_request_notification.html
```
<!DOCTYPE html>
<html>
<head>
    <style>
        body {
            font-family: Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            padding: 20px;
        }
        .header {
            background-color: #f8f9fa;
            padding: 15px;
            border-bottom: 3px solid #007bff;
            margin-bottom: 20px;
        }
        .content {
            background-color: white;
            padding: 20px;
            border-radius: 5px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .leave-details {
            background-color: #f8f9fa;
            padding: 15px;
            border-radius: 4px;
            margin: 15px 0;
        }
        .detail-table {
            width: 100%;
            border-collapse: collapse;
            margin: 15px 0;
        }
        .detail-table th,
        .detail-table td {
            padding: 10px;
            text-align: left;
            border-bottom: 1px solid #dee2e6;
        }
        .detail-table th {
            background-color: #f1f3f5;
            font-weight: bold;
            width: 35%;
        }
        .balance-info {
            background-color: #e8f4ff;
            border: 1px solid #b8daff;
            padding: 15px;
            border-radius: 4px;
            margin: 15px 0;
        }
        .action-buttons {
            margin: 20px 0;
            text-align: center;
        }
        .btn {
            display: inline-block;
            padding: 10px 20px;
            margin: 0 10px;
            text-decoration: none;
            border-radius: 4px;
            font-weight: bold;
        }
        .btn-approve {
            background-color: #28a745;
            color: white;
        }
        .btn-reject {
            background-color: #dc3545;
            color: white;
        }
        .note {
            background-color: #fff3cd;
            border: 1px solid #ffeeba;
            padding: 15px;
            border-radius: 4px;
            margin: 15px 0;
        }
        .footer {
            margin-top: 20px;
            padding-top: 20px;
            border-top: 1px solid #eee;
            font-size: 12px;
            color: #666;
        }
        .document-section {
            background-color: #f8f9fa;
            padding: 15px;
            border-radius: 4px;
            margin: 15px 0;
        }
        .document-list {
            list-style: none;
            padding: 0;
        }
        .document-list li {
            margin-bottom: 10px;
            padding: 8px;
            background-color: #fff;
            border: 1px solid #dee2e6;
            border-radius: 4px;
        }
        .status-tag {
            display: inline-block;
            padding: 3px 8px;
            border-radius: 3px;
            font-size: 12px;
            font-weight: bold;
        }
        .status-pending {
            background-color: #ffc107;
            color: #000;
        }
    </style>
</head>
<body>
    <div class="header">
        <h2>Leave Request Notification</h2>
        <span class="status-tag status-pending">Pending Approval</span>
    </div>

    <div class="content">
        <h3>New Leave Request</h3>
        <p>A new leave request has been submitted and requires your approval.</p>

        <div class="leave-details">
            <h4>Request Details</h4>
            <table class="detail-table">
                <tr>
                    <th>Employee:</th>
                    <td>{{ leave.employee.get_full_name }} ({{ leave.employee.employee_number }})</td>
                </tr>
                <tr>
                    <th>Department:</th>
                    <td>{{ leave.employee.department.name }}</td>
                </tr>
                <tr>
                    <th>Leave Type:</th>
                    <td>{{ leave.get_leave_type_display }}</td>
                </tr>
                <tr>
                    <th>Start Date:</th>
                    <td>{{ leave.start_date|date:"l, F j, Y" }}</td>
                </tr>
                <tr>
                    <th>End Date:</th>
                    <td>{{ leave.end_date|date:"l, F j, Y" }}</td>
                </tr>
                <tr>
                    <th>Duration:</th>
                    <td>{{ leave.duration }} day{{ leave.duration|pluralize }}</td>
                </tr>
                {% if leave.reason %}
                <tr>
                    <th>Reason:</th>
                    <td>{{ leave.reason }}</td>
                </tr>
                {% endif %}
            </table>
        </div>

        <div class="balance-info">
            <h4>Leave Balance Information</h4>
            <table class="detail-table">
                <tr>
                    <th>Current Balance:</th>
                    <td>{{ leave.balance_before }} days</td>
                </tr>
                <tr>
                    <th>Requested Days:</th>
                    <td>{{ leave.duration }} days</td>
                </tr>
                <tr>
                    <th>Remaining Balance:</th>
                    <td>{{ leave.balance_after }} days</td>
                </tr>
            </table>
        </div>

        {% if leave.documents.exists %}
        <div class="document-section">
            <h4>Supporting Documents</h4>
            <ul class="document-list">
                {% for doc in leave.documents.all %}
                <li>
                    <i class="far fa-file"></i>
                    {{ doc.filename }}
                    <a href="{{ doc.file.url }}" target="_blank">(View)</a>
                </li>
                {% endfor %}
            </ul>
        </div>
        {% endif %}

        <div class="action-buttons">
            <a href="{{ approve_url }}" class="btn btn-approve">Approve Request</a>
            <a href="{{ reject_url }}" class="btn btn-reject">Reject Request</a>
        </div>

        {% if conflicts %}
        <div class="note">
            <h4>⚠️ Important Notes:</h4>
            <ul>
                {% for conflict in conflicts %}
                <li>{{ conflict }}</li>
                {% endfor %}
            </ul>
        </div>
        {% endif %}
    </div>

    <div class="footer">
        <p>This is an automated notification from the HR Management System.</p>
        <p>Reference: {{ leave.reference_number }}<br>
        Submitted: {{ leave.created_at|date:"l, F j, Y H:i" }}</p>
        <p>Please review and respond to this request promptly. If you have any questions, please contact HR.</p>
    </div>
</body>
</html>

```

### hrms_project\attendance\templates\attendance\email\low_balance_notification.html
```
<!DOCTYPE html>
<html>
<head>
    <style>
        body {
            font-family: Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            padding: 20px;
        }
        .header {
            background-color: #f8f9fa;
            padding: 15px;
            border-bottom: 3px solid #ffc107;
            margin-bottom: 20px;
        }
        .content {
            background-color: white;
            padding: 20px;
            border-radius: 5px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .alert-box {
            background-color: #fff3cd;
            border: 1px solid #ffeeba;
            color: #856404;
            padding: 15px;
            border-radius: 4px;
            margin: 15px 0;
        }
        .balance-info {
            background-color: #f8f9fa;
            padding: 15px;
            border-radius: 4px;
            margin: 15px 0;
        }
        .info-table {
            width: 100%;
            border-collapse: collapse;
            margin: 15px 0;
        }
        .info-table th,
        .info-table td {
            padding: 10px;
            text-align: left;
            border-bottom: 1px solid #dee2e6;
        }
        .info-table th {
            background-color: #f1f3f5;
            font-weight: bold;
            width: 40%;
        }
        .accrual-info {
            background-color: #e8f4ff;
            border: 1px solid #b8daff;
            padding: 15px;
            border-radius: 4px;
            margin: 15px 0;
        }
        .upcoming-leaves {
            background-color: #f8f9fa;
            padding: 15px;
            border-radius: 4px;
            margin: 15px 0;
        }
        .footer {
            margin-top: 20px;
            padding-top: 20px;
            border-top: 1px solid #eee;
            font-size: 12px;
            color: #666;
        }
        .progress-bar {
            width: 100%;
            height: 20px;
            background-color: #e9ecef;
            border-radius: 10px;
            overflow: hidden;
            margin: 10px 0;
        }
        .progress-fill {
            height: 100%;
            background-color: #ffc107;
            transition: width 0.3s ease;
        }
        .recommendation-box {
            background-color: #d4edda;
            border: 1px solid #c3e6cb;
            color: #155724;
            padding: 15px;
            border-radius: 4px;
            margin: 15px 0;
        }
    </style>
</head>
<body>
    <div class="header">
        <h2>Low Leave Balance Alert</h2>
    </div>

    <div class="content">
        <p>Dear {{ employee.get_full_name }},</p>

        <div class="alert-box">
            <h3>⚠️ Low Leave Balance Notice</h3>
            <p>This is to inform you that your leave balance is running low.</p>
        </div>

        <div class="balance-info">
            <h4>Current Leave Balance</h4>
            <table class="info-table">
                <tr>
                    <th>Leave Type</th>
                    <td>{{ leave_type }}</td>
                </tr>
                <tr>
                    <th>Current Balance</th>
                    <td>{{ current_balance }} days</td>
                </tr>
                <tr>
                    <th>Threshold Level</th>
                    <td>{{ threshold }} days</td>
                </tr>
            </table>

            <div class="progress-bar">
                <div class="progress-fill" style="width: {{ balance_percentage }}%"></div>
            </div>
        </div>

        <div class="accrual-info">
            <h4>Next Accrual Information</h4>
            <table class="info-table">
                <tr>
                    <th>Next Accrual Date</th>
                    <td>{{ next_accrual_date|date:"F j, Y" }}</td>
                </tr>
                <tr>
                    <th>Expected Days to be Added</th>
                    <td>{{ expected_accrual }} days</td>
                </tr>
            </table>
        </div>

        {% if upcoming_leaves %}
        <div class="upcoming-leaves">
            <h4>Upcoming Approved Leaves</h4>
            <table class="info-table">
                <thead>
                    <tr>
                        <th>Period</th>
                        <th>Duration</th>
                    </tr>
                </thead>
                <tbody>
                    {% for leave in upcoming_leaves %}
                    <tr>
                        <td>{{ leave.start_date|date:"M j" }} - {{ leave.end_date|date:"M j, Y" }}</td>
                        <td>{{ leave.duration }} day{{ leave.duration|pluralize }}</td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
        {% endif %}

        <div class="recommendation-box">
            <h4>Recommendations</h4>
            <ul>
                <li>Plan your upcoming leaves carefully considering your current balance</li>
                <li>Consider spreading out your leave requests over time</li>
                <li>Discuss with your supervisor if you need to take emergency leave</li>
                {% if has_unused_leaves %}
                <li>You have unused leaves from other categories that you might want to consider using</li>
                {% endif %}
            </ul>
        </div>
    </div>

    <div class="footer">
        <p>This is an automated notification from the HR Management System.</p>
        <p>Generated on: {{ generated_at|date:"l, F j, Y" }}</p>
        <p>For any questions about your leave balance or policy, please contact HR.</p>
        {% if help_link %}
        <p><a href="{{ help_link }}">View Leave Policy Documentation</a></p>
        {% endif %}
    </div>
</body>
</html>

```

### hrms_project\attendance\templates\attendance\email\missing_attendance_report.html
```
<!DOCTYPE html>
<html>
<head>
    <style>
        body {
            font-family: Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            padding: 20px;
        }
        .header {
            background-color: #f8f9fa;
            padding: 15px;
            border-bottom: 3px solid #dc3545;
            margin-bottom: 20px;
        }
        .content {
            background-color: white;
            padding: 20px;
            border-radius: 5px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .alert-box {
            background-color: #f8d7da;
            border: 1px solid #f5c6cb;
            color: #721c24;
            padding: 15px;
            border-radius: 4px;
            margin: 15px 0;
        }
        .missing-records {
            background-color: #f8f9fa;
            padding: 15px;
            border-radius: 4px;
            margin: 15px 0;
        }
        .records-table {
            width: 100%;
            border-collapse: collapse;
            margin: 15px 0;
        }
        .records-table th,
        .records-table td {
            padding: 10px;
            text-align: left;
            border-bottom: 1px solid #dee2e6;
        }
        .records-table th {
            background-color: #f1f3f5;
            font-weight: bold;
        }
        .records-table tbody tr:hover {
            background-color: #f8f9fa;
        }
        .instructions {
            background-color: #e8f4ff;
            border: 1px solid #b8daff;
            padding: 15px;
            border-radius: 4px;
            margin: 15px 0;
        }
        .footer {
            margin-top: 20px;
            padding-top: 20px;
            border-top: 1px solid #eee;
            font-size: 12px;
            color: #666;
        }
        .action-required {
            background-color: #fff3cd;
            border: 1px solid #ffeeba;
            color: #856404;
            padding: 15px;
            border-radius: 4px;
            margin: 15px 0;
        }
        .summary-box {
            background-color: #f8f9fa;
            padding: 15px;
            border-radius: 4px;
            margin: 15px 0;
            display: flex;
            justify-content: space-around;
            text-align: center;
        }
        .summary-item {
            padding: 10px;
        }
        .summary-number {
            font-size: 24px;
            font-weight: bold;
            color: #dc3545;
        }
        .summary-label {
            font-size: 14px;
            color: #666;
        }
        .deadline-notice {
            font-weight: bold;
            color: #dc3545;
        }
    </style>
</head>
<body>
    <div class="header">
        <h2>Missing Attendance Records Report</h2>
    </div>

    <div class="content">
        <p>Dear {{ employee.get_full_name }},</p>

        <div class="alert-box">
            <h3>⚠️ Missing Attendance Records</h3>
            <p>We have noticed that you have missing attendance records for the following period:</p>
            <p><strong>Period:</strong> {{ period_start|date:"F j, Y" }} - {{ period_end|date:"F j, Y" }}</p>
        </div>

        <div class="summary-box">
            <div class="summary-item">
                <div class="summary-number">{{ total_missing_records }}</div>
                <div class="summary-label">Total Missing Records</div>
            </div>
            <div class="summary-item">
                <div class="summary-number">{{ missing_in_records }}</div>
                <div class="summary-label">Missing Check-ins</div>
            </div>
            <div class="summary-item">
                <div class="summary-number">{{ missing_out_records }}</div>
                <div class="summary-label">Missing Check-outs</div>
            </div>
        </div>

        <div class="missing-records">
            <h4>Missing Record Details</h4>
            <table class="records-table">
                <thead>
                    <tr>
                        <th>Date</th>
                        <th>Day</th>
                        <th>Missing Record Type</th>
                        <th>Status</th>
                    </tr>
                </thead>
                <tbody>
                    {% for record in missing_records %}
                    <tr>
                        <td>{{ record.date|date:"d/m/Y" }}</td>
                        <td>{{ record.date|date:"l" }}</td>
                        <td>{{ record.missing_type }}</td>
                        <td>{{ record.status }}</td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>

        <div class="action-required">
            <h4>Action Required</h4>
            <p>Please take the following actions:</p>
            <ol>
                <li>Review the missing records listed above</li>
                <li>Submit justification for each missing record through the HR portal</li>
                <li>Attach any supporting documents if available</li>
                <li>Submit your response by <span class="deadline-notice">{{ submission_deadline|date:"F j, Y" }}</span></li>
            </ol>
        </div>

        <div class="instructions">
            <h4>How to Submit Your Response</h4>
            <ol>
                <li>Log in to the HR Portal</li>
                <li>Go to the "Attendance" section</li>
                <li>Click on "Missing Records Resolution"</li>
                <li>Fill in the required information for each missing record</li>
                <li>Submit for approval</li>
            </ol>
            {% if portal_link %}
            <p><a href="{{ portal_link }}">Click here to access the HR Portal</a></p>
            {% endif %}
        </div>

        {% if policy_reminders %}
        <div class="instructions">
            <h4>Policy Reminders</h4>
            <ul>
                {% for reminder in policy_reminders %}
                <li>{{ reminder }}</li>
                {% endfor %}
            </ul>
        </div>
        {% endif %}
    </div>

    <div class="footer">
        <p>This is an automated notification from the HR Management System.</p>
        <p>Generated on: {{ generated_at|date:"l, F j, Y" }}</p>
        <p>If you believe there is an error in this report or need assistance, please contact HR immediately.</p>
        <p>Reference: {{ report_reference }}</p>
    </div>
</body>
</html>

```

### hrms_project\attendance\templates\attendance\email\missing_shift_notification.html
```
<!DOCTYPE html>
<html>
<head>
    <style>
        body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
        .container { max-width: 600px; margin: 20px auto; padding: 20px; }
        .header { background-color: #f8f9fa; padding: 15px; border-radius: 5px; }
        .content { padding: 20px 0; }
        .alert { color: #721c24; background-color: #f8d7da; padding: 15px; border-radius: 5px; margin: 10px 0; }
        .employee-list { background-color: #f1f3f5; padding: 15px; border-radius: 5px; margin: 10px 0; }
        .employee-item { padding: 8px; border-bottom: 1px solid #dee2e6; }
        .employee-item:last-child { border-bottom: none; }
        .department { color: #6c757d; font-size: 0.9em; }
        .summary { font-weight: bold; color: #dc3545; margin: 15px 0; }
        .footer { color: #6c757d; font-size: 0.9em; margin-top: 20px; }
        table { width: 100%; border-collapse: collapse; margin: 15px 0; }
        th { background-color: #f8f9fa; text-align: left; padding: 10px; }
        td { padding: 8px; border-top: 1px solid #dee2e6; }
        .action-needed { color: #dc3545; font-weight: bold; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h2>Missing Shift Assignments Alert</h2>
        </div>
        
        <div class="content">
            <div class="alert">
                <strong>Action Required:</strong> {{ count }} employee(s) currently have no active shift assignment.
            </div>
            
            <p>The following employees require shift assignments:</p>
            
            <div class="employee-list">
                <table>
                    <thead>
                        <tr>
                            <th>Employee</th>
                            <th>Department</th>
                            <th>Status</th>
                        </tr>
                    </thead>
                    <tbody>
                        {% for employee in employees %}
                        <tr class="employee-item">
                            <td>
                                <strong>{{ employee.get_full_name }}</strong><br>
                                <small>{{ employee.employee_number }}</small>
                            </td>
                            <td class="department">
                                {{ employee.department.name|default:'No Department' }}
                            </td>
                            <td>
                                <span class="action-needed">No Shift Assigned</span>
                            </td>
                        </tr>
                        {% endfor %}
                    </tbody>
                </table>
            </div>
            
            <div class="summary">
                <p>Please assign appropriate shifts to these employees to ensure proper attendance tracking.</p>
            </div>
            
            <p>Quick actions:</p>
            <ul>
                <li>Review each employee's work schedule requirements</li>
                <li>Assign appropriate shifts based on department needs</li>
                <li>Ensure shift assignments are properly documented</li>
                <li>Update HR records accordingly</li>
            </ul>
            
            <p>To assign shifts, please visit the <a href="{{ site_url }}{% url 'attendance:shift_assignment_create' %}">Shift Assignment</a> page.</p>
        </div>
        
        <div class="footer">
            <p>This is an automated system notification.</p>
            <p>Generated on {{ today|date:"l, F d, Y" }} at {{ today|time:"g:i A" }}</p>
            <hr>
            <p>Human Resources Management System<br>
            Attendance Management Module</p>
        </div>
    </div>
</body>
</html>

```

### hrms_project\attendance\templates\attendance\email\monthly_attendance_summary.html
```
<!DOCTYPE html>
<html>
<head>
    <style>
        body {
            font-family: Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            padding: 20px;
        }
        .header {
            background-color: #f8f9fa;
            padding: 15px;
            border-bottom: 3px solid #28a745;
            margin-bottom: 20px;
        }
        .content {
            background-color: white;
            padding: 20px;
            border-radius: 5px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .summary-box {
            background-color: #f8f9fa;
            padding: 20px;
            border-radius: 4px;
            margin: 15px 0;
            display: flex;
            justify-content: space-around;
            flex-wrap: wrap;
        }
        .summary-item {
            padding: 15px;
            text-align: center;
            min-width: 120px;
        }
        .summary-number {
            font-size: 24px;
            font-weight: bold;
            margin-bottom: 5px;
        }
        .summary-label {
            font-size: 14px;
            color: #666;
        }
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin: 15px 0;
        }
        .stats-card {
            background-color: #fff;
            border: 1px solid #dee2e6;
            border-radius: 4px;
            padding: 15px;
        }
        .stats-title {
            font-weight: bold;
            margin-bottom: 10px;
            color: #495057;
        }
        .detail-table {
            width: 100%;
            border-collapse: collapse;
            margin: 15px 0;
        }
        .detail-table th,
        .detail-table td {
            padding: 10px;
            text-align: left;
            border-bottom: 1px solid #dee2e6;
        }
        .detail-table th {
            background-color: #f8f9fa;
            font-weight: bold;
        }
        .detail-table tbody tr:hover {
            background-color: #f8f9fa;
        }
        .chart-container {
            background-color: #fff;
            border: 1px solid #dee2e6;
            border-radius: 4px;
            padding: 15px;
            margin: 15px 0;
        }
        .chart-title {
            font-weight: bold;
            margin-bottom: 10px;
            color: #495057;
        }
        .attendance-pattern {
            display: flex;
            gap: 2px;
            margin: 15px 0;
        }
        .pattern-day {
            width: 20px;
            height: 20px;
            border-radius: 4px;
        }
        .present { background-color: #28a745; }
        .absent { background-color: #dc3545; }
        .late { background-color: #ffc107; }
        .leave { background-color: #17a2b8; }
        .weekend { background-color: #6c757d; }
        .holiday { background-color: #6610f2; }
        .footer {
            margin-top: 20px;
            padding-top: 20px;
            border-top: 1px solid #eee;
            font-size: 12px;
            color: #666;
        }
        .trend-indicator {
            display: inline-block;
            margin-left: 5px;
        }
        .trend-up { color: #28a745; }
        .trend-down { color: #dc3545; }
        .trend-neutral { color: #6c757d; }
        .highlight-box {
            background-color: #e8f4ff;
            border: 1px solid #b8daff;
            padding: 15px;
            border-radius: 4px;
            margin: 15px 0;
        }
    </style>
</head>
<body>
    <div class="header">
        <h2>Monthly Attendance Summary</h2>
        <p>{{ month_name }} {{ year }}</p>
    </div>

    <div class="content">
        <p>Dear {{ employee.get_full_name }},</p>

        <p>Here's your attendance summary for {{ month_name }} {{ year }}:</p>

        <div class="summary-box">
            <div class="summary-item">
                <div class="summary-number">{{ total_working_days }}</div>
                <div class="summary-label">Working Days</div>
            </div>
            <div class="summary-item">
                <div class="summary-number">{{ present_days }}</div>
                <div class="summary-label">Present Days</div>
            </div>
            <div class="summary-item">
                <div class="summary-number">{{ late_days }}</div>
                <div class="summary-label">Late Arrivals</div>
            </div>
            <div class="summary-item">
                <div class="summary-number">{{ absent_days }}</div>
                <div class="summary-label">Absent Days</div>
            </div>
            <div class="summary-item">
                <div class="summary-number">{{ leave_days }}</div>
                <div class="summary-label">Leave Days</div>
            </div>
        </div>

        <div class="highlight-box">
            <h4>Monthly Highlights</h4>
            <ul>
                <li>Attendance Rate: {{ attendance_rate }}%
                    <span class="trend-indicator {{ attendance_trend_class }}">
                        {{ attendance_trend_icon }} {{ attendance_trend }}%
                    </span>
                </li>
                <li>Average Arrival Time: {{ avg_arrival_time }}
                    <span class="trend-indicator {{ arrival_trend_class }}">
                        {{ arrival_trend_icon }}
                    </span>
                </li>
                <li>Total Working Hours: {{ total_working_hours }} hours</li>
                {% if overtime_hours %}
                <li>Overtime Hours: {{ overtime_hours }} hours</li>
                {% endif %}
            </ul>
        </div>

        <div class="stats-grid">
            <div class="stats-card">
                <div class="stats-title">Arrival Time Distribution</div>
                <table class="detail-table">
                    <tr>
                        <td>On Time (Before {{ regular_time }})</td>
                        <td>{{ ontime_count }} days</td>
                    </tr>
                    <tr>
                        <td>Late ({{ grace_period }} grace period)</td>
                        <td>{{ late_within_grace }} days</td>
                    </tr>
                    <tr>
                        <td>Late (After grace period)</td>
                        <td>{{ late_after_grace }} days</td>
                    </tr>
                </table>
            </div>

            <div class="stats-card">
                <div class="stats-title">Leave Summary</div>
                <table class="detail-table">
                    {% for leave in leave_summary %}
                    <tr>
                        <td>{{ leave.type }}</td>
                        <td>{{ leave.days }} days</td>
                    </tr>
                    {% endfor %}
                </table>
            </div>
        </div>

        <div class="chart-container">
            <div class="chart-title">Monthly Attendance Pattern</div>
            <div class="attendance-pattern">
                {% for day in attendance_pattern %}
                <div class="pattern-day {{ day.status }}" title="{{ day.date|date:'D, M d' }}: {{ day.status|title }}"></div>
                {% endfor %}
            </div>
            <div style="margin-top: 10px;">
                <small>
                    <span class="pattern-day present" style="display: inline-block;"></span> Present
                    <span class="pattern-day absent" style="display: inline-block; margin-left: 10px;"></span> Absent
                    <span class="pattern-day late" style="display: inline-block; margin-left: 10px;"></span> Late
                    <span class="pattern-day leave" style="display: inline-block; margin-left: 10px;"></span> Leave
                    <span class="pattern-day weekend" style="display: inline-block; margin-left: 10px;"></span> Weekend
                    <span class="pattern-day holiday" style="display: inline-block; margin-left: 10px;"></span> Holiday
                </small>
            </div>
        </div>

        {% if improvement_areas %}
        <div class="highlight-box">
            <h4>Areas for Improvement</h4>
            <ul>
                {% for area in improvement_areas %}
                <li>{{ area }}</li>
                {% endfor %}
            </ul>
        </div>
        {% endif %}

        {% if next_month_holidays %}
        <div class="highlight-box">
            <h4>Upcoming Holidays ({{ next_month_name }})</h4>
            <ul>
                {% for holiday in next_month_holidays %}
                <li>{{ holiday.date|date:"F j" }} - {{ holiday.description }}</li>
                {% endfor %}
            </ul>
        </div>
        {% endif %}
    </div>

    <div class="footer">
        <p>This is an automated monthly summary from the HR Management System.</p>
        <p>Generated on: {{ generated_at|date:"l, F j, Y" }}</p>
        <p>For detailed attendance records, please visit the HR Portal.</p>
        {% if portal_link %}
        <p><a href="{{ portal_link }}">Access HR Portal</a></p>
        {% endif %}
        <p>If you notice any discrepancies, please contact HR within 3 working days.</p>
    </div>
</body>
</html>

```

### hrms_project\attendance\templates\attendance\email\ramadan_timing_notification.html
```
<!DOCTYPE html>
<html>
<head>
    <style>
        body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
        .container { max-width: 600px; margin: 20px auto; padding: 20px; }
        .header { background-color: #f8f9fa; padding: 15px; border-radius: 5px; }
        .content { padding: 20px 0; }
        .timing-details { background-color: #f1f3f5; padding: 15px; border-radius: 5px; margin: 10px 0; }
        .ramadan-note { color: #856404; background-color: #fff3cd; padding: 10px; border-radius: 5px; }
        .footer { color: #6c757d; font-size: 0.9em; margin-top: 20px; }
        .blessing { font-style: italic; color: #28a745; margin: 15px 0; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h2>{% if is_end %}Regular Working Hours Resume{% else %}Ramadan Working Hours{% endif %}</h2>
        </div>
        
        <div class="content">
            <p>Dear {{ employee.get_full_name }},</p>
            
            {% if is_end %}
                <p>This is to inform you that regular working hours will resume after Ramadan ends on 
                   <strong>{{ ramadan_period.end_date|date:"l, F d, Y" }}</strong>.</p>
                
                <div class="timing-details">
                    <h3>Regular Shift Details:</h3>
                    <p><strong>Shift:</strong> {{ shift.name }}</p>
                    <p><strong>Timing:</strong> {{ shift.start_time|time:"g:i A" }} - {{ shift.end_time|time:"g:i A" }}</p>
                    {% if shift.break_duration %}
                        <p><strong>Break Duration:</strong> {{ shift.break_duration }} minutes</p>
                    {% endif %}
                </div>
                
                <p class="blessing">Thank you for your dedication during the blessed month of Ramadan.</p>
            {% else %}
                <p>In observance of the holy month of Ramadan, your working hours will be adjusted from 
                   <strong>{{ ramadan_period.start_date|date:"l, F d, Y" }}</strong>.</p>
                
                <div class="timing-details">
                    <h3>Adjusted Ramadan Timing:</h3>
                    <p><strong>Shift:</strong> {{ shift.name }}</p>
                    <p><strong>Timing:</strong> {{ adjusted_timing.start_time|time:"g:i A" }} - {{ adjusted_timing.end_time|time:"g:i A" }}</p>
                    {% if shift.break_duration %}
                        <p><strong>Break Duration:</strong> {{ shift.break_duration }} minutes</p>
                    {% endif %}
                </div>
                
                <div class="ramadan-note">
                    <p><strong>Note:</strong> These adjusted hours will be in effect throughout Ramadan 
                       ({{ ramadan_period.start_date|date:"M d" }} - {{ ramadan_period.end_date|date:"M d, Y" }}).</p>
                </div>
                
                <p class="blessing">Ramadan Kareem! رمضان كريم</p>
            {% endif %}
            
            <p>If you have any questions about your working hours, please contact HR.</p>
        </div>
        
        <div class="footer">
            <p>This is an automated message. Please do not reply to this email.</p>
            <p>Human Resources Department</p>
        </div>
    </div>
</body>
</html>

```

### hrms_project\attendance\templates\attendance\email\shift_change_notification.html
```
<!DOCTYPE html>
<html>
<head>
    <style>
        body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
        .container { max-width: 600px; margin: 20px auto; padding: 20px; }
        .header { background-color: #f8f9fa; padding: 15px; border-radius: 5px; }
        .content { padding: 20px 0; }
        .shift-details { background-color: #f1f3f5; padding: 15px; border-radius: 5px; margin: 10px 0; }
        .footer { color: #6c757d; font-size: 0.9em; margin-top: 20px; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h2>Shift Change Notification</h2>
        </div>
        <div class="content">
            <p>Dear {{ employee.get_full_name }},</p>
            
            <p>This is to inform you that your work shift will change effective from <strong>{{ start_date|date:"l, F d, Y" }}</strong>.</p>
            
            <div class="shift-details">
                <h3>Shift Details:</h3>
                <p><strong>Current Shift:</strong> {{ old_shift.name }}<br>
                   Timing: {{ old_shift.start_time|time:"g:i A" }} - {{ old_shift.end_time|time:"g:i A" }}</p>
                
                <p><strong>New Shift:</strong> {{ new_shift.name }}<br>
                   Timing: {{ new_shift.start_time|time:"g:i A" }} - {{ new_shift.end_time|time:"g:i A" }}</p>
                
                {% if new_shift.grace_period %}
                <p><em>Note: Grace period of {{ new_shift.grace_period }} minutes applies.</em></p>
                {% endif %}
            </div>
            
            <p>Please ensure you adjust your schedule accordingly. If you have any questions, please contact HR.</p>
        </div>
        <div class="footer">
            <p>This is an automated message. Please do not reply to this email.</p>
            <p>Human Resources Department</p>
        </div>
    </div>
</body>
</html>

```

### hrms_project\attendance\templates\attendance\holiday_create.html
```
{% extends 'attendance/base.html' %}
{% load static %}

{% block attendance_content %}
<div class="card">
    <div class="card-header">
        <h5 class="card-title mb-0">
            <i class="fas fa-plus"></i> Add New Holiday
        </h5>
    </div>
    <div class="card-body">
        <form method="POST" class="needs-validation" novalidate>
            {% csrf_token %}
            <div class="row">
                <div class="col-md-6">
                    <div class="mb-3">
                        <label for="holidayName" class="form-label">Holiday Name</label>
                        <input type="text" class="form-control" id="holidayName" name="name" required>
                        <div class="invalid-feedback">
                            Please provide a holiday name.
                        </div>
                    </div>
                </div>
                <div class="col-md-6">
                    <div class="mb-3">
                        <label for="holidayDate" class="form-label">Date</label>
                        <input type="date" class="form-control" id="holidayDate" name="date" required>
                        <div class="invalid-feedback">
                            Please select a date.
                        </div>
                    </div>
                </div>
            </div>
            <div class="mb-3">
                <label for="holidayDescription" class="form-label">Description</label>
                <textarea class="form-control" id="holidayDescription" name="description" rows="3"></textarea>
            </div>
            <div class="mb-3">
                <div class="form-check">
                    <input class="form-check-input" type="checkbox" id="holidayRecurring" name="is_recurring">
                    <label class="form-check-label" for="holidayRecurring">
                        Recurring Holiday
                    </label>
                    <div class="form-text">
                        Check this if the holiday occurs on the same date every year.
                    </div>
                </div>
            </div>
            <div class="d-flex justify-content-between">
                <a href="{% url 'attendance:holiday_list' %}" class="btn btn-secondary">
                    <i class="fas fa-arrow-left"></i> Back to List
                </a>
                <button type="submit" class="btn btn-primary">
                    <i class="fas fa-save"></i> Save Holiday
                </button>
            </div>
        </form>
    </div>
</div>
{% endblock %}

{% block extra_js %}
{{ block.super }}
<script>
// Form validation
(function () {
    'use strict'
    var forms = document.querySelectorAll('.needs-validation')
    Array.prototype.slice.call(forms)
        .forEach(function (form) {
            form.addEventListener('submit', function (event) {
                if (!form.checkValidity()) {
                    event.preventDefault()
                    event.stopPropagation()
                }
                form.classList.add('was-validated')
            }, false)
        })
})()
</script>
{% endblock %}

```

### hrms_project\attendance\templates\attendance\holiday_form.html
```
{% extends 'attendance/base.html' %}
{% load static %}

{% block attendance_content %}
<div class="card">
    <div class="card-header">
        <h5 class="mb-0">{% if form.instance.pk %}Edit Holiday{% else %}Add Holiday{% endif %}</h5>
    </div>
    <div class="card-body">
        <form method="post" class="needs-validation" novalidate>
            {% csrf_token %}
            
            {% if form.non_field_errors %}
            <div class="alert alert-danger">
                {% for error in form.non_field_errors %}
                {{ error }}
                {% endfor %}
            </div>
            {% endif %}

            <!-- Holiday Name -->
            <div class="mb-3">
                <label for="name" class="form-label">Holiday Name *</label>
                <input type="text" 
                       class="form-control {% if form.name.errors %}is-invalid{% endif %}" 
                       id="name" 
                       name="name"
                       value="{{ form.name.value|default:'' }}"
                       required>
                {% if form.name.errors %}
                <div class="invalid-feedback">
                    {{ form.name.errors|join:", " }}
                </div>
                {% endif %}
            </div>

            <!-- Holiday Date -->
            <div class="mb-3">
                <label for="date" class="form-label">Date *</label>
                <input type="date" 
                       class="form-control {% if form.date.errors %}is-invalid{% endif %}" 
                       id="date" 
                       name="date"
                       value="{{ form.date.value|date:'Y-m-d'|default:'' }}"
                       required>
                {% if form.date.errors %}
                <div class="invalid-feedback">
                    {{ form.date.errors|join:", " }}
                </div>
                {% endif %}
                <div id="friday-notice" class="text-muted small mt-1" style="display: none;">
                    <i class="fas fa-info-circle"></i> This is a Friday
                </div>
            </div>

            <!-- Holiday Type -->
            <div class="mb-3">
                <label for="holiday_type" class="form-label">Holiday Type *</label>
                <select class="form-select {% if form.holiday_type.errors %}is-invalid{% endif %}" 
                        id="holiday_type" 
                        name="holiday_type"
                        required>
                    <option value="">Select Type</option>
                    <option value="PUBLIC" {% if form.holiday_type.value == 'PUBLIC' %}selected{% endif %}>Public Holiday</option>
                    <option value="COMPANY" {% if form.holiday_type.value == 'COMPANY' %}selected{% endif %}>Company Holiday</option>
                    <option value="OPTIONAL" {% if form.holiday_type.value == 'OPTIONAL' %}selected{% endif %}>Optional Holiday</option>
                </select>
                {% if form.holiday_type.errors %}
                <div class="invalid-feedback">
                    {{ form.holiday_type.errors|join:", " }}
                </div>
                {% endif %}
            </div>

            <!-- Description -->
            <div class="mb-3">
                <label for="description" class="form-label">Description</label>
                <textarea class="form-control {% if form.description.errors %}is-invalid{% endif %}" 
                          id="description" 
                          name="description" 
                          rows="3">{{ form.description.value|default:'' }}</textarea>
                {% if form.description.errors %}
                <div class="invalid-feedback">
                    {{ form.description.errors|join:", " }}
                </div>
                {% endif %}
            </div>

            <!-- Applicable Departments -->
            <div class="mb-3">
                <label class="form-label">Applicable Departments</label>
                <div class="border rounded p-3">
                    <div class="mb-2">
                        <input type="checkbox" 
                               class="form-check-input" 
                               id="select-all-departments">
                        <label class="form-check-label" for="select-all-departments">
                            Select All
                        </label>
                    </div>
                    <div class="row">
                        {% for dept in departments %}
                        <div class="col-md-4 mb-2">
                            <div class="form-check">
                                <input type="checkbox" 
                                       class="form-check-input department-checkbox" 
                                       id="dept_{{ dept.id }}" 
                                       name="applicable_departments" 
                                       value="{{ dept.id }}"
                                       {% if dept.id in form.applicable_departments.value %}checked{% endif %}>
                                <label class="form-check-label" for="dept_{{ dept.id }}">
                                    {{ dept.name }}
                                </label>
                            </div>
                        </div>
                        {% endfor %}
                    </div>
                </div>
                {% if form.applicable_departments.errors %}
                <div class="text-danger small mt-1">
                    {{ form.applicable_departments.errors|join:", " }}
                </div>
                {% endif %}
            </div>

            <!-- Holiday Options -->
            <div class="mb-3">
                <div class="form-check">
                    <input type="checkbox" 
                           class="form-check-input" 
                           id="is_recurring" 
                           name="is_recurring"
                           {% if form.is_recurring.value %}checked{% endif %}>
                    <label class="form-check-label" for="is_recurring">
                        Recurring Holiday (repeats yearly)
                    </label>
                </div>
                <div class="form-check">
                    <input type="checkbox" 
                           class="form-check-input" 
                           id="is_paid" 
                           name="is_paid"
                           {% if form.is_paid.value %}checked{% endif %}>
                    <label class="form-check-label" for="is_paid">
                        Paid Holiday
                    </label>
                </div>
            </div>

            <!-- Submit Buttons -->
            <div class="mt-4">
                <button type="submit" class="btn btn-primary">
                    {% if form.instance.pk %}Update{% else %}Create{% endif %} Holiday
                </button>
                <a href="{% url 'attendance:holiday_list' %}" class="btn btn-secondary">
                    Cancel
                </a>
            </div>
        </form>
    </div>
</div>
{% endblock %}

{% block extra_js %}
{{ block.super }}
<script>
$(document).ready(function() {
    // Handle select all departments
    $('#select-all-departments').change(function() {
        $('.department-checkbox').prop('checked', $(this).prop('checked'));
    });

    // Update select all when individual checkboxes change
    $('.department-checkbox').change(function() {
        if ($('.department-checkbox:checked').length === $('.department-checkbox').length) {
            $('#select-all-departments').prop('checked', true);
        } else {
            $('#select-all-departments').prop('checked', false);
        }
    });

    // Show notice when date is Friday
    $('#date').change(function() {
        const date = new Date($(this).val());
        if (date.getDay() === 5) { // 5 is Friday (0 is Sunday)
            $('#friday-notice').show();
        } else {
            $('#friday-notice').hide();
        }
    });

    // Form validation
    (function() {
        'use strict';
        var forms = document.querySelectorAll('.needs-validation');
        Array.prototype.slice.call(forms).forEach(function(form) {
            form.addEventListener('submit', function(event) {
                if (!form.checkValidity()) {
                    event.preventDefault();
                    event.stopPropagation();
                }
                form.classList.add('was-validated');
            }, false);
        });
    })();

    // If editing, check Friday on page load
    if ($('#date').val()) {
        const date = new Date($('#date').val());
        if (date.getDay() === 5) {
            $('#friday-notice').show();
        }
    }
});
</script>
{% endblock %}

```

### hrms_project\attendance\templates\attendance\holiday_list.html
```

{% extends 'attendance/base.html' %}
{% load static %}

{% block attendance_content %}
<div class="card">
    <div class="card-header d-flex justify-content-between align-items-center">
        <h5 class="card-title mb-0">
            <i class="fas fa-star"></i> Holidays
        </h5>
        <a href="{% url 'attendance:holiday_create' %}" class="btn btn-primary btn-sm">
            <i class="fas fa-plus"></i> Add Holiday
        </a>
    </div>
    <div class="card-body">
        <div class="table-responsive">
            <table class="table table-striped table-hover">
                <thead>
                    <tr>
                        <th>Name</th>
                        <th>Date</th>
                        <th>Description</th>
                        <th>Recurring</th>
                        <th>Actions</th>
                    </tr>
                </thead>
                <tbody>
                    {% for holiday in holidays %}
                    <tr>
                        <td>{{ holiday.name }}</td>
                        <td>{{ holiday.date|date:"d M Y" }}</td>
                        <td>{{ holiday.description }}</td>
                        <td>
                            {% if holiday.is_recurring %}
                            <span class="badge bg-success">Yes</span>
                            {% else %}
                            <span class="badge bg-secondary">No</span>
                            {% endif %}
                        </td>
                        <td>
                            <div class="btn-group">
                                <button type="button" class="btn btn-sm btn-outline-primary edit-holiday" 
                                        data-id="{{ holiday.id }}"
                                        data-name="{{ holiday.name }}"
                                        data-date="{{ holiday.date|date:'Y-m-d' }}"
                                        data-description="{{ holiday.description }}"
                                        data-recurring="{{ holiday.is_recurring|yesno:'true,false' }}">
                                    <i class="fas fa-edit"></i>
                                </button>
                                <button type="button" class="btn btn-sm btn-outline-danger delete-holiday" 
                                        data-id="{{ holiday.id }}"
                                        data-name="{{ holiday.name }}">
                                    <i class="fas fa-trash"></i>
                                </button>
                            </div>
                        </td>
                    </tr>
                    {% empty %}
                    <tr>
                        <td colspan="5" class="text-center">No holidays found</td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
    </div>
</div>

<!-- Edit Holiday Modal -->
<div class="modal fade" id="editHolidayModal" tabindex="-1">
    <div class="modal-dialog">
        <div class="modal-content">
            <div class="modal-header">
                <h5 class="modal-title">Edit Holiday</h5>
                <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
            </div>
            <form id="editHolidayForm" method="POST">
                {% csrf_token %}
                <div class="modal-body">
                    <input type="hidden" name="holiday_id" id="editHolidayId">
                    <div class="mb-3">
                        <label for="editHolidayName" class="form-label">Holiday Name</label>
                        <input type="text" class="form-control" id="editHolidayName" name="name" required>
                    </div>
                    <div class="mb-3">
                        <label for="editHolidayDate" class="form-label">Date</label>
                        <input type="date" class="form-control" id="editHolidayDate" name="date" required>
                    </div>
                    <div class="mb-3">
                        <label for="editHolidayDescription" class="form-label">Description</label>
                        <textarea class="form-control" id="editHolidayDescription" name="description" rows="3"></textarea>
                    </div>
                    <div class="mb-3">
                        <div class="form-check">
                            <input class="form-check-input" type="checkbox" id="editHolidayRecurring" name="is_recurring">
                            <label class="form-check-label" for="editHolidayRecurring">
                                Recurring Holiday
                            </label>
                        </div>
                    </div>
                </div>
                <div class="modal-footer">
                    <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
                    <button type="submit" class="btn btn-primary">Save Changes</button>
                </div>
            </form>
        </div>
    </div>
</div>

<!-- Delete Holiday Modal -->
<div class="modal fade" id="deleteHolidayModal" tabindex="-1">
    <div class="modal-dialog">
        <div class="modal-content">
            <div class="modal-header">
                <h5 class="modal-title">Delete Holiday</h5>
                <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
            </div>
            <div class="modal-body">
                <p>Are you sure you want to delete the holiday "<span id="deleteHolidayName"></span>"?</p>
                <p class="text-danger">This action cannot be undone.</p>
            </div>
            <div class="modal-footer">
                <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
                <form id="deleteHolidayForm" method="POST">
                    {% csrf_token %}
                    <input type="hidden" name="holiday_id" id="deleteHolidayId">
                    <button type="submit" class="btn btn-danger">Delete</button>
                </form>
            </div>
        </div>
    </div>
</div>
{% endblock %}

{% block extra_js %}
{{ block.super }}
<script src="{% static 'attendance/js/holiday_list.js' %}"></script>
{% endblock %}
```

### hrms_project\attendance\templates\attendance\leave_balance.html
```
{% extends 'attendance/base.html' %}
{% load static %}

{% block attendance_content %}
<div class="card">
    <div class="card-header">
        <h5 class="card-title mb-0">
            <i class="fas fa-balance-scale"></i> Leave Balances
        </h5>
    </div>
    <div class="card-body">
        <div class="row">
            {% for balance in balances %}
            <div class="col-md-6 col-lg-4 mb-4">
                <div class="card h-100">
                    <div class="card-body">
                        <h6 class="card-title">{{ balance.leave_type.name }}</h6>
                        <div class="progress mb-3" style="height: 20px;">
                            {% with percentage=balance.used_days|div:balance.allowed_days|mul:100 %}
                            <div class="progress-bar {% if percentage > 75 %}bg-danger{% elif percentage > 50 %}bg-warning{% else %}bg-success{% endif %}"
                                 role="progressbar"
                                 style="width: {{ percentage }}%"
                                 aria-valuenow="{{ percentage }}"
                                 aria-valuemin="0"
                                 aria-valuemax="100">
                                {{ percentage|floatformat:1 }}%
                            </div>
                            {% endwith %}
                        </div>
                        <div class="row text-center">
                            <div class="col">
                                <small class="text-muted d-block">Allowed</small>
                                <strong>{{ balance.allowed_days }}</strong>
                            </div>
                            <div class="col">
                                <small class="text-muted d-block">Used</small>
                                <strong>{{ balance.used_days }}</strong>
                            </div>
                            <div class="col">
                                <small class="text-muted d-block">Remaining</small>
                                <strong>{{ balance.remaining_days }}</strong>
                            </div>
                        </div>
                        {% if balance.leave_type.description %}
                        <div class="mt-3">
                            <small class="text-muted">{{ balance.leave_type.description }}</small>
                        </div>
                        {% endif %}
                    </div>
                    <div class="card-footer bg-transparent">
                        <div class="d-grid">
                            <a href="{% url 'attendance:leave_request_create' %}?type={{ balance.leave_type.id }}" 
                               class="btn btn-outline-primary btn-sm">
                                <i class="fas fa-plus"></i> Apply for {{ balance.leave_type.name }}
                            </a>
                        </div>
                    </div>
                </div>
            </div>
            {% empty %}
            <div class="col-12">
                <div class="alert alert-info">
                    No leave balances found.
                </div>
            </div>
            {% endfor %}
        </div>
    </div>
</div>
{% endblock %}

```

### hrms_project\attendance\templates\attendance\leave_detail.html
```
{% extends 'attendance/base.html' %}
{% load static %}

{% block attendance_content %}
<div class="card">
    <div class="card-header d-flex justify-content-between align-items-center">
        <h5 class="mb-0">Leave Request Details</h5>
        <div>
            {% if leave.status == 'pending' %}
                {% if leave.employee == user.employee %}
                <button class="btn btn-danger cancel-leave">
                    <i class="fas fa-times"></i> Cancel Request
                </button>
                {% elif perms.attendance.can_approve_leave %}
                <button class="btn btn-success approve-leave">
                    <i class="fas fa-check"></i> Approve
                </button>
                <button class="btn btn-danger reject-leave">
                    <i class="fas fa-times"></i> Reject
                </button>
                {% endif %}
            {% endif %}
            <a href="{% url 'attendance:leave_request_list' %}" class="btn btn-secondary">
                <i class="fas fa-arrow-left"></i> Back to List
            </a>
        </div>
    </div>
    <div class="card-body">
        <div class="row">
            <!-- Leave Request Details -->
            <div class="col-md-8">
                <div class="card mb-4">
                    <div class="card-header">
                        <h6 class="mb-0">Leave Information</h6>
                    </div>
                    <div class="card-body">
                        <div class="row mb-3">
                            <div class="col-md-4">
                                <strong>Employee:</strong>
                            </div>
                            <div class="col-md-8">
                                {{ leave.employee.get_full_name }}
                                <br>
                                <small class="text-muted">{{ leave.employee.department.name }}</small>
                            </div>
                        </div>
                        <div class="row mb-3">
                            <div class="col-md-4">
                                <strong>Leave Type:</strong>
                            </div>
                            <div class="col-md-8">
                                {{ leave.leave_type.name }}
                            </div>
                        </div>
                        <div class="row mb-3">
                            <div class="col-md-4">
                                <strong>Duration:</strong>
                            </div>
                            <div class="col-md-8">
                                {{ leave.duration }} days
                                <br>
                                <small class="text-muted">
                                    From: {{ leave.start_date|date:"M d, Y" }}
                                    {% if leave.start_half %} (Half Day){% endif %}
                                    <br>
                                    To: {{ leave.end_date|date:"M d, Y" }}
                                    {% if leave.end_half %} (Half Day){% endif %}
                                </small>
                            </div>
                        </div>
                        <div class="row mb-3">
                            <div class="col-md-4">
                                <strong>Status:</strong>
                            </div>
                            <div class="col-md-8">
                                {% if leave.status == 'pending' %}
                                <span class="badge bg-warning">Pending</span>
                                {% elif leave.status == 'approved' %}
                                <span class="badge bg-success">Approved</span>
                                {% elif leave.status == 'rejected' %}
                                <span class="badge bg-danger">Rejected</span>
                                {% else %}
                                <span class="badge bg-secondary">Cancelled</span>
                                {% endif %}
                            </div>
                        </div>
                        <div class="row mb-3">
                            <div class="col-md-4">
                                <strong>Reason:</strong>
                            </div>
                            <div class="col-md-8">
                                {{ leave.reason }}
                            </div>
                        </div>
                        
                        {% if leave.rejection_reason %}
                        <div class="row mb-3">
                            <div class="col-md-4">
                                <strong>Rejection Reason:</strong>
                            </div>
                            <div class="col-md-8 text-danger">
                                {{ leave.rejection_reason }}
                            </div>
                        </div>
                        {% endif %}

                        {% if leave.cancellation_reason %}
                        <div class="row mb-3">
                            <div class="col-md-4">
                                <strong>Cancellation Reason:</strong>
                            </div>
                            <div class="col-md-8">
                                {{ leave.cancellation_reason }}
                            </div>
                        </div>
                        {% endif %}
                    </div>
                </div>

                <!-- Supporting Documents -->
                {% if leave.documents.all %}
                <div class="card mb-4">
                    <div class="card-header">
                        <h6 class="mb-0">Supporting Documents</h6>
                    </div>
                    <div class="card-body">
                        <div class="list-group">
                            {% for doc in leave.documents.all %}
                            <a href="{{ doc.document.url }}" class="list-group-item list-group-item-action" target="_blank">
                                <i class="fas fa-file-{{ doc.document.name|slice:'-3:' }}"></i>
                                {{ doc.document.name|split:'/'|last }}
                                <span class="float-end text-muted">
                                    <small>{{ doc.uploaded_at|date:"M d, Y H:i" }}</small>
                                </span>
                            </a>
                            {% endfor %}
                        </div>
                    </div>
                </div>
                {% endif %}
            </div>

            <!-- Activity Timeline -->
            <div class="col-md-4">
                <div class="card">
                    <div class="card-header">
                        <h6 class="mb-0">Activity Timeline</h6>
                    </div>
                    <div class="card-body p-0">
                        <div class="timeline">
                            {% for activity in leave.activities.all %}
                            <div class="timeline-item">
                                <div class="timeline-marker 
                                    {% if activity.action == 'create' %}bg-primary
                                    {% elif activity.action == 'approve' %}bg-success
                                    {% elif activity.action == 'reject' %}bg-danger
                                    {% elif activity.action == 'cancel' %}bg-secondary
                                    {% else %}bg-info{% endif %}">
                                </div>
                                <div class="timeline-content">
                                    <div class="timeline-heading">
                                        <strong>{{ activity.get_action_display }}</strong>
                                        <small class="float-end text-muted">
                                            {{ activity.created_at|date:"M d, Y H:i" }}
                                        </small>
                                    </div>
                                    <div class="timeline-body">
                                        {% if activity.actor %}
                                        <small>By: {{ activity.actor.get_full_name }}</small><br>
                                        {% endif %}
                                        {{ activity.details }}
                                    </div>
                                </div>
                            </div>
                            {% endfor %}
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
</div>

<!-- Action Modals -->
<!-- Cancel Leave Modal -->
<div class="modal fade" id="cancelModal" tabindex="-1">
    <div class="modal-dialog">
        <div class="modal-content">
            <div class="modal-header">
                <h5 class="modal-title">Cancel Leave Request</h5>
                <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
            </div>
            <div class="modal-body">
                <form id="cancelForm">
                    <div class="mb-3">
                        <label for="cancellation_reason" class="form-label">Reason for Cancellation</label>
                        <textarea class="form-control" id="cancellation_reason" rows="3" required></textarea>
                    </div>
                </form>
            </div>
            <div class="modal-footer">
                <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Close</button>
                <button type="button" class="btn btn-danger" id="confirmCancel">Cancel Leave</button>
            </div>
        </div>
    </div>
</div>

<!-- Approve Leave Modal -->
<div class="modal fade" id="approveModal" tabindex="-1">
    <div class="modal-dialog">
        <div class="modal-content">
            <div class="modal-header">
                <h5 class="modal-title">Approve Leave Request</h5>
                <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
            </div>
            <div class="modal-body">
                <form id="approveForm">
                    <div class="mb-3">
                        <label for="approval_remarks" class="form-label">Remarks (Optional)</label>
                        <textarea class="form-control" id="approval_remarks" rows="3"></textarea>
                    </div>
                </form>
            </div>
            <div class="modal-footer">
                <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Close</button>
                <button type="button" class="btn btn-success" id="confirmApprove">Approve</button>
            </div>
        </div>
    </div>
</div>

<!-- Reject Leave Modal -->
<div class="modal fade" id="rejectModal" tabindex="-1">
    <div class="modal-dialog">
        <div class="modal-content">
            <div class="modal-header">
                <h5 class="modal-title">Reject Leave Request</h5>
                <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
            </div>
            <div class="modal-body">
                <form id="rejectForm">
                    <div class="mb-3">
                        <label for="rejection_reason" class="form-label">Reason for Rejection</label>
                        <textarea class="form-control" id="rejection_reason" rows="3" required></textarea>
                    </div>
                </form>
            </div>
            <div class="modal-footer">
                <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Close</button>
                <button type="button" class="btn btn-danger" id="confirmReject">Reject</button>
            </div>
        </div>
    </div>
</div>

{% endblock %}

{% block extra_css %}
{{ block.super }}
<style>
.timeline {
    position: relative;
    padding: 1rem;
}

.timeline-item {
    position: relative;
    padding-left: 2rem;
    margin-bottom: 1.5rem;
}

.timeline-marker {
    position: absolute;
    left: 0;
    width: 15px;
    height: 15px;
    border-radius: 50%;
    margin-top: 0.25rem;
}

.timeline-content {
    position: relative;
    background: #f8f9fa;
    border-radius: 0.25rem;
    padding: 0.75rem;
}

.timeline-heading {
    margin-bottom: 0.5rem;
}

.timeline-body {
    font-size: 0.875rem;
}

.timeline-item::before {
    content: '';
    position: absolute;
    left: 7px;
    height: 100%;
    width: 1px;
    background-color: #dee2e6;
}

.timeline-item:last-child::before {
    display: none;
}
</style>
{% endblock %}

{% block extra_js %}
{{ block.super }}
<script>
$(document).ready(function() {
    // Cancel leave request
    $('.cancel-leave').click(function() {
        $('#cancelModal').modal('show');
    });

    $('#confirmCancel').click(function() {
        const reason = $('#cancellation_reason').val();
        if (!reason) {
            alert('Please provide a reason for cancellation');
            return;
        }

        $.ajax({
            url: '{% url "attendance:leave_request_cancel" pk=leave.id %}',
            type: 'POST',
            data: { reason: reason },
            headers: {
                'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
            },
            success: function() {
                window.location.reload();
            },
            error: function(xhr) {
                alert('Error cancelling leave request');
            }
        });
        $('#cancelModal').modal('hide');
    });

    // Approve leave request
    $('.approve-leave').click(function() {
        $('#approveModal').modal('show');
    });

    $('#confirmApprove').click(function() {
        const remarks = $('#approval_remarks').val();
        $.ajax({
            url: '{% url "attendance:leave_request_approve" pk=leave.id %}',
            type: 'POST',
            data: { remarks: remarks },
            headers: {
                'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
            },
            success: function() {
                window.location.reload();
            },
            error: function(xhr) {
                alert('Error approving leave request');
            }
        });
        $('#approveModal').modal('hide');
    });

    // Reject leave request
    $('.reject-leave').click(function() {
        $('#rejectModal').modal('show');
    });

    $('#confirmReject').click(function() {
        const reason = $('#rejection_reason').val();
        if (!reason) {
            alert('Please provide a reason for rejection');
            return;
        }

        $.ajax({
            url: '{% url "attendance:leave_request_reject" pk=leave.id %}',
            type: 'POST',
            data: { reason: reason },
            headers: {
                'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
            },
            success: function() {
                window.location.reload();
            },
            error: function(xhr) {
                alert('Error rejecting leave request');
            }
        });
        $('#rejectModal').modal('hide');
    });
});
</script>
{% endblock %}

```

### hrms_project\attendance\templates\attendance\leave_form.html
```
{% extends 'attendance/base.html' %}
{% load static %}

{% block attendance_content %}
<div class="card">
    <div class="card-header">
        <h5 class="mb-0">Apply for Leave</h5>
    </div>
    <div class="card-body">
        <!-- Leave Balance Summary -->
        <div class="card bg-light mb-4">
            <div class="card-body">
                <h6 class="card-title">Your Leave Balances</h6>
                <div class="row">
                    {% for balance in leave_balances %}
                    <div class="col-md-3 mb-2">
                        <div class="d-flex justify-content-between">
                            <span>{{ balance.leave_type.name }}:</span>
                            <strong>{{ balance.available_days }} days</strong>
                        </div>
                        {% if balance.pending_days > 0 %}
                        <small class="text-muted">
                            ({{ balance.pending_days }} days pending approval)
                        </small>
                        {% endif %}
                    </div>
                    {% endfor %}
                </div>
            </div>
        </div>

        <form method="post" enctype="multipart/form-data" class="needs-validation" novalidate>
            {% csrf_token %}
            
            {% if form.non_field_errors %}
            <div class="alert alert-danger">
                {% for error in form.non_field_errors %}
                {{ error }}
                {% endfor %}
            </div>
            {% endif %}

            <!-- Leave Type Selection -->
            <div class="mb-3">
                <label for="leave_type" class="form-label">Leave Type *</label>
                <select class="form-select {% if form.leave_type.errors %}is-invalid{% endif %}" 
                        id="leave_type" 
                        name="leave_type"
                        required>
                    <option value="">Select Leave Type</option>
                    {% for type in leave_types %}
                    <option value="{{ type.id }}" 
                            data-requires-document="{{ type.requires_document|yesno:'true,false' }}"
                            data-balance="{{ type.balance }}"
                            data-gender-specific="{{ type.gender_specific }}"
                            {% if type.id == form.leave_type.value|stringformat:'i' %}selected{% endif %}>
                        {{ type.name }}
                        {% if type.balance %}({{ type.balance }} days available){% endif %}
                    </option>
                    {% endfor %}
                </select>
                {% if form.leave_type.errors %}
                <div class="invalid-feedback">
                    {{ form.leave_type.errors|join:", " }}
                </div>
                {% endif %}
                <div id="leave-type-info" class="form-text mt-1"></div>
            </div>

            <!-- Date Range -->
            <div class="row">
                <div class="col-md-6 mb-3">
                    <label for="start_date" class="form-label">Start Date *</label>
                    <input type="date" 
                           class="form-control {% if form.start_date.errors %}is-invalid{% endif %}" 
                           id="start_date" 
                           name="start_date"
                           value="{{ form.start_date.value|date:'Y-m-d'|default:'' }}"
                           required>
                    {% if form.start_date.errors %}
                    <div class="invalid-feedback">
                        {{ form.start_date.errors|join:", " }}
                    </div>
                    {% endif %}
                    <div class="form-check mt-2">
                        <input type="checkbox" 
                               class="form-check-input" 
                               id="start_half" 
                               name="start_half"
                               {% if form.start_half.value %}checked{% endif %}>
                        <label class="form-check-label" for="start_half">
                            Half Day (Morning)
                        </label>
                    </div>
                </div>
                <div class="col-md-6 mb-3">
                    <label for="end_date" class="form-label">End Date *</label>
                    <input type="date" 
                           class="form-control {% if form.end_date.errors %}is-invalid{% endif %}" 
                           id="end_date" 
                           name="end_date"
                           value="{{ form.end_date.value|date:'Y-m-d'|default:'' }}"
                           required>
                    {% if form.end_date.errors %}
                    <div class="invalid-feedback">
                        {{ form.end_date.errors|join:", " }}
                    </div>
                    {% endif %}
                    <div class="form-check mt-2">
                        <input type="checkbox" 
                               class="form-check-input" 
                               id="end_half" 
                               name="end_half"
                               {% if form.end_half.value %}checked{% endif %}>
                        <label class="form-check-label" for="end_half">
                            Half Day (Afternoon)
                        </label>
                    </div>
                </div>
            </div>

            <!-- Duration Summary -->
            <div class="mb-3">
                <div class="alert alert-info" id="duration-info">
                    Please select dates to see leave duration
                </div>
            </div>

            <!-- Reason -->
            <div class="mb-3">
                <label for="reason" class="form-label">Reason *</label>
                <textarea class="form-control {% if form.reason.errors %}is-invalid{% endif %}" 
                          id="reason" 
                          name="reason" 
                          rows="3"
                          required>{{ form.reason.value|default:'' }}</textarea>
                {% if form.reason.errors %}
                <div class="invalid-feedback">
                    {{ form.reason.errors|join:", " }}
                </div>
                {% endif %}
            </div>

            <!-- Documents -->
            <div id="document-section" class="mb-3" style="display: none;">
                <label class="form-label">Supporting Documents</label>
                <div class="input-group">
                    <input type="file" 
                           class="form-control {% if form.documents.errors %}is-invalid{% endif %}" 
                           id="documents" 
                           name="documents"
                           multiple
                           accept=".pdf,.jpg,.jpeg,.png">
                    <label class="input-group-text" for="documents">Upload</label>
                </div>
                {% if form.documents.errors %}
                <div class="invalid-feedback d-block">
                    {{ form.documents.errors|join:", " }}
                </div>
                {% endif %}
                <div class="form-text">
                    Supported formats: PDF, JPG, PNG. Maximum file size: 5MB
                </div>
            </div>

            <!-- Submit Buttons -->
            <div class="mt-4">
                <button type="submit" class="btn btn-primary" id="submit-btn">Submit Leave Request</button>
                <a href="{% url 'attendance:leave_request_list' %}" class="btn btn-secondary">Cancel</a>
            </div>
        </form>
    </div>
</div>
{% endblock %}

{% block extra_js %}
{{ block.super }}
<script>
$(document).ready(function() {
    // Handle leave type change
    $('#leave_type').change(function() {
        const selected = $(this).find('option:selected');
        const requiresDocument = selected.data('requires-document');
        const genderSpecific = selected.data('gender-specific');
        const balance = selected.data('balance');
        
        // Show/hide document section
        if (requiresDocument) {
            $('#document-section').slideDown();
            $('#documents').prop('required', true);
        } else {
            $('#document-section').slideUp();
            $('#documents').prop('required', false);
        }
        
        // Update info text
        let infoText = [];
        if (balance !== undefined) {
            infoText.push(`Available balance: ${balance} days`);
        }
        if (requiresDocument) {
            infoText.push('Supporting documents required');
        }
        if (genderSpecific && genderSpecific !== 'A') {
            infoText.push(`Only available for ${genderSpecific === 'M' ? 'male' : 'female'} employees`);
        }
        
        $('#leave-type-info').html(infoText.join(' • '));
    });

    // Calculate duration
    function calculateDuration() {
        const startDate = $('#start_date').val();
        const endDate = $('#end_date').val();
        const startHalf = $('#start_half').prop('checked');
        const endHalf = $('#end_half').prop('checked');
        
        if (startDate && endDate) {
            $.ajax({
                url: '{% url "attendance:calculate_leave_duration" %}',
                data: {
                    start_date: startDate,
                    end_date: endDate,
                    start_half: startHalf,
                    end_half: endHalf
                },
                success: function(response) {
                    $('#duration-info').html(
                        `Leave duration: ${response.days} day${response.days !== 1 ? 's' : ''}<br>` +
                        `Working days: ${response.working_days} day${response.working_days !== 1 ? 's' : ''}`
                    );
                }
            });
        }
    }

    $('#start_date, #end_date, #start_half, #end_half').on('change', calculateDuration);

    // Validate end date not before start date
    $('#end_date').change(function() {
        const startDate = new Date($('#start_date').val());
        const endDate = new Date($(this).val());
        
        if (endDate < startDate) {
            alert('End date cannot be before start date');
            $(this).val($('#start_date').val());
        }
    });

    // Form validation
    (function() {
        'use strict';
        var forms = document.querySelectorAll('.needs-validation');
        Array.prototype.slice.call(forms).forEach(function(form) {
            form.addEventListener('submit', function(event) {
                if (!form.checkValidity()) {
                    event.preventDefault();
                    event.stopPropagation();
                }
                form.classList.add('was-validated');
            }, false);
        });
    })();

    // Initialize leave type info if type is pre-selected
    $('#leave_type').trigger('change');
});
</script>
{% endblock %}

```

### hrms_project\attendance\templates\attendance\leave_list.html
```
{% extends 'attendance/base.html' %}
{% load static %}

{% block attendance_content %}
<div class="card">
    <div class="card-header d-flex justify-content-between align-items-center">
        <h5 class="mb-0">Leave Requests</h5>
        <div>
            <a href="{% url 'attendance:leave_request_create' %}" class="btn btn-primary">
                <i class="fas fa-plus"></i> Apply for Leave
            </a>
        </div>
    </div>
    <div class="card-body">
        <!-- Filters -->
        <div class="row mb-4">
            <div class="col-md-3">
                <label class="form-label">Status</label>
                <select class="form-select" id="status-filter">
                    <option value="">All Status</option>
                    <option value="pending">Pending</option>
                    <option value="approved">Approved</option>
                    <option value="rejected">Rejected</option>
                    <option value="cancelled">Cancelled</option>
                </select>
            </div>
            <div class="col-md-3">
                <label class="form-label">Leave Type</label>
                <select class="form-select" id="type-filter">
                    <option value="">All Types</option>
                    {% for type in leave_types %}
                    <option value="{{ type.code }}">{{ type.name }}</option>
                    {% endfor %}
                </select>
            </div>
            <div class="col-md-3">
                <label class="form-label">Department</label>
                <select class="form-select" id="department-filter">
                    <option value="">All Departments</option>
                    {% for dept in departments %}
                    <option value="{{ dept.id }}">{{ dept.name }}</option>
                    {% endfor %}
                </select>
            </div>
            <div class="col-md-3 d-flex align-items-end">
                <button class="btn btn-primary" id="apply-filters">Apply Filters</button>
            </div>
        </div>

        <!-- Leave Balance Summary -->
        {% if user_leave_balances %}
        <div class="row mb-4">
            <div class="col-12">
                <div class="card bg-light">
                    <div class="card-body">
                        <h6 class="card-title">Your Leave Balances</h6>
                        <div class="row">
                            {% for balance in user_leave_balances %}
                            <div class="col-md-3 mb-2">
                                <div class="d-flex justify-content-between">
                                    <span>{{ balance.leave_type.name }}:</span>
                                    <strong>{{ balance.available_days }} days</strong>
                                </div>
                                {% if balance.pending_days > 0 %}
                                <small class="text-muted">
                                    ({{ balance.pending_days }} days pending approval)
                                </small>
                                {% endif %}
                            </div>
                            {% endfor %}
                        </div>
                    </div>
                </div>
            </div>
        </div>
        {% endif %}

        <!-- Leave Requests Table -->
        <div class="table-responsive">
            <table class="table table-hover">
                <thead>
                    <tr>
                        <th>Employee</th>
                        <th>Leave Type</th>
                        <th>Duration</th>
                        <th>Status</th>
                        <th>Submitted</th>
                        <th>Actions</th>
                    </tr>
                </thead>
                <tbody>
                    {% for leave in leaves %}
                    <tr>
                        <td>
                            {{ leave.employee.get_full_name }}
                            <br>
                            <small class="text-muted">{{ leave.employee.department.name }}</small>
                        </td>
                        <td>
                            {{ leave.leave_type.name }}
                            {% if leave.start_half or leave.end_half %}
                            <br>
                            <small class="text-muted">
                                {% if leave.start_half %}Start: Half Day{% endif %}
                                {% if leave.end_half %}End: Half Day{% endif %}
                            </small>
                            {% endif %}
                        </td>
                        <td>
                            {{ leave.duration }} days
                            <br>
                            <small class="text-muted">
                                {{ leave.start_date|date:"M d, Y" }} - {{ leave.end_date|date:"M d, Y" }}
                            </small>
                        </td>
                        <td>
                            {% if leave.status == 'pending' %}
                            <span class="badge bg-warning">Pending</span>
                            {% elif leave.status == 'approved' %}
                            <span class="badge bg-success">Approved</span>
                            {% elif leave.status == 'rejected' %}
                            <span class="badge bg-danger">Rejected</span>
                            {% else %}
                            <span class="badge bg-secondary">Cancelled</span>
                            {% endif %}
                        </td>
                        <td>
                            {{ leave.created_at|date:"M d, Y" }}
                            <br>
                            <small class="text-muted">{{ leave.created_at|time:"H:i" }}</small>
                        </td>
                        <td>
                            <a href="{% url 'attendance:leave_request_detail' pk=leave.id %}" 
                               class="btn btn-sm btn-info">
                                <i class="fas fa-eye"></i>
                            </a>
                            {% if leave.status == 'pending' and leave.employee == user.employee %}
                            <button class="btn btn-sm btn-danger cancel-leave" data-id="{{ leave.id }}">
                                <i class="fas fa-times"></i>
                            </button>
                            {% endif %}
                            {% if perms.attendance.can_approve_leave and leave.status == 'pending' %}
                            <button class="btn btn-sm btn-success approve-leave" data-id="{{ leave.id }}">
                                <i class="fas fa-check"></i>
                            </button>
                            <button class="btn btn-sm btn-danger reject-leave" data-id="{{ leave.id }}">
                                <i class="fas fa-times"></i>
                            </button>
                            {% endif %}
                        </td>
                    </tr>
                    {% empty %}
                    <tr>
                        <td colspan="6" class="text-center">No leave requests found</td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>

        <!-- Pagination -->
        {% if is_paginated %}
        <nav aria-label="Page navigation" class="mt-4">
            <ul class="pagination justify-content-center">
                {% if page_obj.has_previous %}
                <li class="page-item">
                    <a class="page-link" href="?page=1">&laquo; First</a>
                </li>
                <li class="page-item">
                    <a class="page-link" href="?page={{ page_obj.previous_page_number }}">Previous</a>
                </li>
                {% endif %}

                {% for num in page_obj.paginator.page_range %}
                    {% if page_obj.number == num %}
                    <li class="page-item active">
                        <span class="page-link">{{ num }}</span>
                    </li>
                    {% elif num > page_obj.number|add:'-3' and num < page_obj.number|add:'3' %}
                    <li class="page-item">
                        <a class="page-link" href="?page={{ num }}">{{ num }}</a>
                    </li>
                    {% endif %}
                {% endfor %}

                {% if page_obj.has_next %}
                <li class="page-item">
                    <a class="page-link" href="?page={{ page_obj.next_page_number }}">Next</a>
                </li>
                <li class="page-item">
                    <a class="page-link" href="?page={{ page_obj.paginator.num_pages }}">Last &raquo;</a>
                </li>
                {% endif %}
            </ul>
        </nav>
        {% endif %}
    </div>
</div>

<!-- Action Modals -->
<!-- Cancel Leave Modal -->
<div class="modal fade" id="cancelModal" tabindex="-1">
    <div class="modal-dialog">
        <div class="modal-content">
            <div class="modal-header">
                <h5 class="modal-title">Cancel Leave Request</h5>
                <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
            </div>
            <div class="modal-body">
                <form id="cancelForm">
                    <div class="mb-3">
                        <label for="cancellation_reason" class="form-label">Reason for Cancellation</label>
                        <textarea class="form-control" id="cancellation_reason" rows="3" required></textarea>
                    </div>
                </form>
            </div>
            <div class="modal-footer">
                <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Close</button>
                <button type="button" class="btn btn-danger" id="confirmCancel">Cancel Leave</button>
            </div>
        </div>
    </div>
</div>

<!-- Approve Leave Modal -->
<div class="modal fade" id="approveModal" tabindex="-1">
    <div class="modal-dialog">
        <div class="modal-content">
            <div class="modal-header">
                <h5 class="modal-title">Approve Leave Request</h5>
                <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
            </div>
            <div class="modal-body">
                <form id="approveForm">
                    <div class="mb-3">
                        <label for="approval_remarks" class="form-label">Remarks (Optional)</label>
                        <textarea class="form-control" id="approval_remarks" rows="3"></textarea>
                    </div>
                </form>
            </div>
            <div class="modal-footer">
                <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Close</button>
                <button type="button" class="btn btn-success" id="confirmApprove">Approve</button>
            </div>
        </div>
    </div>
</div>

<!-- Reject Leave Modal -->
<div class="modal fade" id="rejectModal" tabindex="-1">
    <div class="modal-dialog">
        <div class="modal-content">
            <div class="modal-header">
                <h5 class="modal-title">Reject Leave Request</h5>
                <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
            </div>
            <div class="modal-body">
                <form id="rejectForm">
                    <div class="mb-3">
                        <label for="rejection_reason" class="form-label">Reason for Rejection</label>
                        <textarea class="form-control" id="rejection_reason" rows="3" required></textarea>
                    </div>
                </form>
            </div>
            <div class="modal-footer">
                <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Close</button>
                <button type="button" class="btn btn-danger" id="confirmReject">Reject</button>
            </div>
        </div>
    </div>
</div>

{% endblock %}

{% block extra_js %}
{{ block.super }}
<script>
$(document).ready(function() {
    let currentLeaveId = null;

    // Cancel leave request
    $('.cancel-leave').click(function() {
        currentLeaveId = $(this).data('id');
        $('#cancelModal').modal('show');
    });

    $('#confirmCancel').click(function() {
        const reason = $('#cancellation_reason').val();
        if (!reason) {
            alert('Please provide a reason for cancellation');
            return;
        }

        $.ajax({
            url: `/attendance/leave/${currentLeaveId}/cancel/`,
            type: 'POST',
            data: { reason: reason },
            headers: {
                'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
            },
            success: function() {
                location.reload();
            },
            error: function(xhr) {
                alert('Error cancelling leave request');
            }
        });
        $('#cancelModal').modal('hide');
    });

    // Approve leave request
    $('.approve-leave').click(function() {
        currentLeaveId = $(this).data('id');
        $('#approveModal').modal('show');
    });

    $('#confirmApprove').click(function() {
        const remarks = $('#approval_remarks').val();
        $.ajax({
            url: `/attendance/leave/${currentLeaveId}/approve/`,
            type: 'POST',
            data: { remarks: remarks },
            headers: {
                'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
            },
            success: function() {
                location.reload();
            },
            error: function(xhr) {
                alert('Error approving leave request');
            }
        });
        $('#approveModal').modal('hide');
    });

    // Reject leave request
    $('.reject-leave').click(function() {
        currentLeaveId = $(this).data('id');
        $('#rejectModal').modal('show');
    });

    $('#confirmReject').click(function() {
        const reason = $('#rejection_reason').val();
        if (!reason) {
            alert('Please provide a reason for rejection');
            return;
        }

        $.ajax({
            url: `/attendance/leave/${currentLeaveId}/reject/`,
            type: 'POST',
            data: { reason: reason },
            headers: {
                'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
            },
            success: function() {
                location.reload();
            },
            error: function(xhr) {
                alert('Error rejecting leave request');
            }
        });
        $('#rejectModal').modal('hide');
    });

    // Apply filters
    $('#apply-filters').click(function() {
        const status = $('#status-filter').val();
        const type = $('#type-filter').val();
        const department = $('#department-filter').val();
        
        window.location.href = `?status=${status}&type=${type}&department=${department}`;
    });
});
</script>
{% endblock %}

```

### hrms_project\attendance\templates\attendance\leave_request_detail.html
```
{% extends 'attendance/base.html' %}
{% load static %}

{% block attendance_content %}
<div class="card">
    <div class="card-header">
        <div class="row align-items-center">
            <div class="col">
                <h5 class="mb-0">Leave Request Details</h5>
            </div>
            <div class="col-auto">
                <a href="{% url 'attendance:leave_request_list' %}" class="btn btn-secondary">
                    <i class="fas fa-arrow-left"></i> Back to List
                </a>
            </div>
        </div>
    </div>
    <div class="card-body">
        <div class="row">
            <!-- Employee Information -->
            <div class="col-md-6">
                <div class="card mb-3">
                    <div class="card-header">
                        <h6 class="mb-0">Employee Information</h6>
                    </div>
                    <div class="card-body">
                        <div class="row mb-2">
                            <div class="col-sm-4 text-muted">Employee ID:</div>
                            <div class="col-sm-8">{{ leave.employee.employee_number }}</div>
                        </div>
                        <div class="row mb-2">
                            <div class="col-sm-4 text-muted">Name:</div>
                            <div class="col-sm-8">{{ leave.employee.get_full_name }}</div>
                        </div>
                        <div class="row mb-2">
                            <div class="col-sm-4 text-muted">Department:</div>
                            <div class="col-sm-8">{{ leave.employee.department.name }}</div>
                        </div>
                        <div class="row mb-2">
                            <div class="col-sm-4 text-muted">Position:</div>
                            <div class="col-sm-8">{{ leave.employee.designation }}</div>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Leave Balance -->
            <div class="col-md-6">
                <div class="card mb-3">
                    <div class="card-header">
                        <h6 class="mb-0">Leave Balance</h6>
                    </div>
                    <div class="card-body">
                        <div class="row g-3">
                            <div class="col-sm-4">
                                <div class="border rounded p-2 text-center">
                                    <small class="text-muted d-block">Annual Leave</small>
                                    <strong class="d-block" id="annual-balance">{{ balance.annual.remaining }}</strong>
                                    <small class="text-muted">remaining</small>
                                </div>
                            </div>
                            <div class="col-sm-4">
                                <div class="border rounded p-2 text-center">
                                    <small class="text-muted d-block">Sick Leave</small>
                                    <strong class="d-block" id="sick-balance">{{ balance.sick.remaining }}</strong>
                                    <small class="text-muted">remaining</small>
                                </div>
                            </div>
                            <div class="col-sm-4">
                                <div class="border rounded p-2 text-center">
                                    <small class="text-muted d-block">Permission</small>
                                    <strong class="d-block" id="permission-balance">{{ balance.permission.remaining }}</strong>
                                    <small class="text-muted">hours</small>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <!-- Leave Request Details -->
        <div class="card mb-3">
            <div class="card-header">
                <h6 class="mb-0">Leave Details</h6>
            </div>
            <div class="card-body">
                <div class="row">
                    <div class="col-md-6">
                        <div class="row mb-2">
                            <div class="col-sm-4 text-muted">Leave Type:</div>
                            <div class="col-sm-8">
                                <span class="badge bg-info">{{ leave.get_leave_type_display }}</span>
                            </div>
                        </div>
                        <div class="row mb-2">
                            <div class="col-sm-4 text-muted">Duration:</div>
                            <div class="col-sm-8">{{ leave.start_date|date:"M d, Y" }} - {{ leave.end_date|date:"M d, Y" }}</div>
                        </div>
                        <div class="row mb-2">
                            <div class="col-sm-4 text-muted">Total Days:</div>
                            <div class="col-sm-8">{{ leave.duration }} days</div>
                        </div>
                        <div class="row mb-2">
                            <div class="col-sm-4 text-muted">Status:</div>
                            <div class="col-sm-8">
                                <span class="badge bg-{{ leave.status|lower }}">
                                    {{ leave.get_status_display }}
                                </span>
                            </div>
                        </div>
                    </div>
                    <div class="col-md-6">
                        <div class="row mb-2">
                            <div class="col-sm-4 text-muted">Submitted On:</div>
                            <div class="col-sm-8">{{ leave.created_at|date:"M d, Y H:i" }}</div>
                        </div>
                        <div class="row mb-2">
                            <div class="col-sm-4 text-muted">Last Updated:</div>
                            <div class="col-sm-8">{{ leave.updated_at|date:"M d, Y H:i" }}</div>
                        </div>
                        <div class="row mb-2">
                            <div class="col-sm-4 text-muted">Approved By:</div>
                            <div class="col-sm-8">
                                {% if leave.approved_by %}
                                    {{ leave.approved_by.get_full_name }}
                                {% else %}
                                    -
                                {% endif %}
                            </div>
                        </div>
                    </div>
                </div>

                {% if leave.remarks %}
                <div class="mt-3">
                    <h6 class="text-muted">Remarks</h6>
                    <p class="mb-0">{{ leave.remarks }}</p>
                </div>
                {% endif %}

                {% if leave.attachment %}
                <div class="mt-3">
                    <h6 class="text-muted">Attachment</h6>
                    <a href="{{ leave.attachment.url }}" class="btn btn-sm btn-outline-primary" target="_blank">
                        <i class="fas fa-paperclip"></i> View Attachment
                    </a>
                </div>
                {% endif %}
            </div>
        </div>

        <!-- Approval Actions -->
        {% if leave.status == 'pending' and perms.attendance.can_approve_leave %}
        <div class="card">
            <div class="card-header">
                <h6 class="mb-0">Approval Action</h6>
            </div>
            <div class="card-body">
                <form id="approval-form" class="row g-3">
                    <div class="col-12">
                        <label for="approval-remarks" class="form-label">Remarks</label>
                        <textarea class="form-control" id="approval-remarks" rows="3"></textarea>
                    </div>
                    <div class="col-12">
                        <button type="button" class="btn btn-success me-2" onclick="updateLeaveStatus('approved')">
                            <i class="fas fa-check"></i> Approve
                        </button>
                        <button type="button" class="btn btn-danger" onclick="updateLeaveStatus('rejected')">
                            <i class="fas fa-times"></i> Reject
                        </button>
                    </div>
                </form>
            </div>
        </div>
        {% endif %}
    </div>
</div>
{% endblock %}

{% block footer_scripts %}
{{ block.super }}
<script>
function updateLeaveStatus(status) {
    const remarks = document.getElementById('approval-remarks').value;
    
    fetch(`/api/attendance/leaves/{{ leave.id }}/`, {
        method: 'PATCH',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken')
        },
        body: JSON.stringify({
            status: status,
            remarks: remarks
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            throw new Error(data.error);
        }
        window.location.reload();
    })
    .catch(error => {
        alert('Error updating leave status: ' + error.message);
    });
}

function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}
</script>
{% endblock %}
```

### hrms_project\attendance\templates\attendance\leave_request_list.html
```
{% extends 'attendance/base.html' %}
{% load static %}

{% block attendance_content %}
<div class="card">
    <div class="card-header">
        <div class="row align-items-center">
            <div class="col">
                <h5 class="mb-0">Leave Requests</h5>
            </div>
            <div class="col-auto">
                <button type="button" class="btn btn-primary" data-bs-toggle="modal" data-bs-target="#newLeaveModal">
                    <i class="fas fa-plus"></i> New Leave Request
                </button>
            </div>
        </div>
    </div>
    <div class="card-body">
        <!-- Filters -->
        <div class="row mb-3">
            <div class="col-md-3">
                <label class="form-label">Date Range</label>
                <div class="input-group">
                    <input type="date" class="form-control" id="start-date">
                    <span class="input-group-text">to</span>
                    <input type="date" class="form-control" id="end-date">
                </div>
            </div>
            <div class="col-md-3">
                <label class="form-label">Leave Type</label>
                <select class="form-select" id="type-filter">
                    <option value="">All Types</option>
                    <option value="annual">Annual Leave</option>
                    <option value="sick">Sick Leave</option>
                    <option value="permission">Permission</option>
                </select>
            </div>
            <div class="col-md-3">
                <label class="form-label">Status</label>
                <select class="form-select" id="status-filter">
                    <option value="">All Status</option>
                    <option value="pending">Pending</option>
                    <option value="approved">Approved</option>
                    <option value="rejected">Rejected</option>
                </select>
            </div>
            <div class="col-md-3">
                <label class="form-label">Search</label>
                <input type="text" class="form-control" id="search-input" placeholder="Search employees...">
            </div>
        </div>

        <!-- Leave Balance Summary -->
        <div class="row mb-3">
            <div class="col-md-4">
                <div class="card">
                    <div class="card-body">
                        <h6 class="card-title">Annual Leave Balance</h6>
                        <div class="d-flex justify-content-between align-items-center">
                            <h3 class="mb-0" id="annual-balance">0</h3>
                            <small class="text-muted">days remaining</small>
                        </div>
                        <div class="progress mt-2" style="height: 5px;">
                            <div class="progress-bar bg-success" id="annual-progress" style="width: 0%"></div>
                        </div>
                    </div>
                </div>
            </div>
            <div class="col-md-4">
                <div class="card">
                    <div class="card-body">
                        <h6 class="card-title">Sick Leave Balance</h6>
                        <div class="d-flex justify-content-between align-items-center">
                            <h3 class="mb-0" id="sick-balance">0</h3>
                            <small class="text-muted">days remaining</small>
                        </div>
                        <div class="progress mt-2" style="height: 5px;">
                            <div class="progress-bar bg-info" id="sick-progress" style="width: 0%"></div>
                        </div>
                    </div>
                </div>
            </div>
            <div class="col-md-4">
                <div class="card">
                    <div class="card-body">
                        <h6 class="card-title">Permission Hours</h6>
                        <div class="d-flex justify-content-between align-items-center">
                            <h3 class="mb-0" id="permission-balance">0</h3>
                            <small class="text-muted">hours remaining</small>
                        </div>
                        <div class="progress mt-2" style="height: 5px;">
                            <div class="progress-bar bg-warning" id="permission-progress" style="width: 0%"></div>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <!-- Leave Requests Table -->
        <div class="table-responsive">
            <table class="table table-striped table-hover" id="leave-table">
                <thead>
                    <tr>
                        <th>Employee</th>
                        <th>Leave Type</th>
                        <th>Start Date</th>
                        <th>End Date</th>
                        <th>Duration</th>
                        <th>Status</th>
                        <th>Approved By</th>
                        <th>Actions</th>
                    </tr>
                </thead>
                <tbody>
                    <!-- Data will be loaded dynamically -->
                </tbody>
            </table>
        </div>

        <!-- Pagination -->
        <nav aria-label="Page navigation" class="mt-3">
            <ul class="pagination justify-content-center" id="pagination">
                <!-- Pagination will be generated dynamically -->
            </ul>
        </nav>
    </div>
</div>

<!-- New Leave Request Modal -->
<div class="modal fade" id="newLeaveModal" tabindex="-1">
    <div class="modal-dialog">
        <div class="modal-content">
            <div class="modal-header">
                <h5 class="modal-title">New Leave Request</h5>
                <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
            </div>
            <div class="modal-body">
                <form id="leave-form">
                    <div class="mb-3">
                        <label class="form-label">Leave Type</label>
                        <select class="form-select" id="leave-type" required>
                            <option value="">Select Type</option>
                            <option value="annual">Annual Leave</option>
                            <option value="sick">Sick Leave</option>
                            <option value="permission">Permission</option>
                        </select>
                    </div>
                    <div class="mb-3">
                        <label class="form-label">Start Date</label>
                        <input type="date" class="form-control" id="leave-start" required>
                    </div>
                    <div class="mb-3">
                        <label class="form-label">End Date</label>
                        <input type="date" class="form-control" id="leave-end" required>
                    </div>
                    <div class="mb-3">
                        <label class="form-label">Remarks</label>
                        <textarea class="form-control" id="leave-remarks" rows="3"></textarea>
                    </div>
                    <div class="mb-3">
                        <label class="form-label">Attachment</label>
                        <input type="file" class="form-control" id="leave-attachment">
                    </div>
                </form>
            </div>
            <div class="modal-footer">
                <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
                <button type="button" class="btn btn-primary" id="submit-leave">Submit Request</button>
            </div>
        </div>
    </div>
</div>

{% endblock %}

{% block footer_scripts %}
{{ block.super }}
<script>
document.addEventListener('DOMContentLoaded', function() {
    // Set default date range to current month
    const now = new Date();
    const firstDay = new Date(now.getFullYear(), now.getMonth(), 1);
    const lastDay = new Date(now.getFullYear(), now.getMonth() + 1, 0);
    
    document.getElementById('start-date').value = firstDay.toISOString().split('T')[0];
    document.getElementById('end-date').value = lastDay.toISOString().split('T')[0];

    // Load initial data
    loadLeaveRequests();
    loadLeaveBalance();

    // Event listeners for filters
    document.getElementById('start-date').addEventListener('change', loadLeaveRequests);
    document.getElementById('end-date').addEventListener('change', loadLeaveRequests);
    document.getElementById('type-filter').addEventListener('change', loadLeaveRequests);
    document.getElementById('status-filter').addEventListener('change', loadLeaveRequests);
    
    let searchTimeout;
    document.getElementById('search-input').addEventListener('input', function() {
        clearTimeout(searchTimeout);
        searchTimeout = setTimeout(loadLeaveRequests, 500);
    });

    // Submit new leave request
    document.getElementById('submit-leave').addEventListener('click', submitLeaveRequest);
});

function loadLeaveRequests(page = 1) {
    const params = new URLSearchParams({
        start_date: document.getElementById('start-date').value,
        end_date: document.getElementById('end-date').value,
        type: document.getElementById('type-filter').value,
        status: document.getElementById('status-filter').value,
        search: document.getElementById('search-input').value,
        page: page
    });

    fetch(`/api/attendance/leaves/?${params}`)
        .then(response => response.json())
        .then(data => {
            updateLeaveTable(data.results);
            updatePagination(data.total_pages, data.current_page);
        })
        .catch(error => console.error('Error:', error));
}

function loadLeaveBalance() {
    fetch('/api/attendance/leave-balance/')
        .then(response => response.json())
        .then(data => {
            updateBalanceCards(data);
        })
        .catch(error => console.error('Error:', error));
}

function updateLeaveTable(leaves) {
    const tbody = document.querySelector('#leave-table tbody');
    tbody.innerHTML = leaves.map(leave => `
        <tr>
            <td>${leave.employee_name}</td>
            <td>${formatLeaveType(leave.leave_type)}</td>
            <td>${leave.start_date}</td>
            <td>${leave.end_date}</td>
            <td>${leave.duration} days</td>
            <td>
                <span class="badge bg-${getStatusBadgeClass(leave.status)}">
                    ${leave.status}
                </span>
            </td>
            <td>${leave.approved_by || '-'}</td>
            <td>
                ${getActionButtons(leave)}
            </td>
        </tr>
    `).join('');
}

function updateBalanceCards(balance) {
    // Annual Leave
    document.getElementById('annual-balance').textContent = balance.annual.remaining;
    document.getElementById('annual-progress').style.width = 
        `${(balance.annual.remaining / balance.annual.total) * 100}%`;

    // Sick Leave
    document.getElementById('sick-balance').textContent = balance.sick.remaining;
    document.getElementById('sick-progress').style.width = 
        `${(balance.sick.remaining / balance.sick.total) * 100}%`;

    // Permission Hours
    document.getElementById('permission-balance').textContent = balance.permission.remaining;
    document.getElementById('permission-progress').style.width = 
        `${(balance.permission.remaining / balance.permission.total) * 100}%`;
}

function submitLeaveRequest() {
    const formData = new FormData();
    formData.append('leave_type', document.getElementById('leave-type').value);
    formData.append('start_date', document.getElementById('leave-start').value);
    formData.append('end_date', document.getElementById('leave-end').value);
    formData.append('remarks', document.getElementById('leave-remarks').value);
    
    const attachment = document.getElementById('leave-attachment').files[0];
    if (attachment) {
        formData.append('attachment', attachment);
    }

    fetch('/api/attendance/leaves/', {
        method: 'POST',
        body: formData,
        headers: {
            'X-CSRFToken': getCookie('csrftoken')
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            throw new Error(data.error);
        }
        bootstrap.Modal.getInstance(document.getElementById('newLeaveModal')).hide();
        loadLeaveRequests();
        loadLeaveBalance();
        alert('Leave request submitted successfully');
    })
    .catch(error => {
        alert('Error submitting leave request: ' + error.message);
    });
}

// Helper functions
function formatLeaveType(type) {
    return type.charAt(0).toUpperCase() + type.slice(1) + ' Leave';
}

function getStatusBadgeClass(status) {
    const classes = {
        'pending': 'warning',
        'approved': 'success',
        'rejected': 'danger'
    };
    return classes[status] || 'secondary';
}

function getActionButtons(leave) {
    if (leave.status === 'pending') {
        return `
            <button class="btn btn-sm btn-success" onclick="updateLeaveStatus(${leave.id}, 'approved')">
                <i class="fas fa-check"></i>
            </button>
            <button class="btn btn-sm btn-danger" onclick="updateLeaveStatus(${leave.id}, 'rejected')">
                <i class="fas fa-times"></i>
            </button>
        `;
    }
    return `
        <button class="btn btn-sm btn-primary" onclick="viewLeaveDetails(${leave.id})">
            <i class="fas fa-eye"></i>
        </button>
    `;
}

function updateLeaveStatus(id, status) {
    fetch(`/api/attendance/leaves/${id}/`, {
        method: 'PATCH',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken')
        },
        body: JSON.stringify({ status })
    })
    .then(response => response.json())
    .then(() => {
        loadLeaveRequests();
        loadLeaveBalance();
    })
    .catch(error => console.error('Error:', error));
}

function viewLeaveDetails(id) {
    // Implement leave details view
    window.location.href = `/attendance/leave/${id}/`;
}

function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}
</script>
{% endblock %}
```

### hrms_project\attendance\templates\attendance\leave_types.html
```
{% extends 'attendance/base.html' %}
{% load static %}

{% block attendance_content %}
<div class="card">
    <div class="card-header d-flex justify-content-between align-items-center">
        <h5 class="card-title mb-0">
            <i class="fas fa-tags"></i> Leave Types
        </h5>
        {% if perms.attendance.add_leavetype %}
        <button type="button" class="btn btn-primary btn-sm" data-bs-toggle="modal" data-bs-target="#addLeaveTypeModal">
            <i class="fas fa-plus"></i> Add Leave Type
        </button>
        {% endif %}
    </div>
    <div class="card-body">
        <div class="table-responsive">
            <table class="table table-striped table-hover">
                <thead>
                    <tr>
                        <th>Name</th>
                        <th>Code</th>
                        <th>Category</th>
                        <th>Days Allowed</th>
                        <th>Paid</th>
                        <th>Document Required</th>
                        <th>Gender Specific</th>
                        <th>Actions</th>
                    </tr>
                </thead>
                <tbody>
                    {% for leave_type in leave_types %}
                    <tr>
                        <td>{{ leave_type.name }}</td>
                        <td><code>{{ leave_type.code }}</code></td>
                        <td>
                            <span class="badge bg-info">{{ leave_type.category }}</span>
                        </td>
                        <td>{{ leave_type.days_allowed }}</td>
                        <td>
                            {% if leave_type.is_paid %}
                            <span class="badge bg-success">Yes</span>
                            {% else %}
                            <span class="badge bg-danger">No</span>
                            {% endif %}
                        </td>
                        <td>
                            {% if leave_type.requires_document %}
                            <span class="badge bg-warning">Required</span>
                            {% else %}
                            <span class="badge bg-secondary">Optional</span>
                            {% endif %}
                        </td>
                        <td>
                            {% if leave_type.gender_specific == 'A' %}
                            <span class="badge bg-primary">All</span>
                            {% elif leave_type.gender_specific == 'M' %}
                            <span class="badge bg-info">Male</span>
                            {% else %}
                            <span class="badge bg-info">Female</span>
                            {% endif %}
                        </td>
                        <td>
                            {% if perms.attendance.change_leavetype %}
                            <div class="btn-group">
                                <button type="button" 
                                        class="btn btn-sm btn-outline-primary edit-leave-type"
                                        data-id="{{ leave_type.id }}"
                                        data-name="{{ leave_type.name }}"
                                        data-code="{{ leave_type.code }}"
                                        data-category="{{ leave_type.category }}"
                                        data-days="{{ leave_type.days_allowed }}"
                                        data-paid="{{ leave_type.is_paid|yesno:'true,false' }}"
                                        data-document="{{ leave_type.requires_document|yesno:'true,false' }}"
                                        data-gender="{{ leave_type.gender_specific }}"
                                        data-description="{{ leave_type.description }}"
                                        data-bs-toggle="modal" 
                                        data-bs-target="#editLeaveTypeModal">
                                    <i class="fas fa-edit"></i>
                                </button>
                                {% if perms.attendance.delete_leavetype %}
                                <button type="button" 
                                        class="btn btn-sm btn-outline-danger delete-leave-type"
                                        data-id="{{ leave_type.id }}"
                                        data-name="{{ leave_type.name }}"
                                        data-bs-toggle="modal" 
                                        data-bs-target="#deleteLeaveTypeModal">
                                    <i class="fas fa-trash"></i>
                                </button>
                                {% endif %}
                            </div>
                            {% endif %}
                        </td>
                    </tr>
                    {% empty %}
                    <tr>
                        <td colspan="8" class="text-center">No leave types found</td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
    </div>
</div>

<!-- Add Leave Type Modal -->
<div class="modal fade" id="addLeaveTypeModal" tabindex="-1">
    <div class="modal-dialog">
        <div class="modal-content">
            <div class="modal-header">
                <h5 class="modal-title">Add Leave Type</h5>
                <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
            </div>
            <form id="addLeaveTypeForm" method="POST">
                {% csrf_token %}
                <div class="modal-body">
                    <div class="mb-3">
                        <label for="name" class="form-label">Name</label>
                        <input type="text" class="form-control" id="name" name="name" required>
                    </div>
                    <div class="mb-3">
                        <label for="code" class="form-label">Code</label>
                        <input type="text" class="form-control" id="code" name="code" required>
                        <div class="form-text">Unique identifier for this leave type (e.g., ANNUAL, SICK)</div>
                    </div>
                    <div class="mb-3">
                        <label for="category" class="form-label">Category</label>
                        <select class="form-select" id="category" name="category" required>
                            <option value="REGULAR">Regular</option>
                            <option value="MEDICAL">Medical</option>
                            <option value="SPECIAL">Special</option>
                        </select>
                    </div>
                    <div class="mb-3">
                        <label for="days_allowed" class="form-label">Days Allowed</label>
                        <input type="number" class="form-control" id="days_allowed" name="days_allowed" required min="0">
                    </div>
                    <div class="mb-3">
                        <div class="form-check">
                            <input class="form-check-input" type="checkbox" id="is_paid" name="is_paid" checked>
                            <label class="form-check-label" for="is_paid">
                                Paid Leave
                            </label>
                        </div>
                    </div>
                    <div class="mb-3">
                        <div class="form-check">
                            <input class="form-check-input" type="checkbox" id="requires_document" name="requires_document">
                            <label class="form-check-label" for="requires_document">
                                Requires Supporting Document
                            </label>
                        </div>
                    </div>
                    <div class="mb-3">
                        <label for="gender_specific" class="form-label">Gender Specific</label>
                        <select class="form-select" id="gender_specific" name="gender_specific" required>
                            <option value="A">All</option>
                            <option value="M">Male Only</option>
                            <option value="F">Female Only</option>
                        </select>
                    </div>
                    <div class="mb-3">
                        <label for="description" class="form-label">Description</label>
                        <textarea class="form-control" id="description" name="description" rows="3"></textarea>
                    </div>
                </div>
                <div class="modal-footer">
                    <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
                    <button type="submit" class="btn btn-primary">Add Leave Type</button>
                </div>
            </form>
        </div>
    </div>
</div>

<!-- Edit Leave Type Modal -->
<div class="modal fade" id="editLeaveTypeModal" tabindex="-1">
    <div class="modal-dialog">
        <div class="modal-content">
            <div class="modal-header">
                <h5 class="modal-title">Edit Leave Type</h5>
                <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
            </div>
            <form id="editLeaveTypeForm" method="POST">
                {% csrf_token %}
                <input type="hidden" id="edit_id" name="id">
                <div class="modal-body">
                    <!-- Same fields as Add Modal -->
                    <div class="mb-3">
                        <label for="edit_name" class="form-label">Name</label>
                        <input type="text" class="form-control" id="edit_name" name="name" required>
                    </div>
                    <div class="mb-3">
                        <label for="edit_code" class="form-label">Code</label>
                        <input type="text" class="form-control" id="edit_code" name="code" required>
                    </div>
                    <div class="mb-3">
                        <label for="edit_category" class="form-label">Category</label>
                        <select class="form-select" id="edit_category" name="category" required>
                            <option value="REGULAR">Regular</option>
                            <option value="MEDICAL">Medical</option>
                            <option value="SPECIAL">Special</option>
                        </select>
                    </div>
                    <div class="mb-3">
                        <label for="edit_days_allowed" class="form-label">Days Allowed</label>
                        <input type="number" class="form-control" id="edit_days_allowed" name="days_allowed" required min="0">
                    </div>
                    <div class="mb-3">
                        <div class="form-check">
                            <input class="form-check-input" type="checkbox" id="edit_is_paid" name="is_paid">
                            <label class="form-check-label" for="edit_is_paid">
                                Paid Leave
                            </label>
                        </div>
                    </div>
                    <div class="mb-3">
                        <div class="form-check">
                            <input class="form-check-input" type="checkbox" id="edit_requires_document" name="requires_document">
                            <label class="form-check-label" for="edit_requires_document">
                                Requires Supporting Document
                            </label>
                        </div>
                    </div>
                    <div class="mb-3">
                        <label for="edit_gender_specific" class="form-label">Gender Specific</label>
                        <select class="form-select" id="edit_gender_specific" name="gender_specific" required>
                            <option value="A">All</option>
                            <option value="M">Male Only</option>
                            <option value="F">Female Only</option>
                        </select>
                    </div>
                    <div class="mb-3">
                        <label for="edit_description" class="form-label">Description</label>
                        <textarea class="form-control" id="edit_description" name="description" rows="3"></textarea>
                    </div>
                </div>
                <div class="modal-footer">
                    <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
                    <button type="submit" class="btn btn-primary">Save Changes</button>
                </div>
            </form>
        </div>
    </div>
</div>

<!-- Delete Leave Type Modal -->
<div class="modal fade" id="deleteLeaveTypeModal" tabindex="-1">
    <div class="modal-dialog">
        <div class="modal-content">
            <div class="modal-header">
                <h5 class="modal-title">Delete Leave Type</h5>
                <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
            </div>
            <div class="modal-body">
                <p>Are you sure you want to delete the leave type "<span id="deleteLeaveTypeName"></span>"?</p>
                <p class="text-danger">This action cannot be undone. All associated leave records will be affected.</p>
            </div>
            <div class="modal-footer">
                <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
                <form id="deleteLeaveTypeForm" method="POST">
                    {% csrf_token %}
                    <input type="hidden" id="delete_id" name="id">
                    <button type="submit" class="btn btn-danger">Delete</button>
                </form>
            </div>
        </div>
    </div>
</div>

{% endblock %}

{% block extra_js %}
{{ block.super }}
<script src="{% static 'attendance/js/leave_types.js' %}"></script>
{% endblock %}

```

### hrms_project\attendance\templates\attendance\mark_attendance.html
```
{% extends 'attendance/base.html' %}
{% load static %}

{% block attendance_content %}
<div class="card">
    <div class="card-header">
        <h5 class="mb-0">Mark Attendance</h5>
    </div>
    <div class="card-body">
        <form id="mark-attendance-form">
            <div class="row">
                <!-- Employee Selection -->
                <div class="col-md-6 mb-3">
                    <label for="employee-select" class="form-label">Employee</label>
                    <select class="form-select" id="employee-select" required>
                        <option value="">Select Employee</option>
                        {% for emp in employees %}
                        <option value="{{ emp.id }}">{{ emp.get_full_name }} ({{ emp.employee_number }})</option>
                        {% endfor %}
                    </select>
                </div>

                <!-- Date Selection -->
                <div class="col-md-6 mb-3">
                    <label for="attendance-date" class="form-label">Date</label>
                    <input type="date" class="form-control" id="attendance-date" required 
                           value="{{ today|date:'Y-m-d' }}">
                </div>

                <!-- Time Selection -->
                <div class="col-md-6 mb-3">
                    <label for="first-in" class="form-label">First In Time</label>
                    <input type="time" class="form-control" id="first-in" required>
                </div>

                <div class="col-md-6 mb-3">
                    <label for="last-out" class="form-label">Last Out Time</label>
                    <input type="time" class="form-control" id="last-out" required>
                </div>

                <!-- Shift Selection -->
                <div class="col-md-6 mb-3">
                    <label for="shift-select" class="form-label">Shift</label>
                    <select class="form-select" id="shift-select">
                        <option value="">No Shift</option>
                        {% for shift in shifts %}
                        <option value="{{ shift.id }}">{{ shift.name }}</option>
                        {% endfor %}
                    </select>
                </div>

                <!-- Source -->
                <div class="col-md-6 mb-3">
                    <label for="source" class="form-label">Source</label>
                    <select class="form-select" id="source" required>
                        <option value="manual">Manual Entry</option>
                        <option value="system">System</option>
                    </select>
                </div>

                <!-- Remarks -->
                <div class="col-12 mb-3">
                    <label for="remarks" class="form-label">Remarks</label>
                    <textarea class="form-control" id="remarks" rows="3"></textarea>
                </div>

                <!-- Submit Button -->
                <div class="col-12">
                    <button type="submit" class="btn btn-primary">
                        <i class="fas fa-save"></i> Save Attendance
                    </button>
                </div>
            </div>
        </form>
    </div>
</div>
{% endblock %}

{% block extra_js %}
{{ block.super }}
<script>
document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('mark-attendance-form');
    
    form.addEventListener('submit', function(e) {
        e.preventDefault();
        
        const formData = {
            employee: document.getElementById('employee-select').value,
            date: document.getElementById('attendance-date').value,
            first_in_time: document.getElementById('first-in').value,
            last_out_time: document.getElementById('last-out').value,
            shift: document.getElementById('shift-select').value,
            source: document.getElementById('source').value,
            remarks: document.getElementById('remarks').value
        };

        fetch('/api/attendance/logs/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: JSON.stringify(formData)
        })
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                throw new Error(data.error);
            }
            alert('Attendance marked successfully');
            form.reset();
        })
        .catch(error => {
            alert('Error marking attendance: ' + error.message);
        });
    });
});
</script>
{% endblock %}
```

### hrms_project\attendance\templates\attendance\recurring_holidays.html
```
{% extends 'attendance/base.html' %}
{% load static %}

{% block attendance_content %}
<div class="card">
    <div class="card-header d-flex justify-content-between align-items-center">
        <h5 class="mb-0">Recurring Holidays</h5>
        <div>
            <button id="generate-next-year" class="btn btn-success">
                <i class="fas fa-sync"></i> Generate Next Year's Holidays
            </button>
            <a href="{% url 'attendance:holiday_create' %}?recurring=true" class="btn btn-primary">
                <i class="fas fa-plus"></i> Add Recurring Holiday
            </a>
        </div>
    </div>
    <div class="card-body">
        <!-- Filters -->
        <div class="row mb-4">
            <div class="col-md-3">
                <label class="form-label">Holiday Type</label>
                <select class="form-select" id="type-filter">
                    <option value="">All Types</option>
                    <option value="PUBLIC">Public Holiday</option>
                    <option value="COMPANY">Company Holiday</option>
                    <option value="OPTIONAL">Optional Holiday</option>
                </select>
            </div>
            <div class="col-md-3">
                <label class="form-label">Department</label>
                <select class="form-select" id="department-filter">
                    <option value="">All Departments</option>
                    {% for dept in departments %}
                    <option value="{{ dept.id }}">{{ dept.name }}</option>
                    {% endfor %}
                </select>
            </div>
            <div class="col-md-3 d-flex align-items-end">
                <button class="btn btn-primary" id="apply-filters">Apply Filters</button>
            </div>
        </div>

        <!-- Holiday Table -->
        <div class="table-responsive">
            <table class="table table-hover" id="recurring-holidays-table">
                <thead>
                    <tr>
                        <th>Date Pattern</th>
                        <th>Name</th>
                        <th>Type</th>
                        <th>Departments</th>
                        <th>Last Generated</th>
                        <th>Actions</th>
                    </tr>
                </thead>
                <tbody>
                    {% for holiday in holidays %}
                    <tr>
                        <td>{{ holiday.date|date:"d M" }} <em class="text-muted">(yearly)</em></td>
                        <td>{{ holiday.name }}</td>
                        <td>
                            <span class="badge bg-{{ holiday.holiday_type|lower }}">
                                {{ holiday.get_holiday_type_display }}
                            </span>
                        </td>
                        <td>
                            {% if holiday.applicable_departments.all %}
                            {% for dept in holiday.applicable_departments.all %}
                            <span class="badge bg-info">{{ dept.name }}</span>
                            {% endfor %}
                            {% else %}
                            <span class="badge bg-secondary">All Departments</span>
                            {% endif %}
                        </td>
                        <td>
                            {% if holiday.last_generated %}
                            {{ holiday.last_generated|date:"d M Y" }}
                            {% else %}
                            <span class="text-muted">Never</span>
                            {% endif %}
                        </td>
                        <td>
                            <a href="{% url 'attendance:holiday_edit' pk=holiday.id %}" class="btn btn-sm btn-primary">
                                <i class="fas fa-edit"></i>
                            </a>
                            <button class="btn btn-sm btn-danger delete-holiday" data-id="{{ holiday.id }}">
                                <i class="fas fa-trash"></i>
                            </button>
                        </td>
                    </tr>
                    {% empty %}
                    <tr>
                        <td colspan="6" class="text-center">No recurring holidays defined</td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>

        <!-- Pagination -->
        {% if is_paginated %}
        <nav aria-label="Page navigation" class="mt-4">
            <ul class="pagination justify-content-center">
                {% if page_obj.has_previous %}
                <li class="page-item">
                    <a class="page-link" href="?page=1">&laquo; First</a>
                </li>
                <li class="page-item">
                    <a class="page-link" href="?page={{ page_obj.previous_page_number }}">Previous</a>
                </li>
                {% endif %}

                {% for num in page_obj.paginator.page_range %}
                    {% if page_obj.number == num %}
                    <li class="page-item active">
                        <span class="page-link">{{ num }}</span>
                    </li>
                    {% elif num > page_obj.number|add:'-3' and num < page_obj.number|add:'3' %}
                    <li class="page-item">
                        <a class="page-link" href="?page={{ num }}">{{ num }}</a>
                    </li>
                    {% endif %}
                {% endfor %}

                {% if page_obj.has_next %}
                <li class="page-item">
                    <a class="page-link" href="?page={{ page_obj.next_page_number }}">Next</a>
                </li>
                <li class="page-item">
                    <a class="page-link" href="?page={{ page_obj.paginator.num_pages }}">Last &raquo;</a>
                </li>
                {% endif %}
            </ul>
        </nav>
        {% endif %}
    </div>
</div>

<!-- Delete Confirmation Modal -->
<div class="modal fade" id="deleteModal" tabindex="-1">
    <div class="modal-dialog">
        <div class="modal-content">
            <div class="modal-header">
                <h5 class="modal-title">Confirm Delete</h5>
                <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
            </div>
            <div class="modal-body">
                <p>Are you sure you want to delete this recurring holiday?</p>
                <p class="text-danger"><strong>Note:</strong> This will not delete any already generated holiday instances.</p>
            </div>
            <div class="modal-footer">
                <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
                <button type="button" class="btn btn-danger" id="confirmDelete">Delete</button>
            </div>
        </div>
    </div>
</div>

<!-- Generation Confirmation Modal -->
<div class="modal fade" id="generateModal" tabindex="-1">
    <div class="modal-dialog">
        <div class="modal-content">
            <div class="modal-header">
                <h5 class="modal-title">Generate Next Year's Holidays</h5>
                <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
            </div>
            <div class="modal-body">
                <p>This will generate holiday entries for next year based on recurring holidays.</p>
                <div id="generation-preview">
                    <h6>Holidays to be generated:</h6>
                    <ul id="preview-list"></ul>
                </div>
            </div>
            <div class="modal-footer">
                <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
                <button type="button" class="btn btn-success" id="confirmGenerate">Generate</button>
            </div>
        </div>
    </div>
</div>
{% endblock %}

{% block extra_js %}
{{ block.super }}
<script>
$(document).ready(function() {
    let deleteId = null;

    // Delete holiday
    $('.delete-holiday').click(function() {
        deleteId = $(this).data('id');
        $('#deleteModal').modal('show');
    });

    $('#confirmDelete').click(function() {
        if (deleteId) {
            $.ajax({
                url: `/attendance/holiday/${deleteId}/delete/`,
                type: 'POST',
                headers: {
                    'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
                },
                success: function() {
                    location.reload();
                },
                error: function(xhr) {
                    alert('Error deleting holiday');
                }
            });
        }
        $('#deleteModal').modal('hide');
    });

    // Generate next year's holidays
    $('#generate-next-year').click(function() {
        // First get preview
        $.ajax({
            url: '{% url "attendance:preview_next_year_holidays" %}',
            type: 'GET',
            success: function(data) {
                const previewList = $('#preview-list');
                previewList.empty();
                
                data.holidays.forEach(function(holiday) {
                    const li = $('<li>').text(
                        `${holiday.name} - ${holiday.date} (${holiday.type})`
                    );
                    previewList.append(li);
                });
                
                $('#generateModal').modal('show');
            },
            error: function() {
                alert('Error loading preview');
            }
        });
    });

    $('#confirmGenerate').click(function() {
        $.ajax({
            url: '{% url "attendance:generate_next_year_holidays" %}',
            type: 'POST',
            headers: {
                'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
            },
            success: function(data) {
                $('#generateModal').modal('hide');
                alert(`Successfully generated ${data.count} holidays for next year`);
                location.reload();
            },
            error: function() {
                alert('Error generating holidays');
            }
        });
    });

    // Apply filters
    $('#apply-filters').click(function() {
        const type = $('#type-filter').val();
        const department = $('#department-filter').val();
        
        window.location.href = `?type=${type}&department=${department}`;
    });
});
</script>
{% endblock %}

```

### hrms_project\attendance\templates\attendance\report_template.html
```
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ report_title }}</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background-color: white;
            padding: 20px;
            border-radius: 5px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .header {
            text-align: center;
            margin-bottom: 30px;
            padding-bottom: 20px;
            border-bottom: 2px solid #eee;
        }
        .header h1 {
            color: #333;
            margin: 0;
            font-size: 24px;
        }
        .header .timestamp {
            color: #666;
            font-size: 14px;
            margin-top: 10px;
        }
        table {
            width: 100%;
            border-collapse: collapse;
            margin-bottom: 20px;
        }
        th, td {
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }
        th {
            background-color: #f8f9fa;
            font-weight: bold;
            color: #333;
        }
        tr:hover {
            background-color: #f5f5f5;
        }
        .status-badge {
            display: inline-block;
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 12px;
            font-weight: bold;
            text-transform: uppercase;
        }
        .status-present { background-color: #d4edda; color: #155724; }
        .status-absent { background-color: #f8d7da; color: #721c24; }
        .status-late { background-color: #fff3cd; color: #856404; }
        .status-leave { background-color: #cce5ff; color: #004085; }
        .status-holiday { background-color: #e2e3e5; color: #383d41; }
        .summary {
            margin-top: 30px;
            padding: 20px;
            background-color: #f8f9fa;
            border-radius: 4px;
        }
        .summary h2 {
            font-size: 18px;
            margin-top: 0;
            margin-bottom: 15px;
            color: #333;
        }
        .summary-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
            gap: 15px;
        }
        .summary-item {
            background-color: white;
            padding: 15px;
            border-radius: 4px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }
        .summary-item .label {
            font-size: 14px;
            color: #666;
            margin-bottom: 5px;
        }
        .summary-item .value {
            font-size: 24px;
            font-weight: bold;
            color: #333;
        }
        @media print {
            body {
                background-color: white;
                padding: 0;
            }
            .container {
                box-shadow: none;
                padding: 0;
            }
            .summary {
                break-inside: avoid;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>{{ report_title }}</h1>
            <div class="timestamp">Generated on: {{ generated_at|default:now }}</div>
        </div>

        {% if filters %}
        <div class="filters">
            <strong>Filters:</strong>
            {% for key, value in filters.items %}
            <span>{{ key }}: {{ value }}</span>{% if not forloop.last %} | {% endif %}
            {% endfor %}
        </div>
        {% endif %}

        <div class="table-responsive">
            {{ table_content|safe }}
        </div>

        {% if summary_data %}
        <div class="summary">
            <h2>Summary</h2>
            <div class="summary-grid">
                {% for label, value in summary_data.items %}
                <div class="summary-item">
                    <div class="label">{{ label }}</div>
                    <div class="value">{{ value }}</div>
                </div>
                {% endfor %}
            </div>
        </div>
        {% endif %}

        <script>
            // Add status badges to status column
            document.addEventListener('DOMContentLoaded', function() {
                const statusCells = document.querySelectorAll('td:nth-child(5)'); // Adjust index based on status column
                statusCells.forEach(cell => {
                    const status = cell.textContent.trim().toLowerCase();
                    cell.innerHTML = `<span class="status-badge status-${status}">${cell.textContent}</span>`;
                });
            });
        </script>
    </div>
</body>
</html>

```

### hrms_project\attendance\templates\attendance\reports\department_report.html
```
<!DOCTYPE html>
<html>
<head>
    {% load static %}
    <link href="{% static 'attendance/css/reports.css' %}" rel="stylesheet">
</head>
<body>
    <div class="header">
        <h1>Department Attendance Report</h1>
        <p>{{ period.start_date|date:"F j, Y" }} - {{ period.end_date|date:"F j, Y" }}</p>
    </div>

    <div class="department-info">
        <div class="info-grid">
            <div class="info-item">
                <div class="info-label">Department</div>
                <div class="info-value">{{ department.name }}</div>
            </div>
            <div class="info-item">
                <div class="info-label">Department Code</div>
                <div class="info-value">{{ department.code }}</div>
            </div>
            <div class="info-item">
                <div class="info-label">Total Employees</div>
                <div class="info-value">{{ statistics.total_employees }}</div>
            </div>
            <div class="info-item">
                <div class="info-label">Report Period</div>
                <div class="info-value">{{ period.total_days }} Days</div>
            </div>
        </div>
    </div>

    <div class="stats-container">
        <div class="stat-card stat-present">
            <div class="stat-value">{{ statistics.present_rate|floatformat:1 }}%</div>
            <div class="stat-label">Present Rate</div>
            <div class="progress-bar">
                <div class="progress-fill" style="width: {{ statistics.present_rate }}%; background-color: #28a745"></div>
            </div>
        </div>
        <div class="stat-card stat-late">
            <div class="stat-value">{{ statistics.late_rate|floatformat:1 }}%</div>
            <div class="stat-label">Late Rate</div>
            <div class="progress-bar">
                <div class="progress-fill" style="width: {{ statistics.late_rate }}%; background-color: #ffc107"></div>
            </div>
        </div>
        <div class="stat-card stat-absent">
            <div class="stat-value">{{ statistics.absent_rate|floatformat:1 }}%</div>
            <div class="stat-label">Absent Rate</div>
            <div class="progress-bar">
                <div class="progress-fill" style="width: {{ statistics.absent_rate }}%; background-color: #dc3545"></div>
            </div>
        </div>
        <div class="stat-card stat-leave">
            <div class="stat-value">{{ attendance.total_leave_days }}</div>
            <div class="stat-label">Leave Days</div>
        </div>
    </div>

    <div class="employee-list">
        <h2>Employee Attendance Summary</h2>
        <div class="table-container">
            <table>
                <thead>
                    <tr>
                        <th>Employee</th>
                        <th>ID</th>
                        <th>Present Days</th>
                        <th>Absent Days</th>
                        <th>Late Days</th>
                        <th>Leave Days</th>
                        <th>Attendance Rate</th>
                    </tr>
                </thead>
                <tbody>
                    {% for employee in employees %}
                    <tr>
                        <td>{{ employee.get_full_name }}</td>
                        <td>{{ employee.employee_number }}</td>
                        <td>{{ employee.stats.present_days }}</td>
                        <td>{{ employee.stats.absent_days }}</td>
                        <td>{{ employee.stats.late_days }}</td>
                        <td>{{ employee.stats.leave_days }}</td>
                        <td>
                            {{ employee.stats.attendance_rate|floatformat:1 }}%
                            {% if employee.stats.trend > 0 %}
                            <span class="trend-indicator trend-up">↑</span>
                            {% elif employee.stats.trend < 0 %}
                            <span class="trend-indicator trend-down">↓</span>
                            {% else %}
                            <span class="trend-indicator trend-neutral">→</span>
                            {% endif %}
                        </td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
    </div>

    <div class="leave-section">
        <h2>Leave Statistics</h2>
        <div class="table-container">
            <table>
                <thead>
                    <tr>
                        <th>Leave Type</th>
                        <th>Total Days</th>
                        <th>Employees</th>
                        <th>Average Per Employee</th>
                    </tr>
                </thead>
                <tbody>
                    {% for stat in leave_stats %}
                    <tr>
                        <td>{{ stat.leave_type__name }}</td>
                        <td>{{ stat.total_days }}</td>
                        <td>{{ stat.total_employees }}</td>
                        <td>{{ stat.average_days|floatformat:1 }}</td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
    </div>

    <div class="footer">
        <p>Report generated on {{ generated_at|date:"l, F j, Y" }} at {{ generated_at|time:"h:i A" }}</p>
        <p>For individual employee reports, please use the generate_report command with --employee option.</p>
        <p>This is a system-generated report. Please contact HR for any discrepancies.</p>
    </div>
</body>
</html>

```

### hrms_project\attendance\templates\attendance\reports\employee_report.html
```
<!DOCTYPE html>
<html>
<head>
    {% load static %}
    <link href="{% static 'attendance/css/reports.css' %}" rel="stylesheet">
</head>
<body>
    <div class="header">
        <h1>Employee Attendance Report</h1>
        <p>{{ period.start_date|date:"F j, Y" }} - {{ period.end_date|date:"F j, Y" }}</p>
    </div>

    <div class="employee-info">
        <div class="info-grid">
            <div class="info-item">
                <div class="info-label">Name</div>
                <div class="info-value">{{ employee.get_full_name }}</div>
            </div>
            <div class="info-item">
                <div class="info-label">Employee ID</div>
                <div class="info-value">{{ employee.employee_number }}</div>
            </div>
            <div class="info-item">
                <div class="info-label">Department</div>
                <div class="info-value">{{ employee.department.name }}</div>
            </div>
            <div class="info-item">
                <div class="info-label">Designation</div>
                <div class="info-value">{{ employee.designation }}</div>
            </div>
        </div>
    </div>

    <div class="stats-container">
        <div class="stat-card stat-present">
            <div class="stat-value">{{ statistics.present_days }}</div>
            <div class="stat-label">Present Days</div>
            <div class="progress-bar">
                <div class="progress-fill" style="width: {{ statistics.present_rate }}%; background-color: #28a745"></div>
            </div>
            <div class="percent-indicator">{{ statistics.present_rate|floatformat:1 }}%</div>
        </div>
        <div class="stat-card stat-late">
            <div class="stat-value">{{ statistics.late_days }}</div>
            <div class="stat-label">Late Days</div>
            <div class="progress-bar">
                <div class="progress-fill" style="width: {{ statistics.late_rate }}%; background-color: #ffc107"></div>
            </div>
            <div class="percent-indicator">{{ statistics.late_rate|floatformat:1 }}%</div>
        </div>
        <div class="stat-card stat-absent">
            <div class="stat-value">{{ statistics.absent_days }}</div>
            <div class="stat-label">Absent Days</div>
            <div class="progress-bar">
                <div class="progress-fill" style="width: {{ statistics.absent_rate }}%; background-color: #dc3545"></div>
            </div>
            <div class="percent-indicator">{{ statistics.absent_rate|floatformat:1 }}%</div>
        </div>
        <div class="stat-card stat-leave">
            <div class="stat-value">{{ statistics.leave_days }}</div>
            <div class="stat-label">Leave Days</div>
        </div>
    </div>

    <div class="daily-attendance">
        <h2>Daily Attendance Log</h2>
        <div class="table-container">
            <table>
                <thead>
                    <tr>
                        <th>Date</th>
                        <th>Day</th>
                        <th>First In</th>
                        <th>Last Out</th>
                        <th>Total Hours</th>
                        <th>Status</th>
                        <th>Remarks</th>
                    </tr>
                </thead>
                <tbody>
                    {% for log in attendance_logs %}
                    <tr>
                        <td>{{ log.date|date:"M d, Y" }}</td>
                        <td>{{ log.date|date:"l" }}</td>
                        <td>{{ log.first_in_time|time:"h:i A"|default:"-" }}</td>
                        <td>{{ log.last_out_time|time:"h:i A"|default:"-" }}</td>
                        <td>{{ log.total_hours|floatformat:2 }}</td>
                        <td>
                            <span class="status-badge {{ log.status|lower }}">
                                {{ log.status }}
                            </span>
                        </td>
                        <td>{{ log.remarks|default:"-" }}</td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
    </div>

    <div class="leave-section">
        <h2>Leave Summary</h2>
        <div class="table-container">
            <table>
                <thead>
                    <tr>
                        <th>Leave Type</th>
                        <th>Taken</th>
                        <th>Balance</th>
                        <th>Expiry</th>
                    </tr>
                </thead>
                <tbody>
                    {% for leave in leave_summary %}
                    <tr>
                        <td>{{ leave.type }}</td>
                        <td>{{ leave.taken }}</td>
                        <td>{{ leave.balance }}</td>
                        <td>{{ leave.expiry_date|date:"M d, Y"|default:"N/A" }}</td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
    </div>

    {% if leave_records %}
    <div class="leave-details">
        <h2>Leave Details</h2>
        <div class="table-container">
            <table>
                <thead>
                    <tr>
                        <th>Leave Type</th>
                        <th>From</th>
                        <th>To</th>
                        <th>Days</th>
                        <th>Status</th>
                        <th>Approved By</th>
                    </tr>
                </thead>
                <tbody>
                    {% for record in leave_records %}
                    <tr>
                        <td>{{ record.leave_type }}</td>
                        <td>{{ record.start_date|date:"M d, Y" }}</td>
                        <td>{{ record.end_date|date:"M d, Y" }}</td>
                        <td>{{ record.days }}</td>
                        <td>
                            <span class="status-badge {{ record.status|lower }}">
                                {{ record.status }}
                            </span>
                        </td>
                        <td>{{ record.approved_by|default:"-" }}</td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
    </div>
    {% endif %}

    <div class="footer">
        <p>Report generated on {{ generated_at|date:"l, F j, Y" }} at {{ generated_at|time:"h:i A" }}</p>
        <p>For any discrepancies in this report, please contact the HR department.</p>
    </div>
</body>
</html>

```

### hrms_project\attendance\templates\attendance\reports\organization_report.html
```
<!DOCTYPE html>
<html>
<head>
    {% load static %}
    <link href="{% static 'attendance/css/reports.css' %}" rel="stylesheet">
</head>
<body>
    <div class="header">
        <h1>Organization Attendance Report</h1>
        <p>{{ period.start_date|date:"F j, Y" }} - {{ period.end_date|date:"F j, Y" }}</p>
    </div>

    <div class="org-overview">
        <div class="overview-card">
            <div class="overview-value">{{ organization.total_departments }}</div>
            <div class="overview-label">Departments</div>
        </div>
        <div class="overview-card">
            <div class="overview-value">{{ organization.total_employees }}</div>
            <div class="overview-label">Active Employees</div>
        </div>
        <div class="overview-card">
            <div class="overview-value">{{ organization.stats.total_present }}</div>
            <div class="overview-label">Total Present Days</div>
        </div>
        <div class="overview-card">
            <div class="overview-value">{{ organization.stats.total_absent }}</div>
            <div class="overview-label">Total Absent Days</div>
        </div>
    </div>

    <div class="department-section">
        <h2>Department Analysis</h2>
        <div class="department-grid">
            {% for dept in department_stats %}
            <div class="department-card">
                <div class="department-header">
                    <div class="department-name">{{ dept.department.name }}</div>
                    <small>{{ dept.stats.total_employees }} Employees</small>
                </div>
                <div class="department-stats">
                    <div class="stat-item">
                        <div class="overview-value">{{ dept.stats.present_rate|floatformat:1 }}%</div>
                        <div class="overview-label">Present Rate</div>
                        <div class="progress-bar">
                            <div class="progress-fill fill-present" style="width: {{ dept.stats.present_rate }}%"></div>
                        </div>
                    </div>
                    <div class="stat-item">
                        <div class="overview-value">{{ dept.stats.late_rate|floatformat:1 }}%</div>
                        <div class="overview-label">Late Rate</div>
                        <div class="progress-bar">
                            <div class="progress-fill fill-late" style="width: {{ dept.stats.late_rate }}%"></div>
                        </div>
                    </div>
                    <div class="stat-item">
                        <div class="overview-value">{{ dept.stats.absent_rate|floatformat:1 }}%</div>
                        <div class="overview-label">Absent Rate</div>
                        <div class="progress-bar">
                            <div class="progress-fill fill-absent" style="width: {{ dept.stats.absent_rate }}%"></div>
                        </div>
                    </div>
                    <div class="stat-item">
                        <div class="overview-value">{{ dept.stats.leave_days }}</div>
                        <div class="overview-label">Leave Days</div>
                    </div>
                </div>
            </div>
            {% endfor %}
        </div>
    </div>

    <div class="leave-summary">
        <h2>Leave Statistics</h2>
        <div class="table-container">
            <table>
                <thead>
                    <tr>
                        <th>Leave Type</th>
                        <th>Total Days</th>
                        <th>Total Employees</th>
                        <th>Average Days/Employee</th>
                    </tr>
                </thead>
                <tbody>
                    {% for stat in leave_stats %}
                    <tr>
                        <td>{{ stat.leave_type__name }}</td>
                        <td>{{ stat.total_days }}</td>
                        <td>{{ stat.total_employees }}</td>
                        <td>{{ stat.total_days|divisibleby:stat.total_employees }}</td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
    </div>

    <div class="footer">
        <p>Report generated on {{ generated_at|date:"l, F j, Y" }} at {{ generated_at|time:"h:i A" }}</p>
        <p>For detailed department-wise reports, please use the generate_report command with --department option.</p>
        <p>This is a system-generated report. Please contact HR for any discrepancies.</p>
    </div>
</body>
</html>

```

### hrms_project\attendance\templates\attendance\shifts\assignment_form.html
```
{% extends 'attendance/base.html' %}
{% load static %}

{% block attendance_content %}
<div class="card">
    <div class="card-header">
        <div class="d-flex justify-content-between align-items-center">
            <h5 class="mb-0">Assign Shift</h5>
        </div>
    </div>
    <div class="card-body">
        <form id="shift-assignment-form" method="post">
            {% csrf_token %}
            <div class="mb-3">
                <label class="form-label">Employee</label>
                <select class="form-select" id="employee" name="employee" required>
                    <option value="">Select Employee</option>
                    {% for employee in employees %}
                        <option value="{{ employee.id }}" {% if employee.id == form.employee.value %}selected{% endif %}>
                            {{ employee.get_full_name }} ({{ employee.employee_number }})
                        </option>
                    {% endfor %}
                </select>
            </div>
            
            <div class="mb-3">
                <label class="form-label">Shift</label>
                <select class="form-select" id="shift" name="shift" required>
                    <option value="">Select Shift</option>
                    {% for shift in shifts %}
                        <option value="{{ shift.id }}" {% if shift.id == form.shift.value %}selected{% endif %}>
                            {{ shift.name }} ({{ shift.start_time|time:"g:i A" }} - {{ shift.end_time|time:"g:i A" }})
                        </option>
                    {% endfor %}
                </select>
            </div>

            <div class="mb-3">
                <label class="form-label">Start Date</label>
                <input type="date" class="form-control" id="start_date" name="start_date" 
                       value="{{ form.start_date.value|date:'Y-m-d' }}" required>
            </div>

            <div class="mb-3">
                <label class="form-label">End Date (Optional)</label>
                <input type="date" class="form-control" id="end_date" name="end_date"
                       value="{{ form.end_date.value|date:'Y-m-d' }}">
                <small class="text-muted">Leave blank for permanent assignment</small>
            </div>

            <div class="form-check mb-3">
                <input type="checkbox" class="form-check-input" id="is_active" name="is_active"
                       {% if form.is_active.value %}checked{% endif %}>
                <label class="form-check-label" for="is_active">Active</label>
            </div>

            <div class="mb-3">
                <button type="submit" class="btn btn-primary">Save Assignment</button>
                <a href="{% url 'attendance:shift_list' %}" class="btn btn-secondary">Cancel</a>
            </div>
        </form>
    </div>
</div>

{% endblock %}

{% block extra_js %}
{{ block.super }}
<script>
document.addEventListener('DOMContentLoaded', function() {
    const startDateInput = document.getElementById('start_date');
    const endDateInput = document.getElementById('end_date');

    // Set minimum date for start date as today
    startDateInput.min = new Date().toISOString().split('T')[0];

    // Update end date minimum when start date changes
    startDateInput.addEventListener('change', function() {
        endDateInput.min = this.value;
        
        // If end date is before new start date, clear it
        if (endDateInput.value && endDateInput.value < this.value) {
            endDateInput.value = '';
        }
    });
});
</script>
{% endblock %}

```

### hrms_project\attendance\templates\attendance\shifts\assignment_list.html
```
{% extends 'attendance/base.html' %}
{% load static %}

{% block attendance_content %}
<div class="card">
    <div class="card-header">
        <div class="d-flex justify-content-between align-items-center">
            <h5 class="mb-0">Shift Assignments</h5>
            <a href="{% url 'attendance:shift_assignment_create' %}" class="btn btn-primary">
                <i class="fas fa-plus"></i> New Assignment
            </a>
        </div>
    </div>
    <div class="card-body">
        <!-- Filters -->
        <div class="row mb-4">
            <div class="col-md-3">
                <label class="form-label">Department</label>
                <select class="form-select" id="department-filter">
                    <option value="">All Departments</option>
                    {% for dept in departments %}
                        <option value="{{ dept.id }}">{{ dept.name }}</option>
                    {% endfor %}
                </select>
            </div>
            <div class="col-md-3">
                <label class="form-label">Shift</label>
                <select class="form-select" id="shift-filter">
                    <option value="">All Shifts</option>
                    {% for shift in shifts %}
                        <option value="{{ shift.id }}">{{ shift.name }}</option>
                    {% endfor %}
                </select>
            </div>
            <div class="col-md-3">
                <label class="form-label">Status</label>
                <select class="form-select" id="status-filter">
                    <option value="">All Status</option>
                    <option value="active">Active</option>
                    <option value="inactive">Inactive</option>
                </select>
            </div>
            <div class="col-md-3">
                <label class="form-label">Assignment Type</label>
                <select class="form-select" id="type-filter">
                    <option value="">All Types</option>
                    <option value="permanent">Permanent</option>
                    <option value="temporary">Temporary</option>
                </select>
            </div>
        </div>

        <!-- Search Bar -->
        <div class="row mb-4">
            <div class="col">
                <div class="input-group">
                    <input type="text" class="form-control" id="search-input" 
                           placeholder="Search by employee name or number...">
                    <button class="btn btn-outline-secondary" type="button" id="search-btn">
                        <i class="fas fa-search"></i>
                    </button>
                </div>
            </div>
        </div>

        <!-- Assignments Table -->
        <div class="table-responsive">
            <table class="table table-hover">
                <thead>
                    <tr>
                        <th>Employee</th>
                        <th>Department</th>
                        <th>Shift</th>
                        <th>Period</th>
                        <th>Status</th>
                        <th>Created</th>
                        <th>Actions</th>
                    </tr>
                </thead>
                <tbody id="assignments-tbody">
                    {% for assignment in page_obj %}
                    <tr>
                        <td>
                            <div>{{ assignment.employee.get_full_name }}</div>
                            <small class="text-muted">{{ assignment.employee.employee_number }}</small>
                        </td>
                        <td>{{ assignment.employee.department.name|default:'-' }}</td>
                        <td>
                            <div>{{ assignment.shift.name }}</div>
                            <small class="text-muted">
                                {{ assignment.shift.start_time|time:"g:i A" }} - {{ assignment.shift.end_time|time:"g:i A" }}
                            </small>
                        </td>
                        <td>
                            <div>{{ assignment.start_date|date:"M d, Y" }}</div>
                            {% if assignment.end_date %}
                                <small class="text-muted">Until {{ assignment.end_date|date:"M d, Y" }}</small>
                            {% else %}
                                <small class="text-success">Permanent</small>
                            {% endif %}
                        </td>
                        <td>
                            <span class="badge {% if assignment.is_active %}bg-success{% else %}bg-danger{% endif %}">
                                {% if assignment.is_active %}Active{% else %}Inactive{% endif %}
                            </span>
                        </td>
                        <td>
                            <div>{{ assignment.created_by.get_full_name }}</div>
                            <small class="text-muted">{{ assignment.created_at|date:"M d, Y" }}</small>
                        </td>
                        <td>
                            <div class="btn-group">
                                <a href="{% url 'attendance:shift_assignment_edit' assignment.id %}" 
                                   class="btn btn-sm btn-outline-primary" title="Edit">
                                    <i class="fas fa-edit"></i>
                                </a>
                                <button type="button" class="btn btn-sm btn-outline-danger" 
                                        onclick="confirmDelete('{{ assignment.id }}')" title="Delete">
                                    <i class="fas fa-trash"></i>
                                </button>
                            </div>
                        </td>
                    </tr>
                    {% empty %}
                    <tr>
                        <td colspan="7" class="text-center py-4">
                            <div class="text-muted">
                                <i class="fas fa-info-circle me-2"></i>No shift assignments found
                            </div>
                        </td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>

        <!-- Pagination -->
        {% if page_obj.has_other_pages %}
        <nav aria-label="Shift assignments pagination" class="mt-4">
            <ul class="pagination justify-content-center">
                {% if page_obj.has_previous %}
                <li class="page-item">
                    <a class="page-link" href="?page=1" aria-label="First">
                        <span aria-hidden="true">&laquo;&laquo;</span>
                    </a>
                </li>
                <li class="page-item">
                    <a class="page-link" href="?page={{ page_obj.previous_page_number }}" aria-label="Previous">
                        <span aria-hidden="true">&laquo;</span>
                    </a>
                </li>
                {% endif %}

                {% for num in page_obj.paginator.page_range %}
                    {% if num == page_obj.number %}
                    <li class="page-item active">
                        <span class="page-link">{{ num }}</span>
                    </li>
                    {% elif num > page_obj.number|add:'-3' and num < page_obj.number|add:'3' %}
                    <li class="page-item">
                        <a class="page-link" href="?page={{ num }}">{{ num }}</a>
                    </li>
                    {% endif %}
                {% endfor %}

                {% if page_obj.has_next %}
                <li class="page-item">
                    <a class="page-link" href="?page={{ page_obj.next_page_number }}" aria-label="Next">
                        <span aria-hidden="true">&raquo;</span>
                    </a>
                </li>
                <li class="page-item">
                    <a class="page-link" href="?page={{ page_obj.paginator.num_pages }}" aria-label="Last">
                        <span aria-hidden="true">&raquo;&raquo;</span>
                    </a>
                </li>
                {% endif %}
            </ul>
        </nav>
        {% endif %}
    </div>
</div>

<!-- Delete Confirmation Modal -->
<div class="modal fade" id="deleteModal" tabindex="-1">
    <div class="modal-dialog">
        <div class="modal-content">
            <div class="modal-header">
                <h5 class="modal-title">Confirm Delete</h5>
                <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
            </div>
            <div class="modal-body">
                <p>Are you sure you want to delete this shift assignment? This action cannot be undone.</p>
            </div>
            <div class="modal-footer">
                <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
                <form id="deleteForm" method="post" style="display: inline;">
                    {% csrf_token %}
                    <button type="submit" class="btn btn-danger">Delete</button>
                </form>
            </div>
        </div>
    </div>
</div>

{% endblock %}

{% block extra_js %}
{{ block.super }}
<script>
// Filter functionality
document.addEventListener('DOMContentLoaded', function() {
    const filters = {
        department: document.getElementById('department-filter'),
        shift: document.getElementById('shift-filter'),
        status: document.getElementById('status-filter'),
        type: document.getElementById('type-filter'),
        search: document.getElementById('search-input')
    };

    function applyFilters() {
        const params = new URLSearchParams(window.location.search);
        
        // Update params based on filter values
        Object.keys(filters).forEach(key => {
            const value = filters[key].value;
            if (value) {
                params.set(key, value);
            } else {
                params.delete(key);
            }
        });

        // Reset to first page when filtering
        params.set('page', '1');
        
        // Update URL and reload
        window.location.search = params.toString();
    }

    // Add change event listeners to all filters
    Object.values(filters).forEach(filter => {
        filter.addEventListener('change', applyFilters);
    });

    // Add search button click handler
    document.getElementById('search-btn').addEventListener('click', applyFilters);

    // Add enter key handler for search input
    filters.search.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            applyFilters();
        }
    });

    // Set initial filter values from URL params
    const params = new URLSearchParams(window.location.search);
    Object.keys(filters).forEach(key => {
        const value = params.get(key);
        if (value) {
            filters[key].value = value;
        }
    });
});

function confirmDelete(assignmentId) {
    const modal = new bootstrap.Modal(document.getElementById('deleteModal'));
    const form = document.getElementById('deleteForm');
    form.action = `/attendance/shifts/assignments/${assignmentId}/delete/`;
    modal.show();
}
</script>
{% endblock %}

```

### hrms_project\attendance\templates\attendance\shifts\ramadan_periods.html
```
{% extends 'attendance/base.html' %}
{% load static %}

{% block extra_css %}
{{ block.super }}
<style>
.validation-message {
    margin-top: 0.5rem;
    font-size: 0.875rem;
}
</style>
{% endblock %}

{% block attendance_content %}
<div class="card">
    <div class="card-header">
        <div class="d-flex justify-content-between align-items-center">
            <h5 class="mb-0">Ramadan Periods</h5>
            <button class="btn btn-primary" data-bs-toggle="modal" data-bs-target="#addPeriodModal">
                <i class="fas fa-plus"></i> Add New Period
            </button>
        </div>
    </div>
    <div class="card-body">
        <div class="table-responsive">
            <table class="table table-hover">
                <thead>
                    <tr>
                        <th>Year</th>
                        <th>Start Date</th>
                        <th>End Date</th>
                        <th>Duration</th>
                        <th>Status</th>
                        <th>Actions</th>
                    </tr>
                </thead>
                <tbody>
                    {% for period in periods %}
                    <tr>
                        <td>{{ period.year }}</td>
                        <td>{{ period.start_date|date:"M d, Y" }}</td>
                        <td>{{ period.end_date|date:"M d, Y" }}</td>
                        <td>{{ period.duration }} days</td>
                        <td>
                            <span class="badge {% if period.is_active %}bg-success{% else %}bg-danger{% endif %}">
                                {% if period.is_active %}Active{% else %}Inactive{% endif %}
                            </span>
                        </td>
                        <td>
                            <div class="btn-group">
                                <button class="btn btn-sm btn-outline-primary" 
                                        onclick="ramadanManager.editPeriod({{ period.id }})"
                                        title="Edit">
                                    <i class="fas fa-edit"></i>
                                </button>
                                <button class="btn btn-sm btn-outline-danger" 
                                        onclick="ramadanManager.confirmDelete({{ period.id }})"
                                        title="Delete">
                                    <i class="fas fa-trash"></i>
                                </button>
                            </div>
                        </td>
                    </tr>
                    {% empty %}
                    <tr>
                        <td colspan="6" class="text-center py-4">
                            <div class="text-muted">
                                <i class="fas fa-calendar-times me-2"></i>No Ramadan periods defined
                            </div>
                        </td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
    </div>
</div>

<!-- Add Period Modal -->
<div class="modal fade" id="addPeriodModal" tabindex="-1">
    <div class="modal-dialog">
        <div class="modal-content">
            <div class="modal-header">
                <h5 class="modal-title">Add Ramadan Period</h5>
                <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
            </div>
            <div class="modal-body">
                <form id="addPeriodForm">
                    <div class="mb-3">
                        <label class="form-label">Year*</label>
                        <input type="number" class="form-control" name="year" id="year" required
                               min="2020" max="2050">
                    </div>
                    <div class="mb-3">
                        <label class="form-label">Start Date*</label>
                        <input type="date" class="form-control" name="start_date" id="start_date" required>
                    </div>
                    <div class="mb-3">
                        <label class="form-label">End Date*</label>
                        <input type="date" class="form-control" name="end_date" id="end_date" required>
                    </div>
                    <div id="periodValidation" class="alert alert-info d-none validation-message">
                        <i class="fas fa-info-circle me-2"></i>
                        <span id="validationMessage"></span>
                    </div>
                </form>
            </div>
            <div class="modal-footer">
                <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
                <button type="button" class="btn btn-primary" onclick="ramadanManager.savePeriod()">Save Period</button>
            </div>
        </div>
    </div>
</div>

<!-- Edit Period Modal -->
<div class="modal fade" id="editPeriodModal" tabindex="-1">
    <div class="modal-dialog">
        <div class="modal-content">
            <div class="modal-header">
                <h5 class="modal-title">Edit Ramadan Period</h5>
                <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
            </div>
            <div class="modal-body">
                <form id="editPeriodForm">
                    <input type="hidden" id="edit_period_id">
                    <div class="mb-3">
                        <label class="form-label">Year*</label>
                        <input type="number" class="form-control" name="year" id="edit_year" required
                               min="2020" max="2050">
                    </div>
                    <div class="mb-3">
                        <label class="form-label">Start Date*</label>
                        <input type="date" class="form-control" name="start_date" id="edit_start_date" required>
                    </div>
                    <div class="mb-3">
                        <label class="form-label">End Date*</label>
                        <input type="date" class="form-control" name="end_date" id="edit_end_date" required>
                    </div>
                    <div class="mb-3">
                        <div class="form-check form-switch">
                            <input type="checkbox" class="form-check-input" name="is_active" id="edit_is_active">
                            <label class="form-check-label">Active</label>
                        </div>
                    </div>
                    <div id="editValidation" class="alert alert-info d-none validation-message">
                        <i class="fas fa-info-circle me-2"></i>
                        <span id="editValidationMessage"></span>
                    </div>
                </form>
            </div>
            <div class="modal-footer">
                <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
                <button type="button" class="btn btn-primary" onclick="ramadanManager.updatePeriod()">Update Period</button>
            </div>
        </div>
    </div>
</div>

<!-- Delete Confirmation Modal -->
<div class="modal fade" id="deleteModal" tabindex="-1">
    <div class="modal-dialog">
        <div class="modal-content">
            <div class="modal-header">
                <h5 class="modal-title">Confirm Delete</h5>
                <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
            </div>
            <div class="modal-body">
                <p>Are you sure you want to delete this Ramadan period? This action cannot be undone.</p>
            </div>
            <div class="modal-footer">
                <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
                <button type="button" class="btn btn-danger" onclick="ramadanManager.deletePeriod()">Delete</button>
            </div>
        </div>
    </div>
</div>
{% endblock %}

{% block extra_js %}
{{ block.super }}
<script src="{% static 'attendance/js/ramadan.js' %}"></script>
{% endblock %}

```

### hrms_project\attendance\templates\attendance\shifts\shift_form.html
```
{% extends 'attendance/base.html' %}
{% load static %}

{% block attendance_content %}
<div class="card">
    <div class="card-header">
        <h5 class="mb-0">{% if shift %}Edit{% else %}Create{% endif %} Shift</h5>
    </div>
    <div class="card-body">
        <form method="post" id="shift-form">
            {% csrf_token %}
            
            <div class="row">
                <!-- Basic Information -->
                <div class="col-md-6">
                    <div class="mb-3">
                        <label class="form-label">Name*</label>
                        <input type="text" class="form-control" name="name" 
                               value="{{ shift.name|default:'' }}" required>
                    </div>

                    <div class="mb-3">
                        <label class="form-label">Shift Type*</label>
                        <select class="form-select" name="shift_type" required>
                            <option value="">Select Shift Type</option>
                            {% for type, label in shift_types %}
                                <option value="{{ type }}" {% if shift.shift_type == type %}selected{% endif %}>
                                    {{ label }}
                                </option>
                            {% endfor %}
                        </select>
                    </div>
                </div>

                <!-- Timing Information -->
                <div class="col-md-6">
                    <div class="mb-3">
                        <label class="form-label">Start Time*</label>
                        <input type="time" class="form-control" name="start_time" 
                               value="{{ shift.start_time|time:'H:i'|default:'' }}" required>
                    </div>

                    <div class="mb-3">
                        <label class="form-label">End Time*</label>
                        <input type="time" class="form-control" name="end_time" 
                               value="{{ shift.end_time|time:'H:i'|default:'' }}" required>
                    </div>
                </div>

                <!-- Additional Settings -->
                <div class="col-md-6">
                    <div class="mb-3">
                        <label class="form-label">Grace Period (minutes)</label>
                        <input type="number" class="form-control" name="grace_period" 
                               value="{{ shift.grace_period|default:'15' }}" min="0" max="60">
                        <small class="text-muted">
                            Allowed late arrival time before marking attendance as late
                        </small>
                    </div>

                    <div class="mb-3">
                        <label class="form-label">Break Duration (minutes)</label>
                        <input type="number" class="form-control" name="break_duration" 
                               value="{{ shift.break_duration|default:'60' }}" min="0" max="180">
                        <small class="text-muted">
                            Official break time during the shift
                        </small>
                    </div>
                </div>

                <!-- Status -->
                <div class="col-md-6">
                    <div class="mb-3">
                        <div class="form-check form-switch">
                            <input type="checkbox" class="form-check-input" name="is_night_shift" id="is_night_shift"
                                   {% if shift.is_night_shift %}checked{% endif %}>
                            <label class="form-check-label" for="is_night_shift">Night Shift</label>
                        </div>
                        <small class="text-muted">
                            Enable for shifts that span across midnight
                        </small>
                    </div>

                    <div class="mb-3">
                        <div class="form-check form-switch">
                            <input type="checkbox" class="form-check-input" name="is_active" id="is_active"
                                   {% if shift.is_active or shift is None %}checked{% endif %}>
                            <label class="form-check-label" for="is_active">Active</label>
                        </div>
                        <small class="text-muted">
                            Inactive shifts cannot be assigned to employees
                        </small>
                    </div>
                </div>
            </div>

            <!-- Submit Buttons -->
            <div class="mt-4">
                <button type="submit" class="btn btn-primary">
                    {% if shift %}Save Changes{% else %}Create Shift{% endif %}
                </button>
                <a href="{% url 'attendance:shift_list' %}" class="btn btn-secondary">Cancel</a>
            </div>
        </form>
    </div>
</div>
{% endblock %}

{% block extra_js %}
{{ block.super }}
<script>
document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('shift-form');
    const startTimeInput = form.querySelector('[name="start_time"]');
    const endTimeInput = form.querySelector('[name="end_time"]');
    const isNightShiftCheckbox = document.getElementById('is_night_shift');

    // Function to check if end time is before start time (indicating night shift)
    function checkNightShift() {
        const startTime = startTimeInput.value;
        const endTime = endTimeInput.value;
        
        if (startTime && endTime) {
            const start = new Date(`2000-01-01T${startTime}`);
            const end = new Date(`2000-01-01T${endTime}`);
            
            if (end < start) {
                isNightShiftCheckbox.checked = true;
            }
        }
    }

    // Add event listeners
    [startTimeInput, endTimeInput].forEach(input => {
        input.addEventListener('change', checkNightShift);
    });

    // Form validation
    form.addEventListener('submit', function(e) {
        const startTime = startTimeInput.value;
        const endTime = endTimeInput.value;
        
        if (startTime === endTime) {
            e.preventDefault();
            alert('Start time and end time cannot be the same');
            return;
        }
        
        const start = new Date(`2000-01-01T${startTime}`);
        const end = new Date(`2000-01-01T${endTime}`);
        
        // If end time is before start time and not marked as night shift
        if (end < start && !isNightShiftCheckbox.checked) {
            e.preventDefault();
            if (confirm('This appears to be a night shift. Would you like to mark it as such?')) {
                isNightShiftCheckbox.checked = true;
                form.submit();
            }
        }
    });
});
</script>
{% endblock %}

```

### hrms_project\attendance\templates\attendance\shifts\shift_list.html
```
{% extends 'attendance/base.html' %}
{% load static %}

{% block attendance_content %}
<div class="card">
    <div class="card-header">
        <div class="d-flex justify-content-between align-items-center">
            <h5 class="mb-0">Shifts</h5>
            <div>
                <a href="{% url 'attendance:shift_create' %}" class="btn btn-primary">
                    <i class="fas fa-plus"></i> New Shift
                </a>
                <a href="{% url 'attendance:shift_assignment_create' %}" class="btn btn-success">
                    <i class="fas fa-user-clock"></i> Assign Shift
                </a>
            </div>
        </div>
    </div>
    <div class="card-body">
        <!-- Tabs -->
        <ul class="nav nav-tabs mb-3" id="shiftTabs" role="tablist">
            <li class="nav-item" role="presentation">
                <button class="nav-link active" id="shifts-tab" data-bs-toggle="tab" data-bs-target="#shifts" 
                        type="button" role="tab" aria-controls="shifts" aria-selected="true">
                    Shift Types
                </button>
            </li>
            <li class="nav-item" role="presentation">
                <button class="nav-link" id="assignments-tab" data-bs-toggle="tab" data-bs-target="#assignments" 
                        type="button" role="tab" aria-controls="assignments" aria-selected="false">
                    Shift Assignments
                </button>
            </li>
        </ul>

        <!-- Tab Content -->
        <div class="tab-content" id="shiftTabsContent">
            <!-- Shifts Tab -->
            <div class="tab-pane fade show active" id="shifts" role="tabpanel" aria-labelledby="shifts-tab">
                <div class="table-responsive">
                    <table class="table table-hover">
                        <thead>
                            <tr>
                                <th>Name</th>
                                <th>Type</th>
                                <th>Timing</th>
                                <th>Grace Period</th>
                                <th>Break Duration</th>
                                <th>Status</th>
                                <th>Actions</th>
                            </tr>
                        </thead>
                        <tbody>
                            {% for shift in shifts %}
                            <tr>
                                <td>{{ shift.name }}</td>
                                <td>{{ shift.get_shift_type_display }}</td>
                                <td>
                                    {{ shift.start_time|time:"g:i A" }} - {{ shift.end_time|time:"g:i A" }}
                                    {% if shift.is_night_shift %}
                                        <span class="badge bg-dark ms-1">Night</span>
                                    {% endif %}
                                </td>
                                <td>{{ shift.grace_period }} minutes</td>
                                <td>{{ shift.break_duration }} minutes</td>
                                <td>
                                    <span class="badge {% if shift.is_active %}bg-success{% else %}bg-danger{% endif %}">
                                        {% if shift.is_active %}Active{% else %}Inactive{% endif %}
                                    </span>
                                </td>
                                <td>
                                    <a href="{% url 'attendance:shift_edit' shift.id %}" 
                                       class="btn btn-sm btn-outline-primary me-1">
                                        <i class="fas fa-edit"></i>
                                    </a>
                                </td>
                            </tr>
                            {% empty %}
                            <tr>
                                <td colspan="7" class="text-center">No shifts found.</td>
                            </tr>
                            {% endfor %}
                        </tbody>
                    </table>
                </div>
            </div>

            <!-- Assignments Tab -->
            <div class="tab-pane fade" id="assignments" role="tabpanel" aria-labelledby="assignments-tab">
                <div class="table-responsive">
                    <table class="table table-hover">
                        <thead>
                            <tr>
                                <th>Employee</th>
                                <th>Shift</th>
                                <th>Start Date</th>
                                <th>End Date</th>
                                <th>Status</th>
                                <th>Created By</th>
                                <th>Actions</th>
                            </tr>
                        </thead>
                        <tbody>
                            {% for assignment in page_obj %}
                            <tr>
                                <td>
                                    {{ assignment.employee.get_full_name }}
                                    <small class="text-muted d-block">
                                        {{ assignment.employee.employee_number }}
                                    </small>
                                </td>
                                <td>{{ assignment.shift.name }}</td>
                                <td>{{ assignment.start_date|date:"M d, Y" }}</td>
                                <td>
                                    {% if assignment.end_date %}
                                        {{ assignment.end_date|date:"M d, Y" }}
                                    {% else %}
                                        <span class="text-muted">Permanent</span>
                                    {% endif %}
                                </td>
                                <td>
                                    <span class="badge {% if assignment.is_active %}bg-success{% else %}bg-danger{% endif %}">
                                        {% if assignment.is_active %}Active{% else %}Inactive{% endif %}
                                    </span>
                                </td>
                                <td>
                                    <small>{{ assignment.created_by.get_full_name }}</small>
                                    <small class="text-muted d-block">
                                        {{ assignment.created_at|date:"M d, Y" }}
                                    </small>
                                </td>
                                <td>
                                    <div class="btn-group">
                                        <a href="{% url 'attendance:shift_assignment_edit' assignment.id %}"
                                           class="btn btn-sm btn-outline-primary">
                                            <i class="fas fa-edit"></i>
                                        </a>
                                        <button type="button" class="btn btn-sm btn-outline-danger"
                                                onclick="confirmDelete('{{ assignment.id }}')">
                                            <i class="fas fa-trash"></i>
                                        </button>
                                    </div>
                                </td>
                            </tr>
                            {% empty %}
                            <tr>
                                <td colspan="7" class="text-center">No shift assignments found.</td>
                            </tr>
                            {% endfor %}
                        </tbody>
                    </table>
                </div>

                {% if page_obj.has_other_pages %}
                <nav aria-label="Shift assignments pagination" class="mt-3">
                    <ul class="pagination justify-content-center">
                        {% if page_obj.has_previous %}
                        <li class="page-item">
                            <a class="page-link" href="?page=1" aria-label="First">
                                <span aria-hidden="true">&laquo;&laquo;</span>
                            </a>
                        </li>
                        <li class="page-item">
                            <a class="page-link" href="?page={{ page_obj.previous_page_number }}" aria-label="Previous">
                                <span aria-hidden="true">&laquo;</span>
                            </a>
                        </li>
                        {% endif %}

                        {% for num in page_obj.paginator.page_range %}
                            {% if num == page_obj.number %}
                            <li class="page-item active">
                                <span class="page-link">{{ num }}</span>
                            </li>
                            {% elif num > page_obj.number|add:'-3' and num < page_obj.number|add:'3' %}
                            <li class="page-item">
                                <a class="page-link" href="?page={{ num }}">{{ num }}</a>
                            </li>
                            {% endif %}
                        {% endfor %}

                        {% if page_obj.has_next %}
                        <li class="page-item">
                            <a class="page-link" href="?page={{ page_obj.next_page_number }}" aria-label="Next">
                                <span aria-hidden="true">&raquo;</span>
                            </a>
                        </li>
                        <li class="page-item">
                            <a class="page-link" href="?page={{ page_obj.paginator.num_pages }}" aria-label="Last">
                                <span aria-hidden="true">&raquo;&raquo;</span>
                            </a>
                        </li>
                        {% endif %}
                    </ul>
                </nav>
                {% endif %}
            </div>
        </div>
    </div>
</div>

<!-- Delete Confirmation Modal -->
<div class="modal fade" id="deleteModal" tabindex="-1">
    <div class="modal-dialog">
        <div class="modal-content">
            <div class="modal-header">
                <h5 class="modal-title">Confirm Delete</h5>
                <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
            </div>
            <div class="modal-body">
                <p>Are you sure you want to delete this shift assignment? This action cannot be undone.</p>
            </div>
            <div class="modal-footer">
                <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
                <form id="deleteForm" method="post" style="display: inline;">
                    {% csrf_token %}
                    <button type="submit" class="btn btn-danger">Delete</button>
                </form>
            </div>
        </div>
    </div>
</div>

{% endblock %}

{% block extra_js %}
{{ block.super }}
<script>
function confirmDelete(assignmentId) {
    const modal = new bootstrap.Modal(document.getElementById('deleteModal'));
    const form = document.getElementById('deleteForm');
    form.action = `/attendance/shift_assignment_delete/${assignmentId}/`;
    modal.show();
}

// Store active tab in session storage
document.addEventListener('DOMContentLoaded', function() {
    const activeTab = sessionStorage.getItem('activeShiftTab');
    if (activeTab) {
        const tab = new bootstrap.Tab(document.querySelector(`#shiftTabs button[data-bs-target="${activeTab}"]`));
        tab.show();
    }

    document.querySelectorAll('#shiftTabs button').forEach(button => {
        button.addEventListener('shown.bs.tab', function(event) {
            sessionStorage.setItem('activeShiftTab', event.target.dataset.bsTarget);
        });
    });
});
</script>
{% endblock %}

```

### hrms_project\attendance\templates\attendance\upload_attendance.html
```
{% extends "core/base.html" %}
{% load static %}

{% block title %}Upload Attendance Records{% endblock %}

{% block extra_css %}
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/5.15.4/css/all.min.css">
<style>
.preview-table {
    font-size: 0.875rem;
}
.preview-table th {
    background-color: #f8f9fa;
}
.preview-container {
    max-height: 300px;
    overflow-y: auto;
    overflow-x: auto;
}
.new-employees-list {
    max-height: 200px;
    overflow-y: auto;
}
.small {
    font-size: 0.75em;
}
</style>
{% endblock %}

{% block content %}
<div class="container mt-4">
    <div class="card">
        <div class="card-header">
            <h5 class="mb-0">Upload Attendance Records</h5>
        </div>
        <div class="card-body">
            <form id="uploadForm" enctype="multipart/form-data">
                {% csrf_token %}
                <div class="mb-3">
                    <label for="file" class="form-label">Excel File</label>
                    <input type="file" class="form-control" id="file" name="file" accept=".xlsx,.xls" required>
                    <div class="form-text">
                        <strong>Required columns:</strong>
                        <ul class="mb-0">
                            <li>Date And Time</li>
                            <li>Personnel ID</li>
                            <li>Device Name</li>
                            <li>Event Point</li>
                            <li>Verify Type</li>
                            <li>Event Description</li>
                            <li>Remarks</li>
                        </ul>
                    </div>
                </div>
                
                <!-- File Preview -->
                <div id="previewContainer" class="mb-3" style="display: none;">
                    <h6>File Preview</h6>
                    <div class="preview-container">
                        <table class="table table-sm table-bordered preview-table">
                            <thead id="previewHeader"></thead>
                            <tbody id="previewBody"></tbody>
                        </table>
                    </div>
                    <small class="text-muted">Showing first 5 rows</small>
                </div>
                
                <button type="submit" class="btn btn-primary" id="submitBtn">Upload</button>
            </form>
            
            <!-- Result Messages -->
            <div id="successAlert" class="alert alert-success mt-3" style="display: none;">
                <h6 class="alert-heading mb-2">Upload Summary:</h6>
                <ul class="mb-0">
                    <li>New records added: <span id="newRecords">0</span></li>
                    <li>Duplicate records skipped: <span id="duplicateRecords">0</span></li>
                    <li>Total records in database: <span id="totalRecords">0</span></li>
                    <li>Attendance logs created: <span id="logsCreated">0</span></li>
                </ul>
                
                <!-- New Employees Section -->
                <div id="newEmployeesSection" class="mt-3" style="display: none;">
                    <h6 class="alert-heading mb-2">New Employees Created:</h6>
                    <div class="new-employees-list">
                        <table class="table table-sm table-bordered mb-0">
                            <thead>
                                <tr>
                                    <th>ID</th>
                                    <th>Personnel ID</th>
                                    <th>Name</th>
                                </tr>
                            </thead>
                            <tbody id="newEmployeesList"></tbody>
                        </table>
                    </div>
                </div>
            </div>
            <div id="errorAlert" class="alert alert-danger mt-3" style="display: none;">
                <div id="errorMessage"></div>
            </div>
        </div>
    </div>
</div>
{% endblock %}

{% block extra_js %}
<script src="https://cdnjs.cloudflare.com/ajax/libs/xlsx/0.18.5/xlsx.full.min.js"></script>
<script>
// Preview functionality
document.getElementById('file').addEventListener('change', function(e) {
    const file = e.target.files[0];
    if (!file) return;
    
    const reader = new FileReader();
    reader.onload = function(e) {
        try {
            const data = new Uint8Array(e.target.result);
            const workbook = XLSX.read(data, {type: 'array'});
            
            // Get first sheet
            const firstSheet = workbook.Sheets[workbook.SheetNames[0]];
            
            // Convert to JSON
            const jsonData = XLSX.utils.sheet_to_json(firstSheet, {header: 1});
            
            if (jsonData.length > 0) {
                const headerRow = jsonData[0];
                const dataRows = jsonData.slice(1, 6); // Get first 5 data rows
                
                // Create header
                const headerHtml = '<tr>' + headerRow.map(cell => 
                    `<th>${cell}</th>`
                ).join('') + '</tr>';
                
                // Create body
                const bodyHtml = dataRows.map(row => 
                    '<tr>' + row.map(cell => 
                        `<td>${cell || ''}</td>`
                    ).join('') + '</tr>'
                ).join('');
                
                // Update preview
                document.getElementById('previewHeader').innerHTML = headerHtml;
                document.getElementById('previewBody').innerHTML = bodyHtml;
                document.getElementById('previewContainer').style.display = 'block';
            }
        } catch (error) {
            console.error('Error reading file:', error);
        }
    };
    reader.readAsArrayBuffer(file);
});

// Form submission
document.getElementById('uploadForm').addEventListener('submit', function(e) {
    e.preventDefault();
    
    const formData = new FormData(this);
    const successAlert = document.getElementById('successAlert');
    const errorAlert = document.getElementById('errorAlert');
    const errorMessage = document.getElementById('errorMessage');
    const submitBtn = document.getElementById('submitBtn');
    const newEmployeesSection = document.getElementById('newEmployeesSection');
    
    // Hide any existing alerts
    successAlert.style.display = 'none';
    errorAlert.style.display = 'none';
    newEmployeesSection.style.display = 'none';
    
    // Disable submit button and show loading state
    submitBtn.disabled = true;
    submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Uploading...';
    
    fetch('/attendance/api/records/upload_excel/', {
        method: 'POST',
        body: formData,
        headers: {
            'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            document.getElementById('newRecords').textContent = data.new_records;
            document.getElementById('duplicateRecords').textContent = data.duplicate_records;
            document.getElementById('totalRecords').textContent = data.total_records;
            document.getElementById('logsCreated').textContent = data.logs_created;
            
            // Display new employees if any
            if (data.new_employees && data.new_employees.length > 0) {
                const newEmployeesList = document.getElementById('newEmployeesList');
                newEmployeesList.innerHTML = data.new_employees.map(emp => `
                    <tr>
                        <td>${emp.id}</td>
                        <td>${emp.employee_number}</td>
                        <td>
                            <a href="/employees/${emp.id}/" class="text-decoration-none">
                                ${emp.name}
                                <i class="fas fa-external-link-alt ms-1 small"></i>
                            </a>
                        </td>
                    </tr>
                `).join('');
                newEmployeesSection.style.display = 'block';
            }
            
            successAlert.style.display = 'block';
            this.reset();
            document.getElementById('previewContainer').style.display = 'none';
        } else {
            errorMessage.textContent = data.error;
            errorAlert.style.display = 'block';
        }
    })
    .catch(error => {
        errorMessage.textContent = 'Error uploading file: ' + error.message;
        errorAlert.style.display = 'block';
    })
    .finally(() => {
        // Re-enable submit button and restore text
        submitBtn.disabled = false;
        submitBtn.innerHTML = 'Upload';
    });
});
</script>
{% endblock %}

```

### hrms_project\attendance\templates\base.html
```
{% extends 'core/base.html' %}
{% load static %}

{% block extra_css %}
<!-- Bootstrap CSS -->
<link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
<!-- Font Awesome -->
<link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/5.15.4/css/all.min.css" rel="stylesheet">
<!-- FullCalendar CSS -->
<link href="https://cdn.jsdelivr.net/npm/fullcalendar@5.11.3/main.min.css" rel="stylesheet">
<!-- Custom attendance CSS -->
<link href="{% static 'attendance/css/attendance.css' %}" rel="stylesheet" />
{% endblock %}

{% block content %}
<div class="container-fluid mt-4">
    <div class="row">
        <!-- Sidebar -->
        <div class="col-md-3 col-lg-2">
            <div class="list-group">
                <a href="{% url 'attendance:attendance_list' %}" 
                   class="list-group-item list-group-item-action {% if request.resolver_match.url_name == 'attendance_list' %}active{% endif %}">
                    <i class="fas fa-clock"></i> Daily Attendance
                </a>
                <a href="{% url 'attendance:mark_attendance' %}"
                   class="list-group-item list-group-item-action {% if request.resolver_match.url_name == 'mark_attendance' %}active{% endif %}">
                    <i class="fas fa-edit"></i> Mark Attendance
                </a>
                <a href="{% url 'attendance:leave_request_list' %}"
                   class="list-group-item list-group-item-action {% if 'leave' in request.resolver_match.view_name %}active{% endif %}">
                    <i class="fas fa-calendar-minus"></i> Leave Management
                </a>
                <a href="{% url 'attendance:calendar' %}"
                   class="list-group-item list-group-item-action {% if request.resolver_match.url_name == 'calendar' %}active{% endif %}">
                    <i class="fas fa-calendar-alt"></i> Calendar View
                </a>
                <a href="{% url 'attendance:upload_attendance' %}"
                   class="list-group-item list-group-item-action {% if request.resolver_match.url_name == 'upload_attendance' %}active{% endif %}">
                    <i class="fas fa-upload"></i> Upload Attendance
                </a>
            </div>

            <!-- Status Legend -->
            <div class="card mt-3">
                <div class="card-header">
                    <h6 class="mb-0">Status Legend</h6>
                </div>
                <div class="card-body p-2">
                    <div class="d-flex align-items-center mb-2">
                        <div class="status-dot bg-success"></div>
                        <span class="ms-2">Present</span>
                    </div>
                    <div class="d-flex align-items-center mb-2">
                        <div class="status-dot bg-danger"></div>
                        <span class="ms-2">Absent</span>
                    </div>
                    <div class="d-flex align-items-center mb-2">
                        <div class="status-dot bg-warning"></div>
                        <span class="ms-2">Late</span>
                    </div>
                    <div class="d-flex align-items-center mb-2">
                        <div class="status-dot bg-info"></div>
                        <span class="ms-2">Leave</span>
                    </div>
                    <div class="d-flex align-items-center">
                        <div class="status-dot bg-primary"></div>
                        <span class="ms-2">Holiday</span>
                    </div>
                </div>
            </div>
        </div>

        <!-- Main Content -->
        <div class="col-md-9 col-lg-10">
            {% block attendance_content %}{% endblock %}
        </div>
    </div>
</div>
{% endblock %}

{% block extra_js %}
<!-- Bootstrap Bundle with Popper -->
<script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
<!-- jQuery -->
<script src="https://code.jquery.com/jquery-3.6.0.min.js"></script>
<!-- FullCalendar Bundle -->
<script src="https://cdn.jsdelivr.net/npm/fullcalendar@5.11.3/main.min.js"></script>
<!-- Custom attendance JS -->
<script src="{% static 'attendance/js/attendance.js' %}"></script>
{% endblock %}
```

### hrms_project\attendance\templatetags\__init__.py
```
"""
Template tags for attendance app.

Available template tags:
- format_time: Format time object as HH:MM AM/PM
- format_duration: Format duration in days, handling half days
- attendance_status_badge: Return HTML badge for attendance status
- leave_type_badge: Return HTML badge for leave type
- leave_balance_display: Display leave balance with consumed/remaining days
- monthly_attendance_summary: Generate monthly attendance summary
- is_holiday: Check if a date is a holiday
- get_leave_status: Get leave status for a date
- attendance_date_class: Return CSS class for calendar date based on attendance

Usage:
    {% load attendance_tags %}
    
    {{ time_value|format_time }}
    {{ duration_value|format_duration }}
    
    {% attendance_status_badge status is_late %}
    {% leave_type_badge leave_type %}
    {% leave_balance_display employee leave_type %}
    {% monthly_attendance_summary employee year month %}
    {% is_holiday date %}
    {% get_leave_status employee date %}
    {{ date|attendance_date_class:employee }}
"""

```

### hrms_project\attendance\templatetags\attendance_tags.py
```
from django import template
from django.utils import timezone
from django.utils.html import format_html
from datetime import datetime, time

from attendance.services import ShiftService, RamadanService
from attendance.models import AttendanceLog, Leave, Holiday

register = template.Library()

@register.filter
def format_time(value):
    """Format time object to 12-hour format"""
    if not value:
        return '-'
    if isinstance(value, str):
        try:
            value = datetime.strptime(value, '%H:%M:%S').time()
        except ValueError:
            return value
    return value.strftime('%I:%M %p')

@register.filter
def total_hours(minutes):
    """Convert minutes to hours and minutes format"""
    if not minutes:
        return '-'
    hours = minutes // 60
    remaining_minutes = minutes % 60
    return f"{hours}h {remaining_minutes}m"

@register.simple_tag
def get_attendance_status(employee, date=None):
    """Get attendance status with styled badge"""
    if not date:
        date = timezone.now().date()
    
    log = AttendanceLog.objects.filter(employee=employee, date=date).first()
    
    if not log:
        return format_html(
            '<span class="badge bg-secondary">No Record</span>'
        )
    
    if log.is_leave:
        return format_html(
            '<span class="badge bg-info">Leave</span>'
        )
    elif log.is_holiday:
        return format_html(
            '<span class="badge bg-primary">Holiday</span>'
        )
    elif not log.first_in_time:
        return format_html(
            '<span class="badge bg-danger">Absent</span>'
        )
    elif log.is_late:
        return format_html(
            '<span class="badge bg-warning text-dark">Late</span>'
        )
    else:
        return format_html(
            '<span class="badge bg-success">Present</span>'
        )

@register.simple_tag
def get_current_shift(employee, date=None):
    """Get employee's current shift with timing"""
    if not date:
        date = timezone.now().date()
    
    shift = ShiftService.get_employee_current_shift(employee)
    if not shift:
        return format_html(
            '<span class="text-muted">No Shift Assigned</span>'
        )
    
    # Check for Ramadan timing
    ramadan_timing = RamadanService.get_ramadan_shift_timing(shift, date)
    if ramadan_timing:
        start_time = ramadan_timing['start_time']
        end_time = ramadan_timing['end_time']
        return format_html(
            '{} ({} - {}) <span class="badge bg-info ms-1">Ramadan</span>',
            shift.name,
            format_time(start_time),
            format_time(end_time)
        )
    
    return format_html(
        '{} ({} - {})',
        shift.name,
        format_time(shift.start_time),
        format_time(shift.end_time)
    )

@register.simple_tag
def get_leave_balance(employee, leave_type):
    """Get employee's leave balance with color coding"""
    balance = employee.get_leave_balance(leave_type)
    color = 'success'
    if balance <= 0:
        color = 'danger'
    elif balance <= 5:
        color = 'warning'
        
    return format_html(
        '<span class="text-{}">{} days</span>',
        color, balance
    )

@register.filter
def is_holiday(date):
    """Check if date is a holiday"""
    return Holiday.objects.filter(date=date, is_active=True).exists()

@register.filter
def is_leave(employee, date):
    """Check if employee is on leave for given date"""
    return Leave.objects.filter(
        employee=employee,
        start_date__lte=date,
        end_date__gte=date,
        status='APPROVED'
    ).exists()

@register.filter
def attendance_timing(log):
    """Format attendance timing with status indicators"""
    if not log:
        return '-'
        
    in_time = format_time(log.first_in_time) if log.first_in_time else '-'
    out_time = format_time(log.last_out_time) if log.last_out_time else '-'
    
    timing = f"{in_time} - {out_time}"
    
    status_indicators = []
    if log.is_late:
        status_indicators.append(
            f'<span class="badge bg-warning text-dark ms-1" title="Late by {log.late_minutes} minutes">Late</span>'
        )
    if log.early_departure:
        status_indicators.append(
            f'<span class="badge bg-warning text-dark ms-1" title="Left early by {log.early_minutes} minutes">Early Out</span>'
        )
    
    if status_indicators:
        timing += ' ' + ' '.join(status_indicators)
    
    return format_html(timing)

@register.simple_tag
def shift_timing_display(shift, date=None):
    """Display shift timing with Ramadan adjustment if applicable"""
    if not date:
        date = timezone.now().date()
        
    ramadan_timing = RamadanService.get_ramadan_shift_timing(shift, date)
    if ramadan_timing:
        return format_html(
            '{} - {} <span class="badge bg-info ms-1">Ramadan</span>',
            format_time(ramadan_timing['start_time']),
            format_time(ramadan_timing['end_time'])
        )
    
    return format_html(
        '{} - {}',
        format_time(shift.start_time),
        format_time(shift.end_time)
    )

@register.filter
def work_hours_display(log):
    """Display work hours with color coding based on expected hours"""
    if not log or not log.total_work_minutes:
        return '-'
        
    expected_minutes = log.expected_work_minutes or 480  # Default 8 hours
    actual_minutes = log.total_work_minutes
    
    hours = actual_minutes / 60
    
    if actual_minutes >= expected_minutes:
        color = 'success'
    elif actual_minutes >= (expected_minutes * 0.75):
        color = 'warning'
    else:
        color = 'danger'
        
    return format_html(
        '<span class="text-{}">{:.1f}h</span>',
        color, hours
    )

@register.simple_tag(takes_context=True)
def get_shift_assignments(context, employee):
    """Get list of shift assignments for display"""
    assignments = employee.shiftassignment_set.filter(
        is_active=True
    ).select_related('shift').order_by('-start_date')[:5]
    
    result = []
    for assignment in assignments:
        timing = shift_timing_display(assignment.shift)
        period = "Permanent" if not assignment.end_date else f"Until {assignment.end_date.strftime('%b %d, %Y')}"
        
        result.append({
            'shift': assignment.shift.name,
            'timing': timing,
            'period': period,
            'start_date': assignment.start_date
        })
    
    return result

```

### hrms_project\attendance\tests\test_cache.py
```
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

```

### hrms_project\attendance\tests\test_cleanup_shifts.py
```
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

```

### hrms_project\attendance\tests\test_ramadan.py
```
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

```

### hrms_project\attendance\tests\test_shifts.py
```
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

```

### hrms_project\attendance\tests\test_timing.py
```
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

```

### hrms_project\attendance\urls.py
```
from django.urls import path
from rest_framework.routers import DefaultRouter
from . import views

app_name = 'attendance'

# Create a router and register the ShiftViewSet
router = DefaultRouter()
router.register(r'api/shifts', views.ShiftViewSet, basename='shift')

urlpatterns = [
    # Existing URLs
    path('attendance_list/', views.attendance_list, name='attendance_list'),
    path('calendar/', views.calendar_view, name='calendar'),
    path('calendar/month/', views.calendar_month, name='calendar_month'),
    path('calendar/week/', views.calendar_week, name='calendar_week'),
    path('calendar/department/', views.calendar_department, name='calendar_department'),
    path('mark_attendance/', views.mark_attendance, name='mark_attendance'),
    path('leave_request_list/', views.leave_request_list, name='leave_request_list'),
    path('detail/', views.attendance_detail_view, name='attendance_detail'),

    path('leave_request_create/', views.leave_request_create, name='leave_request_create'),
    path('leave_request_detail/<int:pk>/', views.leave_request_detail, name='leave_request_detail'),
    path('upload_attendance/', views.upload_attendance, name='upload_attendance'),
    path('attendance_report/', views.attendance_report, name='attendance_report'),
    path('holiday_list/', views.holiday_list, name='holiday_list'),
    path('holiday_create/', views.holiday_create, name='holiday_create'),
    path('recurring_holidays/', views.recurring_holidays, name='recurring_holidays'),
    path('leave_balance/', views.leave_balance, name='leave_balance'),
    path('leave_types/', views.leave_types, name='leave_types'),
    path('get_department_employees/', views.get_department_employees, name='get_department_employees'),
    
    # API endpoints
    path('api/get_calendar_events/', views.get_calendar_events, name='get_calendar_events'),
    path('api/get_employee_attendance/<int:employee_id>/', views.get_employee_attendance, name='get_employee_attendance'),
    path('api/attendance_detail/', views.attendance_detail_api, name='attendance_detail_api'),
    path('api/attendance_record/<int:record_id>/', views.attendance_record_api, name='attendance_record_api'),
    path('api/add_attendance_record/', views.add_attendance_record, name='add_attendance_record'),
    path('api/search_employees/', views.search_employees, name='search_employees'),
    path('api/calendar_events/', views.calendar_events, name='calendar_events'),
    path('api/attendance_details/', views.attendance_details, name='attendance_details'),
    
    # Ramadan Period URLs
    path('ramadan_periods/', views.ramadan_periods, name='ramadan_periods'),
    path('ramadan_period_add/', views.ramadan_period_add, name='ramadan_period_add'),
    path('ramadan_period_detail/<int:pk>/', views.ramadan_period_detail, name='ramadan_period_detail'),
]

# Add the router URLs to the urlpatterns
urlpatterns += router.urls

```

### hrms_project\attendance\utils\timing.py
```
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

```

### hrms_project\attendance\utils.py
```
import pandas as pd
from datetime import datetime, time, timedelta
from django.utils import timezone
from django.db import transaction
from .models import AttendanceRecord, AttendanceLog
from employees.models import Employee

def process_attendance_excel(file_path):
    """
    Process attendance Excel file from the machine
    Expected columns: Date And Time, Personnel ID, Device Name, Event Point, 
                     Verify Type, Event Description, Remarks
    Returns: records_created, duplicates, total_records, new_employees, unique_dates
    """
    try:
        # Determine the engine based on file extension
        file_extension = str(file_path).lower()
        engine = 'xlrd' if file_extension.endswith('.xls') else 'openpyxl'
        
        # Read Excel file
        df = pd.read_excel(file_path, engine=engine)
        
        if df.empty:
            return 0, 0, 0, [], set()
            
        # Standardize column names
        df.columns = [c.strip().lower().replace(' ', '_') for c in df.columns]
        
        # Verify required columns
        required_columns = ['date_and_time', 'personnel_id']
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            raise Exception(f"Missing required columns: {', '.join(missing_columns)}")
        
        records_to_create = []
        duplicates = 0
        new_employees = []
        unique_dates = set()
        
        # Get existing timestamps for each employee to check duplicates
        existing_records = {
            (str(r.employee_id), r.timestamp.strftime('%Y-%m-%d %H:%M:%S')): True 
            for r in AttendanceRecord.objects.all()
        }
        
        # Get existing employee numbers
        existing_employee_numbers = set(Employee.objects.values_list('employee_number', flat=True))
        
        for _, row in df.iterrows():
            try:
                # Convert date_and_time to datetime
                timestamp = pd.to_datetime(row['date_and_time'])
                unique_dates.add(timestamp.date())
                
                # Try to get employee or create placeholder
                try:
                    employee = Employee.objects.get(employee_number=row['personnel_id'])
                except Employee.DoesNotExist:
                    # Only create employee if not already created in this session
                    if row['personnel_id'] not in existing_employee_numbers:
                        employee = Employee.objects.create(
                            employee_number=row['personnel_id'],
                            first_name=row.get('first_name', f"Employee {row['personnel_id']}"),
                            last_name=row.get('last_name', ''),
                            email=f"employee{row['personnel_id']}@placeholder.com"
                        )
                        new_employees.append({
                            'id': employee.id,
                            'employee_number': employee.employee_number,
                            'name': f"{employee.first_name} {employee.last_name}".strip()
                        })
                        existing_employee_numbers.add(row['personnel_id'])
                    else:
                        employee = Employee.objects.get(employee_number=row['personnel_id'])
                
                # Check for duplicates
                record_key = (str(employee.id), timestamp.strftime('%Y-%m-%d %H:%M:%S'))
                if record_key in existing_records:
                    duplicates += 1
                    continue
                
                # Create attendance record
                record = AttendanceRecord(
                    employee=employee,
                    timestamp=timestamp,
                    device_name=row.get('device_name', ''),
                    event_point=row.get('event_point', ''),
                    verify_type=row.get('verify_type', ''),
                    event_description=row.get('event_description', ''),
                    remarks=row.get('remarks', '')
                )
                records_to_create.append(record)
                existing_records[record_key] = True
                
            except Exception as e:
                continue
        
        # Bulk create records
        records_created = 0
        if records_to_create:
            AttendanceRecord.objects.bulk_create(records_to_create, ignore_conflicts=True)
            records_created = len(records_to_create)
        
        total_records = AttendanceRecord.objects.count()
        
        return records_created, duplicates, total_records, new_employees, unique_dates
        
    except Exception as e:
        raise Exception(f"Error processing Excel file: {str(e)}")

def generate_attendance_log(date, employee):
    """
    Generate attendance log for an employee on a specific date
    Returns first in and last out times
    """
    try:
        # Get all attendance records for the employee on the date
        records = AttendanceRecord.objects.filter(
            employee=employee,
            timestamp__date=date,
            is_active=True
        ).order_by('timestamp')
        
        if not records.exists():
            return None, None
        
        # Get first and last records
        first_record = records.first()
        last_record = records.last()
        
        first_in = first_record.timestamp.time()
        last_out = last_record.timestamp.time()
        
        return first_in, last_out
    
    except Exception as e:
        print(f"Error generating attendance log: {str(e)}")
        return None, None

def process_daily_attendance(date=None):
    """
    Process attendance records and create attendance logs for all employees
    """
    if date is None:
        date = timezone.now().date()
    
    try:
        # Get all employees with attendance records for the date
        employees = Employee.objects.filter(
            attendance_records__timestamp__date=date,
            attendance_records__is_active=True
        ).distinct()
        
        logs_created = 0
        
        for employee in employees:
            first_in, last_out = generate_attendance_log(date, employee)
            
            if first_in and last_out:
                # Create or update attendance log
                AttendanceLog.objects.update_or_create(
                    employee=employee,
                    date=date,
                    defaults={
                        'first_in_time': first_in,
                        'last_out_time': last_out,
                        'source': 'system'
                    }
                )
                logs_created += 1
        
        return logs_created
    
    except Exception as e:
        raise Exception(f"Error processing daily attendance: {str(e)}")

def validate_attendance_edit(original_log, edited_in_time, edited_out_time):
    """
    Validate attendance edit times
    """
    try:
        # Convert string times to time objects if necessary
        if isinstance(edited_in_time, str):
            edited_in_time = datetime.strptime(edited_in_time, '%H:%M').time()
        if isinstance(edited_out_time, str):
            edited_out_time = datetime.strptime(edited_out_time, '%H:%M').time()
        
        # Basic validation
        if edited_in_time > edited_out_time:
            raise ValueError("First in time cannot be after last out time")
        
        # Check if times are within 24 hours
        time_diff = datetime.combine(datetime.today(), edited_out_time) - \
                   datetime.combine(datetime.today(), edited_in_time)
        
        if time_diff > timedelta(hours=24):
            raise ValueError("Time difference cannot be more than 24 hours")
        
        return True
        
    except Exception as e:
        raise ValueError(f"Invalid time format or values: {str(e)}")

def get_attendance_summary(employee, start_date, end_date):
    """
    Get attendance summary for an employee within a date range
    """
    logs = AttendanceLog.objects.filter(
        employee=employee,
        date__range=(start_date, end_date),
        is_active=True
    ).order_by('date')
    
    summary = {
        'total_days': (end_date - start_date).days + 1,
        'present_days': logs.count(),
        'absent_days': 0,
        'leave_days': 0,
        'holidays': 0,
        'attendance_details': []
    }
    
    for log in logs:
        summary['attendance_details'].append({
            'date': log.date,
            'first_in': log.first_in_time,
            'last_out': log.last_out_time,
            'source': log.source
        })
    
    return summary
```

### hrms_project\attendance\views\shifts.py
```
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.db import transaction
from django.urls import reverse

from attendance.models import Shift, ShiftAssignment, RamadanPeriod
from employees.models import Employee

@login_required
def shift_list(request):
    """View for listing all shifts"""
    shifts = Shift.objects.all().order_by('start_time')
    return render(request, 'attendance/shifts/shift_list.html', {'shifts': shifts})

@login_required
def shift_create(request):
    """View for creating a new shift"""
    if request.method == 'POST':
        name = request.POST.get('name')
        shift_type = request.POST.get('shift_type')
        start_time = request.POST.get('start_time')
        end_time = request.POST.get('end_time')
        is_night_shift = request.POST.get('is_night_shift') == 'on'
        grace_period = int(request.POST.get('grace_period', 15))
        break_duration = int(request.POST.get('break_duration', 60))

        shift = Shift.objects.create(
            name=name,
            shift_type=shift_type,
            start_time=start_time,
            end_time=end_time,
            is_night_shift=is_night_shift,
            grace_period=grace_period,
            break_duration=break_duration
        )
        messages.success(request, 'Shift created successfully.')
        return redirect('attendance:shift_list')

    return render(request, 'attendance/shifts/shift_form.html')

@login_required
def shift_edit(request, pk):
    """View for editing an existing shift"""
    shift = get_object_or_404(Shift, pk=pk)

    if request.method == 'POST':
        shift.name = request.POST.get('name')
        shift.shift_type = request.POST.get('shift_type')
        shift.start_time = request.POST.get('start_time')
        shift.end_time = request.POST.get('end_time')
        shift.is_night_shift = request.POST.get('is_night_shift') == 'on'
        shift.grace_period = int(request.POST.get('grace_period', 15))
        shift.break_duration = int(request.POST.get('break_duration', 60))
        shift.save()

        messages.success(request, 'Shift updated successfully.')
        return redirect('attendance:shift_list')

    return render(request, 'attendance/shifts/shift_form.html', {'shift': shift})

@login_required
def shift_assignment_list(request):
    """View for listing shift assignments"""
    assignments = ShiftAssignment.objects.select_related(
        'employee', 'shift'
    ).order_by('-start_date')
    
    paginator = Paginator(assignments, 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'attendance/shifts/assignment_list.html', {
        'page_obj': page_obj
    })

@login_required
def shift_assignment_create(request):
    """View for creating a new shift assignment"""
    if request.method == 'POST':
        employee_id = request.POST.get('employee')
        shift_id = request.POST.get('shift')
        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date') or None
        is_active = request.POST.get('is_active') == 'on'

        try:
            with transaction.atomic():
                # Deactivate any existing active assignments
                ShiftAssignment.objects.filter(
                    employee_id=employee_id,
                    is_active=True
                ).update(is_active=False)

                # Create new assignment
                ShiftAssignment.objects.create(
                    employee_id=employee_id,
                    shift_id=shift_id,
                    start_date=start_date,
                    end_date=end_date,
                    is_active=is_active,
                    created_by=request.user
                )
                messages.success(request, 'Shift assigned successfully.')
                return redirect('attendance:shift_assignment_list')

        except Exception as e:
            messages.error(request, f'Error assigning shift: {str(e)}')

    employees = Employee.objects.filter(is_active=True)
    shifts = Shift.objects.filter(is_active=True)

    return render(request, 'attendance/shifts/assignment_form.html', {
        'employees': employees,
        'shifts': shifts
    })

@login_required
def shift_assignment_edit(request, pk):
    """View for editing a shift assignment"""
    assignment = get_object_or_404(ShiftAssignment, pk=pk)

    if request.method == 'POST':
        try:
            with transaction.atomic():
                # If making this assignment active, deactivate other active assignments
                if request.POST.get('is_active') == 'on' and not assignment.is_active:
                    ShiftAssignment.objects.filter(
                        employee=assignment.employee,
                        is_active=True
                    ).exclude(pk=pk).update(is_active=False)

                assignment.shift_id = request.POST.get('shift')
                assignment.start_date = request.POST.get('start_date')
                assignment.end_date = request.POST.get('end_date') or None
                assignment.is_active = request.POST.get('is_active') == 'on'
                assignment.save()

                messages.success(request, 'Shift assignment updated successfully.')
                return redirect('attendance:shift_assignment_list')

        except Exception as e:
            messages.error(request, f'Error updating shift assignment: {str(e)}')

    employees = Employee.objects.filter(is_active=True)
    shifts = Shift.objects.filter(is_active=True)

    return render(request, 'attendance/shifts/assignment_form.html', {
        'form': assignment,
        'employees': employees,
        'shifts': shifts
    })

@login_required
def shift_assignment_delete(request, pk):
    """View for deleting a shift assignment"""
    assignment = get_object_or_404(ShiftAssignment, pk=pk)
    
    try:
        assignment.delete()
        messages.success(request, 'Shift assignment deleted successfully.')
    except Exception as e:
        messages.error(request, f'Error deleting shift assignment: {str(e)}')
    
    return redirect('attendance:shift_assignment_list')

@login_required
def get_employee_shifts(request, employee_id):
    """API endpoint for getting an employee's shift history"""
    assignments = ShiftAssignment.objects.filter(
        employee_id=employee_id
    ).select_related('shift').order_by('-start_date')
    
    data = [{
        'id': a.id,
        'shift_name': a.shift.name,
        'start_date': a.start_date.strftime('%Y-%m-%d'),
        'end_date': a.end_date.strftime('%Y-%m-%d') if a.end_date else None,
        'is_active': a.is_active
    } for a in assignments]
    
    return JsonResponse({'assignments': data})

```

### hrms_project\attendance\views.py
```
from datetime import datetime, date, timedelta, time
from typing import List, Dict, Any

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Q
from django.http import JsonResponse, Http404
from django.utils import timezone
from django.contrib import messages
from rest_framework import status
from rest_framework import viewsets
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser

from employees.models import Employee, Department
from .models import (
    AttendanceRecord, AttendanceLog, Leave, Holiday, LeaveType,
    RamadanPeriod
)
from .services import ShiftService, RamadanService
from .serializers import ShiftSerializer, AttendanceRecordSerializer, AttendanceLogSerializer, LeaveSerializer, HolidaySerializer


@login_required
def attendance_list(request):
    """Display attendance list page"""
    context = {
        'departments': Department.objects.all()
    }
    return render(request, 'attendance/attendance_list.html', context)

@login_required
def calendar_view(request):
    """View for displaying attendance calendar"""
    return render(request, 'attendance/calendar.html')

@login_required
def calendar_month(request):
    """View for monthly calendar"""
    context = {
        'view_type': 'month',
        'departments': Department.objects.all()
    }
    return render(request, 'attendance/calendar.html', context)

@login_required
def calendar_week(request):
    """View for weekly calendar"""
    context = {
        'view_type': 'week',
        'departments': Department.objects.all()
    }
    return render(request, 'attendance/calendar.html', context)

@login_required
def calendar_department(request):
    """View for department-wise calendar"""
    context = {
        'view_type': 'department',
        'departments': Department.objects.all()
    }
    return render(request, 'attendance/calendar.html', context)

@login_required
def mark_attendance(request):
    """View for manual attendance marking"""
    return render(request, 'attendance/mark_attendance.html')

@login_required
def leave_request_list(request):
    """Display leave requests list page"""
    return render(request, 'attendance/leave_request_list.html')

@login_required
def leave_request_create(request):
    """Display leave request creation page"""
    return render(request, 'attendance/leave_request_form.html')

@login_required
def leave_request_detail(request, pk):
    """Display leave request details page"""
    leave = get_object_or_404(Leave, pk=pk)
    return render(request, 'attendance/leave_request_detail.html', {'leave': leave})

@login_required
def upload_attendance(request):
    """Display attendance upload page"""
    return render(request, 'attendance/upload_attendance.html')

@login_required
def attendance_detail_view(request):
    """View for displaying and editing attendance details"""
    try:
        personnel_id = request.GET.get('personnel_id')
        date_str = request.GET.get('date')
        
        if not personnel_id or not date_str:
            raise Http404("Missing required parameters")
            
        try:
            # Parse the date from the URL
            date = datetime.strptime(date_str.strip(), '%b %d, %Y').date()
        except ValueError:
            raise Http404("Invalid date format")
            
        try:
            employee = Employee.objects.get(employee_number=personnel_id)
        except Employee.DoesNotExist:
            raise Http404("Employee not found")

        # Get or create the attendance log
        log, created = AttendanceLog.objects.get_or_create(
            employee=employee,
            date=date,
            defaults={
                'source': 'Web Interface'
            }
        )
            
        # Get all raw attendance records for this employee on this date
        attendance_records = AttendanceRecord.objects.filter(
            employee=log.employee,
            timestamp__date=date,
            is_active=True
        ).order_by('timestamp')
        
        # Calculate statistics
        total_hours = timedelta()
        status = 'Absent'
        is_late = False
        first_in = None
        last_out = None
        
        # Default shift start time (8:00 AM)
        shift_start = time(8, 0)  # Using datetime.time
        
        records = []
        if attendance_records:
            # First record of the day is IN, last is OUT
            first_record = attendance_records.first()
            last_record = attendance_records.last()
            
            # Set first IN
            first_in = first_record.timestamp.time()
            is_late = first_in > shift_start
            status = 'Late' if is_late else 'Present'
            
            # Set last OUT
            last_out = last_record.timestamp.time()
            
            # Calculate total hours from first IN to last OUT
            if first_in and last_out:
                in_datetime = datetime.combine(date, first_in)
                out_datetime = datetime.combine(date, last_out)
                
                # Handle case where checkout is next day
                if out_datetime < in_datetime:
                    out_datetime += timedelta(days=1)
                    
                total_hours = out_datetime - in_datetime
            
            # Prepare records for template, alternating between IN and OUT
            for i, record in enumerate(attendance_records):
                # First record is IN, last record is OUT, others alternate
                if record == first_record:
                    record_type = 'IN'
                    is_special = True
                    badge_class = 'bg-primary'
                    label = ' (First)'
                elif record == last_record:
                    record_type = 'OUT'
                    is_special = True
                    badge_class = 'bg-primary'
                    label = ' (Last)'
                else:
                    # Alternate between IN and OUT for middle records
                    record_type = 'IN' if i % 2 == 0 else 'OUT'
                    is_special = False
                    badge_class = 'bg-success' if record_type == 'IN' else 'bg-danger'
                    label = ''
                
                records.append({
                    'id': record.id,
                    'time': record.timestamp.strftime('%I:%M %p'),
                    'type': record_type,
                    'label': label,
                    'source': record.event_description or '-',
                    'device_name': record.device_name or '-',
                    'is_special': is_special,
                    'badge_class': badge_class
                })
        
        # Format total hours as decimal
        total_hours_decimal = total_hours.total_seconds() / 3600
        
        context = {
            'log': log,
            'employee_name': log.employee.get_full_name(),
            'personnel_id': log.employee.employee_number,
            'department': log.employee.department.name if log.employee.department else '-',
            'designation': log.employee.designation or '-',
            'date': date.strftime('%b %d, %Y'),
            'day': date.strftime('%A'),
            'records': records,
            'stats': {
                'total_hours': f"{total_hours_decimal:.2f}",
                'is_late': is_late,
                'status': status,
                'first_in': first_in.strftime('%I:%M %p') if first_in else '-',
                'last_out': last_out.strftime('%I:%M %p') if last_out else '-',
            }
        }
            
        return render(request, 'attendance/attendance_detail.html', context)
        
    except AttendanceLog.DoesNotExist:
        raise Http404("Attendance log not found")

@login_required
def attendance_report(request):
    """View for displaying attendance reports and analytics"""
    context = {
        'departments': Department.objects.all()
    }
    return render(request, 'attendance/attendance_report.html', context)

@login_required
def holiday_list(request):
    """View for displaying list of holidays"""
    holidays = Holiday.objects.all().order_by('-date')
    context = {
        'holidays': holidays
    }
    return render(request, 'attendance/holiday_list.html', context)

@login_required
def holiday_create(request):
    """View for creating new holidays"""
    if request.method == 'POST':
        # Handle form submission
        name = request.POST.get('name')
        date = request.POST.get('date')
        description = request.POST.get('description')
        is_recurring = request.POST.get('is_recurring', False)
        
        Holiday.objects.create(
            name=name,
            date=date,
            description=description,
            is_recurring=is_recurring
        )
        return redirect('attendance:holiday_list')
    
    return render(request, 'attendance/holiday_create.html')

@login_required
def recurring_holidays(request):
    """View for managing recurring holidays"""
    holidays = Holiday.objects.filter(is_recurring=True).order_by('-date')
    context = {
        'holidays': holidays
    }
    return render(request, 'attendance/recurring_holidays.html', context)

@login_required
def leave_balance(request):
    """View for showing employee leave balances"""
    employee = None  # Initialize employee to None
    try:
        employee = request.user.employee
    except AttributeError:
        messages.error(request, "No employee record found for your user account. Please contact HR.")
        return redirect('attendance:attendance_list')

    if not employee:
        # Handle the case where employee is None
        messages.error(request, "No employee record found for your user account. Please contact HR.")
        return redirect('attendance:attendance_list')

    leave_types = LeaveType.objects.all()
    balances = []
    
    for leave_type in leave_types:
        used_leaves = Leave.objects.filter(
            employee=employee,
            leave_type=leave_type,
            status='APPROVED',
            start_date__year=timezone.now().year
        ).aggregate(
            total_days=models.Sum('days')
        )['total_days'] or 0
        
        remaining = leave_type.days_allowed - used_leaves
        balances.append({
            'leave_type': leave_type,
            'allowed_days': leave_type.days_allowed,
            'used_days': used_leaves,
            'remaining_days': remaining
        })
    
    context = {
        'balances': balances
    }
    return render(request, 'attendance/leave_balance.html', context)

@login_required
def leave_types(request):
    """View for managing leave types"""
    leave_types = LeaveType.objects.all().order_by('name')
    context = {
        'leave_types': leave_types
    }
    return render(request, 'attendance/leave_types.html', context)

@login_required
def get_department_employees(request):
    """AJAX view to get employees by department"""
    department_id = request.GET.get('department')
    search_query = request.GET.get('q', '').strip()

    if search_query:
        employees = Employee.objects.filter(
            Q(employee_number__icontains=search_query) |
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query)
        )
        if department_id:
            employees = employees.filter(department_id=department_id)
    elif department_id:
        employees = Employee.objects.filter(department_id=department_id)
    else:
        employees = Employee.objects.all()

    employees = employees.values('id', 'user__first_name', 'user__last_name')

    employee_list = [
        {
            'id': emp['id'],
            'name': f"{emp['user__first_name']} {emp['user__last_name']}"
        }
        for emp in employees
    ]

    return JsonResponse({'employees': employee_list})

# API ViewSets
class ShiftViewSet(viewsets.ModelViewSet):
    """ViewSet for managing shifts"""
    serializer_class = ShiftSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Shift.objects.filter(is_active=True)

class AttendanceRecordViewSet(viewsets.ModelViewSet):
    """ViewSet for managing raw attendance records"""
    serializer_class = AttendanceRecordSerializer
    permission_classes = [IsAuthenticated]
    queryset = AttendanceRecord.objects.all()

    @action(detail=False, methods=['post'], parser_classes=[MultiPartParser])
    def upload_excel(self, request):
        """Handle Excel file upload"""
        if 'file' not in request.FILES:
            return Response({'error': 'No file provided'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            excel_file = request.FILES['file']
            records_created, duplicates, total_records, new_employees, unique_dates = process_attendance_excel(excel_file)
            
            # Process logs for each unique date in the uploaded file
            logs_created = 0
            for date in unique_dates:
                logs_created += process_daily_attendance(date)

            return Response({
                'message': 'File processed successfully',
                'new_records': records_created,
                'duplicate_records': duplicates,
                'total_records': total_records,
                'logs_created': logs_created,
                'new_employees': new_employees,
                'success': True
            })
        except Exception as e:
            return Response({
                'error': str(e),
                'success': False
            }, status=status.HTTP_400_BAD_REQUEST)

class AttendanceLogViewSet(viewsets.ModelViewSet):
    """ViewSet for managing processed attendance logs"""
    serializer_class = AttendanceLogSerializer
    permission_classes = [IsAuthenticated]
    queryset = AttendanceLog.objects.all()

    def get_queryset(self):
        queryset = AttendanceLog.objects.filter(is_active=True)
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        employee_id = self.request.query_params.get('employee')
        department_id = self.request.query_params.get('department')

        if start_date:
            queryset = queryset.filter(date__gte=start_date)
        if end_date:
            queryset = queryset.filter(date__lte=end_date)
        if employee_id:
            queryset = queryset.filter(employee_id=employee_id)
        if department_id:
            queryset = queryset.filter(employee__department_id=department_id)

        return queryset

class LeaveViewSet(viewsets.ModelViewSet):
    """ViewSet for managing leave requests"""
    serializer_class = LeaveSerializer
    permission_classes = [IsAuthenticated]
    queryset = Leave.objects.all()

    def get_queryset(self):
        queryset = Leave.objects.filter(is_active=True)
        status = self.request.query_params.get('status')
        if status:
            queryset = queryset.filter(status=status)
        return queryset

class HolidayViewSet(viewsets.ModelViewSet):
    """ViewSet for managing holidays"""
    serializer_class = HolidaySerializer
    permission_classes = [IsAuthenticated]
    queryset = Holiday.objects.all()

    def get_queryset(self):
        return Holiday.objects.filter(is_active=True)

from rest_framework.pagination import PageNumberPagination

class LargeResultsSetPagination(PageNumberPagination):
    """Custom pagination class for large result sets"""
    page_size = 400
    page_size_query_param = 'page_size'
    max_page_size = 1000

class AttendanceLogListViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for listing and retrieving attendance logs with filtering"""
    serializer_class = AttendanceLogSerializer
    permission_classes = [IsAuthenticated]
    queryset = AttendanceLog.objects.select_related('employee').all()
    pagination_class = LargeResultsSetPagination

    def get_queryset(self):
        queryset = super().get_queryset().order_by('-date')
        
        # Get filter parameters
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        department = self.request.query_params.get('department')
        status = self.request.query_params.get('status')
        search = self.request.query_params.get('search')

        # Apply filters
        if start_date:
            try:
                start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
                queryset = queryset.filter(date__gte=start_date)
            except ValueError:
                pass

        if end_date:
            try:
                end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
                queryset = queryset.filter(date__lte=end_date)
            except ValueError:
                pass

        if department:
            queryset = queryset.filter(employee__department_id=department)

        if status:
            if status == 'late':
                queryset = queryset.filter(is_late=True)
            elif status == 'present':
                queryset = queryset.filter(first_in_time__isnull=False)
            elif status == 'absent':
                queryset = queryset.filter(first_in_time__isnull=True)

        if search:
            queryset = queryset.filter(
                Q(employee__first_name__icontains=search) |
                Q(employee__last_name__icontains=search) |
                Q(employee__employee_number__icontains=search)
            )

        return queryset

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context

# API Views
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_calendar_events(request):
    """API endpoint for getting calendar events"""
    start_date = request.query_params.get('start')
    end_date = request.query_params.get('end')
    
    try:
        start = datetime.strptime(start_date, '%Y-%m-%d').date()
        end = datetime.strptime(end_date, '%Y-%m-%d').date()
        
        logs = AttendanceLog.objects.filter(
            date__range=[start, end]
        ).select_related('employee')
        
        events = []
        for log in logs:
            status = 'Present'
            color = '#28a745'  # green
            
            if not log.first_in_time:
                status = 'Absent'
                color = '#dc3545'  # red
            elif log.is_late:
                status = 'Late'
                color = '#ffc107'  # yellow
                
            events.append({
                'id': log.id,
                'title': f"{log.employee.get_full_name()} - {status}",
                'start': log.date.isoformat(),
                'end': log.date.isoformat(),
                'color': color,
                'extendedProps': {
                    'employee_id': log.employee.id,
                    'status': status,
                    'in_time': log.first_in_time.strftime('%H:%M') if log.first_in_time else None,
                    'out_time': log.last_out_time.strftime('%H:%M') if log.last_out_time else None
                }
            })
            
        return Response(events)
    except (ValueError, TypeError):
        return Response({'error': 'Invalid date format'}, status=400)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_employee_attendance(request, employee_id):
    """Get attendance summary for an employee"""
    start_date = request.query_params.get('start_date')
    end_date = request.query_params.get('end_date')
    
    if not start_date or not end_date:
        return Response(
            {'error': 'Start date and end date are required'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        employee = get_object_or_404(Employee, id=employee_id)
        summary = get_attendance_summary(employee, start_date, end_date)
        return Response(summary)
    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def attendance_detail_api(request):
    """API endpoint for getting attendance details"""
    try:
        personnel_id = request.GET.get('personnel_id')
        date_str = request.GET.get('date')
        
        if not personnel_id or not date_str:
            return Response({'error': 'Missing required parameters'}, status=400)
        
        try:
            date = datetime.strptime(date_str.strip(), '%b %d, %Y').date()
        except ValueError:
            return Response({'error': 'Invalid date format'}, status=400)
            
        employee = Employee.objects.get(employee_number=personnel_id)
        log = AttendanceLog.objects.select_related('employee').get(employee=employee, date=date)
        data = {
            'id': log.id,
            'employee_name': log.employee.get_full_name(),
            'personnel_id': log.employee.employee_number,
            'department': log.employee.department.name if log.employee.department else None,
            'designation': log.employee.designation,
            'date': log.date,
            'records': [
                {
                    'id': log.id,
                    'timestamp': log.first_in_time.isoformat() if log.first_in_time else None,
                    'event_point': 'IN',
                    'source': log.source,
                    'device_name': log.device
                }
            ]
        }
        
        # Add out time if exists
        if log.last_out_time:
            data['records'].append({
                'id': log.id,
                'timestamp': log.last_out_time.isoformat(),
                'event_point': 'OUT',
                'source': log.source,
                'device_name': log.device
            })
            
        return Response(data)
    except AttendanceLog.DoesNotExist:
        return Response({'error': 'Log not found'}, status=404)

@api_view(['PATCH', 'DELETE'])
@permission_classes([IsAuthenticated])
def attendance_record_api(request, record_id):
    """API endpoint for updating or deleting attendance records"""
    try:
        log = AttendanceLog.objects.get(id=record_id)
        
        if request.method == 'DELETE':
            log.delete()
            return Response(status=204)
            
        if request.method == 'PATCH':
            time = request.data.get('time')
            reason = request.data.get('reason')
            
            if not time or not reason:
                return Response({'error': 'Time and reason are required'}, status=400)
                
            # Parse the time string
            try:
                hour, minute = map(int, time.split(':'))
                new_time = datetime.combine(log.date, time(hour, minute))
                
                # Update the appropriate time field based on the record type
                if log.first_in_time and log.first_in_time.time() == time:
                    log.first_in_time = new_time
                elif log.last_out_time and log.last_out_time.time() == time:
                    log.last_out_time = new_time
                    
                log.save()
                return Response({'status': 'success'})
            except ValueError:
                return Response({'error': 'Invalid time format'}, status=400)
                
    except AttendanceLog.DoesNotExist:
        return Response({'error': 'Record not found'}, status=404)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def add_attendance_record(request):
    """API endpoint for adding a new attendance record"""
    personnel_id = request.data.get('personnel_id')
    date = request.data.get('date')
    time = request.data.get('time')
    type = request.data.get('type')
    reason = request.data.get('reason')
    
    if not all([personnel_id, date, time, type, reason]):
        return Response({'error': 'All fields are required'}, status=400)
        
    try:
        employee = Employee.objects.get(employee_number=personnel_id)
        log_date = datetime.strptime(date, '%Y-%m-%d').date()
        hour, minute = map(int, time.split(':'))
        log_time = datetime.combine(log_date, time(hour, minute))
        
        # Get or create attendance log for the date
        log, created = AttendanceLog.objects.get_or_create(
            employee=employee,
            date=log_date,
            defaults={
                'source': 'Manual',
                'device': 'Web Interface'
            }
        )
        
        # Update the appropriate time field
        if type == 'IN':
            log.first_in_time = log_time
        else:
            log.last_out_time = log_time
            
        log.save()
        return Response({'status': 'success'})
        
    except (Employee.DoesNotExist, ValueError) as e:
        return Response({'error': str(e)}, status=400)

@api_view(['GET'])
def search_employees(request):
    """Search employees by ID or name"""
    query = request.GET.get('q', '').strip()
    department_id = request.GET.get('department')
    
    if not query:
        return Response([])
        
    try:
        # Build the query
        employee_query = Q(employee_number__icontains=query) | \
                        Q(first_name__icontains=query) | \
                        Q(last_name__icontains=query)
                        
        # Add department filter if specified
        if department_id:
            employee_query &= Q(department_id=department_id)
            
        # Get employees matching the criteria
        employees = Employee.objects.filter(employee_query, is_active=True) \
                                 .select_related('department') \
                                 .order_by('employee_number')[:10]
        
        # Format response
        employee_list = [{
            'id': emp.id,
            'employee_number': emp.employee_number,
            'full_name': emp.get_full_name(),
            'department': emp.department.name if emp.department else None
        } for emp in employees]
        
        return Response(employee_list)
        
    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['GET'])
def calendar_events(request):
    """Get attendance events for calendar"""
    try:
        # Get date parameters
        start_str = request.GET.get('start', '')
        end_str = request.GET.get('end', '')
        department = request.GET.get('department')
        employee = request.GET.get('employee')
        
        # Parse dates from ISO format
        try:
            start_date = datetime.strptime(start_str.split('T')[0], '%Y-%m-%d').date()
            end_date = datetime.strptime(end_str.split('T')[0], '%Y-%m-%d').date()
        except (ValueError, IndexError):
            return Response({
                'error': 'Invalid date format. Expected YYYY-MM-DD.'
            }, status=400)
        
        # Build query
        logs_query = Q(date__range=[start_date, end_date])
        if employee:
            logs_query &= Q(employee_id=employee)
        elif department:
            logs_query &= Q(employee__department_id=department)
            
        # Get logs with related data
        logs = AttendanceLog.objects.filter(
            logs_query
        ).select_related('employee', 'employee__department')
        
        # Convert logs to calendar events
        events = []
        for log in logs:
            # Get current shift for the employee on this date
            shift = ShiftService.get_employee_current_shift(log.employee)
            
            # Get attendance details
            attendance_info = {
                'time_in': log.first_in_time.strftime('%I:%M %p') if log.first_in_time else None,
                'time_out': log.last_out_time.strftime('%I:%M %p') if log.last_out_time else None,
                'total_hours': f"{log.total_work_minutes / 60:.2f}" if log.total_work_minutes else None,
                'late_by': f"{log.late_minutes} min" if log.late_minutes else None,
                'early_by': f"{log.early_minutes} min" if log.early_minutes else None,
                'shift': shift.name if shift else 'No Shift'
            }

            # Determine event color and status
            status_colors = {
                'present': '#28a745',  # green
                'absent': '#dc3545',   # red
                'late': '#ffc107',     # yellow
                'leave': '#17a2b8',    # info
                'holiday': '#6f42c1'   # purple
            }

            if log.is_leave:
                status = 'leave'
            elif log.is_holiday:
                status = 'holiday'
            elif not log.first_in_time:
                status = 'absent'
            elif log.is_late:
                status = 'late'
            else:
                status = 'present'

            # Build event data
            event = {
                'id': log.id,
                'title': f"{log.employee.employee_number} - {log.employee.get_full_name()}",
                'start': log.date.isoformat(),
                'color': status_colors.get(status, '#6c757d'),  # default to gray
                'extendedProps': {
                    'employee_id': log.employee.id,
                    'employee_number': log.employee.employee_number,
                    'employee_name': log.employee.get_full_name(),
                    'department': log.employee.department.name if log.employee.department else '',
                    'type': 'attendance',
                    'status': status,
                    'attendance_info': attendance_info
                }
            }

            # Add timing info to title if available
            if attendance_info['time_in']:
                event['title'] += f" ({attendance_info['time_in']}"
                if attendance_info['time_out']:
                    event['title'] += f" - {attendance_info['time_out']}"
                event['title'] += ")"

            if status == 'late' and attendance_info['late_by']:
                event['title'] += f" [Late: {attendance_info['late_by']}]"

            events.append(event)
        
        return Response(events)
        
    except Exception as e:
        return Response({'error': str(e)}, status=400)

@login_required
def ramadan_periods(request):
    """View for managing Ramadan periods"""
    try:
        periods = RamadanService.get_all_periods()
        context = {'periods': periods}
        return render(request, 'attendance/shifts/ramadan_periods.html', context)
    except Exception as e:
        messages.error(request, f"Error loading Ramadan periods: {str(e)}")
        return redirect('attendance:attendance_list')

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def ramadan_period_add(request):
    """API endpoint for adding a new Ramadan period"""
    try:
        year = int(request.data.get('year'))
        start_date = datetime.strptime(request.data.get('start_date'), '%Y-%m-%d').date()
        end_date = datetime.strptime(request.data.get('end_date'), '%Y-%m-%d').date()
        
        # Validate period dates
        RamadanService.validate_period_dates(start_date, end_date, year)
        
        # Create period
        period = RamadanService.create_period(year, start_date, end_date)
        
        return Response({
            'message': 'Ramadan period added successfully',
            'id': period.id
        }, status=status.HTTP_201_CREATED)
        
    except ValueError as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET', 'PUT', 'DELETE'])
@permission_classes([IsAuthenticated])
def ramadan_period_detail(request, pk):
    """API endpoint for managing a specific Ramadan period"""
    try:
        period = RamadanPeriod.objects.get(pk=pk)
    except RamadanPeriod.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        return Response({
            'year': period.year,
            'start_date': period.start_date.isoformat(),
            'end_date': period.end_date.isoformat(),
            'is_active': period.is_active
        })

    elif request.method == 'PUT':
        try:
            year = int(request.data.get('year'))
            start_date = datetime.strptime(request.data.get('start_date'), '%Y-%m-%d').date()
            end_date = datetime.strptime(request.data.get('end_date'), '%Y-%m-%d').date()
            is_active = request.data.get('is_active', True)
            
            # Update period
            period = RamadanService.update_period(
                period.id, year, start_date, end_date, is_active
            )
            
            return Response({'message': 'Ramadan period updated successfully'})
            
        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    elif request.method == 'DELETE':
        try:
            period.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Exception as e:
            return Response(
                {'error': f"Unable to delete period: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


@api_view(['GET'])
def attendance_details(request):
    """Get detailed attendance information for a specific log"""
    try:
        personnel_id = request.GET.get('personnel_id')
        date_str = request.GET.get('date')
        
        if not personnel_id or not date_str:
            return Response({'error': 'Missing required parameters'}, status=400)
        
        try:
            date = datetime.strptime(date_str.strip(), '%b %d, %Y').date()
        except ValueError:
            return Response({'error': 'Invalid date format'}, status=400)
            
        employee = Employee.objects.get(employee_number=personnel_id)
        log = AttendanceLog.objects.select_related('employee').get(employee=employee, date=date)
        
        # Get raw attendance records for this date
        records = AttendanceRecord.objects.filter(
            employee=log.employee,
            timestamp__date=log.date,
            is_active=True
        ).order_by('timestamp')
        
        raw_records = []
        for record in records:
            raw_records.append({
                'time': record.timestamp.strftime('%I:%M %p'),
                'device': record.device_name,
                'event_point': record.event_point,
                'description': record.event_description
            })
        
        return Response({
            'log_id': log.id,
            'date': log.date.strftime('%b %d, %Y'),
            'employee': log.employee.get_full_name(),
            'status': 'Late' if log.is_late else ('Present' if log.first_in_time else 'Absent'),
            'source': log.source or '-',
            'original_in': log.original_in_time.strftime('%I:%M %p') if log.original_in_time else '-',
            'original_out': log.original_out_time.strftime('%I:%M %p') if log.original_out_time else '-',
            'current_in': log.first_in_time.strftime('%I:%M %p') if log.first_in_time else '-',
            'current_out': log.last_out_time.strftime('%I:%M %p') if log.last_out_time else '-',
            'raw_records': raw_records
        })
    except AttendanceLog.DoesNotExist:
        return Response({'error': 'Log not found'}, status=404)

```

### hrms_project\employees\models.py
```
from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.core.files.uploadedfile import UploadedFile
from django.core.validators import FileExtensionValidator
import os

class Department(models.Model):
    name = models.CharField(max_length=100)
    name_ar = models.CharField(max_length=100, verbose_name="Name (Arabic)", blank=True, null=True)
    code = models.CharField(max_length=20, default='DEPT', unique=True)
    parent = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True)
    manager = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    
    def __str__(self):
        return self.name

class Division(models.Model):
    name = models.CharField(max_length=100)
    name_ar = models.CharField(max_length=100, verbose_name="Name (Arabic)")
    code = models.CharField(max_length=20, unique=True)
    department = models.ForeignKey(Department, on_delete=models.CASCADE)

    def __str__(self):
        return self.name

class Location(models.Model):
    name = models.CharField(max_length=100)
    address = models.TextField()
    code = models.CharField(max_length=20, unique=True)

    def __str__(self):
        return self.name

class Bank(models.Model):
    name = models.CharField(max_length=100)
    swift_code = models.CharField(max_length=20)

    def __str__(self):
        return self.name

class CostProfitCenter(models.Model):
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=20, unique=True)
    description = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.code} - {self.name}"

    class Meta:
        verbose_name = 'Cost/Profit Center'
        verbose_name_plural = 'Cost/Profit Centers'
        ordering = ['code']

class Employee(models.Model):
    # Choice Fields
    GENDER_CHOICES = [
        ('M', 'Male'),
        ('F', 'Female'),
    ]
    MARITAL_STATUS_CHOICES = [
        ('S', 'Single'),
        ('M', 'Married'),
        ('D', 'Divorced'),
        ('W', 'Widowed'),
    ]
    CONTRACT_TYPE_CHOICES = [
        ('FT', 'Full Time'),
        ('PT', 'Part Time'),
        ('CT', 'Contract'),
        ('INT', 'Intern'),
    ]
    EMPLOYEE_CATEGORY_CHOICES = [
        ('GEN', 'General'),
        ('SUP', 'Supervisor'),
        ('MGR', 'Manager'),
        ('EXE', 'Executive'),
    ]
    NATIONALITY_CHOICES = [
        ('ALGERIAN', 'Algerian'),
        ('AMERICAN', 'American'),
        ('ARGENTINA', 'Argentina'),
        ('AUSTRALIAN', 'Australian'),
        ('BAHRAINI', 'Bahraini'),
        ('BANGLADESHI', 'Bangladeshi'),
        ('BELGIAN', 'Belgian'),
        ('BRAZILIAN', 'Brazilian'),
        ('BRITISH', 'British'),
        ('BULGARIAN', 'Bulgarian'),
        ('CAMEROONIAN', 'Cameroonian'),
        ('CANADIAN', 'Canadian'),
        ('CHILEAN', 'Chilean'),
        ('CHINESE', 'Chinese'),
        ('COLOMBIAN', 'Colombian'),
        ('CROATIAN', 'Croatian'),
        ('CUBAN', 'Cuban'),
        ('CYPRIOT', 'Cypriot'),
        ('CZECH', 'Czech'),
        ('DANISH', 'Danish'),
        ('DJIBOUTIAN', 'Djiboutian'),
        ('EGYPTIAN', 'Egyptian'),
        ('FILIPINO', 'Filipino'),
        ('FRENCH', 'French'),
        ('GERMAN', 'German'),
        ('GHANAIAN', 'Ghanaian'),
        ('GREEK', 'Greek'),
        ('DUTCH', 'Dutch'),
        ('HONG_KONGER', 'Hong Konger'),
        ('INDIAN', 'Indian'),
        ('INDONESIAN', 'Indonesian'),
        ('IRANIAN', 'Iranian'),
        ('IRAQI', 'Iraqi'),
        ('IRISH', 'Irish'),
        ('ITALIAN', 'Italian'),
        ('JAMAICAN', 'Jamaican'),
        ('JAPANESE', 'Japanese'),
        ('JORDANIAN', 'Jordanian'),
        ('KENYAN', 'Kenyan'),
        ('KUWAITI', 'Kuwaiti'),
        ('LEBANESE', 'Lebanese'),
        ('MALAWIAN', 'Malawian'),
        ('MALAYSIAN', 'Malaysian'),
        ('MEXICAN', 'Mexican'),
        ('MOROCCAN', 'Moroccan'),
        ('NEPALI', 'Nepali'),
        ('DUTCH', 'Dutch'),
        ('NEW_ZEALANDER', 'New Zealander'),
        ('NIGERIAN', 'Nigerian'),
        ('NORWEGIAN', 'Norwegian'),
        ('OMANI', 'Omani'),
        ('PAKISTANI', 'Pakistani'),
        ('POLISH', 'Polish'),
        ('PORTUGUESE', 'Portuguese'),
        ('RUSSIAN', 'Russian'),
        ('SAUDI', 'Saudi'),
        ('SCOTTISH', 'Scottish'),
        ('SERBIAN', 'Serbian'),
        ('SEYCHELLOIS', 'Seychellois'),
        ('SINGAPOREAN', 'Singaporean'),
        ('SOUTH_AFRICAN', 'South African'),
        ('SPANISH', 'Spanish'),
        ('SRI_LANKAN', 'Sri Lankan'),
        ('SUDANESE', 'Sudanese'),
        ('SWEDISH', 'Swedish'),
        ('SWISS', 'Swiss'),
        ('SYRIAN', 'Syrian'),
        ('TAIWANESE', 'Taiwanese'),
        ('TANZANIAN', 'Tanzanian'),
        ('THAI', 'Thai'),
        ('TUNISIAN', 'Tunisian'),
        ('TURKISH', 'Turkish'),
        ('EMIRATI', 'Emirati'),
        ('UGANDAN', 'Ugandan'),
        ('UKRAINIAN', 'Ukrainian'),
        ('VENEZUELAN', 'Venezuelan'),
        ('VIETNAMESE', 'Vietnamese'),
        ('YEMENI', 'Yemeni'),
        ('ZIMBABWEAN', 'Zimbabwean'),
        ('OTHER', 'Other'),
    ]

    # General Information
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='employee',
        null=True,
        blank=True
    )
    employee_number = models.CharField(max_length=20, unique=True, default='EMP0001')
    profile_picture = models.ImageField(upload_to='employee_pictures/', blank=True, null=True)
    first_name = models.CharField(max_length=50, default='First')
    middle_name = models.CharField(max_length=50, blank=True, null=True)
    last_name = models.CharField(max_length=50, default='Last')
    first_name_ar = models.CharField(max_length=50, verbose_name="First Name (Arabic)", blank=True, null=True)
    middle_name_ar = models.CharField(max_length=50, verbose_name="Middle Name (Arabic)", blank=True, null=True)
    last_name_ar = models.CharField(max_length=50, verbose_name="Last Name (Arabic)", blank=True, null=True)
    date_of_birth = models.DateField(blank=True, null=True)
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, blank=True, null=True)
    marital_status = models.CharField(max_length=20, choices=MARITAL_STATUS_CHOICES, blank=True, null=True)
    nationality = models.CharField(
        max_length=50,
        choices=NATIONALITY_CHOICES,
        blank=True,
        null=True,
        verbose_name='Nationality'
    )
    religion = models.CharField(max_length=50, blank=True, null=True)
    education_category = models.CharField(max_length=50, blank=True, null=True)
    cpr_number = models.CharField(max_length=20, unique=True, blank=True, null=True)
    email = models.EmailField(max_length=254, blank=True, null=True)
    primary_phone = models.CharField(max_length=20, blank=True, null=True, verbose_name='Primary Number')
    secondary_phone = models.CharField(max_length=20, blank=True, null=True, verbose_name='Secondary Number')
    address = models.TextField(blank=True, null=True)
    in_probation = models.BooleanField(default=True)

    # Employment Information
    designation = models.CharField(max_length=100, blank=True, null=True)
    division = models.ForeignKey(Division, on_delete=models.SET_NULL, null=True, blank=True)
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, blank=True)
    location = models.ForeignKey(Location, on_delete=models.SET_NULL, null=True, blank=True)
    contract_type = models.CharField(max_length=20, choices=CONTRACT_TYPE_CHOICES, blank=True, null=True)
    joined_date = models.DateField(blank=True, null=True)
    cost_center = models.ForeignKey(CostProfitCenter, on_delete=models.SET_NULL, null=True, blank=True, related_name='cost_center_employees')
    profit_center = models.ForeignKey(CostProfitCenter, on_delete=models.SET_NULL, null=True, blank=True, related_name='profit_center_employees')
    employee_category = models.CharField(max_length=20, choices=EMPLOYEE_CATEGORY_CHOICES, blank=True, null=True)

    # System Fields
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Employee'
        verbose_name_plural = 'Employees'
        ordering = ['employee_number']

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.employee_number})"

    def get_full_name(self):
        middle = f" {self.middle_name}" if self.middle_name else ""
        return f"{self.first_name}{middle} {self.last_name}"

    def get_full_name_ar(self):
        middle = f" {self.middle_name_ar}" if self.middle_name_ar else ""
        return f"{self.first_name_ar}{middle} {self.last_name_ar}"

class EmployeeBankAccount(models.Model):
    employee = models.ForeignKey('Employee', on_delete=models.CASCADE, related_name='bank_accounts')
    bank = models.CharField(max_length=100)
    account_number = models.CharField(max_length=50)
    iban = models.CharField(max_length=50, verbose_name="IBAN No")
    transfer_amount = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        verbose_name="Amount to be Transferred",
        null=True,
        blank=True
    )
    is_primary = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-is_primary', '-created_at']
        verbose_name = "Employee Bank Account"
        verbose_name_plural = "Employee Bank Accounts"

    def __str__(self):
        return f"{self.employee.get_full_name()} - {self.bank} ({self.account_number})"

    def save(self, *args, **kwargs):
        # If this account is being set as primary, unset primary for other accounts
        if self.is_primary:
            EmployeeBankAccount.objects.filter(
                employee=self.employee, 
                is_primary=True
            ).exclude(pk=self.pk).update(is_primary=False)
        super().save(*args, **kwargs)

class EmployeeDependent(models.Model):
    RELATIONSHIP_CHOICES = [
        ('spouse', 'Spouse'),
        ('child', 'Child'),
        ('parent', 'Parent'),
        ('sibling', 'Sibling'),
        ('other', 'Other'),
    ]
    
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='dependents')
    name = models.CharField(max_length=100)
    relation = models.CharField(max_length=20, choices=RELATIONSHIP_CHOICES)
    date_of_birth = models.DateField()
    passport_number = models.CharField(max_length=50, blank=True, null=True)
    passport_expiry = models.DateField(blank=True, null=True)
    cpr_number = models.CharField(max_length=20, blank=True, null=True)
    cpr_expiry = models.DateField(blank=True, null=True)
    valid_passage = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Employee Dependent"
        verbose_name_plural = "Employee Dependents"
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.get_relation_display()})"

class DependentDocument(models.Model):
    DOCUMENT_TYPES = [
        ('PASSPORT', 'Passport'),
        ('CPR', 'CPR'),
        ('BIRTH_CERTIFICATE', 'Birth Certificate'),
        ('MARRIAGE_CERTIFICATE', 'Marriage Certificate'),
        ('OTHER', 'Other'),
    ]

    dependent = models.ForeignKey(EmployeeDependent, on_delete=models.CASCADE, related_name='documents')
    document_type = models.CharField(max_length=50, choices=DOCUMENT_TYPES)
    document_number = models.CharField(max_length=50, blank=True, null=True)
    name = models.CharField(max_length=255)
    issue_date = models.DateField(blank=True, null=True)
    expiry_date = models.DateField(blank=True, null=True)
    nationality = models.CharField(max_length=50, choices=Employee.NATIONALITY_CHOICES, blank=True, null=True)
    document_file = models.FileField(upload_to='dependent_documents/', blank=True, null=True)
    status = models.CharField(max_length=20, default='active')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.dependent.name} - {self.get_document_type_display()}"

class EmergencyContact(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='emergency_contacts')
    name = models.CharField(max_length=100)
    relationship = models.CharField(max_length=50)
    phone_number = models.CharField(max_length=20)
    alternative_phone = models.CharField(max_length=20, blank=True)
    address = models.TextField(blank=True)

    def __str__(self):
        return f"{self.name} ({self.relationship})"

class EmployeeDocument(models.Model):
    DOCUMENT_TYPES = [
        ('PASSPORT', 'Passport'),
        ('RESIDENT', 'Resident Permit'),
        ('CPR', 'C.P.R'),
        ('GATE', 'Gate Pass'),
        ('CONTRACT', 'Contract'),
        ('CV', 'CV'),
        ('DRIVING', 'Driving License'),
    ]
    
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='documents')
    document_type = models.CharField(max_length=10, choices=DOCUMENT_TYPES)
    document_number = models.CharField(max_length=50)
    profession_title = models.CharField(max_length=100, blank=True, null=True, verbose_name="Profession / Title")
    issue_date = models.DateField(null=True, blank=True)
    issue_place = models.CharField(max_length=100, null=True, blank=True)
    expiry_date = models.DateField(null=True, blank=True)
    other_info = models.TextField(blank=True, null=True)
    document_file = models.FileField(
        upload_to='employee_documents/%Y/%m/',
        validators=[
            FileExtensionValidator(
                allowed_extensions=['pdf', 'jpg', 'jpeg', 'png', 'doc', 'docx']
            )
        ],
        null=True,
        blank=True
    )
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Employee Document"
        verbose_name_plural = "Employee Documents"

    def __str__(self):
        return f"{self.employee.get_full_name()} - {self.get_document_type_display()}"

    def clean(self):
        if self.expiry_date and self.issue_date:
            if self.expiry_date < self.issue_date:
                raise ValidationError({
                    'expiry_date': 'Expiry date cannot be earlier than issue date.'
                })

    def save(self, *args, **kwargs):
        if not self.pk:  # Only set created_at for new instances
            self.created_at = timezone.now()
            
        if self.document_file:
            # Get file extension
            _, ext = os.path.splitext(self.document_file.name)
            
            # Create new filename
            new_filename = f"{self.employee.employee_number}_{self.employee.get_full_name().replace(' ', '_')}_{self.get_document_type_display()}_{self.document_number}{ext}"
            
            # Set the new filename
            self.document_file.name = os.path.join(
                'employee_documents',
                timezone.now().strftime('%Y'),
                timezone.now().strftime('%m'),
                new_filename
            )
            
        self.full_clean()
        super().save(*args, **kwargs)

    @property
    def is_expired(self):
        return self.expiry_date < timezone.now().date() if self.expiry_date else False

    @property
    def file_extension(self):
        name, extension = os.path.splitext(self.document_file.name)
        return extension.lower()

    @property
    def is_image(self):
        return self.file_extension in ['.jpg', '.jpeg', '.png']

class AssetType(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['name']
        verbose_name = "Asset Type"
        verbose_name_plural = "Asset Types"

class EmployeeAsset(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='assets')
    asset_type = models.ForeignKey(AssetType, on_delete=models.PROTECT, related_name='assets', null=True)
    asset_name = models.CharField(max_length=100)
    asset_number = models.CharField(max_length=50, blank=True, null=True)
    issue_date = models.DateField(default=timezone.now)
    return_date = models.DateField(null=True, blank=True)
    condition = models.TextField(default='New')
    return_condition = models.TextField(null=True, blank=True)
    value = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    notes = models.TextField(blank=True, null=True)
    return_notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        if self.asset_number:
            return f"{self.asset_name} - {self.asset_number}"
        return self.asset_name

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Employee Asset"
        verbose_name_plural = "Employee Assets"

class EmployeeEducation(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='education')
    institution = models.CharField(max_length=100, default='Unknown Institution')
    major = models.CharField(max_length=100, default='General')
    degree = models.CharField(max_length=50, default='Unknown Degree')
    graduation_year = models.IntegerField(default=2000)
    gpa = models.DecimalField(max_digits=3, decimal_places=2, blank=True, null=True)
    description = models.TextField(blank=True)

    def __str__(self):
        return f"{self.degree} from {self.institution}"

class OffenseRule(models.Model):
    PENALTY_CHOICES = [
        ('ORAL', 'Oral Warning'),
        ('WRITTEN', 'Written Warning'),
        ('D005', '0.05 Day Deduction'),
        ('D010', '0.10 Day Deduction'),
        ('D015', '0.15 Day Deduction'),
        ('D025', '0.25 Day Deduction'),
        ('D030', '0.30 Day Deduction'),
        ('D050', '0.50 Day Deduction'),
        ('D075', '0.75 Day Deduction'),
        ('D100', '1 Day Deduction'),
        ('D200', '2 Days Deduction'),
        ('D300', '3 Days Deduction'),
        ('D500', '5 Days Deduction'),
        ('MONETARY', 'Monetary Penalty'),
        ('DISMISS', 'Dismissal'),
    ]
    GROUP_CHOICES = [
        ('ATTENDANCE_TIME', 'Violations Concerning Attendance Time'),
        ('WORK_ORG', 'Violations Concerning Work Organization'),
        ('BEHAVIOR', 'Violations Concerning Employee Behavior'),
        ('SAFETY', 'Violations Concerning Safety'),
        ('PROPERTY', 'Violations Concerning Company Property'),
        ('OTHER', 'Other Violations'),
    ]

    rule_id = models.CharField(max_length=20, unique=True)
    group = models.CharField(max_length=20, choices=GROUP_CHOICES)
    name = models.CharField(max_length=200)
    description = models.TextField()
    first_penalty = models.CharField(max_length=10, choices=PENALTY_CHOICES)
    second_penalty = models.CharField(max_length=10, choices=PENALTY_CHOICES)
    third_penalty = models.CharField(max_length=10, choices=PENALTY_CHOICES)
    fourth_penalty = models.CharField(max_length=10, choices=PENALTY_CHOICES)
    remarks = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['group', 'rule_id']
        verbose_name = 'Offense Rule'
        verbose_name_plural = 'Offense Rules'

    def __str__(self):
        return f"{self.rule_id} - {self.name}"

    def get_penalty_for_count(self, count):
        if count == 1:
            return self.first_penalty
        elif count == 2:
            return self.second_penalty
        elif count == 3:
            return self.third_penalty
        elif count >= 4:
            return self.fourth_penalty
        return None

    def get_penalty_display(self, penalty_code):
        return dict(self.PENALTY_CHOICES).get(penalty_code, penalty_code)


class EmployeeOffence(models.Model):
    employee = models.ForeignKey('Employee', on_delete=models.CASCADE, related_name='employee_offence_records')
    rule = models.ForeignKey(OffenseRule, on_delete=models.PROTECT)
    offense_date = models.DateField()
    applied_penalty = models.CharField(max_length=10, choices=OffenseRule.PENALTY_CHOICES)
    original_penalty = models.CharField(max_length=10, choices=OffenseRule.PENALTY_CHOICES, null=True, blank=True)
    offense_count = models.PositiveIntegerField(default=1)
    details = models.TextField(blank=True)
    
    # Monetary penalty fields
    monetary_amount = models.DecimalField(max_digits=10, decimal_places=3, null=True, blank=True)
    remaining_amount = models.DecimalField(max_digits=10, decimal_places=3, null=True, blank=True)
    monthly_deduction = models.DecimalField(max_digits=10, decimal_places=3, null=True, blank=True)
    
    # Status tracking
    is_acknowledged = models.BooleanField(default=False)
    acknowledged_at = models.DateTimeField(null=True, blank=True)
    signed_date = models.DateTimeField(null=True, blank=True)
    refused_date = models.DateTimeField(null=True, blank=True)
    refused_reason = models.TextField(blank=True, null=True)
    sent_date = models.DateTimeField(null=True, blank=True)
    completed_date = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    
    # Audit fields
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='created_offence_records')
    modified_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='modified_offence_records')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-offense_date', '-created_at']
        verbose_name = 'Employee Offense'
        verbose_name_plural = 'Employee Offenses'

    def __str__(self):
        return f"{self.employee} - {self.rule.name} ({self.offense_date})"

    def save(self, *args, **kwargs):
        # If this is a new offense, set the offense count
        if not self.pk:
            self.offense_count = self.get_offense_count()
            
            # If this is a monetary penalty, set the remaining amount
            if self.applied_penalty == 'MONETARY' and self.monetary_amount:
                self.remaining_amount = self.monetary_amount

        super().save(*args, **kwargs)

    def get_offense_count(self):
        """Get the count of active offenses for this rule and employee"""
        return EmployeeOffence.objects.filter(
            employee=self.employee,
            rule=self.rule,
            offense_date__year=self.offense_date.year,
            is_active=True
        ).count() + 1

    def get_original_penalty_display(self):
        return dict(OffenseRule.PENALTY_CHOICES).get(self.original_penalty, '')

    def get_applied_penalty_display(self):
        penalty = dict(OffenseRule.PENALTY_CHOICES).get(self.applied_penalty, '')
        if self.applied_penalty == 'MONETARY' and self.monetary_amount:
            penalty += f" ({self.monetary_amount} BHD)"
        return penalty

    @classmethod
    def deactivate_previous_year_offenses(cls):
        """Deactivate all offenses from previous years"""
        current_year = timezone.now().year
        cls.objects.filter(
            offense_date__year__lt=current_year,
            is_active=True
        ).update(is_active=False)

class OffenseDocument(models.Model):
    offense = models.ForeignKey(EmployeeOffence, on_delete=models.CASCADE, related_name='documents')
    document = models.FileField(upload_to='offense_documents/')
    document_type = models.CharField(max_length=50)
    notes = models.TextField(blank=True, null=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-uploaded_at']

    def __str__(self):
        return f"{self.offense} - {self.document_type}"

class LifeEvent(models.Model):
    EVENT_TYPES = [
        ('MAR', 'Marriage'),
        ('CHD', 'Child Birth'),
        ('DEA', 'Death in Family'),
        ('OTH', 'Other'),
    ]

    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='life_events')
    event_type = models.CharField(max_length=3, choices=EVENT_TYPES)
    date = models.DateField()
    description = models.TextField()
    documents = models.FileField(upload_to='life_event_documents/', blank=True)

    def __str__(self):
        return f"{self.get_event_type_display()} on {self.date}"

class SalaryDetail(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='salary_details')
    basic_salary = models.DecimalField(max_digits=10, decimal_places=3)
    housing_allowance = models.DecimalField(max_digits=10, decimal_places=3, default=0)
    transportation_allowance = models.DecimalField(max_digits=10, decimal_places=3, default=0)
    other_allowances = models.JSONField(default=dict, help_text="Store other allowances as key-value pairs")
    total_salary = models.DecimalField(max_digits=10, decimal_places=3)
    currency = models.CharField(max_length=3, default='BHD')
    effective_from = models.DateField()
    effective_to = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='created_salary_details')

    class Meta:
        ordering = ['-effective_from']
        verbose_name = "Salary Detail"
        verbose_name_plural = "Salary Details"

    def __str__(self):
        return f"{self.employee.get_full_name()} - {self.effective_from}"

    def save(self, *args, **kwargs):
        # Calculate total salary
        self.total_salary = (
            self.basic_salary +
            self.housing_allowance +
            self.transportation_allowance +
            sum(float(amount) for amount in self.other_allowances.values())
        )
        
        # If this is a new active salary detail, deactivate other active ones
        if self.is_active and not self.pk:
            SalaryDetail.objects.filter(
                employee=self.employee,
                is_active=True
            ).update(
                is_active=False,
                effective_to=self.effective_from
            )
            
        super().save(*args, **kwargs)

class SalaryRevision(models.Model):
    REVISION_TYPES = [
        ('INC', 'Increment'),
        ('PRO', 'Promotion'),
        ('ADJ', 'Adjustment'),
        ('DEM', 'Demotion'),
        ('PEN', 'Penalty'),
        ('OTH', 'Other'),
    ]

    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='salary_revisions')
    revision_type = models.CharField(max_length=3, choices=REVISION_TYPES)
    previous_salary = models.ForeignKey(SalaryDetail, on_delete=models.PROTECT, related_name='revisions_from')
    new_salary = models.ForeignKey(SalaryDetail, on_delete=models.PROTECT, related_name='revisions_to')
    revision_date = models.DateField()
    reason = models.TextField()
    reference_number = models.CharField(max_length=50, blank=True, null=True)
    approved_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-revision_date']
        verbose_name = "Salary Revision"
        verbose_name_plural = "Salary Revisions"

    def __str__(self):
        return f"{self.employee.get_full_name()} - {self.get_revision_type_display()} on {self.revision_date}"

    @property
    def difference(self):
        return self.new_salary.total_salary - self.previous_salary.total_salary

    @property
    def percentage_change(self):
        return (self.difference / self.previous_salary.total_salary) * 100

class SalaryCertificate(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='salary_certificates')
    certificate_number = models.CharField(max_length=50, unique=True)
    issued_date = models.DateField()
    purpose = models.CharField(max_length=200)
    salary_detail = models.ForeignKey(SalaryDetail, on_delete=models.PROTECT)
    issued_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    is_valid = models.BooleanField(default=True)
    expiry_date = models.DateField(null=True, blank=True)
    additional_notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-issued_date']
        verbose_name = "Salary Certificate"
        verbose_name_plural = "Salary Certificates"

    def __str__(self):
        return f"{self.employee.get_full_name()} - {self.certificate_number}"

```

