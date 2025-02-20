from django.apps import AppConfig
from django.db.models.signals import post_save, post_delete
from typing import Dict, Tuple, Callable


class AttendanceConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'attendance'
    verbose_name = 'Attendance Management'

    def _connect_model_signals(self):
        """
        Dynamically connect signal handlers for models.
        Uses a configuration dictionary to map models to their signal handlers.
        """
        from . import signals

        # Define signal handlers for each model
        # Format: 'model_name': (post_save_handler, post_delete_handler)
        signal_handlers: Dict[str, Tuple[Callable, Callable]] = {
            'AttendanceRecord': (
                signals.process_attendance_record,
                signals.cleanup_attendance_record
            ),
            'Leave': (
                signals.process_leave_request,
                signals.cleanup_leave_request
            ),
            'Holiday': (
                signals.process_holiday,
                signals.cleanup_holiday
            ),
        }

        # Special case for LeaveType which only needs post_save
        single_handlers = {
            'LeaveType': (signals.create_leave_balances, None)
        }

        # Connect regular signals (post_save and post_delete)
        for model_name, (save_handler, delete_handler) in signal_handlers.items():
            sender = f'{self.name}.{model_name}'
            post_save.connect(save_handler, sender=sender)
            post_delete.connect(delete_handler, sender=sender)

        # Connect single signals
        for model_name, (save_handler, delete_handler) in single_handlers.items():
            sender = f'{self.name}.{model_name}'
            if save_handler:
                post_save.connect(save_handler, sender=sender)
            if delete_handler:
                post_delete.connect(delete_handler, sender=sender)

    def _setup_celery_schedule(self):
        """
        Set up Celery Beat schedule from the schedules module.
        Handles the case where Celery is not installed or configured.
        """
        try:
            from django.conf import settings
            from .schedules import BEAT_SCHEDULE

            # Only update if Celery is configured
            if hasattr(settings, 'CELERY_BEAT_SCHEDULE'):
                settings.CELERY_BEAT_SCHEDULE.update(BEAT_SCHEDULE)
        except ImportError:
            # Celery not installed or configured, skip task scheduling
            pass

    def ready(self):
        """
        Initialize app configuration when Django is ready.
        Connects signal handlers and sets up periodic tasks.
        """
        # Connect model signals
        self._connect_model_signals()

        # Setup Celery Beat schedule
        self._setup_celery_schedule()

        # Load and register custom template tags
        from django.template.backends.django import get_installed_libraries
        get_installed_libraries()
