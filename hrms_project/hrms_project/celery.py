import os
from celery import Celery
from django.conf import settings
from attendance.schedules import get_schedule_config

# Set default Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hrms_project.settings')

# Create Celery app
app = Celery('hrms_project')

# Load settings from Django settings.py
app.config_from_object('django.conf:settings', namespace='CELERY')

# Auto-discover tasks from all installed apps
app.autodiscover_tasks()

# Get schedule configuration
schedule_config = get_schedule_config()

# Configure beat schedule
app.conf.beat_schedule = schedule_config['schedules']

# Configure task routing based on priorities
app.conf.task_routes = {
    task_name: {'queue': priority}
    for task_name, priority in schedule_config['priorities'].items()
}

# Configure task default settings
app.conf.task_default_queue = 'normal'
app.conf.task_queues = {
    'high': {'exchange': 'high', 'routing_key': 'high'},
    'normal': {'exchange': 'normal', 'routing_key': 'normal'},
    'low': {'exchange': 'low', 'routing_key': 'low'}
}

# Configure retry settings
app.conf.task_annotations = {
    task_name: {
        'max_retries': (
            schedule_config['retry']['critical']['max_retries']
            if task_name in schedule_config['groups']['critical']
            else schedule_config['retry']['default']['max_retries']
        ),
        'retry_backoff': True,
        'retry_backoff_max': (
            schedule_config['retry']['critical']['interval_max']
            if task_name in schedule_config['groups']['critical']
            else schedule_config['retry']['default']['interval_max']
        )
    }
    for task_name in schedule_config['schedules'].keys()
}

# Error handling setup
app.conf.task_send_sent_event = True
app.conf.worker_send_task_events = True

# Task result settings
app.conf.result_expires = 60 * 60 * 24  # Results expire after 24 hours
app.conf.task_ignore_result = True  # Don't store results by default

# Performance optimizations
app.conf.worker_prefetch_multiplier = 1  # Prevent worker from prefetching too many tasks
app.conf.task_acks_late = True  # Only acknowledge task after completion
app.conf.task_reject_on_worker_lost = True  # Reject task if worker dies

# Task soft and hard time limits
app.conf.task_soft_time_limit = 60 * 30  # 30 minutes soft limit
app.conf.task_time_limit = 60 * 60  # 1 hour hard limit

@app.task(bind=True)
def debug_task(self):
    """Task for debugging Celery configuration"""
    print(f'Request: {self.request!r}')

@app.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):
    """Setup any additional periodic tasks after configuration"""
    # You can add dynamic task scheduling here if needed
    pass

@app.on_after_finalize.connect
def setup_error_handlers(sender, **kwargs):
    """Setup error handlers for tasks"""
    from celery.signals import task_failure
    
    @task_failure.connect
    def handle_task_failure(task_id, exception, args, kwargs, traceback, einfo, **error_kwargs):
        """Handle task failures and send notifications if needed"""
        from django.core.mail import send_mail
        from django.conf import settings
        
        error_config = schedule_config['error_handling']
        if error_config['notify_on_error']:
            subject = f'Task Failure Alert: {task_id}'
            message = (
                f'Task {task_id} failed with exception: {exception}\n'
                f'Args: {args}\nKwargs: {kwargs}\n'
                f'Traceback:\n{einfo}'
            )
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=error_config['error_recipients']
            )

if __name__ == '__main__':
    app.start()
