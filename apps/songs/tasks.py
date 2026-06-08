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

        # Guardar letra generada por IA (solo si el usuario no la proporcionó)
        if job.mode in ('from_description', 'with_described_lyrics'):
            generated_lyrics = response.get('lyrics', '')
            if generated_lyrics:
                song.lyrics = generated_lyrics
                song.lyrics_source = 'ai_generated'

        song.save(update_fields=['audio_s3_key', 'thumbnail_s3_key', 'status', 'lyrics', 'lyrics_source', 'updated_at'])

        # Calcular timestamps de letra en background (si hay letra y audio)
        if not song.instrumental:
            compute_lyrics_timestamps.delay(str(song.id))

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
        'vocal_type': song.vocal_type,
        'language': song.language,
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


@shared_task(bind=True, max_retries=1)
def compute_lyrics_timestamps(self, song_id: str):
    """Descarga el audio de una canción, corre Whisper y guarda los timestamps de letra."""
    import os
    import shutil
    import tempfile
    import boto3
    from django.db import connection
    from django.conf import settings

    # Verificar que ffmpeg está disponible
    if not shutil.which('ffmpeg'):
        return  # sin ffmpeg no podemos procesar

    try:
        from apps.songs.models import Song
        song = Song.objects.get(id=song_id, status='ready')
        if not song.audio_s3_key or song.instrumental:
            return

        s3 = boto3.client(
            's3',
            region_name=settings.AWS_S3_REGION_NAME,
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        )

        fd, tmp_path = tempfile.mkstemp(suffix='.wav')
        os.close(fd)

        try:
            s3.download_file(settings.AWS_STORAGE_BUCKET_NAME, song.audio_s3_key, tmp_path)

            lang = song.language if song.language in ('es', 'en') else None

            # Cerrar la conexión DB antes de la transcripción larga
            connection.close()

            import whisper
            model = whisper.load_model('base')
            result = model.transcribe(
                tmp_path,
                language=lang,
                task='transcribe',
                fp16=False,
                verbose=False,
                word_timestamps=True,
            )

            segments = result.get('segments', [])
            timestamps = [
                {'start': round(seg['start'], 2), 'end': round(seg['end'], 2), 'text': seg['text'].strip()}
                for seg in segments
                if seg.get('text', '').strip()
            ]

            if timestamps:
                Song.objects.filter(id=song_id).update(lyrics_timestamps=timestamps)

        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

    except Exception as exc:
        raise self.retry(exc=exc, countdown=120)