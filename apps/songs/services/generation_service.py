# apps/songs/services/generation_service.py
from apps.songs.models import Song, GenerationJob, Tag, SongTag


def request_generation(user, *, title: str, description: str = None,
                       prompt: str = None, lyrics: str = None,
                       described_lyrics: str = None,
                       instrumental: bool = False,
                       guidance_scale: float = 15.0,
                       audio_duration: float = 180.0
                       ) -> GenerationJob:
    
    """
    Punto de entrada para generar una canción.
    Valida créditos → crea Song + Job → encola tarea Celery.
    """
    from apps.credits.services.credit_service import check_balance

    if not check_balance(user, required=1):
        raise InsufficientCreditsError("Sin créditos disponibles.")

    mode = _determine_mode(description, prompt, lyrics, described_lyrics)

    song = Song.objects.create(
        user=user,
        title=_default_title(title, description, described_lyrics),
        description=description,
        prompt=prompt,
        lyrics=lyrics,
        described_lyrics=described_lyrics,
        instrumental=instrumental,
        guidance_scale=guidance_scale,
        audio_duration=audio_duration,
        status='draft',
    )

    job = GenerationJob.objects.create(user=user, song=song, mode=mode, status='queued')

    from apps.songs.tasks import process_generation_job
    process_generation_job.delay(str(job.id))

    return job


def _determine_mode(description, prompt, lyrics, described_lyrics) -> str:
    if description:
        return 'from_description'
    elif lyrics and prompt:
        return 'with_lyrics'
    elif described_lyrics and prompt:
        return 'with_described_lyrics'
    raise ValueError("Parámetros insuficientes para determinar el modo.")


def _default_title(title, description, described_lyrics) -> str:
    raw = title or description or described_lyrics or "Untitled"
    return (raw[:1].upper() + raw[1:].strip())[:199]


class InsufficientCreditsError(Exception):
    pass