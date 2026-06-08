from apps.recommendations.models import ListeningHistory
from django.utils import timezone

def update_listening_history(user, song):
    """
    Llamar desde community.record_play() cada vez que alguien escucha una canción.
    Actualiza el historial agregado por tag.
    """
    for tag in song.tags.all():
        history, _ = ListeningHistory.objects.get_or_create(
            user=user, tag=tag,
            defaults={'play_count': 0, 'total_seconds': 0}
        )
        history.play_count += 1
        history.last_played_at = timezone.now()
        history.save(update_fields=['play_count', 'last_played_at', 'updated_at'])
