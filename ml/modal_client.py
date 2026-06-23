from __future__ import annotations

import time
import requests
from django.conf import settings

_COLD_START_WAIT = 30    # segundos entre reintentos mientras Modal arranca
_COLD_START_ATTEMPTS = 6  # máximo ~2.5 min de espera (5 esperas × 30 s)


def call_modal_endpoint(endpoint_url: str, body: dict) -> dict:
    """
    Llama a uno de los endpoints del MusicGenServer desplegado en Modal.
    Si Modal responde 404 "app is stopped" (cold start), reintenta
    automáticamente hasta _COLD_START_ATTEMPTS veces antes de fallar.
    """
    headers = {
        "Content-Type": "application/json",
        "Modal-Key": settings.MODAL_KEY,
        "Modal-Secret": settings.MODAL_SECRET,
    }

    for attempt in range(_COLD_START_ATTEMPTS):
        response = requests.post(
            endpoint_url,
            json=body,
            headers=headers,
            timeout=600,  # ACE-Step puede tardar hasta 5-10 min
        )

        # Cold start: Modal devuelve 404 mientras el app arranca.
        # Esperamos y reintentamos; el primer request ya disparó el wake-up.
        if response.status_code == 404 and "is stopped" in response.text:
            if attempt < _COLD_START_ATTEMPTS - 1:
                time.sleep(_COLD_START_WAIT)
                continue
            raise ModalGenerationError(
                f"Modal no arrancó tras {_COLD_START_ATTEMPTS} intentos: {response.text[:200]}"
            )

        if not response.ok:
            raise ModalGenerationError(f"Modal {response.status_code}: {response.text[:300]}")

        data = response.json()
        if "s3_key" not in data and "stems" not in data:
            raise ModalGenerationError(f"Respuesta inesperada: {data}")
        return data

    raise ModalGenerationError("Modal no respondió.")


def get_presigned_url(s3_key: str, expiry_seconds: int = 3600) -> str:
    """
    Genera una URL prefirmada de S3 para acceso temporal a un objeto.

    Utilizada tanto para reproducir audio como para mostrar thumbnails
    en el frontend sin exponer las credenciales de AWS.

    Args:
        s3_key: Clave del objeto en el bucket de S3.
        expiry_seconds: Tiempo de validez de la URL en segundos. Por defecto 3600 (1 hora).

    Returns:
        URL prefirmada como cadena de texto.
    """
    import boto3

    s3 = boto3.client(
        "s3",
        region_name=settings.AWS_S3_REGION_NAME,
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
    )
    return s3.generate_presigned_url(
        "get_object",
        Params={"Bucket": settings.AWS_STORAGE_BUCKET_NAME, "Key": s3_key},
        ExpiresIn=expiry_seconds,
    )


class ModalGenerationError(Exception):
    """Se lanza cuando la llamada al servidor Modal falla o retorna datos inesperados."""


def upload_to_s3(file_obj, folder: str = "") -> str:
    """
    Sube un archivo al bucket de S3 configurado con un nombre único.

    Genera un UUID como nombre de archivo para evitar colisiones, preservando
    la extensión original del archivo subido.

    Args:
        file_obj: Objeto de archivo compatible con upload_fileobj de boto3
            (p. ej. InMemoryUploadedFile de Django).
        folder: Prefijo de carpeta dentro del bucket. Si está vacío el
            archivo se sube a la raíz del bucket.

    Returns:
        Clave S3 (s3_key) del archivo subido, incluyendo el prefijo de carpeta.
    """
    import os
    import uuid

    import boto3

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
