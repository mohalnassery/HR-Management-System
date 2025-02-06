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
