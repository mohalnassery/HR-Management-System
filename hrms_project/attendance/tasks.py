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


def process_monthly_leave_accruals():
    """Process monthly leave accruals for all employees"""
    today = timezone.now().date()
    
    # Check if it's the first day of the month
    if today.day == 1:
        employees = Employee.objects.filter(
            is_active=True
        )
        
        for employee in employees:
            with transaction.atomic():
                # Increment leave balance for each leave type
                for leave_type in employee.leave_types.all():
                    employee.leave_balances.create(
                        leave_type=leave_type,
                        year=today.year,
                        balance=leave_type.accrual_rate
                    )
        
        logger.info("Processed monthly leave accruals")
        return employees.count()
    
    return 0