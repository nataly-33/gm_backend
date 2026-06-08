from django.db.models import F
from django.utils import timezone
from datetime import timedelta


def toggle_like(user, song) -> dict:
    """Alterna el like de un usuario sobre una canción pública. Retorna {liked, like_count}."""
    from apps.community.models import SongLike
    from apps.songs.models import Song

    like, created = SongLike.objects.get_or_create(user=user, song=song)

    if created:
        Song.objects.filter(pk=song.pk).update(like_count=F('like_count') + 1)
        song.refresh_from_db(fields=['like_count'])
        return {'liked': True, 'like_count': song.like_count}
    else:
        like.delete()
        Song.objects.filter(pk=song.pk, like_count__gt=0).update(like_count=F('like_count') - 1)
        song.refresh_from_db(fields=['like_count'])
        return {'liked': False, 'like_count': song.like_count}


def record_play(user, song, duration_seconds: int = 0) -> None:
    """Registra una reproducción e incrementa play_count en la canción."""
    from apps.community.models import SongPlay
    from apps.songs.models import Song

    SongPlay.objects.create(user=user, song=song, duration_seconds=duration_seconds)
    Song.objects.filter(pk=song.pk).update(play_count=F('play_count') + 1)

    # Actualizar historial de escucha para recomendaciones
    if user and user.is_authenticated:
        try:
            from apps.recommendations.services.history_service import update_listening_history
            update_listening_history(user, song)
        except Exception:
            pass


def get_trending(limit: int = 20):
    """Canciones públicas más reproducidas en las últimas 48 horas."""
    from apps.songs.models import Song
    from apps.community.models import SongPlay
    from django.db.models import Count

    cutoff = timezone.now() - timedelta(hours=48)
    trending_ids = (
        SongPlay.objects
        .filter(played_at__gte=cutoff)
        .values('song_id')
        .annotate(recent_plays=Count('id'))
        .order_by('-recent_plays')
        .values_list('song_id', flat=True)[:limit]
    )

    if not trending_ids:
        # Fallback: más reproducidas en general
        return Song.objects.filter(is_public=True, status='ready', deleted_at__isnull=True).order_by('-play_count')[:limit]

    # Preservar el orden del ranking
    songs  = {s.id: s for s in Song.objects.filter(id__in=trending_ids, is_public=True, status='ready')}
    return [songs[sid] for sid in trending_ids if sid in songs]
