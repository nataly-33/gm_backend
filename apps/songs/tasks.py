from celery import shared_task
from django.utils import timezone


@shared_task(bind=True, max_retries=2)
def process_generation_job(self, job_id: str):
    from apps.songs.models import GenerationJob
    from apps.credits.services.credit_service import deduct_credits
    #from apps.notifications.services import notify_user
    from ml.modal_client import call_modal_endpoint, ModalGenerationError

    try:
        job = GenerationJob.objects.select_related('user', 'song').get(id=job_id)
        song = job.song

        # 1. Marcar como processing
        song.status = 'processing'
        song.save(update_fields=['status'])
        job.status = 'processing'
        job.started_at = timezone.now()
        job.save(update_fields=['status', 'started_at'])

        # 2. Construir la llamada según el modo
        endpoint_url, body = _build_modal_request(song, job.mode)
        job.modal_endpoint_used = endpoint_url
        job.save(update_fields=['modal_endpoint_used'])

        # 3. Llamar a Modal
        response = call_modal_endpoint(endpoint_url, body)

        # 4. Guardar resultado en la canción
        song.audio_s3_key = response['s3_key']
        song.thumbnail_s3_key = response['cover_image_s3_key']
        song.status = 'ready'
        song.save(update_fields=['audio_s3_key', 'thumbnail_s3_key', 'status', 'updated_at'])

        # 5. Guardar tags/categorías generados por el LLM
        _save_categories(song, response.get('categories', []))

        # 6. Descontar crédito SOLO si fue exitoso
        deduct_credits(job.user, amount=1, reference_id=str(job.id), reference_type='generation_job')
        job.credits_used = 1
        job.status = 'completed'
        job.completed_at = timezone.now()
        job.save(update_fields=['credits_used', 'status', 'completed_at'])

        # 7. Notificar al usuario
        #notify_user(job.user, type='song_ready', reference_id=str(song.id))

    except Exception as exc:
        try:
            job = GenerationJob.objects.get(id=job_id)
            job.status = 'failed'
            job.error_message = str(exc)
            job.completed_at = timezone.now()
            job.save(update_fields=['status', 'error_message', 'completed_at'])
            job.song.status = 'failed'
            job.song.save(update_fields=['status'])
        except Exception:
            pass
        raise self.retry(exc=exc, countdown=60)


def _build_modal_request(song, mode: str):
    from django.conf import settings
    common = {
        'guidance_scale': song.guidance_scale,
        'infer_step': song.infer_step,
        'audio_duration': song.audio_duration,
        'seed': song.seed,
        'instrumental': song.instrumental,
    }
    if mode == 'from_description':
        return settings.MODAL_ENDPOINT_FROM_DESCRIPTION, {'full_described_song': song.description, **common}
    elif mode == 'with_lyrics':
        return settings.MODAL_ENDPOINT_WITH_LYRICS, {'prompt': song.prompt, 'lyrics': song.lyrics, **common}
    elif mode == 'with_described_lyrics':
        return settings.MODAL_ENDPOINT_FROM_DESCRIBED_LYRICS, {'prompt': song.prompt, 'described_lyrics': song.described_lyrics, **common}
    raise ValueError(f"Modo desconocido: {mode}")


def _save_categories(song, categories: list):
    from apps.songs.models import Tag, SongTag
    for cat_name in categories:
        tag, _ = Tag.objects.get_or_create(
            name=cat_name.strip().lower(),
            defaults={'category': 'genre'}
        )
        SongTag.objects.get_or_create(song=song, tag=tag)