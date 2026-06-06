from apps.recommendations.models import ListeningHistory, UserTasteProfile

def recalculate_profile(user):
    """
    Recalcula el perfil de gustos del usuario basado en su historial.
    Se ejecuta como tarea Celery diaria, y también al registrar un play.
    """
    history = ListeningHistory.objects.filter(user=user).select_related('tag').order_by('-play_count')[:20]

    top_tags = [{'tag_id': h.tag.id, 'name': h.tag.name, 'score': h.play_count} for h in history]
    top_genres = [t for t in top_tags if h.tag.category == 'genre' for h in history if h.tag.id == t['tag_id']]
    top_moods  = [t for t in top_tags if h.tag.category == 'mood'  for h in history if h.tag.id == t['tag_id']]

    UserTasteProfile.objects.update_or_create(
        user=user,
        defaults={'top_tags': top_tags, 'top_genres': top_genres, 'top_moods': top_moods}
    )
