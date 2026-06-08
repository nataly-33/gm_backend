from apps.core.models import BaseModel
from django.db import models
from django.conf import settings
import uuid


class MixProject(BaseModel):
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('processing', 'Processing'),
        ('ready', 'Ready'),
        ('failed', 'Failed'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='mix_projects',
    )
    title            = models.CharField(max_length=200)
    description      = models.TextField(null=True, blank=True)
    bpm              = models.IntegerField(null=True, blank=True)
    status           = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    output_s3_key    = models.TextField(null=True, blank=True)
    duration_seconds = models.IntegerField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} ({self.status})"


class MixClip(models.Model):
    """Un segmento de audio dentro del mix."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    mix_project = models.ForeignKey(
        MixProject, on_delete=models.CASCADE, related_name='clips'
    )

    # Fuente del clip — solo uno de estos tres debe estar lleno
    song = models.ForeignKey(
        'songs.Song', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='mix_clips',
    )
    stem_file = models.ForeignKey(
        'stems.StemFile', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='mix_clips',
    )
    custom_audio_s3_key = models.TextField(null=True, blank=True)

    # Posición y corte (HU-43)
    position      = models.IntegerField()
    start_time_ms = models.IntegerField(default=0)
    end_time_ms   = models.IntegerField()

    # Efectos (HU-44)
    fade_in_ms  = models.IntegerField(default=0)
    fade_out_ms = models.IntegerField(default=0)
    volume      = models.FloatField(default=1.0)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['position']

    @property
    def duration_ms(self):
        return self.end_time_ms - self.start_time_ms

    def __str__(self):
        return f"Clip #{self.position} — {self.mix_project.title}"


class MixExport(BaseModel):
    """Registro de cada exportación de un mix."""
    FORMAT_CHOICES  = [('mp3', 'MP3'), ('wav', 'WAV')]
    QUALITY_CHOICES = [('128k', '128kbps'), ('320k', '320kbps'), ('lossless', 'Lossless WAV')]
    STATUS_CHOICES  = [
        ('queued', 'Queued'),
        ('processing', 'Processing'),
        ('ready', 'Ready'),
        ('failed', 'Failed'),
    ]

    mix_project   = models.ForeignKey(MixProject, on_delete=models.CASCADE, related_name='exports')
    format        = models.CharField(max_length=10, choices=FORMAT_CHOICES, default='mp3')
    quality       = models.CharField(max_length=10, choices=QUALITY_CHOICES, default='320k')
    output_s3_key = models.TextField(null=True, blank=True)
    status        = models.CharField(max_length=20, choices=STATUS_CHOICES, default='queued')
    credits_used  = models.IntegerField(default=3)
    error_message = models.TextField(null=True, blank=True)
