# División de trabajo — Sprint 4 + HU faltantes de Sprint 2-3
> Cierra el product backlog completo  
> HU cubiertas: HU-29 a HU-31 (ML — faltaban en el 06), HU-42 a HU-45 (Sprint 4 Mix DJ)

---

## Estado del backlog antes de este documento

| Doc | HU cubiertas | Estado |
|---|---|---|
| `03_division_trabajo_FINAL.md` | HU-01 a HU-21 | Sprint 0 y 1 ✅ |
| `06_division_trabajo_sprint23.md` | HU-22 a HU-28, HU-32 a HU-41 | Sprint 2 y 3 ✅ |
| `07_ml_datos_sinteticos.md` | HU-29, HU-30, HU-31 | Sprint 2 — código listo, faltaba asignación |
| **Este documento** | HU-29 a HU-31 (asignación formal) + HU-42 a HU-45 | Sprint 4 ✅ |

---

## HU-29, HU-30, HU-31 — Asignación formal del módulo ML

Estas tres HU tienen el código completo en `07_ml_datos_sinteticos.md`.  
Solo faltaba definir formalmente quién las hace y cuándo.

**Responsable: Persona A / Nataly**  
**Cuándo: Sprint 2, en paralelo con stems**  
**No depende de Nicol ni Brandon**

| HU | Descripción corta | Archivo a crear |
|---|---|---|
| HU-29 | Sistema sugiere genre, mood y tempo antes de generar | `ml/predictor.py` + migración en `apps/songs/models.py` |
| HU-30 | Generar dataset sintético ≥1GB | `ml/dataset_generator.py` |
| HU-31 | Entrenar modelo .pkl | `ml/train_model.py` |

**Orden de ejecución:**

```
1. Escribir ml/dataset_generator.py    (3-4 horas de código)
2. Correr: python ml/dataset_generator.py   (~10 min automático → genera 1GB CSV)
3. Escribir ml/train_model.py          (2-3 horas de código)
4. Correr: python ml/train_model.py    (~5 min automático → genera .pkl)
5. Escribir ml/predictor.py            (2 horas)
6. Integrar predict_from_description() en apps/songs/services/generation_service.py
7. Agregar campos ml_predicted_genre, ml_predicted_mood, ml_confidence a Song
8. python manage.py makemigrations songs && python manage.py migrate
```

Ver código completo en `07_ml_datos_sinteticos.md`.

**Checklist antes del merge:**
- [ ] `python ml/dataset_generator.py` genera el CSV sin errores y pesa ≥1GB
- [ ] `python ml/train_model.py` genera `ml/models/music_classifier.pkl` y escribe `ml/TRAINING_REPORT.md`
- [ ] `predictor.predict_from_description("quiero algo triste y lento")` devuelve `{genre, mood, tempo, suggested_tags, confidence}`
- [ ] `POST /api/songs/generate/` con descripción guarda `ml_predicted_genre` y `ml_predicted_mood` en la canción
- [ ] `GET /api/songs/{id}/` incluye los campos de predicción ML en la respuesta
- [ ] `.gitignore` excluye `ml/data/` y `ml/models/*.pkl`
- [ ] `README.md` documenta cómo regenerar el dataset y el modelo

---

---

## SPRINT 4 — Mix tipo DJ

**Duración estimada:** 3 semanas  
**HU:** HU-42, HU-43, HU-44, HU-45

### Mapa de dependencias Sprint 4

```
PERSONA A / Nataly (HU-42, HU-43)
  Necesita: Song ✅, StemFile ✅ (ella misma lo hizo en Sprint 2)
  No depende de Nicol ni Brandon para arrancar

PERSONA B / Nicol (HU-44)
  Necesita: MixProject y MixClip (Nataly los crea)
  Puede arrancar: solo la parte de frontend mientras Nataly termina los modelos

PERSONA C / Brandon (HU-45)
  Necesita: MixProject con clips listos (Nataly), exportación de audio
  Puede arrancar: panel de admin de mix mientras espera a Nataly
```

**Único acuerdo:** Nataly crea los modelos `MixProject` y `MixClip` el día 1 del sprint.

---

## PERSONA A / Nataly — HU-42 y HU-43: Crear y editar mix

**HU-42:** Como usuario, quiero crear un proyecto de mix combinando varias canciones o pistas para armar una secuencia estilo DJ.  
**HU-43:** Como usuario, quiero cortar fragmentos de canciones (definiendo inicio y fin en milisegundos) para usar solo la parte que quiero en el mix.

---

### Backend

#### Paso 1: Modelos en `apps/mix/models.py`

```python
# ⚠️ Crear el día 1 — Nicol y Brandon los necesitan
from apps.core.models import BaseModel
from django.db import models
from django.conf import settings
import uuid

class MixProject(BaseModel):
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('processing', 'Processing'),
        ('ready', 'Ready'),
        ('failed', 'Failed'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='mix_projects'
    )
    title = models.CharField(max_length=200)
    description = models.TextField(null=True, blank=True)
    bpm = models.IntegerField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    output_s3_key = models.TextField(null=True, blank=True)
    duration_seconds = models.IntegerField(null=True, blank=True)

    def __str__(self):
        return f"{self.title} ({self.status})"


class MixClip(models.Model):
    """Un segmento de audio dentro del mix."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    mix_project = models.ForeignKey(
        MixProject, on_delete=models.CASCADE, related_name='clips'
    )
    # Fuente del clip — solo uno de estos tres debe estar lleno
    song = models.ForeignKey(
        'songs.Song', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='mix_clips'
    )
    stem_file = models.ForeignKey(
        'stems.StemFile', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='mix_clips'
    )
    custom_audio_s3_key = models.TextField(null=True, blank=True)

    # Posición y corte — HU-43
    position = models.IntegerField()
    start_time_ms = models.IntegerField(default=0)
    end_time_ms = models.IntegerField()

    # Efectos — HU-44 (Nicol los usa)
    fade_in_ms = models.IntegerField(default=0)
    fade_out_ms = models.IntegerField(default=0)
    volume = models.FloatField(default=1.0)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['position']

    @property
    def duration_ms(self):
        return self.end_time_ms - self.start_time_ms


class MixExport(BaseModel):
    """Registro de cada exportación de un mix."""
    FORMAT_CHOICES = [('mp3', 'MP3'), ('wav', 'WAV')]
    QUALITY_CHOICES = [('128k', '128kbps'), ('320k', '320kbps'), ('lossless', 'Lossless WAV')]

    mix_project = models.ForeignKey(MixProject, on_delete=models.CASCADE, related_name='exports')
    format = models.CharField(max_length=10, choices=FORMAT_CHOICES, default='mp3')
    quality = models.CharField(max_length=10, choices=QUALITY_CHOICES, default='320k')
    output_s3_key = models.TextField(null=True, blank=True)
    status = models.CharField(
        max_length=20,
        choices=[('queued','Queued'),('processing','Processing'),('ready','Ready'),('failed','Failed')],
        default='queued'
    )
    credits_used = models.IntegerField(default=3)
    error_message = models.TextField(null=True, blank=True)
```

```bash
python manage.py makemigrations mix
python manage.py migrate
```

#### Paso 2: `apps/mix/services/mix_service.py`

```python
# apps/mix/services/mix_service.py
from apps.mix.models import MixProject, MixClip
from apps.credits.services.credit_service import check_balance


def create_mix_project(user, title: str, description: str = None, bpm: int = None) -> MixProject:
    return MixProject.objects.create(
        user=user, title=title, description=description, bpm=bpm, status='draft'
    )


def add_clip(mix_project: MixProject, *, position: int,
             song_id: str = None, stem_file_id: str = None,
             start_time_ms: int = 0, end_time_ms: int,
             fade_in_ms: int = 0, fade_out_ms: int = 0,
             volume: float = 1.0) -> MixClip:
    """Agrega un clip al mix. Valida que la fuente sea correcta."""

    if not any([song_id, stem_file_id]):
        raise ValueError("Se requiere song_id o stem_file_id.")

    if end_time_ms <= start_time_ms:
        raise ValueError("end_time_ms debe ser mayor que start_time_ms.")

    # Reordenar clips existentes si la posición ya está ocupada
    MixClip.objects.filter(
        mix_project=mix_project, position__gte=position
    ).update(position=models.F('position') + 1)

    return MixClip.objects.create(
        mix_project=mix_project,
        song_id=song_id,
        stem_file_id=stem_file_id,
        position=position,
        start_time_ms=start_time_ms,
        end_time_ms=end_time_ms,
        fade_in_ms=fade_in_ms,
        fade_out_ms=fade_out_ms,
        volume=volume,
    )


def reorder_clips(mix_project: MixProject, clip_order: list):
    """
    Reordena los clips del mix.
    clip_order: lista de IDs en el nuevo orden deseado.
    """
    for new_position, clip_id in enumerate(clip_order):
        MixClip.objects.filter(id=clip_id, mix_project=mix_project).update(
            position=new_position
        )


def remove_clip(clip_id: str, user) -> None:
    """Elimina un clip. Verifica que pertenezca al usuario."""
    clip = MixClip.objects.select_related('mix_project').get(id=clip_id)
    if clip.mix_project.user_id != user.id:
        raise PermissionError("No tenés permiso para eliminar este clip.")
    clip.delete()
```

#### Paso 3: Views en `apps/mix/views.py`

- `MixProjectListCreateView` (GET/POST `/api/mix/projects/`) — listar propios + crear nuevo
- `MixProjectDetailView` (GET/PATCH/DELETE `/api/mix/projects/{id}/`) — ver, editar, soft delete
- `MixClipView` (POST `/api/mix/projects/{id}/clips/`) — agregar clip con parámetros de corte
- `MixClipDetailView` (PATCH/DELETE `/api/mix/projects/{id}/clips/{clip_id}/`) — editar corte o fade, eliminar
- `MixReorderView` (POST `/api/mix/projects/{id}/reorder/`) — reordenar clips con lista de IDs

#### Paso 4: Agregar endpoints al API_CONTRACT

```markdown
## Mix
POST   /api/mix/projects/                          → crear proyecto
GET    /api/mix/projects/                          → listar propios
GET    /api/mix/projects/{id}/                     → detalle con clips
PATCH  /api/mix/projects/{id}/                     → editar título/bpm
DELETE /api/mix/projects/{id}/                     → soft delete
POST   /api/mix/projects/{id}/clips/               Body: {song_id?, stem_file_id?, position, start_time_ms, end_time_ms} → clip creado
PATCH  /api/mix/projects/{id}/clips/{clip_id}/    Body: {start_time_ms?, end_time_ms?, fade_in_ms?, fade_out_ms?, volume?}
DELETE /api/mix/projects/{id}/clips/{clip_id}/
POST   /api/mix/projects/{id}/reorder/             Body: {clip_ids: [...]} → 200
POST   /api/mix/projects/{id}/export/              Body: {format, quality} → {export_id} (Brandon)
GET    /api/mix/exports/{id}/                      → {status, download_url?} (Brandon)
```

---

### Frontend — Persona A (Mix editor)

- `src/api/modules/mix.api.ts` — todas las funciones de mix
- `src/pages/mix/MixPage.tsx` — lista de proyectos de mix del usuario
- `src/pages/mix/MixEditorPage.tsx` — editor principal (ver abajo)
- `src/components/mix/ClipTimeline.tsx` — línea de tiempo horizontal con los clips en orden
- `src/components/mix/ClipCard.tsx` — tarjeta de un clip con controles de inicio/fin/volumen
- `src/components/mix/AddClipModal.tsx` — modal para elegir fuente (biblioteca / stems)

**Descripción de `MixEditorPage.tsx`:**

```
┌─────────────────────────────────────────────────────┐
│  "Mi Mix de Verano"   BPM: 120   [Exportar] [Guardar]│
├──────────────────────┬──────────────────────────────┤
│  BIBLIOTECA          │  LÍNEA DE TIEMPO             │
│  ┌──────────────┐    │  [Clip 1 ████][Clip 2 ██]   │
│  │ Canción 1    │    │  ↕ drag para reordenar       │
│  │ Canción 2    │    │                              │
│  │ Stem: vocals │    │  Clip seleccionado:          │
│  └──────────────┘    │  Inicio: [0ms] Fin: [30000ms]│
│  [+ Agregar clip]    │  Fade in: [500ms]            │
│                      │  Fade out: [500ms]           │
│                      │  Volumen: [====●====]        │
└──────────────────────┴──────────────────────────────┘
```

---

### ✅ Checklist Sprint 4 — Persona A

**Backend:**
- [ ] `POST /api/mix/projects/` crea un proyecto vacío
- [ ] `POST /api/mix/projects/{id}/clips/` con `end_time_ms <= start_time_ms` devuelve 400
- [ ] `POST /api/mix/projects/{id}/clips/` sin `song_id` ni `stem_file_id` devuelve 400
- [ ] `POST /api/mix/projects/{id}/reorder/` reordena correctamente los `position`
- [ ] `DELETE /api/mix/projects/{id}/clips/{clip_id}/` solo funciona si el mix es del usuario autenticado
- [ ] `python manage.py test apps.mix` pasa sin errores

**Frontend:**
- [ ] La línea de tiempo muestra los clips en orden de `position`
- [ ] Los controles de inicio/fin validan que `end > start`
- [ ] Reordenar clips actualiza el orden en el servidor
- [ ] El modal de agregar clip muestra la biblioteca y los stems del usuario

---

---

## PERSONA B / Nicol — HU-44: Fades y transiciones

**HU-44:** Como usuario, quiero aplicar fade in y fade out entre clips del mix para que las transiciones suenen fluidas y profesionales.

---

### Backend

Los campos `fade_in_ms` y `fade_out_ms` ya existen en el modelo `MixClip` (creados por Nataly).  
Nicol **solo implementa la lógica de audio** en la tarea de exportación.

Agregar en `apps/mix/services/audio_editor.py`:

```python
# apps/mix/services/audio_editor.py
"""
Lógica de edición de audio para el mix.
Usa pydub para cortes, fades y mezcla.
Requiere ffmpeg instalado en el sistema.
"""
from pydub import AudioSegment
import boto3, tempfile, os
from django.conf import settings


def download_audio_from_s3(s3_key: str) -> str:
    """Descarga un archivo de S3 a un archivo temporal. Retorna el path."""
    s3 = boto3.client('s3',
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        region_name=settings.AWS_S3_REGION_NAME
    )
    suffix = '.wav' if s3_key.endswith('.wav') else '.mp3'
    tmp = tempfile.NamedTemporaryFile(suffix=suffix, delete=False)
    s3.download_fileobj(settings.AWS_STORAGE_BUCKET_NAME, s3_key, tmp)
    return tmp.name


def apply_clip_effects(audio: AudioSegment, clip) -> AudioSegment:
    """
    Aplica corte, fade in, fade out y volumen a un segmento de audio.
    Implementa HU-43 (corte) y HU-44 (fades).
    """
    # HU-43: cortar el fragmento
    segment = audio[clip.start_time_ms:clip.end_time_ms]

    # HU-44: aplicar fades
    if clip.fade_in_ms > 0:
        segment = segment.fade_in(clip.fade_in_ms)
    if clip.fade_out_ms > 0:
        segment = segment.fade_out(clip.fade_out_ms)

    # Ajustar volumen (1.0 = sin cambio, 0.5 = -6dB, 2.0 = +6dB)
    if clip.volume != 1.0:
        db_change = 20 * (clip.volume - 1.0)
        segment = segment + db_change

    return segment


def get_clip_s3_key(clip) -> str:
    """Obtiene el s3_key de la fuente del clip."""
    if clip.song and clip.song.audio_s3_key:
        return clip.song.audio_s3_key
    elif clip.stem_file and clip.stem_file.audio_s3_key:
        return clip.stem_file.audio_s3_key
    elif clip.custom_audio_s3_key:
        return clip.custom_audio_s3_key
    raise ValueError(f"Clip {clip.id} no tiene fuente de audio válida.")
```

---

### Frontend — Nicol (controles de fade)

En `src/components/mix/ClipCard.tsx` (componente de Nataly), Nicol agrega los controles de fade:

```typescript
// Agregar dentro de ClipCard.tsx — sección de controles de fade
interface FadeControlsProps {
  fadeIn: number;
  fadeOut: number;
  onChange: (field: 'fade_in_ms' | 'fade_out_ms', value: number) => void;
}

export function FadeControls({ fadeIn, fadeOut, onChange }: FadeControlsProps) {
  return (
    <div className="fade-controls">
      <label>
        Fade in
        <input
          type="range" min={0} max={5000} step={100}
          value={fadeIn}
          onChange={(e) => onChange('fade_in_ms', Number(e.target.value))}
        />
        <span>{fadeIn}ms</span>
      </label>
      <label>
        Fade out
        <input
          type="range" min={0} max={5000} step={100}
          value={fadeOut}
          onChange={(e) => onChange('fade_out_ms', Number(e.target.value))}
        />
        <span>{fadeOut}ms</span>
      </label>
    </div>
  );
}
```

---

### ✅ Checklist Sprint 4 — Nicol

**Backend:**
- [ ] `apply_clip_effects()` con `fade_in_ms=500` agrega fade correcto al audio
- [ ] `apply_clip_effects()` con `volume=0.5` reduce el volumen correctamente
- [ ] `get_clip_s3_key()` devuelve el key correcto para song, stem y custom

**Frontend:**
- [ ] Los sliders de fade in/fade out actualizan el clip en el servidor al soltar
- [ ] El valor en ms se muestra actualizado en tiempo real mientras se mueve el slider

---

---

## PERSONA C / Brandon — HU-45: Exportar el mix

**HU-45:** Como usuario, quiero exportar el mix final como archivo MP3 o WAV para descargarlo y usarlo fuera de la plataforma.

---

### Backend

#### `apps/mix/tasks.py`

```python
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
        download_audio_from_s3, apply_clip_effects, get_clip_s3_key
    )
    from apps.credits.services.credit_service import check_balance, deduct_credits
    from apps.notifications.services import notify_user
    from pydub import AudioSegment
    import boto3, tempfile, os
    from django.conf import settings

    try:
        export = MixExport.objects.select_related('mix_project__user').get(id=export_id)
        mix = export.mix_project
        user = mix.user

        # Verificar créditos
        if not check_balance(user, required=3):
            export.status = 'failed'
            export.error_message = 'Sin créditos suficientes (se necesitan 3).'
            export.save()
            return

        export.status = 'processing'
        export.save(update_fields=['status'])

        # Obtener clips ordenados
        clips = MixClip.objects.filter(mix_project=mix).order_by('position')

        if not clips.exists():
            raise ValueError("El mix no tiene clips.")

        # Construir el audio completo
        final_audio = AudioSegment.empty()

        for clip in clips:
            s3_key = get_clip_s3_key(clip)
            audio_path = download_audio_from_s3(s3_key)

            try:
                audio = AudioSegment.from_file(audio_path)
                processed = apply_clip_effects(audio, clip)
                final_audio += processed
            finally:
                os.unlink(audio_path)  # limpiar archivo temporal

        # Exportar al formato pedido
        with tempfile.NamedTemporaryFile(
            suffix=f'.{export.format}', delete=False
        ) as tmp:
            bitrate = export.quality if export.format == 'mp3' else None
            final_audio.export(tmp.name, format=export.format, bitrate=bitrate)
            output_path = tmp.name

        # Subir a S3
        s3 = boto3.client('s3',
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.AWS_S3_REGION_NAME
        )
        s3_key = f"mix-exports/{mix.id}/{export.id}.{export.format}"
        s3.upload_file(output_path, settings.AWS_STORAGE_BUCKET_NAME, s3_key)
        os.unlink(output_path)

        # Actualizar duración del mix
        mix.duration_seconds = len(final_audio) // 1000
        mix.output_s3_key = s3_key
        mix.status = 'ready'
        mix.save(update_fields=['duration_seconds', 'output_s3_key', 'status'])

        # Descontar créditos y completar export
        deduct_credits(user, amount=3, reference_id=str(export.id), reference_type='mix_export')
        export.output_s3_key = s3_key
        export.status = 'ready'
        export.credits_used = 3
        export.save(update_fields=['output_s3_key', 'status', 'credits_used'])

        notify_user(user, type='mix_ready', reference_id=str(mix.id))

    except Exception as exc:
        try:
            export.status = 'failed'
            export.error_message = str(exc)
            export.save(update_fields=['status', 'error_message'])
        except Exception:
            pass
        raise self.retry(exc=exc, countdown=60)
```

#### Views de exportación

```python
# En apps/mix/views.py — agregar:

class MixExportView(APIView):
    """POST /api/mix/projects/{id}/export/ — Inicia la exportación."""
    permission_classes = [IsAuthenticated]

    def post(self, request, mix_id):
        from apps.mix.models import MixProject, MixExport
        from apps.mix.tasks import render_mix

        mix = MixProject.objects.get(id=mix_id, user=request.user, deleted_at__isnull=True)

        export = MixExport.objects.create(
            mix_project=mix,
            format=request.data.get('format', 'mp3'),
            quality=request.data.get('quality', '320k'),
            status='queued',
        )

        render_mix.delay(str(export.id))

        return Response({'export_id': str(export.id)}, status=202)


class MixExportStatusView(APIView):
    """GET /api/mix/exports/{id}/ — Estado de la exportación + URL de descarga."""
    permission_classes = [IsAuthenticated]

    def get(self, request, export_id):
        from apps.mix.models import MixExport
        from ml.modal_client import get_presigned_url

        export = MixExport.objects.select_related('mix_project').get(
            id=export_id,
            mix_project__user=request.user
        )

        data = {
            'status': export.status,
            'format': export.format,
            'error_message': export.error_message,
        }

        if export.status == 'ready' and export.output_s3_key:
            data['download_url'] = get_presigned_url(
                export.output_s3_key, expiry_seconds=3600
            )

        return Response(data)
```

#### Agregar dependencias

```bash
pip install pydub
# pydub requiere ffmpeg en el sistema:
# Ubuntu/Debian: sudo apt install ffmpeg
# Mac: brew install ffmpeg
# Windows: descargar desde ffmpeg.org
```

Agregar a `requirements/base.txt`: `pydub`

---

### Frontend — Brandon

- `src/hooks/useMixExport.ts` — polling del estado de exportación

```typescript
// src/hooks/useMixExport.ts
import { useEffect, useState } from 'react';
import { getMixExportStatus } from '../api/modules/mix.api';

export function useMixExport(exportId: string | null) {
  const [status, setStatus] = useState<string | null>(null);
  const [downloadUrl, setDownloadUrl] = useState<string | null>(null);

  useEffect(() => {
    if (!exportId) return;
    const FINAL = ['ready', 'failed'];

    const poll = async () => {
      try {
        const data = await getMixExportStatus(exportId);
        setStatus(data.status);
        if (data.download_url) setDownloadUrl(data.download_url);
        if (!FINAL.includes(data.status)) setTimeout(poll, 4000);
      } catch {
        setTimeout(poll, 8000);
      }
    };
    poll();
  }, [exportId]);

  return { status, downloadUrl };
}
```

- En `src/pages/mix/MixEditorPage.tsx` agregar el botón de exportar con modal de opciones:

```typescript
// Agregar en MixEditorPage.tsx — sección de exportación
function ExportModal({ mixId, onClose }) {
  const [format, setFormat] = useState<'mp3' | 'wav'>('mp3');
  const [quality, setQuality] = useState('320k');
  const [exportId, setExportId] = useState<string | null>(null);
  const { status, downloadUrl } = useMixExport(exportId);

  const handleExport = async () => {
    const result = await startMixExport(mixId, { format, quality });
    setExportId(result.export_id);
  };

  return (
    <div className="export-modal">
      <h3>Exportar mix</h3>
      <select value={format} onChange={e => setFormat(e.target.value as 'mp3' | 'wav')}>
        <option value="mp3">MP3</option>
        <option value="wav">WAV</option>
      </select>
      {format === 'mp3' && (
        <select value={quality} onChange={e => setQuality(e.target.value)}>
          <option value="128k">128 kbps</option>
          <option value="320k">320 kbps (recomendado)</option>
        </select>
      )}
      {!exportId && <button onClick={handleExport}>Exportar (3 créditos)</button>}
      {exportId && status !== 'ready' && <p>Procesando tu mix...</p>}
      {status === 'ready' && downloadUrl && (
        <a href={downloadUrl} download>⬇ Descargar {format.toUpperCase()}</a>
      )}
      {status === 'failed' && <p>Error al exportar. Intentar de nuevo.</p>}
    </div>
  );
}
```

---

### ✅ Checklist Sprint 4 — Brandon

**Backend:**
- [ ] `POST /api/mix/projects/{id}/export/` crea el export y devuelve `{export_id}` con status 202
- [ ] `GET /api/mix/exports/{id}/` devuelve `status: processing` mientras Celery trabaja
- [ ] `GET /api/mix/exports/{id}/` devuelve `download_url` (URL firmada S3) cuando `status: ready`
- [ ] La tarea Celery une los clips en el orden correcto de `position`
- [ ] Los fades se aplican correctamente (el audio suena bien con fade in/out)
- [ ] Solo descuenta 3 créditos si el export termina con `status: ready`
- [ ] `GET /api/mix/exports/{id}/` devuelve 403 si el mix no pertenece al usuario
- [ ] `python manage.py test apps.mix` pasa sin errores

**Frontend:**
- [ ] El modal de exportación muestra opciones de formato y calidad
- [ ] Al confirmar exportación aparece indicador de procesamiento
- [ ] El link de descarga aparece automáticamente cuando el export está listo (sin recargar)
- [ ] El link de descarga usa la URL firmada de S3 (no expone el bucket directamente)

---

## Flujo de merges Sprint 4

```
feature/hu-42-mix-project-crud     → PR → develop   (Nataly — día 1: crea modelos)
feature/hu-43-mix-clip-cortes      → PR → develop   (Nataly — sin dependencias)
feature/hu-44-fades-transiciones   → PR → develop   (Nicol — espera modelos de Nataly)
feature/hu-45-mix-export           → PR → develop   (Brandon — espera modelos de Nataly)
```

---

## Resumen final — todos los documentos de división

| Archivo | Sprints | HU |
|---|---|---|
| `03_division_trabajo_FINAL.md` | 0 y 1 | HU-01 a HU-21 |
| `06_division_trabajo_sprint23.md` | 2 y 3 | HU-22 a HU-28, HU-32 a HU-41 |
| `07_ml_datos_sinteticos.md` | 2 (ML) | HU-29, HU-30, HU-31 |
| `09_division_trabajo_sprint4.md` | 4 + faltantes | HU-29-31 (asignación), HU-42 a HU-45 |

**Total HU cubiertas: 45 / 45 ✅**
