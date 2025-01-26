from django import template
from django.utils import timezone
from datetime import datetime, time
from django.utils.html import format_html

register = template.Library()

@register.filter
def format_duration(days):
    """Format duration in days to a human-readable string"""
    if not days:
        return '0 days'
    
    try:
        days = float(days)
        if days == 1:
            return '1 day'
        elif days == 0.5:
            return '½ day'
        elif days % 1 == 0:
            return f'{int(days)} days'
        else:
            return f'{days} days'
    except (ValueError, TypeError):
        return str(days)

@register.filter
def status_badge(status, size=''):
    """Render a status badge with appropriate color"""
    colors = {
        'pending': 'warning',
        'approved': 'success',
        'rejected': 'danger',
        'cancelled': 'secondary',
        'present': 'success',
        'absent': 'danger',
        'late': 'warning',
        'leave': 'info',
        'holiday': 'primary'
    }
    
    status = str(status).lower()
    color = colors.get(status, 'secondary')
    size_class = f'badge-{size}' if size else ''
    
    return format_html(
        '<span class="badge bg-{} {}">{}</span>',
        color,
        size_class,
        status.title()
    )

@register.filter
def format_time(value):
    """Format time value to 12-hour format"""
    if not value:
        return '-'
    
    if isinstance(value, str):
        try:
            value = datetime.strptime(value, '%H:%M:%S').time()
        except ValueError:
            try:
                value = datetime.strptime(value, '%H:%M').time()
            except ValueError:
                return value
    
    if isinstance(value, time):
        return value.strftime('%I:%M %p')
    
    return str(value)

@register.filter
def time_difference(time1, time2):
    """Calculate time difference in hours and minutes"""
    if not time1 or not time2:
        return '-'
    
    if isinstance(time1, str):
        time1 = datetime.strptime(time1, '%H:%M:%S').time()
    if isinstance(time2, str):
        time2 = datetime.strptime(time2, '%H:%M:%S').time()
    
    dt1 = datetime.combine(timezone.now().date(), time1)
    dt2 = datetime.combine(timezone.now().date(), time2)
    
    diff = dt2 - dt1
    hours = diff.seconds // 3600
    minutes = (diff.seconds % 3600) // 60
    
    if hours == 0:
        return f'{minutes} mins'
    elif minutes == 0:
        return f'{hours} hrs'
    else:
        return f'{hours} hrs {minutes} mins'

@register.simple_tag
def is_late(check_in_time, shift_start=None):
    """Check if check-in time is late based on shift"""
    if not check_in_time:
        return False
        
    if not shift_start:
        # Default shift start time (8:00 AM)
        shift_start = time(8, 0)
    
    if isinstance(check_in_time, str):
        check_in_time = datetime.strptime(check_in_time, '%H:%M:%S').time()
    
    return check_in_time > shift_start

@register.filter
def late_by(check_in_time, shift_start=None):
    """Calculate how late the check-in was"""
    if not check_in_time:
        return '-'
        
    if not shift_start:
        # Default shift start time (8:00 AM)
        shift_start = time(8, 0)
    
    if isinstance(check_in_time, str):
        check_in_time = datetime.strptime(check_in_time, '%H:%M:%S').time()
    
    if check_in_time <= shift_start:
        return '-'
    
    dt1 = datetime.combine(timezone.now().date(), shift_start)
    dt2 = datetime.combine(timezone.now().date(), check_in_time)
    
    diff = dt2 - dt1
    minutes = diff.seconds // 60
    
    if minutes < 60:
        return f'{minutes} mins'
    else:
        hours = minutes // 60
        remaining_mins = minutes % 60
        if remaining_mins == 0:
            return f'{hours} hrs'
        return f'{hours} hrs {remaining_mins} mins'

@register.filter
def friday_attendance(employee, date):
    """Get Friday attendance status based on Thursday/Saturday rule"""
    from attendance.services import FridayRuleService
    
    if not isinstance(date, datetime):
        try:
            date = datetime.strptime(date, '%Y-%m-%d')
        except (ValueError, TypeError):
            return '-'
    
    if date.weekday() != 4:  # 4 is Friday
        return None
        
    return FridayRuleService.get_friday_status(employee, date.date())

@register.filter
def leave_balance(employee, leave_type):
    """Get employee's leave balance for a specific leave type"""
    from attendance.models import LeaveBalance
    
    try:
        balance = LeaveBalance.objects.get(
            employee=employee,
            leave_type=leave_type,
            is_active=True
        )
        return balance.available_days
    except LeaveBalance.DoesNotExist:
        return 0

@register.filter
def pending_leave_requests(employee):
    """Get count of pending leave requests for an employee"""
    from attendance.models import Leave
    
    return Leave.objects.filter(
        employee=employee,
        status='pending',
        is_active=True
    ).count()

@register.simple_tag
def get_attendance_stats(employee, start_date=None, end_date=None):
    """Get attendance statistics for an employee in a date range"""
    if not start_date:
        start_date = timezone.now().replace(day=1).date()
    if not end_date:
        end_date = timezone.now().date()
        
    from attendance.models import AttendanceLog, Leave, Holiday
    
    # Get counts
    present = AttendanceLog.objects.filter(
        employee=employee,
        date__range=(start_date, end_date),
        is_active=True,
        first_in_time__isnull=False
    ).count()
    
    absent = (end_date - start_date).days + 1 - present
    
    late = AttendanceLog.objects.filter(
        employee=employee,
        date__range=(start_date, end_date),
        is_active=True,
        is_late=True
    ).count()
    
    leave = Leave.objects.filter(
        employee=employee,
        status='approved',
        start_date__lte=end_date,
        end_date__gte=start_date,
        is_active=True
    ).count()
    
    holidays = Holiday.objects.filter(
        date__range=(start_date, end_date),
        is_active=True
    ).count()
    
    return {
        'present': present,
        'absent': absent - leave - holidays,  # Exclude leaves and holidays from absents
        'late': late,
        'leave': leave,
        'holidays': holidays
    }
