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
    from .cache import RamadanCache
    
    # Clear cache for the period's date range
    current_date = instance.start_date
    while current_date <= instance.end_date:
        RamadanCache.clear_active_period(current_date)
        current_date += timedelta(days=1)
    
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
    # Clear shift statistics cache
    cache_key = f'shift_statistics_{instance.id}'
    cache.delete(cache_key)
    
    # If shift is deactivated, deactivate its assignments
    if not instance.is_active:
        assignments = ShiftAssignment.objects.filter(
            shift=instance,
            is_active=True
        )
        
        # Collect affected employee IDs before deactivating
        affected_employees = list(assignments.values_list('employee_id', flat=True))
        
        # Deactivate assignments
        assignments.update(is_active=False)
        
        # Clear cache for each affected employee
        from .cache import invalidate_employee_caches
        for employee_id in affected_employees:
            invalidate_employee_caches(employee_id)
    # Even if shift isn't deactivated, we need to invalidate caches for affected employees
    else:
        # Get all employees assigned to this shift and clear their caches
        affected_employees = ShiftAssignment.objects.filter(
            shift=instance,
            is_active=True
        ).values_list('employee_id', flat=True)
        
        from .cache import invalidate_employee_caches
        for employee_id in affected_employees:
            invalidate_employee_caches(employee_id)

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
                    total_days=instance.days_allowed if not instance.accrual_enabled else 0,
                    used_days=0,
                    pending_days=0,
                    last_reset_date=timezone.now().date()
                ))
        
        if balances:
            LeaveBalance.objects.bulk_create(balances)
