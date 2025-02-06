from django import template
from django.utils import timezone
from django.utils.safestring import mark_safe
from django.db.models import Sum
from datetime import datetime, date
from attendance.models import (
    AttendanceLog, Leave, LeaveBalance, Holiday
)

register = template.Library()

@register.filter
def format_time(time_obj):
    """Format time object as HH:MM AM/PM"""
    if not time_obj:
        return '-'
    return time_obj.strftime('%I:%M %p')

@register.filter
def format_duration(duration):
    """Format duration in days, handling half days"""
    if not duration:
        return '0'
    if duration.is_integer():
        return str(int(duration))
    return f"{duration:.1f}"

@register.simple_tag
def attendance_status_badge(status, is_late=False):
    """Return HTML badge for attendance status"""
    colors = {
        'present': 'success',
        'absent': 'danger',
        'late': 'warning',
        'leave': 'info',
        'holiday': 'secondary'
    }
    
    status = status.lower()
    if status == 'present' and is_late:
        status = 'late'
        
    color = colors.get(status, 'light')
    
    return mark_safe(
        f'<span class="badge bg-{color}">{status.title()}</span>'
    )

@register.simple_tag
def leave_type_badge(leave_type):
    """Return HTML badge for leave type"""
    colors = {
        'annual': 'primary',
        'sick': 'danger',
        'emergency': 'warning',
        'injury': 'danger',
        'maternity': 'info',
        'paternity': 'info',
        'marriage': 'success',
        'death': 'dark',
        'permission': 'secondary'
    }
    
    color = colors.get(leave_type.code.lower(), 'light')
    
    return mark_safe(
        f'<span class="badge bg-{color}">{leave_type.name}</span>'
    )

@register.simple_tag
def leave_balance_display(employee, leave_type, date_obj=None):
    """Display leave balance with consumed/remaining days"""
    if not date_obj:
        date_obj = timezone.now().date()
    
    try:
        balance = LeaveBalance.objects.get(
            employee=employee,
            leave_type=leave_type,
            is_active=True
        )
        
        # Get leaves taken this year
        year_start = date(date_obj.year, 1, 1)
        year_end = date(date_obj.year, 12, 31)
        
        consumed = Leave.objects.filter(
            employee=employee,
            leave_type=leave_type,
            start_date__gte=year_start,
            end_date__lte=year_end,
            status='approved',
            is_active=True
        ).aggregate(total=Sum('duration'))['total'] or 0
        
        remaining = balance.available_days
        
        return mark_safe(
            f'<span class="text-muted">{consumed}</span> / '
            f'<strong class="text-primary">{remaining}</strong>'
        )
        
    except LeaveBalance.DoesNotExist:
        return mark_safe(
            '<span class="text-muted">0</span> / '
            '<strong class="text-primary">0</strong>'
        )

@register.simple_tag
def monthly_attendance_summary(employee, year, month):
    """Generate monthly attendance summary"""
    start_date = date(year, month, 1)
    if month == 12:
        end_date = date(year + 1, 1, 1)
    else:
        end_date = date(year, month + 1, 1)
    
    logs = AttendanceLog.objects.filter(
        employee=employee,
        date__gte=start_date,
        date__lt=end_date,
        is_active=True
    )
    
    summary = {
        'present': logs.filter(status='present', is_late=False).count(),
        'late': logs.filter(status='present', is_late=True).count(),
        'absent': logs.filter(status='absent').count(),
        'leave': logs.filter(status='leave').count(),
        'holiday': logs.filter(status='holiday').count(),
    }
    
    return mark_safe(
        '<div class="attendance-summary">'
        f'<div class="present">Present: {summary["present"]}</div>'
        f'<div class="late">Late: {summary["late"]}</div>'
        f'<div class="absent">Absent: {summary["absent"]}</div>'
        f'<div class="leave">Leave: {summary["leave"]}</div>'
        f'<div class="holiday">Holiday: {summary["holiday"]}</div>'
        '</div>'
    )

@register.simple_tag
def is_holiday(date_obj):
    """Check if a date is a holiday"""
    return Holiday.objects.filter(
        date=date_obj,
        is_active=True
    ).exists()

@register.simple_tag
def get_leave_status(employee, date_obj):
    """Get leave status for a date"""
    leave = Leave.objects.filter(
        employee=employee,
        start_date__lte=date_obj,
        end_date__gte=date_obj,
        status='approved',
        is_active=True
    ).first()
    
    if leave:
        return {
            'on_leave': True,
            'type': leave.leave_type,
            'start_date': leave.start_date,
            'end_date': leave.end_date
        }
    
    return {'on_leave': False}

@register.filter
def attendance_date_class(date_obj, employee):
    """Return CSS class for calendar date based on attendance"""
    classes = []
    
    # Check if weekend
    if date_obj.weekday() in [4, 5]:  # Friday, Saturday
        classes.append('weekend')
    
    # Check if holiday
    if is_holiday(date_obj):
        classes.append('holiday')
        return ' '.join(classes)
    
    # Check if on leave
    leave_status = get_leave_status(employee, date_obj)
    if leave_status['on_leave']:
        classes.append('leave')
        return ' '.join(classes)
    
    # Get attendance status
    log = AttendanceLog.objects.filter(
        employee=employee,
        date=date_obj,
        is_active=True
    ).first()
    
    if log:
        if log.is_late:
            classes.append('late')
        elif log.status == 'present':
            classes.append('present')
        elif log.status == 'absent':
            classes.append('absent')
    elif date_obj < timezone.now().date():
        classes.append('absent')
        
    return ' '.join(classes)
