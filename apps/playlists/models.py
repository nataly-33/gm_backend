from apps.core.models import BaseModel
from django.db import models
from django.conf import settings
import uuid, secrets

class Playlist(BaseModel):
    TYPE_CHOICES = [
        ('manual', 'Manual'),
        ('auto_mood', 'Auto por estado de ánimo'),
        ('auto_genre', 'Auto por género'),
        ('recommended', 'Recomendada'),
    ]
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='playlists')
    title = models.CharField(max_length=200)
    description = models.TextField(null=True, blank=True)
    cover_url = models.TextField(null=True, blank=True)
    type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='manual')
    is_public = models.BooleanField(default=False)
    share_token = models.CharField(max_length=64, unique=True, null=True, blank=True)
    song_count = models.IntegerField(default=0)

    def generate_share_token(self):
        self.share_token = secrets.token_urlsafe(32)
        self.save(update_fields=['share_token'])
        return self.share_token

class PlaylistSong(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    playlist = models.ForeignKey(Playlist, on_delete=models.CASCADE, related_name='playlist_songs')
    song = models.ForeignKey('songs.Song', on_delete=models.CASCADE)
    position = models.IntegerField()
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [('playlist', 'song')]
        ordering = ['position']
