import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
app = Celery('gm')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

from celery.schedules import crontab
app.conf.beat_schedule = {
    'generate-auto-playlists-daily': {
        'task': 'apps.playlists.tasks.generate_all_auto_playlists',
        'schedule': crontab(hour=3, minute=0),
    },
}
