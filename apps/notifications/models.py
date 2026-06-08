from django.db import models
from django.conf import settings


class Notification(models.Model):
    TYPE_CHOICES = [
        ('song_ready',   'Canción lista'),
        ('stem_ready',   'Stems listos'),
        ('mix_ready',    'Mix exportado'),
        ('credit_grant', 'Créditos otorgados'),
        ('system',       'Sistema'),
    ]

    user         = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notifications')
    type         = models.CharField(max_length=30, choices=TYPE_CHOICES, default='system')
    title        = models.CharField(max_length=200)
    message      = models.TextField(blank=True, default='')
    reference_id = models.CharField(max_length=100, blank=True, default='')
    is_read      = models.BooleanField(default=False)
    created_at   = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.type} → {self.user.email}"
