from django.db.models.signals import pre_save, post_save, pre_delete, post_delete
from django.dispatch import receiver
from django.utils import timezone
from django.db import transaction
from django.db.models import Q
from datetime import datetime, timedelta
from typing import List
import logging

# Configure logging
logger = logging.getLogger(__name__)

# Try to import cache, but don't fail if it's not configured
try:
    from django.core.cache import cache
    logger.info("Successfully imported cache in signals")
except ImportError:
    logger.warning("Failed to import cache in signals, continuing without caching")
    cache = None

from .models import (
    Shift, ShiftAssignment, RamadanPeriod, AttendanceLog,
    AttendanceRecord, Leave, LeaveType, LeaveBalance, Holiday, Employee
)
from .services import (
    ShiftService, RamadanService, AttendanceStatusService
)
from .services.cache_invalidation_service import CacheInvalidationService

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
            
        # Clear caches
        CacheInvalidationService.invalidate_shift_related_caches(
            employee_ids=[instance.employee_id],
            department_ids={instance.employee.department_id} if instance.employee.department_id else None
        )

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
    if cache:
        try:
            cache_key = f'employee_shift_{instance.employee_id}'
            cache.delete(cache_key)
            logger.debug(f"Successfully cleared cache for key: {cache_key}")
        except Exception as e:
            logger.error(f"Error clearing cache: {str(e)}")

@receiver(pre_delete, sender=ShiftAssignment)
def handle_shift_assignment_delete(sender, instance, **kwargs):
    """Handle shift assignment deletion"""
    # Clear caches
    CacheInvalidationService.invalidate_shift_related_caches(
        employee_ids=[instance.employee_id],
        department_ids={instance.employee.department_id} if instance.employee.department_id else None
    )

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
    # Clear caches
    CacheInvalidationService.invalidate_ramadan_related_caches(
        start_date=instance.start_date,
        end_date=instance.end_date
    )
    
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
    # Get affected employees
    affected_employees = list(ShiftAssignment.objects.filter(
        shift=instance,
        is_active=True
    ).values_list('employee_id', flat=True))

    # Get affected departments
    affected_departments = set(Employee.objects.filter(
        id__in=affected_employees
    ).values_list('department_id', flat=True))

    # Clear caches
    CacheInvalidationService.invalidate_shift_related_caches(
        employee_ids=affected_employees,
        shift_id=instance.id,
        department_ids=affected_departments
    )

    # If shift is deactivated, deactivate its assignments
    if not instance.is_active:
        ShiftAssignment.objects.filter(
            shift=instance,
            is_active=True
        ).update(is_active=False)

@receiver(pre_save, sender=AttendanceLog)
def calculate_attendance_status(sender, instance, **kwargs):
    """
    Calculate attendance status based on shift
    """
    # Skip calculation for holidays and leaves
    if instance.status in ['holiday', 'leave']:
        return

    # Get the employee's shift for this date
    shift = instance.shift
    if not shift:
        shift = ShiftAssignment.objects.filter(
            employee=instance.employee,
            start_date__lte=instance.date,
            is_active=True
        ).filter(
            Q(end_date__isnull=True) | Q(end_date__gte=instance.date)
        ).order_by('-start_date').first()

        if shift:
            shift = shift.shift
        else:
            # Use default shift if no assignment found
            shift = Shift.objects.filter(shift_type='DEFAULT', is_active=True).first()

        instance.shift = shift

    if not shift:
        instance.status = 'absent'
        return

    # If we have first_in_time, employee is present
    if instance.first_in_time:
        # Get shift timing considering Ramadan period
        ramadan_timing = RamadanService.get_ramadan_shift_timing(shift, instance.date)
        start_time = ramadan_timing.get('start_time', shift.start_time)
        
        # Convert times to datetime for comparison
        date = instance.date
        shift_start = datetime.combine(date, start_time)
        first_in = datetime.combine(date, instance.first_in_time)

        # Calculate late minutes
        grace_minutes = shift.grace_period if shift else 15
        grace_time = shift_start + timedelta(minutes=grace_minutes)
        
        if first_in > grace_time:
            instance.is_late = True
            instance.late_minutes = int((first_in - grace_time).total_seconds() / 60)
            instance.status = 'late'
        else:
            instance.is_late = False
            instance.late_minutes = 0
            instance.status = 'present'

        # Calculate total work minutes if we have last_out_time
        if instance.last_out_time:
            last_out = datetime.combine(date, instance.last_out_time)
            if last_out < first_in:  # Handle case where checkout is next day
                last_out += timedelta(days=1)
            total_minutes = int((last_out - first_in).total_seconds() / 60)
            instance.total_work_minutes = max(0, total_minutes)
    else:
        instance.status = 'absent'
        instance.total_work_minutes = 0

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
                    source='leave'
                )
            current_date += timedelta(days=1)

        # Update leave balance
        try:
            balance = LeaveBalance.objects.get(
                employee=instance.employee,
                leave_type=instance.leave_type,
                is_active=True
            )
            balance.used_days += instance.duration
            balance.pending_days = max(0, balance.pending_days - instance.duration)  # Remove from pending if was pending
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
            balance.used_days = max(0, balance.used_days - instance.duration)  # Ensure we don't go negative
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

    # Get all active employees
    employees = Employee.objects.filter(is_active=True)

    for employee in employees:
        # Update or create attendance log
        AttendanceLog.objects.update_or_create(
            employee=employee,
            date=instance.date,
            defaults={
                'status': 'holiday',
                'source': 'holiday',
                'is_active': True
            }
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
                    total_days=instance.days_allowed if not instance.accrual_enabled else 0,
                    used_days=0,
                    pending_days=0,
                    last_reset_date=timezone.now().date()
                ))
        
        if balances:
            LeaveBalance.objects.bulk_create(balances)
