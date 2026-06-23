import logging
import os
import shutil
import tempfile

import boto3
from celery import shared_task
from django.conf import settings
from django.utils import timezone

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=2)
def generate_karaoke_track(self, karaoke_track_id: str):
    from apps.karaoke.models import KaraokeTrack
    from ml.modal_client import call_modal_endpoint

    try:
        track = KaraokeTrack.objects.select_related('song').get(id=karaoke_track_id)
        song = track.song

        track.status = 'processing'
        track.save(update_fields=['status'])

        # 1. Separar stems con Demucs vía Modal
        response = call_modal_endpoint(
            settings.MODAL_ENDPOINT_SEPARATE_STEMS,
            {'s3_key': song.audio_s3_key},
        )
        stems = response['stems']  # {'vocals': '...', 'no_vocals': '...'}

        track.instrumental_s3_key = stems.get('no_vocals')
        track.vocals_s3_key       = stems.get('vocals')
        track.save(update_fields=['instrumental_s3_key', 'vocals_s3_key'])

        # 2. Whisper sobre el stem vocal (requiere ffmpeg disponible)
        ffmpeg_path = settings.FFMPEG_PATH
        ffmpeg_exists = os.path.exists(ffmpeg_path) or shutil.which(ffmpeg_path)
        if not ffmpeg_exists:
            logger.warning(f'ffmpeg no encontrado en {ffmpeg_path} — Whisper saltado, lyrics_timestamps quedará null')
        if track.vocals_s3_key and ffmpeg_exists:
            s3 = boto3.client(
                's3',
                region_name=settings.AWS_S3_REGION_NAME,
                aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            )
            fd, tmp_path = tempfile.mkstemp(suffix='.wav')
            os.close(fd)
            try:
                s3.download_file(
                    settings.AWS_STORAGE_BUCKET_NAME,
                    track.vocals_s3_key,
                    tmp_path,
                )

                # Cerrar conexión DB antes de Whisper (proceso largo, evita timeout)
                from django.db import connection
                connection.close()

                # Añadir carpeta de ffmpeg al PATH para que Whisper la encuentre
                ffmpeg_dir = os.path.dirname(os.path.abspath(ffmpeg_path))
                os.environ['PATH'] = f"{ffmpeg_dir};{os.environ.get('PATH', '')}"

                import whisper
                model = whisper.load_model('base')
                language = song.language if song.language in ('es', 'en') else None
                result = model.transcribe(
                    tmp_path,
                    language=language,
                    task='transcribe',
                    fp16=False,
                    word_timestamps=True,
                )
                segments = result.get('segments', [])
                timestamps = [
                    {
                        'start': round(s['start'], 2),
                        'end':   round(s['end'],   2),
                        'text':  s['text'].strip(),
                    }
                    for s in segments if s.get('text', '').strip()
                ]

                # Limpiar lyrics con Gemini si está disponible
                if settings.GEMINI_API_KEY and timestamps:
                    whisper_text = '\n'.join(t['text'] for t in timestamps)
                    reference_lyrics = song.lyrics or song.described_lyrics or song.prompt or ''

                    from google import genai
                    client = genai.Client(api_key=settings.GEMINI_API_KEY)
                    num_lines = len(timestamps)
                    
                    prompt = f"""Eres un experto ingeniero de audio preparando subtítulos para karaoke.
CONTEXTO CRÍTICO:
1. El audio original fue generado por IA, por lo que contiene artefactos sonoros, voces distorsionadas y balbuceos. Whisper intentó transcribir estos ruidos como palabras inventadas o sin sentido.
2. La LETRA DE REFERENCIA suele estar INCOMPLETA. Muchas veces la canción repite estrofas, coros, o hace "ad-libs" al final que no están escritos en la referencia.

TU MISIÓN:
Dada la transcripción fonética (Whisper) y la letra de referencia, limpia el texto línea por línea.

REGLAS ESTRICTAS:
1. ARREGLA LOS BALBUCEOS: Si Whisper detectó palabras raras, busca la frase más parecida en la referencia y corrígela.
2. EXTRAPOLA CON LÓGICA: Si la canción repite una parte o sigue cantando después de que se acaba la letra de referencia, usa tu sentido común. Transforma los intentos raros de Whisper en palabras reales que tengan sentido con el resto de la canción. NO dejes palabras inventadas.
3. MANTÉN LA ESTRUCTURA: Te enviaré {num_lines} líneas. DEBES devolver EXACTAMENTE {num_lines} líneas. No unas ni separes las frases.
4. FORMATO: Devuelve solo las líneas corregidas, una por línea, en texto plano (sin markdown, ni números).

LETRA DE REFERENCIA:
{reference_lyrics[:800]}

TRANSCRIPCIÓN DE WHISPER (Con errores de IA, {num_lines} líneas):
{whisper_text}

LÍNEAS CORREGIDAS:"""

                    response = client.models.generate_content(
                        model='gemini-2.5-flash',
                        contents=prompt
                    )
                    cleaned_text = response.text.strip()
                    cleaned_lines = [line.strip() for line in cleaned_text.split('\n') if line.strip()]

                    # Alinear líneas limpias con timestamps de Whisper
                    for i, timestamp in enumerate(timestamps):
                        if i < len(cleaned_lines):
                            timestamp['text'] = cleaned_lines[i]

                track.lyrics_timestamps = timestamps
                track.lyrics = '\n'.join(t['text'] for t in timestamps)
            finally:
                if os.path.exists(tmp_path):
                    os.remove(tmp_path)

        track.status       = 'ready'
        track.processed_at = timezone.now()
        track.save(update_fields=['status', 'processed_at', 'lyrics', 'lyrics_timestamps'])

    except Exception as exc:
        try:
            KaraokeTrack.objects.filter(id=karaoke_track_id).update(
                status='failed',
                error_message=str(exc)[:500],
            )
        except Exception:
            pass
        raise self.retry(exc=exc, countdown=60)
