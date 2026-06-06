from celery import shared_task

@shared_task
def generate_all_auto_playlists():
    from apps.users.models import User
    from apps.playlists.services.auto_playlist_service import generate_mood_playlists, generate_genre_playlists
    for user in User.objects.filter(is_active=True, deleted_at__isnull=True):
        generate_mood_playlists(user)
        generate_genre_playlists(user)
