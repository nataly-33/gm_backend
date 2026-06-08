from celery import shared_task
from django.utils import timezone

@shared_task(bind=True, max_retries=2)
def process_stem_job(self, job_id: str):
    from apps.stems.models import StemJob, StemFile
    from apps.credits.services.credit_service import deduct_credits
    from apps.notifications.services import notify_user
    from ml.modal_client import call_modal_endpoint, get_presigned_url

    try:
        job = StemJob.objects.select_related('user').get(id=job_id)

        job.status = 'processing'
        job.started_at = timezone.now()
        job.progress_pct = 10
        job.save(update_fields=['status', 'started_at', 'progress_pct'])

        # Llamar al endpoint de Demucs en Modal
        from django.conf import settings
        response = call_modal_endpoint(
            settings.MODAL_ENDPOINT_SEPARATE_STEMS,
            {'s3_key': job.source_audio_url}
        )

        job.progress_pct = 80
        job.save(update_fields=['progress_pct'])

        # Guardar los archivos resultantes
        for stem_type, s3_key in response['stems'].items():
            StemFile.objects.create(
                stem_job=job,
                stem_type=stem_type,
                audio_s3_key=s3_key,
            )

        # Descontar créditos solo si fue exitoso
        deduct_credits(job.user, amount=2,
                       reference_id=str(job.id), reference_type='stem_job')

        job.status = 'completed'
        job.progress_pct = 100
        job.credits_used = 2
        job.completed_at = timezone.now()
        job.save(update_fields=['status', 'progress_pct', 'credits_used', 'completed_at'])

        notify_user(job.user, type='stem_ready', reference_id=str(job.id))

    except Exception as exc:
        try:
            job = StemJob.objects.get(id=job_id)
            job.status = 'failed'
            job.error_message = str(exc)
            job.completed_at = timezone.now()
            job.save(update_fields=['status', 'error_message', 'completed_at'])
        except Exception:
            pass
        raise self.retry(exc=exc, countdown=60)
