from apps.core.models import BaseModel
from django.db import models
from django.conf import settings
import uuid

class StemJob(BaseModel):
    STATUS_CHOICES = [
        ('queued', 'Queued'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='stem_jobs')
    source_audio_url = models.TextField()          # URL temporal en S3 del archivo subido
    source_filename = models.CharField(max_length=255)
    source_file_size_bytes = models.BigIntegerField()
    model_used = models.CharField(max_length=40, default='demucs-v4')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='queued')
    progress_pct = models.IntegerField(default=0)  # 0-100 para barra de progreso
    error_message = models.TextField(null=True, blank=True)
    credits_used = models.IntegerField(default=2)  # separar cuesta más que generar
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)

class StemFile(models.Model):
    """Archivos resultantes de la separación."""
    STEM_TYPES = [
        ('vocals', 'Vocals'),
        ('no_vocals', 'No Vocals (Karaoke)'),
        ('bass', 'Bass'),
        ('drums', 'Drums'),
        ('other', 'Other'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    stem_job = models.ForeignKey(StemJob, on_delete=models.CASCADE, related_name='stem_files')
    stem_type = models.CharField(max_length=20, choices=STEM_TYPES)
    audio_s3_key = models.TextField()
    duration_seconds = models.IntegerField(null=True, blank=True)
    file_size_bytes = models.BigIntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
