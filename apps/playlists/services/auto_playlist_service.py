def generate_mood_playlists(user):
    """
    Genera playlists automáticas agrupando las canciones del usuario por mood tag.
    """
    from apps.playlists.models import Playlist, PlaylistSong
    from apps.songs.models import Song

    MOODS = ['sad', 'happy', 'energetic', 'chill', 'romantic', 'angry']

    for mood in MOODS:
        songs = Song.objects.filter(
            user=user,
            status='ready',
            deleted_at__isnull=True,
            tags__name=mood
        ).distinct()[:30]

        if songs.count() < 2:
            continue

        playlist, created = Playlist.objects.update_or_create(
            user=user,
            type='auto_mood',
            title=f'Canciones {mood.capitalize()}',
            defaults={'song_count': songs.count()}
        )

        # Reconstruir las canciones de la playlist
        PlaylistSong.objects.filter(playlist=playlist).delete()
        for i, song in enumerate(songs):
            PlaylistSong.objects.create(playlist=playlist, song=song, position=i)


def generate_genre_playlists(user):
    """Similar a generate_mood_playlists pero filtrando por tags de categoría 'genre'."""
    from apps.playlists.models import Playlist, PlaylistSong
    from apps.songs.models import Song, Tag

    genres = Tag.objects.filter(
        category='genre',
        songtag__song__user=user,
        songtag__song__status='ready',
        songtag__song__deleted_at__isnull=True
    ).distinct()

    for genre in genres:
        songs = Song.objects.filter(
            user=user, status='ready',
            deleted_at__isnull=True, tags=genre
        ).distinct()[:30]

        if songs.count() < 2:
            continue

        playlist, _ = Playlist.objects.update_or_create(
            user=user, type='auto_genre',
            title=f'Mis canciones de {genre.name.capitalize()}',
            defaults={'song_count': songs.count()}
        )
        PlaylistSong.objects.filter(playlist=playlist).delete()
        for i, song in enumerate(songs):
            PlaylistSong.objects.create(playlist=playlist, song=song, position=i)
