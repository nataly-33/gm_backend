# División de trabajo — Sprint 0 y Sprint 1
> **Este documento reemplaza al 03_division_trabajo_sprint01.md**  
> Incorpora los cambios del 05_integracion_zip_referencia.md  
> Stack: React + Vite + TypeScript · Django + DRF · Stripe · Modal (ACE-Step)  
> Modelo: B2C sin multitenancy · 3 personas de código · 2 personas de documento

---

## Límites de cada sprint

| Sprint | Qué se entrega | HU cubiertas |
|---|---|---|
| **Sprint 0** | Proyecto inicializado, BD creada, Auth funcionando, estructura de carpetas, Modal desplegado, documento base | HU-03 (base técnica) |
| **Sprint 1** | Generación de canciones end-to-end, créditos, Stripe, comunidad, player | HU-01, HU-02, HU-04 al HU-13 |

---

## Regla de oro — Día 1 antes de escribir código

El equipo completo se reúne y acuerda **antes de separarse**:

1. **Contrato de API** — Persona A escribe `API_CONTRACT.md` con todos los endpoints, qué reciben y qué devuelven. Persona B y C lo usan para trabajar en paralelo.
2. **Esquema SQL final** — revisar `01_database_schema_v2_b2c.md` juntos y aprobar.
3. **Variables de entorno** — completar `.env.example` con todas las claves necesarias.
4. **Ramas de Git** — crear `main` y `develop`. Todo trabajo va en `feature/hu-XX-descripcion`.

---

## PERSONA A — Arquitectura, BD, Auth y setup inicial

**Cubre:** Sprint 0 completo + parte del Sprint 1 (estructura base)  
**Depende de:** nadie — es la primera en arrancar  
**Persona B y C esperan:** que Auth esté funcionando antes de integrar sus módulos

---

### SPRINT 0 — Semana 1 Backend

#### Paso 1: Inicializar Django

```bash
python -m venv venv && source venv/bin/activate

pip install django==5.0 djangorestframework==3.15 djangorestframework-simplejwt==5.3 psycopg2-binary python-decouple django-cors-headers celery redis boto3 stripe pillow

pip freeze > requirements.txt
django-admin startproject config .

# Crear todas las apps de una vez
python manage.py startapp core apps/core
python manage.py startapp users apps/users
python manage.py startapp songs apps/songs
python manage.py startapp credits apps/credits
python manage.py startapp community apps/community
python manage.py startapp recommendations apps/recommendations
python manage.py startapp playlists apps/playlists
python manage.py startapp stems apps/stems
python manage.py startapp mix apps/mix
python manage.py startapp notifications apps/notifications
python manage.py startapp audit apps/audit
python manage.py startapp reports apps/reports

# Carpetas adicionales que NO son apps Django
mkdir -p ml workers scripts requirements
touch ml/__init__.py ml/modal_music_server.py ml/prompts.py ml/modal_client.py
touch workers/__init__.py workers/celery.py
```

#### Paso 2: BaseModel en `apps/core/models.py`

```python
import uuid
from django.db import models

class BaseModel(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(null=True, blank=True, db_index=True)

    class Meta:
        abstract = True

    def soft_delete(self):
        from django.utils import timezone
        self.deleted_at = timezone.now()
        self.save(update_fields=['deleted_at'])

    @property
    def is_deleted(self):
        return self.deleted_at is not None
```

#### Paso 3: Modelo User personalizado en `apps/users/models.py`

```python
import uuid
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models

class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra):
        if not email:
            raise ValueError("El email es obligatorio")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra):
        extra.setdefault('is_staff', True)
        extra.setdefault('is_superuser', True)
        return self.create_user(email, password, **extra)

class User(AbstractBaseUser, PermissionsMixin):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True)
    full_name = models.CharField(max_length=200)
    avatar_url = models.TextField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)     # acceso al admin de Django
    credit_balance = models.IntegerField(default=0)
    stripe_customer_id = models.CharField(max_length=100, null=True, blank=True)
    email_verified_at = models.DateTimeField(null=True, blank=True)
    last_login_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(null=True, blank=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['full_name']
    objects = UserManager()

    def __str__(self):
        return self.email


class Role(models.Model):
    name = models.CharField(max_length=40, unique=True)  # 'admin', 'user', 'dj'
    description = models.TextField(null=True, blank=True)
    is_system = models.BooleanField(default=False)

class UserRole(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='user_roles')
    role = models.ForeignKey(Role, on_delete=models.CASCADE)
    assigned_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [('user', 'role')]
```

> Recordar agregar `AUTH_USER_MODEL = 'users.User'` en `config/settings/base.py`.

#### Paso 4: Permisos en `apps/core/permissions.py`

```python
from rest_framework.permissions import BasePermission

class IsAdmin(BasePermission):
    """El usuario tiene rol 'admin' o es staff de Django."""
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        return request.user.is_staff or request.user.user_roles.filter(
            role__name='admin'
        ).exists()

class IsOwnerOrAdmin(BasePermission):
    """El objeto pertenece al usuario autenticado, o es admin."""
    def has_object_permission(self, request, view, obj):
        if request.user.is_staff:
            return True
        return obj.user_id == request.user.id
```

#### Paso 5: Auth en `apps/users/`

Archivos a crear:
- `serializers.py` — `RegisterSerializer`, `LoginSerializer`, `UserProfileSerializer`
- `views.py` — `RegisterView`, `LoginView`, `MeView`, `ChangePasswordView`
- `urls.py` — rutas de auth
- `services.py` — `create_user(email, password, full_name)`, `assign_default_role(user)`

```python
# apps/users/services.py
def create_user(email: str, password: str, full_name: str):
    from apps.users.models import User, Role, UserRole
    user = User.objects.create_user(email=email, password=password, full_name=full_name)
    assign_default_role(user)
    return user

def assign_default_role(user):
    from apps.users.models import Role, UserRole
    role, _ = Role.objects.get_or_create(name='user', defaults={'is_system': True})
    UserRole.objects.get_or_create(user=user, role=role)
```

#### Paso 6: Configurar Celery en `workers/celery.py`

```python
import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
app = Celery('gm')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()
```

#### Paso 7: Script seed en `scripts/seed_db.py`

```python
# Ejecutar con: python manage.py shell < scripts/seed_db.py
from apps.users.models import User, Role
from apps.credits.models import CreditPlan
from apps.songs.models import Tag

# Roles del sistema
for name in ['admin', 'user', 'dj']:
    Role.objects.get_or_create(name=name, defaults={'is_system': True})

# Superadmin
if not User.objects.filter(email='admin@gm.com').exists():
    u = User.objects.create_superuser(email='admin@gm.com', password='admin1234', full_name='Super Admin')
    print(f"Superadmin creado: {u.email}")

# Planes de crédito
CreditPlan.objects.get_or_create(slug='free',   defaults={'name':'Free',   'credits_per_month':5,   'price_usd':0.00})
CreditPlan.objects.get_or_create(slug='pro',    defaults={'name':'Pro',    'credits_per_month':50,  'price_usd':9.00})
CreditPlan.objects.get_or_create(slug='studio', defaults={'name':'Studio', 'credits_per_month':200, 'price_usd':25.00})

# Tags iniciales
tags = [
    ('reggaeton','genre'),('lofi','genre'),('techno','genre'),('pop','genre'),
    ('rock','genre'),('hip-hop','genre'),('jazz','genre'),('classical','genre'),
    ('sad','mood'),('happy','mood'),('energetic','mood'),('chill','mood'),
    ('romantic','mood'),('angry','mood'),
    ('fast','tempo'),('slow','tempo'),('120bpm','tempo'),
]
for name, cat in tags:
    Tag.objects.get_or_create(name=name, defaults={'category': cat})

print("Seed completado.")
```

#### Paso 8: Escribir `API_CONTRACT.md`

```markdown
## Auth
POST /api/auth/register/   Body: {email, password, full_name}  → {user, access, refresh}
POST /api/auth/login/      Body: {email, password}             → {access, refresh}
POST /api/auth/refresh/    Body: {refresh}                     → {access}
GET  /api/auth/me/         (auth requerida)                    → {id, email, full_name, credit_balance, role}
POST /api/auth/logout/     (auth requerida)                    → 204

## Songs
POST /api/songs/generate/           Body: {title, description?, prompt?, lyrics?, described_lyrics?, instrumental?, guidance_scale?}  → {job_id, song_id, status}
GET  /api/songs/jobs/{id}/          → {status, song_id, error_message}
GET  /api/songs/library/            → [{id, title, status, audio_s3_key, thumbnail_s3_key, tags, created_at}]
GET  /api/songs/{id}/               → canción completa
GET  /api/songs/{id}/play-url/      → {url}  (URL firmada S3, expira 1h)
GET  /api/songs/{id}/thumbnail-url/ → {url}  (URL firmada S3)
PATCH /api/songs/{id}/              Body: {title?, is_public?}  → canción actualizada
DELETE /api/songs/{id}/             → 204 (soft delete)
POST /api/songs/{id}/like/          → {liked: true/false}
GET  /api/songs/tags/               → [{id, name, category, emoji}]

## Credits
GET  /api/credits/balance/           → {balance, plan}
GET  /api/credits/plans/             → [{slug, name, credits_per_month, price_usd, features}]
POST /api/credits/checkout/          Body: {plan_slug}  → {checkout_url}
POST /api/credits/stripe-webhook/    (Stripe llama esto — no requiere auth JWT)
GET  /api/credits/transactions/      → [{amount, type, balance_after, created_at}]

## Community
GET  /api/community/trending/        → [{canción + like_count + play_count}] (top 10, últimos 2 días)
GET  /api/community/feed/            → canciones públicas paginadas
POST /api/community/plays/           Body: {song_id, seconds_played, source}  → 201
```

---


### SPRINT 0 — Semana 1 Frontend (también Persona A)

```bash
npm create vite@latest gm-frontend -- --template react-ts
cd gm-frontend
npm install axios react-router-dom zustand @tanstack/react-query
npm install -D tailwindcss postcss autoprefixer eslint @typescript-eslint/eslint-plugin prettier
npx tailwindcss init -p
```

Crear estructura de carpetas completa con archivos vacíos (`.gitkeep`). Implementar:

- `src/api/client.ts` — instancia Axios con interceptors de auth y manejo de errores
- `src/api/endpoints.ts` — **TODOS** los endpoints del API_CONTRACT como constantes TypeScript
- `src/store/auth.store.ts` — estado de usuario con Zustand
- `src/router/index.tsx` — rutas base
- `src/router/PrivateRoute.tsx` y `AdminRoute.tsx`
- `src/layouts/AuthLayout.tsx` y `AppLayout.tsx` — solo esqueleto
- `src/pages/auth/LoginPage.tsx` y `RegisterPage.tsx` — UI completa

---

### ✅ Checklist Sprint 0 — Persona A (antes del merge)

**Backend:**
- [ ] `python manage.py check` sin errores
- [ ] `python manage.py migrate` aplica todas las migraciones
- [ ] `POST /api/auth/register/` crea usuario con contraseña hasheada y rol 'user' asignado
- [ ] `POST /api/auth/login/` devuelve `access` y `refresh` tokens válidos
- [ ] `GET /api/auth/me/` con token válido devuelve datos del usuario incluyendo `credit_balance` y `role`
- [ ] `GET /api/auth/me/` sin token devuelve 401
- [ ] `python manage.py shell < scripts/seed_db.py` crea roles, superadmin, planes y tags sin errores
- [ ] `python manage.py test apps.users` pasa sin errores

**Frontend:**
- [ ] `npm run dev` arranca sin errores en http://localhost:5173
- [ ] Login y Register renderizan correctamente
- [ ] `PrivateRoute` redirige a `/login` si no hay token
- [ ] `src/api/endpoints.ts` tiene definidos todos los endpoints del API_CONTRACT

---

---

## PERSONA B — Generación musical + Motor de IA (Modal)

**Cubre:** Sprint 0 (desplegar Modal) + Sprint 1 (módulo songs completo)  
**Depende de:** que Persona A termine Auth  
**Puede arrancar en paralelo con:** diseño de modelos, copiar archivos del ZIP a `ml/`  
**Persona C depende de:** que `credit_service.check_balance()` exista — acordar con C que lo cree ella primero

---

### SPRINT 0 — Semana 1: Motor de IA en Modal

#### Paso 1: Copiar archivos del ZIP

```
ZIP: backend/main.py      →  gm-backend/ml/modal_music_server.py
ZIP: backend/prompts.py   →  gm-backend/ml/prompts.py
```

Hacer estos cambios en `ml/modal_music_server.py`:

```python
# Cambio 1 — línea 13: renombrar la app
app = modal.App("gm-music-server")

# Cambio 2 — agregar al final de la clase MusicGenServer:
@modal.fastapi_endpoint(method="GET")
def health(self):
    return {"status": "ok", "model": "ace-step"}
```

El archivo `ml/prompts.py` se copia **sin ningún cambio**.

#### Paso 2: Desplegar en Modal

```bash
cd gm-backend/ml
pip install modal
modal setup        # autenticarse con la cuenta de Modal
modal deploy modal_music_server.py
# Guardar las URLs que entrega Modal en el .env del backend
```

---

### SPRINT 1 — Semana 1 y 2: Módulo songs

#### Paso 3: Modelos en `apps/songs/models.py`

Copiar el modelo exacto del archivo `05_integracion_zip_referencia.md` sección "PARTE 2".  
Incluye: `Tag`, `Song`, `SongTag`, `GenerationJob`.

```bash
python manage.py makemigrations songs
python manage.py migrate
```

#### Paso 4: `ml/modal_client.py`

```python
# ml/modal_client.py
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
    if 's3_key' not in data:
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
```

#### Paso 5: `apps/songs/services/generation_service.py`

```python
# apps/songs/services/generation_service.py
from apps.songs.models import Song, GenerationJob, Tag, SongTag


def request_generation(user, *, title: str, description: str = None,
                       prompt: str = None, lyrics: str = None,
                       described_lyrics: str = None,
                       instrumental: bool = False,
                       guidance_scale: float = 15.0) -> GenerationJob:
    """
    Punto de entrada para generar una canción.
    Valida créditos → crea Song + Job → encola tarea Celery.
    """
    from apps.credits.services.credit_service import check_balance

    if not check_balance(user, required=1):
        raise InsufficientCreditsError("Sin créditos disponibles.")

    mode = _determine_mode(description, prompt, lyrics, described_lyrics)

    song = Song.objects.create(
        user=user,
        title=_default_title(title, description, described_lyrics),
        description=description,
        prompt=prompt,
        lyrics=lyrics,
        described_lyrics=described_lyrics,
        instrumental=instrumental,
        guidance_scale=guidance_scale,
        status='draft',
    )

    job = GenerationJob.objects.create(user=user, song=song, mode=mode, status='queued')

    from apps.songs.tasks import process_generation_job
    process_generation_job.delay(str(job.id))

    return job


def _determine_mode(description, prompt, lyrics, described_lyrics) -> str:
    if description:
        return 'from_description'
    elif lyrics and prompt:
        return 'with_lyrics'
    elif described_lyrics and prompt:
        return 'with_described_lyrics'
    raise ValueError("Parámetros insuficientes para determinar el modo.")


def _default_title(title, description, described_lyrics) -> str:
    raw = title or description or described_lyrics or "Untitled"
    return (raw[:1].upper() + raw[1:].strip())[:199]


class InsufficientCreditsError(Exception):
    pass
```

#### Paso 6: `apps/songs/tasks.py`

```python
from celery import shared_task
from django.utils import timezone


@shared_task(bind=True, max_retries=2)
def process_generation_job(self, job_id: str):
    from apps.songs.models import GenerationJob
    from apps.credits.services.credit_service import deduct_credits
    from apps.notifications.services import notify_user
    from ml.modal_client import call_modal_endpoint, ModalGenerationError

    try:
        job = GenerationJob.objects.select_related('user', 'song').get(id=job_id)
        song = job.song

        # 1. Marcar como processing
        song.status = 'processing'
        song.save(update_fields=['status'])
        job.status = 'processing'
        job.started_at = timezone.now()
        job.save(update_fields=['status', 'started_at'])

        # 2. Construir la llamada según el modo
        endpoint_url, body = _build_modal_request(song, job.mode)
        job.modal_endpoint_used = endpoint_url
        job.save(update_fields=['modal_endpoint_used'])

        # 3. Llamar a Modal
        response = call_modal_endpoint(endpoint_url, body)

        # 4. Guardar resultado en la canción
        song.audio_s3_key = response['s3_key']
        song.thumbnail_s3_key = response['cover_image_s3_key']
        song.status = 'ready'
        song.save(update_fields=['audio_s3_key', 'thumbnail_s3_key', 'status', 'updated_at'])

        # 5. Guardar tags/categorías generados por el LLM
        _save_categories(song, response.get('categories', []))

        # 6. Descontar crédito SOLO si fue exitoso
        deduct_credits(job.user, amount=1, reference_id=str(job.id), reference_type='generation_job')
        job.credits_used = 1
        job.status = 'completed'
        job.completed_at = timezone.now()
        job.save(update_fields=['credits_used', 'status', 'completed_at'])

        # 7. Notificar al usuario
        notify_user(job.user, type='song_ready', reference_id=str(song.id))

    except Exception as exc:
        try:
            job = GenerationJob.objects.get(id=job_id)
            job.status = 'failed'
            job.error_message = str(exc)
            job.completed_at = timezone.now()
            job.save(update_fields=['status', 'error_message', 'completed_at'])
            job.song.status = 'failed'
            job.song.save(update_fields=['status'])
        except Exception:
            pass
        raise self.retry(exc=exc, countdown=60)


def _build_modal_request(song, mode: str):
    from django.conf import settings
    common = {
        'guidance_scale': song.guidance_scale,
        'infer_step': song.infer_step,
        'audio_duration': song.audio_duration,
        'seed': song.seed,
        'instrumental': song.instrumental,
    }
    if mode == 'from_description':
        return settings.MODAL_ENDPOINT_FROM_DESCRIPTION, {'full_described_song': song.description, **common}
    elif mode == 'with_lyrics':
        return settings.MODAL_ENDPOINT_WITH_LYRICS, {'prompt': song.prompt, 'lyrics': song.lyrics, **common}
    elif mode == 'with_described_lyrics':
        return settings.MODAL_ENDPOINT_FROM_DESCRIBED_LYRICS, {'prompt': song.prompt, 'described_lyrics': song.described_lyrics, **common}
    raise ValueError(f"Modo desconocido: {mode}")


def _save_categories(song, categories: list):
    from apps.songs.models import Tag, SongTag
    for cat_name in categories:
        tag, _ = Tag.objects.get_or_create(
            name=cat_name.strip().lower(),
            defaults={'category': 'genre'}
        )
        SongTag.objects.get_or_create(song=song, tag=tag)
```

#### Paso 7: Views en `apps/songs/views.py`

Implementar:
- `GenerateView` (POST `/api/songs/generate/`) — llama `generation_service.request_generation()`
- `GenerationJobStatusView` (GET `/api/songs/jobs/{id}/`) — devuelve `{status, song_id, error_message}`
- `SongLibraryView` (GET `/api/songs/library/`) — canciones del usuario autenticado
- `SongDetailView` (GET/PATCH/DELETE `/api/songs/{id}/`) — con soft delete en DELETE
- `SongPlayUrlView` (GET `/api/songs/{id}/play-url/`) — llama `modal_client.get_presigned_url()`
- `TagListView` (GET `/api/songs/tags/`) — todos los tags disponibles

---

### SPRINT 1 — Frontend Persona B

Implementar:
- `src/api/modules/songs.api.ts` — todas las funciones de canciones
- `src/hooks/useGenerationJob.ts` — polling cada 3s para estado del job
- `src/pages/create/CreatePage.tsx` — formulario con los 3 modos de generación
- `src/pages/library/LibraryPage.tsx` — lista de canciones propias
- `src/components/song/SongCard.tsx` — tarjeta con cover, título, tags, botones
- `src/components/song/SongRow.tsx` — fila en lista estilo Spotify
- `src/components/song/SongGrid.tsx` — grid de SongCards
- `src/components/song/TagSelector.tsx` — chips de tags clicables

```typescript
// src/hooks/useGenerationJob.ts
import { useEffect, useState } from 'react';
import { getGenerationJobStatus } from '../api/modules/songs.api';

type JobStatus = 'queued' | 'processing' | 'ready' | 'failed' | 'no_credits';

export function useGenerationJob(jobId: string | null) {
  const [status, setStatus] = useState<JobStatus | null>(null);
  const [songId, setSongId] = useState<string | null>(null);

  useEffect(() => {
    if (!jobId) return;
    const FINAL = ['ready', 'failed', 'no_credits'];

    const poll = async () => {
      try {
        const data = await getGenerationJobStatus(jobId);
        setStatus(data.status);
        if (data.song_id) setSongId(data.song_id);
        if (!FINAL.includes(data.status)) setTimeout(poll, 3000);
      } catch {
        setTimeout(poll, 6000); // back-off en error
      }
    };
    poll();
  }, [jobId]);

  return { status, songId };
}
```

---

### ✅ Checklist Sprint 1 — Persona B (antes del merge)

**Backend:**
- [ ] `POST /api/songs/generate/` con créditos crea el job y devuelve `{job_id, song_id, status: 'queued'}`
- [ ] `POST /api/songs/generate/` sin créditos devuelve 402
- [ ] `POST /api/songs/generate/` sin token devuelve 401
- [ ] `GET /api/songs/jobs/{id}/` devuelve el status actual del job
- [ ] `GET /api/songs/library/` solo devuelve canciones del usuario autenticado
- [ ] `DELETE /api/songs/{id}/` hace soft delete (`deleted_at` se llena, no aparece en library)
- [ ] `GET /api/songs/{id}/play-url/` devuelve una URL firmada de S3
- [ ] La tarea Celery pasa el job a `completed` y llena `audio_s3_key` cuando Modal responde OK
- [ ] La tarea Celery pasa el job a `failed` cuando Modal falla, sin descontar créditos
- [ ] `modal deploy ml/modal_music_server.py` despliega sin errores y el endpoint `/health` responde 200
- [ ] `python manage.py test apps.songs` pasa sin errores

**Frontend:**
- [ ] El formulario valida que haya al menos descripción o prompt antes de enviar
- [ ] Al enviar, aparece spinner con "Generando tu canción..."
- [ ] El polling detecta cuando el job llega a `ready` y muestra el reproductor automáticamente
- [ ] Si el job llega a `no_credits`, muestra mensaje de créditos insuficientes
- [ ] `SongCard` muestra cover (thumbnail), título, tags y botones de like/play
- [ ] La biblioteca muestra canciones ordenadas por fecha más reciente primero

---

---

## PERSONA C — Créditos, Stripe, Comunidad y Player

**Cubre:** Sprint 1 — módulos credits, community, audit, y componentes de player  
**Depende de:** que Persona A haya terminado Auth  
**Persona B depende de:** que `credit_service.check_balance()` y `deduct_credits()` existan

> **Acuerdo crítico de interfaz:** Persona C crea `apps/credits/services/credit_service.py` en los **primeros 2 días** de Sprint 1. Persona B puede importarlo aunque el módulo completo no esté terminado.

---

### SPRINT 1 — Backend

#### Paso 1: Modelos en `apps/credits/models.py`

```python
from apps.core.models import BaseModel
from django.db import models
from django.conf import settings

class CreditPlan(models.Model):
    slug = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=80)
    credits_per_month = models.IntegerField()
    price_usd = models.DecimalField(max_digits=8, decimal_places=2)
    stripe_price_id = models.CharField(max_length=100, null=True, blank=True)
    features = models.JSONField(default=list)
    is_active = models.BooleanField(default=True)

class UserSubscription(BaseModel):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    plan = models.ForeignKey(CreditPlan, on_delete=models.PROTECT)
    stripe_subscription_id = models.CharField(max_length=100, null=True, blank=True)
    status = models.CharField(max_length=20, default='active')
    current_period_end = models.DateTimeField(null=True, blank=True)

class CreditTransaction(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    amount = models.IntegerField()           # positivo = recarga, negativo = consumo
    balance_after = models.IntegerField()
    type = models.CharField(max_length=30)  # 'monthly_grant', 'stripe_purchase', 'generation', 'stem', 'mix'
    reference_id = models.UUIDField(null=True, blank=True)
    reference_type = models.CharField(max_length=30, null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
```

#### Paso 2: `apps/credits/services/credit_service.py` — CREAR PRIMERO

```python
# ⚠️ Crear este archivo antes que cualquier otra cosa — Persona B lo necesita
from django.db import transaction

def check_balance(user, required: int = 1) -> bool:
    """Persona B importa esto para validar antes de generar."""
    return user.credit_balance >= required

def deduct_credits(user, amount: int, reference_id: str = None, reference_type: str = None):
    """Descuenta créditos y registra la transacción. Operación atómica."""
    from apps.credits.models import CreditTransaction
    with transaction.atomic():
        user.credit_balance -= amount
        user.save(update_fields=['credit_balance'])
        CreditTransaction.objects.create(
            user=user,
            amount=-amount,
            balance_after=user.credit_balance,
            type=reference_type or 'generation',
            reference_id=reference_id,
        )

def grant_credits(user, amount: int, type: str = 'monthly_grant', description: str = None):
    """Agrega créditos. Se llama desde el webhook de Stripe."""
    from apps.credits.models import CreditTransaction
    with transaction.atomic():
        user.credit_balance += amount
        user.save(update_fields=['credit_balance'])
        CreditTransaction.objects.create(
            user=user,
            amount=amount,
            balance_after=user.credit_balance,
            type=type,
            description=description,
        )
```

#### Paso 3: `apps/credits/services/stripe_service.py`

```python
import stripe
from django.conf import settings

stripe.api_key = settings.STRIPE_SECRET_KEY

PLANS = {
    'pro':    {'credits': 50,  'price_id': settings.STRIPE_PRO_PRICE_ID},
    'studio': {'credits': 200, 'price_id': settings.STRIPE_STUDIO_PRICE_ID},
}

def create_checkout_session(user, plan_slug: str) -> str:
    plan = PLANS.get(plan_slug)
    if not plan:
        raise ValueError(f"Plan inválido: {plan_slug}")
    session = stripe.checkout.Session.create(
        customer_email=user.email,
        client_reference_id=str(user.id),
        mode='subscription',
        line_items=[{'price': plan['price_id'], 'quantity': 1}],
        success_url=settings.STRIPE_SUCCESS_URL,
        cancel_url=settings.STRIPE_CANCEL_URL,
        metadata={'user_id': str(user.id), 'plan': plan_slug},
    )
    return session.url

def handle_webhook(payload: bytes, sig_header: str):
    from apps.credits.services.credit_service import grant_credits
    from apps.users.models import User

    event = stripe.Webhook.construct_event(payload, sig_header, settings.STRIPE_WEBHOOK_SECRET)

    if event['type'] == 'invoice.paid':
        invoice = event['data']['object']
        meta = invoice.get('subscription_details', {}).get('metadata', {})
        user_id = meta.get('user_id')
        plan = meta.get('plan', 'pro')
        if user_id:
            try:
                user = User.objects.get(id=user_id)
                grant_credits(user, amount=PLANS[plan]['credits'], type='stripe_purchase',
                              description=f"Recarga mensual plan {plan}")
            except User.DoesNotExist:
                pass

    return {'received': True}
```

#### Paso 4: Views de `credits`

- `BalanceView` (GET `/api/credits/balance/`) — devuelve `{balance, plan_slug}`
- `PlanListView` (GET `/api/credits/plans/`) — todos los planes activos
- `CheckoutView` (POST `/api/credits/checkout/`) — crea sesión Stripe y devuelve `{checkout_url}`
- `StripeWebhookView` (POST `/api/credits/stripe-webhook/`) — llama `handle_webhook()`, **sin autenticación JWT**
- `TransactionHistoryView` (GET `/api/credits/transactions/`)

#### Paso 5: Módulo `community`

Modelos en `apps/community/models.py`: `SongLike`, `SongPlay`

Views:
- `TrendingView` (GET `/api/community/trending/`) — canciones públicas con `status='ready'`, ordenadas por `play_count` desc, últimas 48h
- `PublicFeedView` (GET `/api/community/feed/`) — canciones públicas paginadas, con cursor
- `LikeToggleView` (POST `/api/community/like/{song_id}/`) — toggle like/unlike, actualiza `song.like_count`
- `RecordPlayView` (POST `/api/community/plays/`) — registra `SongPlay`, incrementa `song.play_count`

```python
# apps/community/services.py
from django.db import transaction

def toggle_like(user, song):
    from apps.community.models import SongLike
    from apps.songs.models import Song
    with transaction.atomic():
        like, created = SongLike.objects.get_or_create(user=user, song=song)
        if not created:
            like.delete()
            Song.objects.filter(id=song.id).update(like_count=models.F('like_count') - 1)
            return False
        else:
            Song.objects.filter(id=song.id).update(like_count=models.F('like_count') + 1)
            return True

def record_play(user, song_id: str, seconds_played: int, source: str):
    from apps.community.models import SongPlay
    from apps.songs.models import Song
    SongPlay.objects.create(
        user=user, song_id=song_id,
        seconds_played=seconds_played,
        completed=(seconds_played > 0),
        source=source
    )
    Song.objects.filter(id=song_id).update(play_count=models.F('play_count') + 1)
```

#### Paso 6: Módulo `audit` — helper global

```python
# apps/audit/services.py
from apps.audit.models import AuditLog

def log_action(user, action: str, entity_type: str = None,
               entity_id=None, old_value=None, new_value=None, request=None):
    """
    Llamar desde cualquier módulo para registrar acciones importantes.
    Ej: log_action(user, 'song.generate', 'Song', song.id)
    """
    ip = None
    if request:
        x_forwarded = request.META.get('HTTP_X_FORWARDED_FOR')
        ip = x_forwarded.split(',')[0] if x_forwarded else request.META.get('REMOTE_ADDR')

    AuditLog.objects.create(
        user=user,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        old_value=old_value,
        new_value=new_value,
        ip_address=ip,
    )
```

---

### SPRINT 1 — Frontend Persona C

Implementar:
- `src/api/modules/credits.api.ts` y `src/api/modules/community.api.ts`
- `src/store/player.store.ts` — estado completo del reproductor

```typescript
// src/store/player.store.ts
import { create } from 'zustand';

interface PlayerTrack {
  id: string;
  title: string;
  audioUrl: string | null;      // URL firmada S3
  thumbnailUrl: string | null;
  prompt: string | null;
  createdByUserName: string;
}

interface PlayerState {
  currentTrack: PlayerTrack | null;
  isPlaying: boolean;
  queue: PlayerTrack[];
  volume: number;
  play: (track: PlayerTrack) => void;
  pause: () => void;
  resume: () => void;
  setVolume: (vol: number) => void;
  addToQueue: (track: PlayerTrack) => void;
  playNext: () => void;
}

export const usePlayerStore = create<PlayerState>((set, get) => ({
  currentTrack: null, isPlaying: false, queue: [], volume: 0.8,
  play: (track) => set({ currentTrack: track, isPlaying: true }),
  pause: () => set({ isPlaying: false }),
  resume: () => set({ isPlaying: true }),
  setVolume: (volume) => set({ volume }),
  addToQueue: (track) => set((state) => ({ queue: [...state.queue, track] })),
  playNext: () => {
    const { queue } = get();
    if (!queue.length) return;
    const [next, ...rest] = queue;
    set({ currentTrack: next, isPlaying: true, queue: rest });
  },
}));
```

- `src/components/player/PlayerBar.tsx` — barra fija inferior estilo Spotify
- `src/components/player/PlayerControls.tsx`
- `src/pages/home/HomePage.tsx` — feed de tendencias con `SongGrid` de Persona B
- `src/pages/admin/AdminDashboardPage.tsx` — stats de uso
- `src/components/admin/StatsCard.tsx`

---

### ✅ Checklist Sprint 1 — Persona C (antes del merge)

**Backend:**
- [ ] `GET /api/credits/balance/` devuelve saldo actual del usuario
- [ ] `GET /api/credits/plans/` lista los 3 planes
- [ ] `POST /api/credits/checkout/` devuelve una URL de Stripe válida
- [ ] `POST /api/credits/stripe-webhook/` procesa el evento `invoice.paid` y agrega créditos al usuario
- [ ] `check_balance(user, required=1)` retorna False cuando balance es 0
- [ ] `deduct_credits()` es atómico: actualiza balance Y crea transacción en la misma operación
- [ ] `GET /api/community/trending/` devuelve máximo 10 canciones públicas y listas
- [ ] `POST /api/community/like/{song_id}/` hace toggle y actualiza `like_count` en `songs`
- [ ] Llamar al mismo endpoint dos veces: primera vez like=true, segunda vez like=false
- [ ] `log_action()` crea el registro en `audit_logs` sin romper si hay un error
- [ ] `python manage.py test apps.credits apps.community apps.audit` pasa sin errores

**Frontend:**
- [ ] `PlayerBar` es visible fija en la parte inferior cuando hay una canción activa
- [ ] Play/pause actualiza el ícono correctamente
- [ ] El slider de volumen funciona
- [ ] `HomePage` carga canciones de trending desde la API real
- [ ] Al hacer like, el ícono cambia inmediatamente sin esperar la respuesta del servidor (optimistic update)
- [ ] El panel de admin solo es accesible para usuarios con `is_staff = true`

---

## Flujo de merges — reglas del equipo

```
feature/hu-XX  →  (PR con al menos 1 aprobación)  →  develop  →  (fin de sprint)  →  main
```

- Nunca push directo a `main` ni a `develop`
- Antes de abrir un PR: correr todos los tests propios
- El reviewer verifica: tests pasan, no hay `tenant` ni multitenancy hardcodeado, lógica en services no en views

---

## Mapa de dependencias entre personas

```
Persona A (Auth)
    ├─→ Persona B puede arrancar sus modelos y Modal en paralelo
    └─→ Persona C puede arrancar sus modelos en paralelo
         │
         ├─ Persona C crea credit_service.py (día 1-2 de Sprint 1)
         │       └─→ Persona B puede importarlo y completar generation_service
         │
         └─ Persona A termina Auth
                 └─→ Persona B y C conectan sus módulos a la BD real
```
