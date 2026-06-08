from celery import shared_task
from django.utils import timezone


@shared_task(bind=True, max_retries=2)
def render_mix(self, export_id: str):
    """
    Tarea Celery que renderiza el mix completo usando pydub.
    Une todos los clips en orden, aplica efectos, exporta y sube a S3.
    """
    from apps.mix.models import MixExport, MixClip
    from apps.mix.services.audio_editor import (
        download_audio_from_s3, apply_clip_effects, get_clip_s3_key,
    )
    from apps.credits.services.credit_service import check_balance, deduct_credits
    from pydub import AudioSegment
    import boto3
    import tempfile
    import os
    from django.conf import settings

    try:
        export = MixExport.objects.select_related('mix_project__user').get(id=export_id)
        mix    = export.mix_project
        user   = mix.user

        if not check_balance(user, required=3):
            export.status = 'failed'
            export.error_message = 'Sin créditos suficientes (se necesitan 3).'
            export.save(update_fields=['status', 'error_message'])
            return

        export.status = 'processing'
        export.save(update_fields=['status'])

        clips = MixClip.objects.filter(mix_project=mix).order_by('position')
        if not clips.exists():
            raise ValueError("El mix no tiene clips.")

        # Construir el audio concatenando todos los clips en orden
        final_audio = AudioSegment.empty()
        for clip in clips:
            s3_key     = get_clip_s3_key(clip)
            audio_path = download_audio_from_s3(s3_key)
            try:
                audio     = AudioSegment.from_file(audio_path)
                processed = apply_clip_effects(audio, clip)
                final_audio += processed
            finally:
                os.unlink(audio_path)

        # Exportar al formato solicitado
        with tempfile.NamedTemporaryFile(suffix=f'.{export.format}', delete=False) as tmp:
            bitrate     = export.quality if export.format == 'mp3' else None
            output_path = tmp.name
        final_audio.export(output_path, format=export.format, bitrate=bitrate)

        # Subir a S3
        s3 = boto3.client(
            's3',
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.AWS_S3_REGION_NAME,
        )
        s3_key = f"mix-exports/{mix.id}/{export.id}.{export.format}"
        s3.upload_file(output_path, settings.AWS_STORAGE_BUCKET_NAME, s3_key)
        os.unlink(output_path)

        # Actualizar mix y export
        mix.duration_seconds = len(final_audio) // 1000
        mix.output_s3_key    = s3_key
        mix.status           = 'ready'
        mix.save(update_fields=['duration_seconds', 'output_s3_key', 'status'])

        deduct_credits(user, amount=3, reference_id=str(export.id), reference_type='mix_export')

        export.output_s3_key = s3_key
        export.status        = 'ready'
        export.credits_used  = 3
        export.save(update_fields=['output_s3_key', 'status', 'credits_used'])

    except Exception as exc:
        try:
            export = MixExport.objects.get(id=export_id)
            export.status        = 'failed'
            export.error_message = str(exc)
            export.save(update_fields=['status', 'error_message'])
        except Exception:
            pass
        raise self.retry(exc=exc, countdown=60)
