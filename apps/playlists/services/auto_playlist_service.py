def generate_mood_playlists(user):
    """
    Genera playlists automáticas agrupando las canciones del usuario por mood tag.
    Primero intenta usar tags con category='mood'. Si ninguno produce grupos con
    >= 2 canciones, recurre al campo ml_predicted_mood del modelo Song.
    """
    from apps.playlists.models import Playlist, PlaylistSong
    from apps.songs.models import Song, Tag

    created_any = False

    # ── Strategy 1: group by Tag objects with category='mood' ────────────────
    mood_tags = Tag.objects.filter(
        category='mood',
        songtag__song__user=user,
        songtag__song__status='ready',
        songtag__song__deleted_at__isnull=True,
    ).distinct()

    for tag in mood_tags:
        songs = Song.objects.filter(
            user=user,
            status='ready',
            deleted_at__isnull=True,
            tags=tag,
        ).distinct()[:30]

        if songs.count() < 2:
            continue

        playlist, _ = Playlist.objects.update_or_create(
            user=user,
            type='auto_mood',
            title=f'Canciones {tag.name.capitalize()}',
            defaults={'song_count': songs.count()},
        )
        PlaylistSong.objects.filter(playlist=playlist).delete()
        for i, song in enumerate(songs):
            PlaylistSong.objects.create(playlist=playlist, song=song, position=i)
        created_any = True

    # ── Strategy 2: fall back to ml_predicted_mood ───────────────────────────
    if not created_any:
        base_qs = Song.objects.filter(
            user=user,
            status='ready',
            deleted_at__isnull=True,
            ml_predicted_mood__isnull=False,
        ).exclude(ml_predicted_mood='')

        moods_used = (
            base_qs
            .values_list('ml_predicted_mood', flat=True)
            .distinct()
        )

        for mood in moods_used:
            songs = base_qs.filter(ml_predicted_mood=mood)[:30]
            if songs.count() < 2:
                continue

            playlist, _ = Playlist.objects.update_or_create(
                user=user,
                type='auto_mood',
                title=f'Canciones {mood.capitalize()}',
                defaults={'song_count': songs.count()},
            )
            PlaylistSong.objects.filter(playlist=playlist).delete()
            for i, song in enumerate(songs):
                PlaylistSong.objects.create(playlist=playlist, song=song, position=i)
            created_any = True

    # ── Strategy 3: distribute all ready songs into 2 playlists ─────────────
    # Only runs when absolutely no mood groups were found.
    if not created_any:
        all_songs = list(
            Song.objects.filter(
                user=user,
                status='ready',
                deleted_at__isnull=True,
            ).order_by('created_at')[:60]
        )

        if len(all_songs) >= 2:
            mid = len(all_songs) // 2
            halves = [
                ('Mis canciones — Vol. 1', all_songs[:mid]),
                ('Mis canciones — Vol. 2', all_songs[mid:]),
            ]
            for title, chunk in halves:
                if len(chunk) < 2:
                    continue
                playlist, _ = Playlist.objects.update_or_create(
                    user=user,
                    type='auto_mood',
                    title=title,
                    defaults={'song_count': len(chunk)},
                )
                PlaylistSong.objects.filter(playlist=playlist).delete()
                for i, song in enumerate(chunk):
                    PlaylistSong.objects.create(playlist=playlist, song=song, position=i)


def generate_genre_playlists(user):
    """
    Genera playlists automáticas agrupando las canciones del usuario por genre tag.
    Si no hay tags con category='genre', recurre al campo ml_predicted_genre.
    """
    from apps.playlists.models import Playlist, PlaylistSong
    from apps.songs.models import Song, Tag

    created_any = False

    # ── Strategy 1: group by Tag objects with category='genre' ───────────────
    genres = Tag.objects.filter(
        category='genre',
        songtag__song__user=user,
        songtag__song__status='ready',
        songtag__song__deleted_at__isnull=True,
    ).distinct()

    for genre in genres:
        songs = Song.objects.filter(
            user=user,
            status='ready',
            deleted_at__isnull=True,
            tags=genre,
        ).distinct()[:30]

        if songs.count() < 2:
            continue

        playlist, _ = Playlist.objects.update_or_create(
            user=user,
            type='auto_genre',
            title=f'Mis canciones de {genre.name.capitalize()}',
            defaults={'song_count': songs.count()},
        )
        PlaylistSong.objects.filter(playlist=playlist).delete()
        for i, song in enumerate(songs):
            PlaylistSong.objects.create(playlist=playlist, song=song, position=i)
        created_any = True

    # ── Strategy 2: fall back to ml_predicted_genre ──────────────────────────
    if not created_any:
        base_qs = Song.objects.filter(
            user=user,
            status='ready',
            deleted_at__isnull=True,
            ml_predicted_genre__isnull=False,
        ).exclude(ml_predicted_genre='')

        genres_used = (
            base_qs
            .values_list('ml_predicted_genre', flat=True)
            .distinct()
        )

        for genre in genres_used:
            songs = base_qs.filter(ml_predicted_genre=genre)[:30]
            if songs.count() < 2:
                continue

            playlist, _ = Playlist.objects.update_or_create(
                user=user,
                type='auto_genre',
                title=f'Mis canciones de {genre.capitalize()}',
                defaults={'song_count': songs.count()},
            )
            PlaylistSong.objects.filter(playlist=playlist).delete()
            for i, song in enumerate(songs):
                PlaylistSong.objects.create(playlist=playlist, song=song, position=i)
            created_any = True
