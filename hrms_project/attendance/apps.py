from django.apps import AppConfig
from django.db.models.signals import post_save, post_delete


class AttendanceConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'attendance'
    verbose_name = 'Attendance Management'

    def ready(self):
        """
        Connect signal handlers when the app is ready
        """
        # Import signal handlers
        from . import signals

        # Attendance Record Signals
        post_save.connect(signals.process_attendance_record, sender='attendance.AttendanceRecord')
        post_delete.connect(signals.cleanup_attendance_record, sender='attendance.AttendanceRecord')

        # Leave Request Signals
        post_save.connect(signals.process_leave_request, sender='attendance.Leave')
        post_delete.connect(signals.cleanup_leave_request, sender='attendance.Leave')
        
        # Holiday Signals
        post_save.connect(signals.process_holiday, sender='attendance.Holiday')
        post_delete.connect(signals.cleanup_holiday, sender='attendance.Holiday')

        # Leave Type Signals
        post_save.connect(signals.create_leave_balances, sender='attendance.LeaveType')

        # Initialize periodic tasks
        try:
            from django.conf import settings
            from .tasks import (
                process_monthly_leave_accruals,
                process_leave_year_reset,
                process_friday_attendance,
                process_recurring_holidays
            )
            
            # Schedule periodic tasks if Celery is configured
            if hasattr(settings, 'CELERY_BEAT_SCHEDULE'):
                settings.CELERY_BEAT_SCHEDULE.update({
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
                })
        except ImportError:
            # Celery not installed or configured, skip task scheduling
            pass

        # Load and register custom template tags
        from django.template.backends.django import get_installed_libraries
        get_installed_libraries()
