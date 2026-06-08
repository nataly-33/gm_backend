from django.db import models
from django.conf import settings


class AuditLog(models.Model):
    user          = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='audit_logs')
    action        = models.CharField(max_length=100)       # 'song.generate', 'credits.purchase', 'stem.separate'
    resource_type = models.CharField(max_length=60, blank=True, default='')
    resource_id   = models.CharField(max_length=100, blank=True, default='')
    ip_address    = models.CharField(max_length=45, blank=True, default='')
    details       = models.JSONField(null=True, blank=True)
    created_at    = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        indexes  = [
            models.Index(fields=['action']),
            models.Index(fields=['user', 'created_at']),
        ]

    def __str__(self):
        user_email = self.user.email if self.user else 'anónimo'
        return f"{self.action} by {user_email} at {self.created_at:%Y-%m-%d %H:%M}"
