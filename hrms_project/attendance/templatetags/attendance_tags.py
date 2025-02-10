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
