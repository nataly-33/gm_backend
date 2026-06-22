"""
Lógica de edición de audio para el mix.
Usa pydub para cortes, fades y mezcla.
Requiere ffmpeg instalado en el sistema.
"""
from pydub import AudioSegment
import pydub
from decouple import config
import boto3
import tempfile
import os
from django.conf import settings

ffmpeg_path = config('FFMPEG_PATH', default=None)
if ffmpeg_path:
    pydub.AudioSegment.converter = ffmpeg_path


def download_audio_from_s3(s3_key: str) -> str:
    """Descarga un archivo de S3 a un archivo temporal. Retorna el path."""
    s3 = boto3.client(
        's3',
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        region_name=settings.AWS_S3_REGION_NAME,
    )
    suffix = '.wav' if s3_key.endswith('.wav') else '.mp3'
    tmp = tempfile.NamedTemporaryFile(suffix=suffix, delete=False)
    s3.download_fileobj(settings.AWS_STORAGE_BUCKET_NAME, s3_key, tmp)
    tmp.close()
    return tmp.name


def apply_clip_effects(audio: AudioSegment, clip) -> AudioSegment:
    """
    Aplica corte, fade in, fade out y volumen a un segmento de audio.
    Implementa HU-43 (corte) y HU-44 (fades).
    """
    # HU-43: cortar el fragmento exacto que pidió el usuario
    segment = audio[clip.start_time_ms:clip.end_time_ms]

    # HU-44: aplicar fades suaves en los bordes
    if clip.fade_in_ms > 0:
        segment = segment.fade_in(clip.fade_in_ms)
    if clip.fade_out_ms > 0:
        segment = segment.fade_out(clip.fade_out_ms)

    # Ajustar volumen: 1.0 = sin cambio, 0.5 ≈ -6dB, 2.0 ≈ +6dB
    if clip.volume != 1.0:
        db_change = 20 * (clip.volume - 1.0)
        segment = segment + db_change

    return segment


def get_clip_s3_key(clip) -> str:
    """Obtiene el s3_key de la fuente del clip (song, stem o custom)."""
    if clip.song and clip.song.audio_s3_key:
        return clip.song.audio_s3_key
    elif clip.stem_file and clip.stem_file.audio_s3_key:
        return clip.stem_file.audio_s3_key
    elif clip.custom_audio_s3_key:
        return clip.custom_audio_s3_key
    raise ValueError(f"Clip {clip.id} no tiene fuente de audio válida.")