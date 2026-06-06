import requests
from django.conf import settings


def call_modal_endpoint(endpoint_url: str, body: dict) -> dict:
    """
    Llama a uno de los 3 endpoints del MusicGenServer en Modal.
    Retorna: { s3_key, cover_image_s3_key, categories }
    """
    response = requests.post(
        endpoint_url,
        json=body,
        headers={
            "Content-Type": "application/json",
            "Modal-Key": settings.MODAL_KEY,
            "Modal-Secret": settings.MODAL_SECRET,
        },
        timeout=600,  # ACE-Step puede tardar hasta 5-10 min
    )
    if not response.ok:
        raise ModalGenerationError(f"Modal {response.status_code}: {response.text[:300]}")
    data = response.json()
    if 's3_key' not in data and 'stems' not in data:
        raise ModalGenerationError(f"Respuesta inesperada: {data}")
    return data


def get_presigned_url(s3_key: str, expiry_seconds: int = 3600) -> str:
    """
    Genera una URL firmada de S3 para que el frontend reproduzca el audio.
    Usar también para thumbnails.
    """
    import boto3
    s3 = boto3.client(
        "s3",
        region_name=settings.AWS_S3_REGION_NAME,
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
    )
    return s3.generate_presigned_url(
        'get_object',
        Params={'Bucket': settings.AWS_STORAGE_BUCKET_NAME, 'Key': s3_key},
        ExpiresIn=expiry_seconds
    )


class ModalGenerationError(Exception):
    pass


def upload_to_s3(file_obj, folder: str = '') -> str:
    import boto3
    import uuid
    import os

    s3 = boto3.client(
        "s3",
        region_name=settings.AWS_S3_REGION_NAME,
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
    )
    file_ext = os.path.splitext(file_obj.name)[1]
    unique_filename = f"{uuid.uuid4()}{file_ext}"
    s3_key = f"{folder}/{unique_filename}" if folder else unique_filename
    
    s3.upload_fileobj(file_obj, settings.AWS_STORAGE_BUCKET_NAME, s3_key)
    return s3_key