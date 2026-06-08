import os
import shutil
import tempfile
import traceback

import boto3
import whisper
from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import connection
from django.db.models import Q

from apps.songs.models import Song


class Command(BaseCommand):
    help = "Transcribes lyrics for songs that have no lyrics saved using Whisper"

    def add_arguments(self, parser):
        parser.add_argument(
            "--model",
            default="base",
            choices=["tiny", "base", "small", "medium"],
            help="Whisper model size (default: base)",
        )
        parser.add_argument(
            "--song-id",
            help="Process a single song by ID (UUID)",
        )
        parser.add_argument(
            "--force",
            action="store_true",
            help="Re-transcribe songs that already have lyrics",
        )
        parser.add_argument(
            "--timestamps-only",
            action="store_true",
            help="Solo calcular timestamps para canciones que ya tienen letra pero no tienen timestamps",
        )

    def handle(self, *args, **options):
        # Check ffmpeg is available (Whisper requires it to decode audio)
        if not shutil.which("ffmpeg"):
            self.stdout.write(self.style.ERROR(
                "ERROR: ffmpeg no está instalado o no está en el PATH.\n"
                "Instálalo con:\n"
                "  winget install ffmpeg\n"
                "Luego cierra y vuelve a abrir la terminal."
            ))
            return

        model_name = options["model"]
        song_id = options.get("song_id")
        force = options["force"]
        timestamps_only = options["timestamps_only"]

        self.stdout.write(f'Cargando modelo Whisper "{model_name}"...')
        model = whisper.load_model(model_name)
        self.stdout.write(self.style.SUCCESS("Modelo cargado.\n"))

        qs = Song.objects.filter(status="ready", instrumental=False)

        if song_id:
            qs = qs.filter(id=song_id)
        elif timestamps_only:
            # Canciones con letra pero sin timestamps
            qs = qs.exclude(Q(lyrics__isnull=True) | Q(lyrics="")).filter(lyrics_timestamps__isnull=True)
        elif not force:
            qs = qs.filter(Q(lyrics__isnull=True) | Q(lyrics=""))

        songs = list(
            qs.exclude(audio_s3_key="").exclude(audio_s3_key__isnull=True)
        )

        if not songs:
            self.stdout.write("No hay canciones pendientes de transcripción.")
            return

        label = "timestamps" if timestamps_only else "transcripción"
        self.stdout.write(f"Canciones a procesar ({label}): {len(songs)}\n")

        s3 = boto3.client(
            "s3",
            region_name=settings.AWS_S3_REGION_NAME,
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        )

        ok = 0
        failed = 0
        for i, song in enumerate(songs, 1):
            self.stdout.write(f"[{i}/{len(songs)}] {song.title} ({song.id})")
            try:
                if timestamps_only:
                    self._compute_timestamps(song, model, s3)
                    self.stdout.write(self.style.SUCCESS("  ✓ Timestamps guardados"))
                else:
                    self._transcribe_song(song, model, s3)
                    self.stdout.write(self.style.SUCCESS("  ✓ Letra guardada"))
                ok += 1
            except Exception as exc:
                self.stdout.write(self.style.ERROR(f"  ✗ Error: {exc}"))
                self.stdout.write(self.style.WARNING(traceback.format_exc()))
                failed += 1

        self.stdout.write(f"\nListo: {ok} procesadas, {failed} errores.")

    # ──────────────────────────────────────────────────────────────────────────

    def _transcribe_song(self, song: Song, model, s3) -> None:
        # Snapshot fields needed after the long Whisper call so we don't rely
        # on a stale ORM object after the DB connection is recycled.
        song_id = song.id
        audio_s3_key = song.audio_s3_key
        lang = song.language if song.language in ("es", "en") else None
        duration = song.audio_duration or 180.0

        fd, tmp_path = tempfile.mkstemp(suffix=".wav")
        os.close(fd)  # release the handle so boto3 can write to it on Windows

        try:
            s3.download_file(
                settings.AWS_STORAGE_BUCKET_NAME,
                audio_s3_key,
                tmp_path,
            )

            # Close the DB connection before the long Whisper transcription.
            # PostgreSQL drops idle connections after ~30s; closing here lets
            # Django open a fresh connection when we call save() below.
            connection.close()

            result = model.transcribe(
                tmp_path,
                language=lang,
                task="transcribe",
                fp16=False,
                verbose=False,
                word_timestamps=True,
            )

            segments = result.get("segments", [])
            if not segments:
                return

            lyrics = self._format_lyrics(segments, duration)
            if not lyrics:
                return

            timestamps = [
                {'start': round(seg['start'], 2), 'end': round(seg['end'], 2), 'text': seg['text'].strip()}
                for seg in segments
                if seg.get('text', '').strip()
            ]

            # Re-fetch the song to avoid updating a stale object across the
            # now-recycled connection.
            Song.objects.filter(id=song_id).update(
                lyrics=lyrics,
                lyrics_source="ai_generated",
                lyrics_timestamps=timestamps,
            )
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

    def _format_lyrics(self, segments: list, duration: float) -> str:
        lines = [seg["text"].strip() for seg in segments if seg["text"].strip()]
        n = len(lines)
        if not n:
            return ""

        # Split into sections based on total duration
        if duration <= 60:
            sections = [
                ("[verse]", lines[: n // 2]),
                ("[chorus]", lines[n // 2 :]),
            ]
        elif duration <= 120:
            q = n // 3
            sections = [
                ("[verse 1]", lines[:q]),
                ("[chorus]", lines[q : 2 * q]),
                ("[chorus]", lines[2 * q :]),
            ]
        else:
            q = n // 4
            sections = [
                ("[verse 1]", lines[:q]),
                ("[chorus]", lines[q : 2 * q]),
                ("[verse 2]", lines[2 * q : 3 * q]),
                ("[chorus]", lines[3 * q :]),
            ]

        parts = []
        for label, section_lines in sections:
            if section_lines:
                parts.append(label)
                parts.extend(section_lines)
                parts.append("")

        return "\n".join(parts).strip()

    def _compute_timestamps(self, song: Song, model, s3) -> None:
        song_id = song.id
        audio_s3_key = song.audio_s3_key
        lang = song.language if song.language in ("es", "en") else None

        fd, tmp_path = tempfile.mkstemp(suffix=".wav")
        os.close(fd)

        try:
            s3.download_file(settings.AWS_STORAGE_BUCKET_NAME, audio_s3_key, tmp_path)
            connection.close()

            result = model.transcribe(
                tmp_path,
                language=lang,
                task="transcribe",
                fp16=False,
                verbose=False,
                word_timestamps=True,
            )

            segments = result.get("segments", [])
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
