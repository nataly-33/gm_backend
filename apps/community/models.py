from django.db import models
from django.conf import settings


class SongLike(models.Model):
    """Un usuario le da like a una canción pública. El toggle evita duplicados."""
    user       = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='song_likes')
    song       = models.ForeignKey('songs.Song', on_delete=models.CASCADE, related_name='liked_by')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [('user', 'song')]
        ordering        = ['-created_at']


class SongPlay(models.Model):
    """Registro de cada reproducción. El usuario puede ser null si implementamos escucha anónima."""
    user             = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='song_plays')
    song             = models.ForeignKey('songs.Song', on_delete=models.CASCADE, related_name='plays')
    duration_seconds = models.IntegerField(default=0)
    played_at        = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-played_at']
