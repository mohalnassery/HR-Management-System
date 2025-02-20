"""
Celery Beat schedule configurations for attendance tasks
"""

BEAT_SCHEDULE = {
    'process-monthly-leave-accruals': {
        'task': 'attendance.tasks.process_monthly_leave_accruals',
        'schedule': 60 * 60 * 24,  # Daily at midnight (will only run on 1st day of month)
    },
    'process-leave-year-reset': {
        'task': 'attendance.tasks.process_leave_year_reset',
        'schedule': 60 * 60 * 24,  # Daily at midnight (will only run on Jan 1st)
    },
    'process-friday-attendance': {
        'task': 'attendance.tasks.process_friday_attendance',
        'schedule': 60 * 60 * 24,  # Daily at midnight (will only run on Fridays)
    },
    'process-recurring-holidays': {
        'task': 'attendance.tasks.process_recurring_holidays',
        'schedule': 60 * 60 * 24,  # Daily at midnight (will only run on Dec 1st)
    },
}
