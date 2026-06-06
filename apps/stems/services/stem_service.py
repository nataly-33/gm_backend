from apps.stems.models import StemJob
from apps.credits.services.credit_service import check_balance, deduct_credits
from ml.modal_client import upload_to_s3
from apps.stems.tasks import process_stem_job

MAX_FILE_SIZE_BYTES = 50 * 1024 * 1024  # 50 MB — HU-20

class FileTooLargeError(Exception):
    pass

class InsufficientCreditsError(Exception):
    pass

def request_stem_separation(user, file, filename: str) -> StemJob:
    """
    Valida el archivo → sube a S3 → crea job → encola tarea.
    """
    # HU-20: rechazar archivos muy grandes
    if file.size > MAX_FILE_SIZE_BYTES:
        raise FileTooLargeError(f"El archivo excede el límite de 50MB.")

    if not check_balance(user, required=2):
        raise InsufficientCreditsError("Necesitas 2 créditos para separar pistas.")

    # Subir el archivo original a S3
    s3_key = upload_to_s3(file, folder='stems/uploads')

    job = StemJob.objects.create(
        user=user,
        source_audio_url=s3_key,
        source_filename=filename,
        source_file_size_bytes=file.size,
        status='queued',
    )

    process_stem_job.delay(str(job.id))
    return job
