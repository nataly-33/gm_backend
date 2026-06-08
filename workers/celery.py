import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
app = Celery('gm')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

# ── Resiliencia de conexión al broker ────────────────────────────────────────
# Necesario en Windows/WSL2 donde Redis puede caerse y volver.
# broker_connection_retry_on_startup elimina el CPendingDeprecationWarning.
app.conf.broker_connection_retry_on_startup = True
app.conf.broker_connection_retry            = True
app.conf.broker_connection_max_retries      = None   # reintentar indefinidamente
app.conf.broker_heartbeat                   = 10     # detecta caídas en ~10s
app.conf.broker_transport_options = {
    'visibility_timeout': 3600,
    'socket_keepalive':   True,
}
app.conf.worker_cancel_long_running_tasks_on_connection_loss = True

from celery.schedules import crontab
app.conf.beat_schedule = {
    'generate-auto-playlists-daily': {
        'task': 'apps.playlists.tasks.generate_all_auto_playlists',
        'schedule': crontab(hour=3, minute=0),
    },
}
