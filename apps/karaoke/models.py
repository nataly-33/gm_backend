from django.conf import settings
from django.db import models

from apps.core.models import BaseModel


class KaraokeTrack(BaseModel):
    STATUS_CHOICES = [
        ('queued',     'Queued'),
        ('processing', 'Processing'),
        ('ready',      'Ready'),
        ('failed',     'Failed'),
    ]

    song = models.OneToOneField(
        'songs.Song',
        on_delete=models.CASCADE,
        related_name='karaoke_track',
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='queued')

    # S3 keys devueltos por Modal/Demucs
    instrumental_s3_key = models.TextField(null=True, blank=True)  # no_vocals.wav
    vocals_s3_key       = models.TextField(null=True, blank=True)  # vocals.wav (para Whisper)

    # Letra transcripta por Whisper sobre vocals.wav
    lyrics            = models.TextField(null=True, blank=True)
    lyrics_timestamps = models.JSONField(null=True, blank=True)
    # Formato: [{"start": 2.5, "end": 4.1, "text": "primera línea"}, ...]

    error_message = models.TextField(null=True, blank=True)
    processed_at  = models.DateTimeField(null=True, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=['status']),
        ]

    def __str__(self):
        return f"KaraokeTrack({self.song_id}, {self.status})"


class UserKaraokeAccess(models.Model):
    user          = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='karaoke_accesses',
    )
    karaoke_track = models.ForeignKey(
        KaraokeTrack,
        on_delete=models.CASCADE,
        related_name='user_accesses',
    )
    credits_paid = models.IntegerField(default=2)
    granted_at   = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [('user', 'karaoke_track')]

    def __str__(self):
        return f"{self.user_id} → {self.karaoke_track_id}"
