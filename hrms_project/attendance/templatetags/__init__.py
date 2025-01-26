"""
Attendance template tags and filters.

This package provides Django template tags and filters for working with
attendance, leaves, and holidays.

Available tags and filters:
- format_duration: Format duration in days to a human-readable string
- status_badge: Render a status badge with appropriate color
- format_time: Format time value to 12-hour format
- time_difference: Calculate time difference in hours and minutes
- is_late: Check if check-in time is late based on shift
- late_by: Calculate how late the check-in was
- friday_attendance: Get Friday attendance status based on Thursday/Saturday rule
- leave_balance: Get employee's leave balance for a specific leave type
- pending_leave_requests: Get count of pending leave requests for an employee
- get_attendance_stats: Get attendance statistics for an employee in a date range
"""
