# Factores de Calidad del Software — Defensa técnica

> Guía para responder las preguntas del Ing. Martínez sobre los 7 factores de calidad.
> Para cada factor: qué es, dónde se ve en el código y qué decir.

---

## 1. CORRECTO
> *El sistema hace exactamente lo que el cliente pidió.*

### Qué decir
El sistema cumple todos los requisitos funcionales levantados con el cliente:
generar canciones con IA, administrar créditos, hacer recomendaciones personalizadas,
separar stems de audio, y tener un panel de administración.

### Dónde mostrarlo

**Flujo de generación — `apps/songs/services/generation_service.py`**
```python
# 1. Valida créditos antes de hacer cualquier cosa
if not check_balance(user, required=1):
    raise InsufficientCreditsError("Sin créditos disponibles.")

# 2. Crea la canción según el modo que el cliente eligió
song = Song.objects.create(...)

# 3. Encola la tarea para que ACE-Step genere el audio
process_generation_job.delay(str(job.id))
```

**Sistema de créditos — `apps/credits/services/credit_service.py`**
```python
def deduct_credits(user, amount, ...):
    # Solo descuenta si la generación fue exitosa (line 49-58)
    with transaction.atomic():
        user.credit_balance -= amount
        user.save(update_fields=["credit_balance"])
        CreditTransaction.objects.create(...)
```
El crédito no se descuenta al pedir la canción, sino **después de que ACE-Step
confirma que el audio se generó** (`tasks.py` línea 53). Si falla, el usuario
no pierde su crédito.

**Modos de creación — `gm_frontend/src/pages/create/create-page.tsx`**
El frontend expone exactamente los 3 modos que el cliente pidió:
- `description` → Solo Descripción (la IA elige todo)
- `exact_lyrics` → Letra Exacta (el usuario escribe la letra)
- `auto_lyrics` → Letra Autogenerada (la IA redacta en base a una descripción)

---

## 2. EFICIENTE
> *El sistema trabaja de la mejor manera posible, optimizando recursos.*

### Qué decir
El sistema evita bloquear al usuario, minimiza llamadas a la base de datos
y carga solo lo necesario en el navegador.

### Dónde mostrarlo

**Lazy Loading — `gm_frontend/src/router/index.tsx`**
```typescript
// Cada página es un chunk separado que se carga SOLO cuando el usuario navega ahí
const CreatePage   = lazy(() => import('../pages/create/create-page'))
const ForYouPage   = lazy(() => import('../pages/recommendations/for-you-page'))
const MixEditorPage = lazy(() => import('../pages/mix/mix-editor-page'))
// ... todas las páginas usan lazy()
```
El bundle inicial es mínimo. El navegador descarga una página solo cuando
el usuario la visita, no al inicio.

**Generación asíncrona — `apps/songs/tasks.py`**
```python
@shared_task(bind=True, max_retries=2)
def process_generation_job(self, job_id: str):
```
La generación de audio (que tarda minutos) corre en **Celery**, no en el
request HTTP. El frontend hace polling cada 5 segundos. El servidor nunca
se bloquea esperando a Modal.

**Índices en base de datos — `apps/songs/models.py`**
```python
class Meta:
    indexes = [
        models.Index(fields=['user', 'status']),    # búsquedas por usuario
        models.Index(fields=['is_public', 'created_at']),  # feed público
    ]
```

**Guardado parcial — `apps/songs/tasks.py`**
```python
# Solo actualiza los campos que cambiaron, no hace UPDATE de toda la fila
song.save(update_fields=['audio_s3_key', 'thumbnail_s3_key', 'status', ...])
```

**Modelo ML cargado una sola vez — `ml/predictor.py`**
```python
_model_bundle: dict | None = None   # singleton en memoria

def _load_model() -> dict:
    global _model_bundle
    if _model_bundle is None:         # solo carga el .pkl la primera vez
        _model_bundle = joblib.load(MODEL_PATH)
    return _model_bundle
```

**Select related para evitar N+1 — `apps/songs/tasks.py`**
```python
job = GenerationJob.objects.select_related('user', 'song').get(id=job_id)
# Una sola consulta SQL en vez de 3
```

---

## 3. FIABLE
> *El sistema siempre trabaja correctamente. Tolera fallos sin caerse.*

### Qué decir
El sistema tiene múltiples capas de tolerancia a fallos: reintentos automáticos,
fallbacks cuando un servicio externo falla, transacciones atómicas y estados
de máquina que garantizan consistencia.

### Dónde mostrarlo

**Reintentos automáticos ante fallos de Modal — `apps/songs/tasks.py`**
```python
@shared_task(bind=True, max_retries=2)
def process_generation_job(self, job_id: str):
    ...
    except Exception as exc:
        raise self.retry(exc=exc, countdown=60)  # reintenta en 60s, máx 2 veces
```
Si Modal falla por red o timeout, Celery reintenta automáticamente.
El usuario no necesita volver a hacer clic.

**El crédito solo se descuenta si la generación fue exitosa — `apps/songs/tasks.py`**
```python
# 3. Llamar a Modal
response = call_modal_endpoint(endpoint_url, body)       # puede fallar

# 4. Guardar resultado
song.status = 'ready'
song.save(...)

# 6. Descontar crédito SOLO si fue exitoso ← línea 53
deduct_credits(job.user, amount=1, ...)
```

**Fallback si el modelo ML no está listo — `ml/predictor.py` + `views.py`**
```python
if is_model_available():
    pred = predict_from_description(desc)
    tag_names.update(pred['suggested_tags'])
# Si el .pkl no existe, las recomendaciones funcionan igual con el historial
```

**Transacciones atómicas — `apps/credits/services/credit_service.py`**
```python
with transaction.atomic():
    user.credit_balance -= amount
    user.save(update_fields=["credit_balance"])
    CreditTransaction.objects.create(...)  # si esto falla, revierte el balance
```

**Soft delete — `apps/core/models.py`**
```python
def soft_delete(self):
    self.deleted_at = timezone.now()
    self.save(update_fields=['deleted_at'])   # nunca borra datos de la DB
```
Las canciones "eliminadas" quedan en la DB con `deleted_at` marcado.
Nunca se pierde información del usuario.

**SSL obligatorio para la DB — `config/settings.py`**
```python
'OPTIONS': {
    'sslmode': 'require',   # la conexión a Neon siempre es cifrada
},
'CONN_HEALTH_CHECKS': True,  # detecta conexiones muertas automáticamente
```

**Máquina de estados de la canción — `apps/songs/models.py`**
```
draft → queued → processing → ready
                           → failed
                           → no_credits
```
La canción nunca queda en un estado ambiguo. Siempre sabe exactamente
en qué punto está el proceso.

---

## 4. FÁCIL DE USAR
> *El usuario aprende y usa el sistema sin necesidad de manual.*

### Qué decir
El frontend guía al usuario paso a paso: explica qué hace cada modo,
muestra feedback en tiempo real, y nunca deja al usuario sin saber
qué está pasando.

### Dónde mostrarlo

**Tres modos con descripciones — `gm_frontend/src/pages/create/create-page.tsx`**
```typescript
const MODES = [
  { id: 'description', label: 'Solo Descripción',
    hint: 'La IA elige letra e instrumentos' },
  { id: 'exact_lyrics', label: 'Letra Exacta',
    hint: 'Tú escribes la letra completa' },
  { id: 'auto_lyrics', label: 'Letra Autogenerada',
    hint: 'Describes de qué trata, la IA redacta' },
]
```
Cada pestaña tiene una pista que explica qué va a pasar antes de que
el usuario haga clic.

**Feedback en tiempo real durante la generación**
```typescript
const STAGE_LABELS = {
  submitting: 'Enviando tu solicitud...',
  polling:    'Generando tu canción… esto puede tardar un minuto 🎶',
  ready:      '¡Lista!',
  no_credits: 'Créditos insuficientes',
  error:      'Ocurrió un error',
}
```
El usuario siempre sabe en qué estado está su solicitud.

**Suspense con loading intermedio — `gm_frontend/src/router/index.tsx`**
```typescript
function PageLoader() {
  return <div>Cargando...</div>
}
function withSuspense(element) {
  return <Suspense fallback={<PageLoader />}>{element}</Suspense>
}
```
Nunca aparece una pantalla en blanco al navegar.

**Créditos visibles en la pantalla de creación**
```typescript
<span className="text-primary text-xl font-black">
  {user?.credit_balance ?? 0}
</span>
```
El usuario sabe cuántos créditos tiene sin ir a otra pantalla.

**Selector de tags visual** — chips clickeables para género, mood y tempo.
No hace falta que el usuario sepa escribir un prompt técnico.

**Soporte multilenguaje** — el usuario elige español o inglés para la letra
y el tipo de voz (femenina, masculina, auto).

---

## 5. MANTENIBILIDAD
> *El sistema es fácil de escalar, modificar y ampliar con el tiempo.*

### Qué decir
El backend está organizado por dominios, usa una capa de servicios para
la lógica de negocio, y todos los secretos están en variables de entorno.
Se siguen los principios SOLID y se evitan los anti-patrones STUPID.

### Dónde mostrarlo

**Separación por dominios — `gm_backend/apps/`**
```
apps/
├── users/          ← autenticación y perfiles
├── songs/          ← generación y biblioteca
├── credits/        ← facturación y balance
├── recommendations/← recomendaciones ML
├── community/      ← feed público
├── stems/          ← separación de audio
├── playlists/      ← listas de reproducción
├── mix/            ← editor de mezclas
├── notifications/  ← push notifications
├── audit/          ← trazabilidad de acciones
└── reports/        ← reportes de administración
```
Cada app tiene una sola responsabilidad. Agregar una feature nueva
no requiere modificar otras apps.

**Clase base reutilizable — `apps/core/models.py`** (Principio DRY)
```python
class BaseModel(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, ...)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(null=True, blank=True)

    def soft_delete(self): ...
```
Song, GenerationJob, UserSubscription y otros heredan de BaseModel.
UUID como PK, timestamps y soft delete gratis para todos.

**Capa de servicios** — la lógica de negocio no vive en las vistas:
- `apps/songs/services/generation_service.py` → lógica de generación
- `apps/credits/services/credit_service.py` → lógica de créditos
- `apps/recommendations/services/profile_service.py` → lógica de perfil
- `ml/predictor.py` → inferencia ML

**Variables de entorno — `config/settings.py`**
```python
SECRET_KEY    = config('SECRET_KEY')
DB_PASSWORD   = config('DB_PASSWORD')
AWS_SECRET_ACCESS_KEY = config('AWS_SECRET_ACCESS_KEY')
MODAL_KEY     = config('MODAL_KEY')
STRIPE_SECRET_KEY = config('STRIPE_SECRET_KEY')
```
Cambiar de base de datos, bucket S3 o cuenta de Stripe no requiere
tocar el código — solo el archivo `.env`.

**Control de versiones de schema — migraciones Django**
Cada cambio al modelo tiene su migración numerada y reproducible.

---

### SOLID en el proyecto

| Principio | Cómo se aplica | Archivo |
|---|---|---|
| **S** — Single Responsibility | Cada app/servicio tiene una sola razón para cambiar | `apps/credits/services/credit_service.py` solo maneja créditos |
| **O** — Open/Closed | `BaseModel` se extiende sin modificarse | `apps/core/models.py` |
| **L** — Liskov | Los serializers de DRF se intercambian sin romper nada | `apps/songs/serializers.py` |
| **I** — Interface Segregation | Dos permisos separados en vez de uno genérico | `apps/core/permissions.py` → `IsAdmin` vs `IsOwnerOrAdmin` |
| **D** — Dependency Inversion | Las vistas llaman a servicios; los servicios no dependen de vistas | `views.py` llama a `generation_service.py` |

### STUPID — lo que se EVITA

| Anti-patrón | Cómo se evita |
|---|---|
| **S** — Singleton innecesario | Solo hay un singleton intencional: `_model_bundle` en `predictor.py` para no recargar el .pkl en cada request |
| **T** — Tight Coupling | Los servicios son funciones puras importables, no clases acopladas a las vistas |
| **U** — Untestable | Cada app tiene su `tests.py`; los servicios son funciones puras fáciles de testear |
| **P** — Premature Optimization | Las migraciones se agregan cuando se necesitan, no por adelantado |
| **I** — Indescriptive Naming | `deduct_credits`, `predict_from_description`, `process_generation_job` — nombres que se entienden solos |
| **D** — Duplication | `BaseModel` evita repetir `id`, `created_at`, `updated_at`, `soft_delete` en cada modelo |

---

## 6. SEGURIDAD E INTEGRIDAD
> *Los datos del usuario están protegidos y el acceso está controlado.*

### Qué decir
El sistema usa JWT con rotación y blacklist, todas las rutas requieren
autenticación por defecto, y hay permisos granulares por rol.
Además registra todas las acciones importantes en un log de auditoría.

### Dónde mostrarlo

**JWT como default en TODAS las rutas — `config/settings.py`**
```python
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',  # toda ruta requiere token
    ),
}
```
Si alguien intenta llamar a la API sin token, recibe `401 Unauthorized`.

**JWT con rotación y blacklist — `config/settings.py`**
```python
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME':  timedelta(hours=1),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS':  True,      # cada refresh genera un nuevo par
    'BLACKLIST_AFTER_ROTATION': True,    # el refresh viejo queda inválido
}
```

**Logout invalida el token — `apps/users/views.py`**
```python
class LogoutView(APIView):
    def post(self, request):
        token = RefreshToken(request.data.get("refresh"))
        token.blacklist()   # el token queda en la blacklist, no puede reusarse
```

**Validación de contraseñas — `config/settings.py`**
```python
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': '...UserAttributeSimilarityValidator'},  # no parecida al email
    {'NAME': '...MinimumLengthValidator'},            # mínimo 8 caracteres
    {'NAME': '...CommonPasswordValidator'},           # no "123456" ni "password"
    {'NAME': '...NumericPasswordValidator'},          # no solo números
]
```

**Permisos granulares — `apps/core/permissions.py`**
```python
class IsAdmin(BasePermission):
    """Solo usuarios con rol 'admin' o staff de Django."""
    def has_permission(self, request, view):
        return request.user.is_staff or request.user.user_roles.filter(
            role__name='admin'
        ).exists()

class IsOwnerOrAdmin(BasePermission):
    """Solo el dueño del objeto, o un admin, puede acceder."""
    def has_object_permission(self, request, view, obj):
        return request.user.is_staff or obj.user_id == request.user.id
```
Un usuario no puede ver ni modificar canciones o datos de otro usuario.

**Log de auditoría — `apps/audit/models.py`**
```python
class AuditLog(models.Model):
    user          = models.ForeignKey(...)
    action        = models.CharField(...)   # 'song.generate', 'credits.purchase'
    resource_type = models.CharField(...)
    ip_address    = models.CharField(...)
    details       = models.JSONField(...)
    created_at    = models.DateTimeField(auto_now_add=True)
```
Toda acción sensible queda registrada con quién la hizo, desde qué IP y cuándo.

**Transacciones atómicas en créditos — `apps/credits/services/credit_service.py`**
```python
with transaction.atomic():
    user.credit_balance -= amount
    user.save(...)
    CreditTransaction.objects.create(...)
```
Nunca puede quedar el balance descontado sin el registro de la transacción,
ni el registro creado sin el descuento. O los dos, o ninguno.

**Conexión DB cifrada — `config/settings.py`**
```python
'OPTIONS': {'sslmode': 'require'}   # TLS obligatorio a Neon
```

**Autenticación con Modal — `ml/modal_client.py`**
```python
headers={
    "Modal-Key":    settings.MODAL_KEY,
    "Modal-Secret": settings.MODAL_SECRET,
}
```
Las credenciales de Modal vienen del `.env`, nunca están en el código.

**URLs de S3 firmadas y temporales — `ml/modal_client.py`**
```python
s3.generate_presigned_url(
    "get_object",
    Params={"Bucket": ..., "Key": s3_key},
    ExpiresIn=3600,   # la URL expira en 1 hora
)
```
Nadie puede guardar la URL de una canción y acceder a ella para siempre.

---

## 7. PORTABILIDAD
> *El sistema funciona en distintos entornos sin requerir versiones separadas por SO.*

### Qué decir
El frontend compila a archivos estáticos que corren en cualquier navegador.
El backend es una API REST que puede desplegarse en cualquier plataforma.
Ninguna pieza depende del sistema operativo de la máquina.

### Dónde mostrarlo

**Frontend — `gm_frontend/` (React + Vite)**
- Compila a HTML + CSS + JS estático
- Corre en Chrome, Firefox, Safari, Edge — cualquier OS
- No requiere instalación del lado del usuario

**Backend — Django REST API**
- Puede desplegarse en Railway, Render, Heroku, AWS, VPS Linux, o Windows Server
- No usa nada específico del OS

**Configuración por entorno — `config/settings.py`**
```python
# Todo viene del .env, no hay valores hardcodeados que "solo funcionen en mi máquina"
SECRET_KEY    = config('SECRET_KEY')
DB_HOST       = config('DB_HOST')
REDIS_URL     = config('REDIS_URL')
AWS_ACCESS_KEY_ID = config('AWS_ACCESS_KEY_ID')
```
El mismo código corre en la laptop de desarrollo, en el servidor de staging
y en producción, solo cambiando el `.env`.

**Base de datos en la nube — Neon PostgreSQL**
Cualquier integrante del equipo se conecta a la misma DB desde su máquina
(Windows, Mac o Linux) usando la URL de conexión.

**Almacenamiento en la nube — AWS S3**
Las canciones no se guardan en el disco del servidor.
Si el servidor cambia, los archivos siguen en S3.

**Workers independientes — Celery + Redis**
Los workers de Celery pueden correr en una máquina diferente al servidor web.
Se escalan horizontalmente agregando más workers sin tocar el código.

**IA en la nube — Modal**
ACE-Step corre en la infraestructura de Modal, no necesita GPU local.
El backend solo hace una llamada HTTP, funciona desde cualquier máquina.

---

## Tabla resumen para la defensa

| Factor | Evidencia principal en el código |
|---|---|
| Correcto | `generation_service.py` — 3 modos, validación de créditos, flujo completo |
| Eficiente | `router/index.tsx` — lazy loading; `tasks.py` — Celery async; `models.py` — indexes |
| Fiable | `tasks.py` — retry + status machine; `credit_service.py` — atomic; `predictor.py` — fallback |
| Fácil de uso | `create-page.tsx` — 3 modos con hints, tag picker, polling feedback, credits visibles |
| Mantenibilidad | `apps/` por dominio; `core/models.py` BaseModel; servicios separados; `.env` via decouple |
| Seguridad e Integridad | `settings.py` JWT + blacklist; `permissions.py` IsAdmin/IsOwner; `audit/models.py` AuditLog |
| Portabilidad | React SPA → cualquier browser; Django REST → cualquier server; todo config via `.env` |
