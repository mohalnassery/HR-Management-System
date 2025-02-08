import os
from celery import Celery
from celery.schedules import crontab

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hrms_project.settings')

app = Celery('hrms_project')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

# Configure periodic tasks
app.conf.beat_schedule = {
    # Process leave accruals on the 1st of each month
    'process-monthly-leave-accruals': {
        'task': 'attendance.tasks.process_monthly_leave_accruals',
        'schedule': crontab(day_of_month='1', hour='0', minute='0'),
    },
    
    # Reset leave balances on January 1st
    'process-leave-year-reset': {
        'task': 'attendance.tasks.process_leave_year_reset',
        'schedule': crontab(month_of_year='1', day_of_month='1', hour='0', minute='0'),
    },
    
    # Process Friday attendance daily (task will check if it's Friday)
    'process-friday-attendance': {
        'task': 'attendance.tasks.process_friday_attendance',
        'schedule': crontab(hour='22', minute='0'),  # Run at 10 PM daily
    },
    
    # Process recurring holidays on December 1st
    'process-recurring-holidays': {
        'task': 'attendance.tasks.process_recurring_holidays',
        'schedule': crontab(month_of_year='12', day_of_month='1', hour='0', minute='0'),
    },

    # Process attendance records every 15 minutes
    'process-attendance-records': {
        'task': 'attendance.tasks.process_attendance_records',
        'schedule': crontab(minute='*/15'),  # Run every 15 minutes
    },
}

@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')
