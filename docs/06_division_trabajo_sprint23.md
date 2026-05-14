# División de trabajo — Sprint 2 + Sprint 3
> Los tres módulos son independientes entre sí — no hay bloqueos cruzados  
> Cada persona trabaja en su módulo de principio a fin (back + front)  
> HU cubiertas: HU-14 a HU-29

---

## Mapa de dependencias — por qué no hay bloqueos

```
PERSONA A (Stems / Karaoke)
  Necesita: User ✅, S3 ✅, credit_service ✅
  No necesita nada de Nicol ni Brandon

PERSONA B / NICOL (Recomendaciones + Playlists)
  Necesita: Song ✅, Tag ✅, song_plays ✅ (Brandon ya lo hizo)
  No necesita nada de Persona A ni de Brandon Sprint 2+

PERSONA C / BRANDON (Playlists auto + Panel admin completo)
  Necesita: Song ✅, Tag ✅, Playlist (Nicol lo crea primero)
  Acuerdo: Nicol crea el modelo Playlist, Brandon lo usa solo en la parte de auto-playlists
```

> **Un solo acuerdo necesario:** Nicol crea el modelo `Playlist` y `PlaylistSong` primero (día 1),  
> para que Brandon pueda usar esas tablas en las playlists automáticas.

---

## PERSONA A (vos) — Módulo `stems` + Karaoke

**HU cubiertas:** HU-14, HU-15, HU-16, HU-17, HU-18, HU-19, HU-20  
**Depende de:** solo `User` y `credit_service` — podés arrancar hoy mismo  
**Tiempo estimado:** 2.5 semanas

---

### Backend — `apps/stems/`

#### Paso 1: Modelos en `apps/stems/models.py`

```python
from apps.core.models import BaseModel
from django.db import models
from django.conf import settings

class StemJob(BaseModel):
    STATUS_CHOICES = [
        ('queued', 'Queued'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='stem_jobs')
    source_audio_url = models.TextField()          # URL temporal en S3 del archivo subido
    source_filename = models.CharField(max_length=255)
    source_file_size_bytes = models.BigIntegerField()
    model_used = models.CharField(max_length=40, default='demucs-v4')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='queued')
    progress_pct = models.IntegerField(default=0)  # 0-100 para barra de progreso
    error_message = models.TextField(null=True, blank=True)
    credits_used = models.IntegerField(default=2)  # separar cuesta más que generar
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)

class StemFile(models.Model):
    """Archivos resultantes de la separación."""
    STEM_TYPES = [
        ('vocals', 'Vocals'),
        ('no_vocals', 'No Vocals (Karaoke)'),
        ('bass', 'Bass'),
        ('drums', 'Drums'),
        ('other', 'Other'),
    ]

    id = models.UUIDField(primary_key=True, default=__import__('uuid').uuid4, editable=False)
    stem_job = models.ForeignKey(StemJob, on_delete=models.CASCADE, related_name='stem_files')
    stem_type = models.CharField(max_length=20, choices=STEM_TYPES)
    audio_s3_key = models.TextField()
    duration_seconds = models.IntegerField(null=True, blank=True)
    file_size_bytes = models.BigIntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
```

```bash
python manage.py makemigrations stems
python manage.py migrate
```

#### Paso 2: Agregar Demucs al servidor Modal

En `ml/modal_music_server.py` (el que copiaste del ZIP), agregar Demucs como segundo endpoint. Agregar en la clase `MusicGenServer`:

```python
# Agregar en las dependencias de la imagen Modal (al inicio del archivo):
# demucs>=4.0.0

@modal.fastapi_endpoint(method="POST", requires_proxy_auth=True)
def separate_stems(self, request: dict):
    """
    Separa un archivo de audio en pistas con Demucs.
    Input:  { s3_key: str, stems: ['vocals', 'no_vocals'] }
    Output: { stems: { vocals: s3_key, no_vocals: s3_key, ... } }
    """
    import demucs.separate
    import boto3, tempfile, os
    from pathlib import Path

    s3 = boto3.client('s3',
        aws_access_key_id=os.environ['AWS_ACCESS_KEY_ID'],
        aws_secret_access_key=os.environ['AWS_SECRET_ACCESS_KEY'],
        region_name=os.environ['AWS_S3_REGION_NAME']
    )

    # Descargar el audio de S3 a un archivo temporal
    with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as tmp:
        s3.download_fileobj(os.environ['AWS_STORAGE_BUCKET_NAME'], request['s3_key'], tmp)
        input_path = tmp.name

    # Separar con Demucs (modo two-stems: vocals vs no_vocals)
    output_dir = tempfile.mkdtemp()
    demucs.separate.main([
        '--two-stems', 'vocals',
        '--out', output_dir,
        input_path
    ])

    # Subir los stems resultantes a S3
    result = {}
    base_name = Path(input_path).stem
    model_dir = Path(output_dir) / 'htdemucs' / base_name

    for stem_type in ['vocals', 'no_vocals']:
        stem_file = model_dir / f'{stem_type}.wav'
        if stem_file.exists():
            s3_key = f"stems/{request['s3_key'].split('/')[-1]}/{stem_type}.wav"
            s3.upload_file(str(stem_file), os.environ['AWS_STORAGE_BUCKET_NAME'], s3_key)
            result[stem_type] = s3_key

    return {'stems': result}
```

#### Paso 3: `apps/stems/services/stem_service.py`

```python
from apps.stems.models import StemJob
from apps.credits.services.credit_service import check_balance, deduct_credits

MAX_FILE_SIZE_BYTES = 50 * 1024 * 1024  # 50 MB — HU-20

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
    from ml.modal_client import upload_to_s3
    s3_key = upload_to_s3(file, folder='stems/uploads')

    job = StemJob.objects.create(
        user=user,
        source_audio_url=s3_key,
        source_filename=filename,
        source_file_size_bytes=file.size,
        status='queued',
    )

    from apps.stems.tasks import process_stem_job
    process_stem_job.delay(str(job.id))
    return job


class FileTooLargeError(Exception):
    pass

class InsufficientCreditsError(Exception):
    pass
```

#### Paso 4: `apps/stems/tasks.py`

```python
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
```

#### Paso 5: Views en `apps/stems/views.py`

- `UploadAndSeparateView` (POST `/api/stems/separate/`) — recibe el archivo, llama `stem_service.request_stem_separation()`. Retorna `{job_id}`
- `StemJobStatusView` (GET `/api/stems/jobs/{id}/`) — devuelve `{status, progress_pct, stem_files?}`
- `StemJobListView` (GET `/api/stems/jobs/`) — historial de jobs del usuario
- `StemFileDownloadView` (GET `/api/stems/files/{id}/download-url/`) — genera URL firmada de S3 para descargar el stem

#### Paso 6: Agregar a `.env`

```env
MODAL_ENDPOINT_SEPARATE_STEMS=https://TU_ORG--gm-music-server-musicgenserver-separate-stems.modal.run
```

---

### Frontend — Persona A

Implementar:
- `src/api/modules/stems.api.ts`
- `src/pages/stems/StemsPage.tsx` — dos paneles lado a lado:
  - **Panel izquierdo**: drop zone para subir el archivo de audio. Muestra nombre, tamaño, botón "Separar pistas (2 créditos)".
  - **Panel derecho**: historial de jobs anteriores del usuario
- `src/components/stems/AudioUploader.tsx` — drag & drop con validación de tamaño (máx 50MB) y tipo (.mp3, .wav)
- `src/components/stems/StemProgress.tsx` — barra de progreso que hace polling cada 3s hasta `completed`
- `src/components/stems/StemResultCard.tsx` — una vez completado, muestra los stems disponibles con botón de descarga y reproducción para cada uno

```typescript
// src/hooks/useStemJob.ts
import { useEffect, useState } from 'react';
import { getStemJobStatus } from '../api/modules/stems.api';

export function useStemJob(jobId: string | null) {
  const [status, setStatus] = useState<string | null>(null);
  const [progress, setProgress] = useState(0);
  const [stemFiles, setStemFiles] = useState<any[]>([]);

  useEffect(() => {
    if (!jobId) return;
    const FINAL = ['completed', 'failed'];

    const poll = async () => {
      try {
        const data = await getStemJobStatus(jobId);
        setStatus(data.status);
        setProgress(data.progress_pct);
        if (data.stem_files) setStemFiles(data.stem_files);
        if (!FINAL.includes(data.status)) setTimeout(poll, 3000);
      } catch {
        setTimeout(poll, 6000);
      }
    };
    poll();
  }, [jobId]);

  return { status, progress, stemFiles };
}
```

---

### ✅ Checklist Sprint 2 — Persona A

**Backend:**
- [ ] `POST /api/stems/separate/` con archivo de 60MB devuelve 400 con mensaje de tamaño
- [ ] `POST /api/stems/separate/` con menos de 2 créditos devuelve 402
- [ ] `POST /api/stems/separate/` con archivo válido crea el job y devuelve `job_id`
- [ ] `GET /api/stems/jobs/{id}/` actualiza `progress_pct` correctamente
- [ ] La tarea Celery crea los registros `StemFile` para `vocals` y `no_vocals`
- [ ] Solo descuenta 2 créditos si el job termina con `completed` (no si falla)
- [ ] `GET /api/stems/files/{id}/download-url/` devuelve URL firmada de S3 válida
- [ ] `python manage.py test apps.stems` pasa sin errores

**Frontend:**
- [ ] El drop zone rechaza archivos mayores a 50MB con mensaje claro
- [ ] El drop zone rechaza archivos que no sean .mp3 o .wav
- [ ] La barra de progreso se actualiza en tiempo real mientras el job procesa
- [ ] Al completarse, aparecen los botones de descarga para `vocals` y `no_vocals`
- [ ] Cada stem se puede reproducir directamente en el player (sin descargar)

---

---

## PERSONA B / NICOL — Recomendaciones + Playlists manuales

**HU cubiertas:** HU-21, HU-22, HU-23, HU-24, HU-25, HU-26, HU-27, HU-28  
**Depende de:** `Song`, `Tag`, `SongPlay` (todo ya existe de Sprint 1)  
**Acuerdo con Brandon:** crear el modelo `Playlist` y `PlaylistSong` el día 1, para que Brandon pueda usarlo

---

### Backend — `apps/recommendations/` y `apps/playlists/`

#### Modelos de recomendaciones en `apps/recommendations/models.py`

```python
from django.db import models
from django.conf import settings
import uuid

class ListeningHistory(models.Model):
    """Agrega cuánto escucha cada usuario de cada tag."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    tag = models.ForeignKey('songs.Tag', on_delete=models.CASCADE)
    play_count = models.IntegerField(default=0)
    total_seconds = models.IntegerField(default=0)
    last_played_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = [('user', 'tag')]

class UserTasteProfile(models.Model):
    """Perfil de gustos calculado periódicamente para cada usuario."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    top_tags = models.JSONField(default=list)     # [{"tag_id": 5, "score": 0.95}, ...]
    top_genres = models.JSONField(default=list)
    top_moods = models.JSONField(default=list)
    calculated_at = models.DateTimeField(auto_now=True)

class UserSimilarity(models.Model):
    """Similitudes entre usuarios para recomendaciones colaborativas."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user_a = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='similarities_as_a')
    user_b = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='similarities_as_b')
    similarity_score = models.FloatField()   # 0.0 a 1.0
    calculated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = [('user_a', 'user_b')]
```

#### Modelos de playlists en `apps/playlists/models.py`

```python
# ⚠️ CREAR ESTE ARCHIVO EL DÍA 1 — Brandon lo necesita
from apps.core.models import BaseModel
from django.db import models
from django.conf import settings
import uuid, secrets

class Playlist(BaseModel):
    TYPE_CHOICES = [
        ('manual', 'Manual'),
        ('auto_mood', 'Auto por estado de ánimo'),
        ('auto_genre', 'Auto por género'),
        ('recommended', 'Recomendada'),
    ]
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='playlists')
    title = models.CharField(max_length=200)
    description = models.TextField(null=True, blank=True)
    cover_url = models.TextField(null=True, blank=True)
    type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='manual')
    is_public = models.BooleanField(default=False)
    share_token = models.CharField(max_length=64, unique=True, null=True, blank=True)
    song_count = models.IntegerField(default=0)

    def generate_share_token(self):
        self.share_token = secrets.token_urlsafe(32)
        self.save(update_fields=['share_token'])
        return self.share_token

class PlaylistSong(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    playlist = models.ForeignKey(Playlist, on_delete=models.CASCADE, related_name='playlist_songs')
    song = models.ForeignKey('songs.Song', on_delete=models.CASCADE)
    position = models.IntegerField()
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [('playlist', 'song')]
        ordering = ['position']
```

#### Services de recomendaciones

```python
# apps/recommendations/services/history_service.py
def update_listening_history(user, song):
    """
    Llamar desde community.record_play() cada vez que alguien escucha una canción.
    Actualiza el historial agregado por tag.
    """
    from apps.recommendations.models import ListeningHistory
    from django.utils import timezone

    for tag in song.tags.all():
        history, _ = ListeningHistory.objects.get_or_create(
            user=user, tag=tag,
            defaults={'play_count': 0, 'total_seconds': 0}
        )
        history.play_count += 1
        history.last_played_at = timezone.now()
        history.save(update_fields=['play_count', 'last_played_at', 'updated_at'])


# apps/recommendations/services/profile_service.py
def recalculate_profile(user):
    """
    Recalcula el perfil de gustos del usuario basado en su historial.
    Se ejecuta como tarea Celery diaria, y también al registrar un play.
    """
    from apps.recommendations.models import ListeningHistory, UserTasteProfile

    history = ListeningHistory.objects.filter(user=user).select_related('tag').order_by('-play_count')[:20]

    top_tags = [{'tag_id': h.tag.id, 'name': h.tag.name, 'score': h.play_count} for h in history]
    top_genres = [t for t in top_tags if h.tag.category == 'genre' for h in history if h.tag.id == t['tag_id']]
    top_moods  = [t for t in top_tags if h.tag.category == 'mood'  for h in history if h.tag.id == t['tag_id']]

    UserTasteProfile.objects.update_or_create(
        user=user,
        defaults={'top_tags': top_tags, 'top_genres': top_genres, 'top_moods': top_moods}
    )
```

#### Views de recomendaciones

- `ForYouView` (GET `/api/recommendations/for-you/`) — canciones públicas que coincidan con los top tags del usuario
- `SuggestedTagsView` (GET `/api/recommendations/suggested-tags/`) — HU-23: sugiere tags al crear
- `SimilarUsersView` — canciones públicas de usuarios con perfil similar

#### Views de playlists manuales

- `PlaylistListCreateView` (GET/POST `/api/playlists/`) — listar propias + crear
- `PlaylistDetailView` (GET/PATCH/DELETE `/api/playlists/{id}/`)
- `PlaylistSongsView` (POST/DELETE `/api/playlists/{id}/songs/`) — agregar/quitar canciones
- `PlaylistShareView` (POST `/api/playlists/{id}/share/`) — genera `share_token`, devuelve link público
- `PublicPlaylistView` (GET `/api/playlists/public/{share_token}/`) — sin auth

---

### Frontend — Nicol

- `src/api/modules/recommendations.api.ts` y `src/api/modules/playlists.api.ts`
- `src/pages/recommendations/ForYouPage.tsx` — sección "Para ti"
- `src/pages/playlists/PlaylistsPage.tsx` y `PlaylistDetailPage.tsx`
- `src/components/playlist/PlaylistCard.tsx` y `PlaylistRow.tsx`

---

### ✅ Checklist Sprint 2+3 — Nicol

**Backend:**
- [ ] `GET /api/recommendations/for-you/` devuelve canciones ordenadas por afinidad con el perfil del usuario
- [ ] `GET /api/recommendations/suggested-tags/` devuelve los 5 tags que el usuario más usa
- [ ] Al registrar un play (ya lo hace Brandon), `update_listening_history()` se llama automáticamente
- [ ] `GET /api/playlists/` solo devuelve playlists propias del usuario autenticado
- [ ] `POST /api/playlists/` crea una playlist con tipo `manual`
- [ ] `POST /api/playlists/{id}/songs/` agrega una canción y actualiza `song_count`
- [ ] `DELETE /api/playlists/{id}/songs/{song_id}/` quita la canción y actualiza `song_count`
- [ ] `POST /api/playlists/{id}/share/` genera `share_token` y devuelve el link
- [ ] `GET /api/playlists/public/{token}/` funciona sin autenticación
- [ ] `python manage.py test apps.recommendations apps.playlists` pasa sin errores

---

---

## PERSONA C / BRANDON — Playlists automáticas + Panel admin completo

**HU cubiertas:** HU-26, HU-27, HU-29 + reportes admin  
**Depende de:** modelo `Playlist` que crea Nicol el día 1, y `Song`/`Tag` que ya existen  
**Puede arrancar con:** el panel admin (no depende de Nicol para nada)

---

### Backend — Playlists automáticas en `apps/playlists/services/auto_playlist_service.py`

```python
# Playlists auto por estado de ánimo — HU-26
def generate_mood_playlists(user):
    """
    Genera playlists automáticas agrupando las canciones del usuario por mood tag.
    """
    from apps.playlists.models import Playlist, PlaylistSong
    from apps.songs.models import Song, Tag

    MOODS = ['sad', 'happy', 'energetic', 'chill', 'romantic', 'angry']

    for mood in MOODS:
        songs = Song.objects.filter(
            user=user,
            status='ready',
            deleted_at__isnull=True,
            tags__name=mood
        ).distinct()[:30]

        if songs.count() < 2:
            continue

        playlist, created = Playlist.objects.update_or_create(
            user=user,
            type='auto_mood',
            title=f'Canciones {mood.capitalize()}',
            defaults={'song_count': songs.count()}
        )

        # Reconstruir las canciones de la playlist
        PlaylistSong.objects.filter(playlist=playlist).delete()
        for i, song in enumerate(songs):
            PlaylistSong.objects.create(playlist=playlist, song=song, position=i)


# Playlists auto por género — HU-27
def generate_genre_playlists(user):
    """Similar a generate_mood_playlists pero filtrando por tags de categoría 'genre'."""
    from apps.playlists.models import Playlist, PlaylistSong
    from apps.songs.models import Song, Tag

    genres = Tag.objects.filter(
        category='genre',
        songtag__song__user=user,
        songtag__song__status='ready',
        songtag__song__deleted_at__isnull=True
    ).distinct()

    for genre in genres:
        songs = Song.objects.filter(
            user=user, status='ready',
            deleted_at__isnull=True, tags=genre
        ).distinct()[:30]

        if songs.count() < 2:
            continue

        playlist, _ = Playlist.objects.update_or_create(
            user=user, type='auto_genre',
            title=f'Mis canciones de {genre.name.capitalize()}',
            defaults={'song_count': songs.count()}
        )
        PlaylistSong.objects.filter(playlist=playlist).delete()
        for i, song in enumerate(songs):
            PlaylistSong.objects.create(playlist=playlist, song=song, position=i)
```

#### Tarea Celery periódica

```python
# En workers/schedules.py — agregar:
from celery.schedules import crontab

app.conf.beat_schedule = {
    'generate-auto-playlists-daily': {
        'task': 'apps.playlists.tasks.generate_all_auto_playlists',
        'schedule': crontab(hour=3, minute=0),  # todos los días a las 3am
    },
}

# En apps/playlists/tasks.py:
@shared_task
def generate_all_auto_playlists():
    from apps.users.models import User
    from apps.playlists.services.auto_playlist_service import generate_mood_playlists, generate_genre_playlists
    for user in User.objects.filter(is_active=True, deleted_at__isnull=True):
        generate_mood_playlists(user)
        generate_genre_playlists(user)
```

#### Views de playlists automáticas

- `AutoPlaylistListView` (GET `/api/playlists/auto/`) — las playlists automáticas del usuario
- `TriggerAutoPlaylistView` (POST `/api/playlists/auto/generate/`) — genera manualmente para el usuario actual

---

### Backend — Panel de admin completo en `apps/reports/`

```python
# apps/reports/views.py

class UsageReportView(APIView):
    permission_classes = [IsAdmin]

    def get(self, request):
        from apps.songs.models import Song, GenerationJob
        from apps.users.models import User
        from django.db.models import Count
        from django.utils import timezone
        from datetime import timedelta

        now = timezone.now()
        last_30 = now - timedelta(days=30)

        return Response({
            'total_users': User.objects.filter(deleted_at__isnull=True).count(),
            'new_users_30d': User.objects.filter(created_at__gte=last_30).count(),
            'total_songs_generated': Song.objects.filter(status='ready').count(),
            'songs_last_30d': Song.objects.filter(status='ready', created_at__gte=last_30).count(),
            'failed_jobs_30d': GenerationJob.objects.filter(status='failed', created_at__gte=last_30).count(),
            'public_songs': Song.objects.filter(is_public=True, status='ready').count(),
        })

class TopSongsView(APIView):
    permission_classes = [IsAdmin]

    def get(self, request):
        from apps.songs.models import Song
        songs = Song.objects.filter(status='ready', is_public=True).order_by('-play_count')[:20]
        # serializar y devolver
        ...

class AuditLogView(APIView):
    permission_classes = [IsAdmin]

    def get(self, request):
        from apps.audit.models import AuditLog
        # Filtrable por ?action=&user_id=&from=&to=
        ...
```

#### Agregar endpoints al API_CONTRACT

```markdown
## Stems
POST /api/stems/separate/              Body: {file (multipart)}  → {job_id}
GET  /api/stems/jobs/                  → lista de jobs del usuario
GET  /api/stems/jobs/{id}/             → {status, progress_pct, stem_files}
GET  /api/stems/files/{id}/download-url/ → {url}

## Recommendations
GET  /api/recommendations/for-you/     → canciones recomendadas
GET  /api/recommendations/suggested-tags/ → tags sugeridos para crear

## Playlists
GET  /api/playlists/                   → playlists manuales propias
POST /api/playlists/                   Body: {title, description?}  → playlist creada
GET  /api/playlists/{id}/
PATCH /api/playlists/{id}/
DELETE /api/playlists/{id}/
POST /api/playlists/{id}/songs/        Body: {song_id, position}
DELETE /api/playlists/{id}/songs/{song_id}/
POST /api/playlists/{id}/share/        → {share_url}
GET  /api/playlists/public/{token}/    (sin auth)
GET  /api/playlists/auto/              → playlists automáticas
POST /api/playlists/auto/generate/     → genera playlists auto manualmente

## Admin / Reports
GET  /api/reports/usage/               (admin)
GET  /api/reports/top-songs/           (admin)
GET  /api/reports/audit-logs/          (admin, filtrable)
GET  /api/reports/credits-summary/     (admin)
```

---

### Frontend — Brandon

- `src/pages/playlists/AutoPlaylistsPage.tsx` — sección de playlists generadas automáticamente
- `src/pages/admin/UsersAdminPage.tsx` — tabla de usuarios con búsqueda y filtros
- `src/pages/admin/ReportsAdminPage.tsx` — gráficas de uso (canciones generadas, usuarios activos)
- `src/pages/admin/AuditLogAdminPage.tsx` — tabla de logs filtrables
- `src/components/admin/UserTable.tsx`
- `src/components/admin/AuditTable.tsx`

---

### ✅ Checklist Sprint 2+3 — Brandon

**Backend:**
- [ ] `generate_mood_playlists(user)` crea una playlist por cada mood con al menos 2 canciones
- [ ] `generate_genre_playlists(user)` crea una playlist por cada género presente
- [ ] Las playlists auto se regeneran sin duplicar — usan `update_or_create`
- [ ] La tarea Celery corre sin errores y procesa todos los usuarios activos
- [ ] `GET /api/reports/usage/` devuelve las métricas correctas
- [ ] `GET /api/reports/audit-logs/` es filtrable por `action`, `user_id`, rango de fechas
- [ ] Todos los endpoints de reports devuelven 403 si el usuario no es admin

**Frontend:**
- [ ] La página de playlists auto muestra las generadas con cover y cantidad de canciones
- [ ] El panel admin muestra los números de uso correctos
- [ ] La tabla de audit logs tiene paginación y filtros funcionales
- [ ] El panel admin es completamente inaccesible para usuarios sin `is_staff`

---

## Flujo de merges Sprint 2+3

```
feature/hu-14-stems-upload     → PR → develop   (Persona A, sin esperar a nadie)
feature/hu-21-recommendations  → PR → develop   (Nicol, puede arrancar cuando quiera)
feature/hu-26-auto-playlists   → PR → develop   (Brandon, espera modelo Playlist de Nicol)
feature/hu-29-admin-reports    → PR → develop   (Brandon, puede arrancar ya con el panel admin)
```

> Brandon puede dividir su trabajo en dos ramas: primero `hu-29-admin-reports` (no depende de Nicol),
> y luego `hu-26-auto-playlists` (depende del modelo Playlist).
