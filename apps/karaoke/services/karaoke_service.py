from __future__ import annotations

from typing import TYPE_CHECKING

from django.db import transaction

from apps.credits.services.credit_service import check_balance, deduct_credits
from apps.karaoke.models import KaraokeTrack, UserKaraokeAccess
from apps.songs.models import Song

if TYPE_CHECKING:
    from apps.users.models import User

KARAOKE_CREDIT_COST = 2


class InsufficientCreditsError(Exception):
    """El usuario no tiene suficientes créditos para generar karaoke."""


class SongNotEligibleError(Exception):
    """La canción no cumple los requisitos para karaoke."""


def request_karaoke(user: User, song_id: str) -> tuple[KaraokeTrack, bool]:
    """
    Orquesta el flujo de solicitud de karaoke para una canción.

    Returns:
        (karaoke_track, already_owned)
        already_owned=True cuando el usuario ya tenía acceso y no se cobró nada.

    Raises:
        Song.DoesNotExist: Si la canción no existe.
        SongNotEligibleError: Si la canción no es apta para karaoke.
        InsufficientCreditsError: Si el usuario no tiene créditos suficientes.
    """
    song = Song.objects.get(id=song_id)

    if song.status != 'ready':
        raise SongNotEligibleError("La canción todavía no está lista.")
    if song.instrumental:
        raise SongNotEligibleError("Las canciones instrumentales no tienen voz para sincronizar.")

    with transaction.atomic():
        track = KaraokeTrack.objects.select_for_update().filter(song=song).first()

        # Caso C: el usuario ya tiene acceso — sin cobro
        if track is not None:
            already_owned = UserKaraokeAccess.objects.filter(
                user=user, karaoke_track=track
            ).exists()
            if already_owned:
                return track, True

        # Limpiar track fallido para que pueda regenerarse
        if track is not None and track.status == 'failed':
            track.delete()
            track = None

        # Todos los caminos restantes requieren créditos
        if not check_balance(user, required=KARAOKE_CREDIT_COST):
            raise InsufficientCreditsError(
                f"Necesitas {KARAOKE_CREDIT_COST} créditos para generar karaoke."
            )

        if track is None:
            # Caso A: primer procesamiento — crear track y encolar tarea
            track = KaraokeTrack.objects.create(song=song, status='queued')
            deduct_credits(
                user,
                KARAOKE_CREDIT_COST,
                reference_id=str(track.id),
                reference_type='karaoke',
            )
            UserKaraokeAccess.objects.create(
                user=user, karaoke_track=track, credits_paid=KARAOKE_CREDIT_COST
            )
            # Encolar después del commit para garantizar que el registro ya existe en DB
            transaction.on_commit(
                lambda tid=str(track.id): _enqueue_generation(tid)
            )
        else:
            # Caso B: karaoke ya existe (queued/processing/ready) — solo dar acceso
            deduct_credits(
                user,
                KARAOKE_CREDIT_COST,
                reference_id=str(track.id),
                reference_type='karaoke',
            )
            UserKaraokeAccess.objects.create(
                user=user, karaoke_track=track, credits_paid=KARAOKE_CREDIT_COST
            )

    return track, False


def _enqueue_generation(karaoke_track_id: str) -> None:
    from apps.karaoke.tasks import generate_karaoke_track
    generate_karaoke_track.delay(karaoke_track_id)
