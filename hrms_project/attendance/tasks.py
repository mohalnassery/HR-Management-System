from celery import shared_task
from django.utils import timezone
from django.db.models import Q, F
from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from datetime import datetime, timedelta

from .models import (
    Employee, AttendanceLog, Leave, LeaveType,
    LeaveBalance, Holiday
)
from .services import (
    FridayRuleService, LeaveBalanceService,
    RecurringHolidayService, AttendanceStatusService
)

@shared_task
def process_monthly_leave_accruals():
    """
    Process monthly leave accruals for all employees.
    Runs daily at midnight but only executes on the 1st of each month.
    """
    today = timezone.now().date()
    if today.day != 1:  # Only run on first day of month
        return

    try:
        LeaveBalanceService.update_leave_balances()

        # Send email notifications for low balances
        employees = Employee.objects.filter(is_active=True)
        for employee in employees:
            balances = LeaveBalance.objects.filter(
                employee=employee,
                is_active=True
            )
            
            low_balances = []
            for balance in balances:
                if balance.available_days < 5:  # Threshold for low balance
                    low_balances.append({
                        'type': balance.leave_type.name,
                        'balance': balance.available_days
                    })
            
            if low_balances:
                context = {
                    'employee': employee,
                    'balances': low_balances
                }
                html_message = render_to_string(
                    'attendance/email/low_balance_notification.html',
                    context
                )
                
                send_mail(
                    subject='Low Leave Balance Notification',
                    message='',
                    html_message=html_message,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[employee.email],
                    fail_silently=True
                )

        return "Monthly leave accruals processed successfully"
    except Exception as e:
        return f"Error processing monthly leave accruals: {str(e)}"

@shared_task
def process_leave_year_reset():
    """
    Reset annual leave balances at the start of each year.
    Runs daily at midnight but only executes on January 1st.
    """
    today = timezone.now().date()
    if today.month != 1 or today.day != 1:  # Only run on January 1st
        return

    try:
        leave_types = LeaveType.objects.filter(
            is_active=True,
            reset_period='yearly'
        )
        
        for leave_type in leave_types:
            balances = LeaveBalance.objects.filter(
                leave_type=leave_type,
                is_active=True
            )
            
            # Store old balance for carryover calculation
            for balance in balances:
                old_balance = balance.available_days
                
                # Apply carryover rules
                if leave_type.allow_carryover:
                    carryover = min(
                        old_balance,
                        leave_type.max_carryover or old_balance
                    )
                else:
                    carryover = 0
                
                # Reset balance
                balance.total_days = leave_type.default_days + carryover
                balance.available_days = leave_type.default_days + carryover
                balance.save()

        return "Leave year reset processed successfully"
    except Exception as e:
        return f"Error processing leave year reset: {str(e)}"

@shared_task
def process_friday_attendance():
    """
    Process Friday attendance based on Thursday/Saturday rules.
    Runs daily at midnight but only executes on Fridays.
    """
    try:
        FridayRuleService.process_friday_attendance()
        return "Friday attendance processed successfully"
    except Exception as e:
        return f"Error processing Friday attendance: {str(e)}"

@shared_task
def process_recurring_holidays():
    """
    Generate next year's holidays based on recurring holidays.
    Runs daily at midnight but only executes in December.
    """
    try:
        RecurringHolidayService.generate_next_year_holidays()
        return "Recurring holidays processed successfully"
    except Exception as e:
        return f"Error processing recurring holidays: {str(e)}"

@shared_task
def notify_pending_leave_requests():
    """
    Send notifications for pending leave requests.
    Runs every hour to notify managers of pending requests.
    """
    try:
        # Get pending leaves that haven't been notified in the last 24 hours
        pending_leaves = Leave.objects.filter(
            status='pending',
            is_active=True,
            last_notification__lte=timezone.now() - timedelta(hours=24)
        )
        
        for leave in pending_leaves:
            # Get manager email from employee's department
            if leave.employee.department and leave.employee.department.manager:
                manager_email = leave.employee.department.manager.email
                
                context = {
                    'leave': leave,
                    'employee': leave.employee
                }
                html_message = render_to_string(
                    'attendance/email/pending_leave_notification.html',
                    context
                )
                
                send_mail(
                    subject='Pending Leave Request Notification',
                    message='',
                    html_message=html_message,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[manager_email],
                    fail_silently=True
                )
                
                # Update last notification time
                leave.last_notification = timezone.now()
                leave.save()

        return "Pending leave notifications sent successfully"
    except Exception as e:
        return f"Error sending pending leave notifications: {str(e)}"

@shared_task
def process_attendance_records():
    """
    Process attendance records and update statuses.
    Runs periodically to ensure all attendance records are properly processed.
    """
    try:
        # Get records from the last 24 hours that haven't been processed
        yesterday = timezone.now() - timedelta(days=1)
        logs = AttendanceLog.objects.filter(
            Q(date__gte=yesterday) &
            Q(first_in_time__isnull=False) &
            (Q(status='absent') | Q(status__isnull=True))
        ).select_related('employee', 'shift')

        processed = 0
        for log in logs:
            try:
                AttendanceStatusService.update_attendance_status(log)
                processed += 1
            except Exception as e:
                print(f"Error processing log {log.id}: {str(e)}")
                continue

        return f"Processed {processed} attendance logs"
    except Exception as e:
        return f"Error processing attendance records: {str(e)}"

@shared_task
def send_attendance_reminders():
    """
    Send attendance reminders to employees who haven't logged attendance.
    Runs at specific times during the day (e.g., 9 AM, 2 PM).
    """
    try:
        now = timezone.now()
        today = now.date()
        
        # Skip weekends and holidays
        if now.weekday() in [4, 5]:  # Friday and Saturday
            return "Skipped: Weekend"
            
        if Holiday.objects.filter(date=today, is_active=True).exists():
            return "Skipped: Holiday"
        
        # Get employees without attendance logs for today or marked as absent
        employees_without_logs = Employee.objects.filter(
            is_active=True
        ).filter(
            Q(attendancelog__date=today, attendancelog__status='absent') |
            ~Q(attendancelog__date=today)
        )
        
        for employee in employees_without_logs:
            context = {
                'employee': employee,
                'current_time': now.strftime('%I:%M %p')
            }
            html_message = render_to_string(
                'attendance/email/attendance_reminder.html',
                context
            )
            
            send_mail(
                subject='Attendance Log Reminder',
                message='',
                html_message=html_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[employee.email],
                fail_silently=True
            )
            
        return f"Attendance reminders sent to {employees_without_logs.count()} employees"
    except Exception as e:
        return f"Error sending attendance reminders: {str(e)}"
