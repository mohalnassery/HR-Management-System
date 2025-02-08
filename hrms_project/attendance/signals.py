from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.utils import timezone
from django.core.exceptions import ObjectDoesNotExist
from .models import (
    AttendanceRecord, AttendanceLog, Leave, LeaveType, 
    LeaveBalance, Holiday, Employee
)
from .services import AttendanceStatusService
from datetime import datetime, timedelta

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
        log.shift = instance.employee.shift
        
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
