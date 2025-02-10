from celery.schedules import crontab

# Schedule configuration for periodic tasks
SHIFT_SCHEDULES = {
    # Check and deactivate expired shift assignments daily at 00:01 AM
    'update-expired-shifts': {
        'task': 'attendance.tasks.update_expired_shift_assignments',
        'schedule': crontab(hour=0, minute=1),
        'options': {
            'expires': 3600  # Task expires after 1 hour
        }
    },
    
    # Notify about upcoming shift changes daily at 6:00 AM
    'notify-shift-changes': {
        'task': 'attendance.tasks.notify_shift_changes',
        'schedule': crontab(hour=6, minute=0),
        'options': {
            'expires': 3600
        }
    },
    
    # Process Ramadan shift changes daily at 00:05 AM
    'process-ramadan-shifts': {
        'task': 'attendance.tasks.process_ramadan_shift_changes',
        'schedule': crontab(hour=0, minute=5),
        'options': {
            'expires': 3600
        }
    },
    
    # Calculate attendance metrics daily at 1:00 AM
    'calculate-attendance-metrics': {
        'task': 'attendance.tasks.calculate_attendance_metrics',
        'schedule': crontab(hour=1, minute=0),
        'options': {
            'expires': 7200  # Expires after 2 hours
        }
    },
    
    # Check for missing shift assignments weekly on Sunday at 8:00 AM
    'check-missing-shifts': {
        'task': 'attendance.tasks.notify_missing_shift_assignments',
        'schedule': crontab(hour=8, minute=0, day_of_week=0),
        'options': {
            'expires': 3600
        }
    }
}

# Optional overrides for holidays and weekends
SCHEDULE_OVERRIDES = {
    'ignore_dates': [
        # Add specific dates to ignore tasks
        # Format: 'YYYY-MM-DD'
    ],
    'weekend_schedule': {
        # Define different schedules for weekends if needed
        'update-expired-shifts': {
            'schedule': crontab(hour=1, minute=0)  # Run later on weekends
        }
    }
}

# Schedule Groups
SCHEDULE_GROUPS = {
    'critical': [
        'update-expired-shifts',
        'process-ramadan-shifts'
    ],
    'notifications': [
        'notify-shift-changes',
        'notify-missing-shift-assignments'
    ],
    'reports': [
        'calculate-attendance-metrics'
    ]
}

# Retry Settings
RETRY_SETTINGS = {
    'default': {
        'max_retries': 3,
        'interval_start': 0,
        'interval_step': 300,  # 5 minutes
        'interval_max': 3600,  # 1 hour
    },
    'critical': {
        'max_retries': 5,
        'interval_start': 0,
        'interval_step': 180,  # 3 minutes
        'interval_max': 1800,  # 30 minutes
    }
}

# Task Priority Settings
TASK_PRIORITIES = {
    'update-expired-shifts': 'high',
    'process-ramadan-shifts': 'high',
    'notify-shift-changes': 'normal',
    'calculate-attendance-metrics': 'low',
    'notify-missing-shift-assignments': 'normal'
}

# Error Notification Settings
ERROR_NOTIFICATION = {
    'notify_on_error': True,
    'error_recipients': ['hr@example.com', 'tech@example.com'],
    'error_threshold': 3,  # Number of failures before notification
    'error_cooldown': 1800  # 30 minutes between notifications
}

def get_schedule_config():
    """Get complete schedule configuration"""
    return {
        'schedules': SHIFT_SCHEDULES,
        'overrides': SCHEDULE_OVERRIDES,
        'groups': SCHEDULE_GROUPS,
        'retry': RETRY_SETTINGS,
        'priorities': TASK_PRIORITIES,
        'error_handling': ERROR_NOTIFICATION
    }

def get_task_schedule(task_name):
    """Get schedule configuration for a specific task"""
    if task_name in SHIFT_SCHEDULES:
        return {
            'schedule': SHIFT_SCHEDULES[task_name],
            'retry': (
                RETRY_SETTINGS['critical'] 
                if task_name in SCHEDULE_GROUPS['critical']
                else RETRY_SETTINGS['default']
            ),
            'priority': TASK_PRIORITIES.get(task_name, 'normal')
        }
    return None

def is_task_enabled(task_name, date_str=None):
    """Check if a task should run on a given date"""
    if date_str and date_str in SCHEDULE_OVERRIDES['ignore_dates']:
        return False
    return True
