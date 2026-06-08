from django.db import models
from django.conf import settings
import uuid

class ListeningHistory(models.Model):
    """Agrega cuánto escucha cada usuario de cada tag."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    tag = models.ForeignKey('songs.Tag', on_delete=models.CASCADE)
    play_count = models.IntegerField(default=0)
    total_seconds = models.IntegerField(default=0)
    last_played_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = [('user', 'tag')]

class UserTasteProfile(models.Model):
    """Perfil de gustos calculado periódicamente para cada usuario."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    top_tags = models.JSONField(default=list)     # [{"tag_id": 5, "score": 0.95}, ...]
    top_genres = models.JSONField(default=list)
    top_moods = models.JSONField(default=list)
    calculated_at = models.DateTimeField(auto_now=True)

class UserSimilarity(models.Model):
    """Similitudes entre usuarios para recomendaciones colaborativas."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user_a = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='similarities_as_a')
    user_b = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='similarities_as_b')
    similarity_score = models.FloatField()   # 0.0 a 1.0
    calculated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = [('user_a', 'user_b')]
