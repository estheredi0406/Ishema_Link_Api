"""
Celery configuration for IshemaLink
Handles async task processing for notifications and background jobs
"""
import os
from celery import Celery

# Set default Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ishemalink.settings')

# Create Celery app
app = Celery('ishemalink')

# Load config from Django settings (all CELERY_* settings)
app.config_from_object('django.conf:settings', namespace='CELERY')

# Auto-discover tasks in all installed apps
app.autodiscover_tasks()


@app.task(bind=True, ignore_result=True)
def debug_task(self):
    """Debug task for testing Celery setup"""
    print(f'Request: {self.request!r}')