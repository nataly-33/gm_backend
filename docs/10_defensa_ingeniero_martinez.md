# Defensa ante el Ing. Martínez — Guía Completa

> Documento generado para la defensa final del proyecto **Generación Musical IA**.
> Cubre las 5 preguntas conocidas del ingeniero + estrategia de puntuación.

---

## Puntuación objetivo: **80 / 100**

| Pregunta | Título | ¿Lo tenemos? | Puntos |
|---|---|---|---|
| P1 | ¿El proyecto está completo? | ✅ Sí | base |
| P2 | ¿La IA va más allá de un chatbot? | ✅ Sí (ACE-Step + RandomForest) | base |
| P3 | ¿Está en producción con calidad? | ✅ Sí (Neon + Modal + 7 factores) | base |
| P4 | ¿Usan modelos de IA locales? | ✅ Sí (RandomForest .pkl + Whisper) | +20 puntos |
| P5 | ¿Tienen documentación SCRUM/UML 2.5? | según sprint docs | extra |

---

## PREGUNTA 1 — ¿El proyecto está completo?

### Qué decir
"El sistema tiene backend Django REST + frontend React/Vite desplegados. Un usuario puede registrarse, consumir créditos, generar canciones con IA, verlas en su biblioteca, escucharlas con letra sincronizada, publicarlas a la comunidad, y recibir recomendaciones personalizadas. Todas las funcionalidades están integradas end-to-end."

### Qué mostrar
1. **Flujo completo en vivo**: Login → `/create` → polling de generación → `/library` → reproducir canción → ver letra sincronizada.
2. **Django Admin** (`/admin/`): canciones, créditos, audit logs, tags — todo poblado.
3. **Notificaciones in-app** al completar generación.

### Archivos clave a mencionar
- `gm_backend/apps/songs/tasks.py` — orquestación completa del proceso de generación
- `gm_frontend/src/pages/create/create-page.tsx` — tres modos (description / exact_lyrics / auto_lyrics)
- `gm_frontend/src/router/index.tsx` — todas las rutas de la aplicación

---

## PREGUNTA 2 — ¿La IA va más allá de un chatbot / matching learning?

### Qué decir
"Tenemos **dos sistemas de IA distintos** que van mucho más allá de un chatbot:

**Sistema 1 — Generación musical (ACE-Step, modelo externo):**
ACE-Step es un modelo de difusión entrenado específicamente para componer música. No responde preguntas de texto; genera audio WAV completo a partir de una descripción o letra. Es equivalente a Stable Diffusion pero para música.


### Qué mostrar
5. Mostrar `gm_backend/ml/modal_client.py` → `call_modal_endpoint()` que llama a ACE-Step.

### Argumento diferenciador
> "Un chatbot solo retorna texto. Nosotros generamos audio de 3 minutos y clasificamos géneros musicales con un modelo entrenado localmente. Eso es machine learning aplicado, no un chatbot."

---

## PREGUNTA 3 — ¿Está en producción con los factores de calidad del software?

### Qué decir
"El sistema está desplegado en producción real:
- **Base de datos**: PostgreSQL en Neon (cloud, SSL requerido)
- **Cola de tareas**: Celery + Redis para procesamiento asíncrono
- **Audio / storage**: AWS S3 para archivos generados
- **GPU cloud**: Modal para ejecutar ACE-Step

En cuanto a los 7 factores de calidad (ver doc `08_calidad_software.md`):"

### Los 7 factores — respuestas rápidas

| Factor | Evidencia en código |
|---|---|
| **Correcto** | Tests end-to-end documentados; `validate()` en serializers; `SongGenerateSerializer` valida los 3 modos |
| **Eficiente** | `lazy(() => import(...))` en todas las páginas; Celery async para no bloquear requests; `select_related` en ORM |
| **Fiable** | `@shared_task(max_retries=2, countdown=60)` — reintentos automáticos; crédito descontado SOLO tras éxito |
| **Fácil de usar** | UI React con feedback en tiempo real; `STAGE_LABELS` en create-page; notificaciones push FCM |
| **Mantenibilidad** | SOLID aplicado: `generation_service.py` SRP; `IsOwnerOrAdmin` OCP; `BaseModel` DRY |
| **Seguridad e Integridad** | JWT con blacklist en logout; `IsAuthenticated` por defecto; `AuditLog` por acción; SSL en Neon |
| **Portabilidad** | Docker-ready; variables de entorno via `decouple`; sin hardcoding de URLs o secrets |

### Archivos para mostrar en defensa
- `gm_backend/config/settings.py` → `sslmode: 'require'`, `BLACKLIST_AFTER_ROTATION`
- `gm_backend/apps/core/models.py` → `BaseModel` con soft delete
- `gm_backend/apps/audit/models.py` → `AuditLog`
- `gm_backend/apps/credits/services/credit_service.py` → `transaction.atomic()`
- `gm_backend/apps/users/views.py` → `token.blacklist()`

---

## PREGUNTA 4 — ¿Usan modelos de IA locales?

Esta es la pregunta que sube de 60 a 80 puntos. Tenemos **dos respuestas** sólidas.

### Argumento A — RandomForest .pkl (modelo local, ya funcionando)

**Qué decir:**
"Tenemos un modelo Random Forest con TF-IDF entrenado localmente. El archivo `music_classifier.pkl` se carga en memoria al iniciar el servidor Django y clasifica canciones en tiempo real. No hay llamada a ninguna API externa — todo corre en nuestra máquina/servidor."

**Qué mostrar:**
```
gm_backend/ml/
├── music_classifier.pkl        ← el modelo serializado (varios MB)
├── predictor.py                ← predict_from_description(), is_model_available()
├── train_classifier.py         ← cómo se entrenó con datos sintéticos
└── generate_training_data.py   ← los 3M de filas sintéticas
```

Abrir `predictor.py` y mostrar que carga `joblib.load('music_classifier.pkl')` — sin API, sin internet, puro Python local.

---

### Argumento B — OpenAI Whisper (modelo de IA local, ya en código)

**Qué decir:**
"También integramos OpenAI Whisper, un modelo transformer de 74 millones de parámetros que transcribe audio a texto con timestamps precisos. Está en nuestro `requirements.txt` y corre completamente offline — no usa la API de OpenAI, usa los pesos del modelo descargados localmente."

**Qué mostrar:**
1. `requirements.txt` → línea `openai-whisper==20250625`
2. `gm_backend/apps/songs/tasks.py` línea 157 → `import whisper; model = whisper.load_model('base')`
3. El resultado: letra sincronizada en `/library` cuando se reproduce una canción (vista "Letra")

**Cómo funciona el flujo completo:**
```
Canción generada → audio guardado en S3
       ↓
compute_lyrics_timestamps.delay(song_id)   [tarea Celery async]
       ↓
Descarga audio de S3
       ↓
whisper.load_model('base').transcribe(audio)  [74M parámetros, offline]
       ↓
[{start: 0.5, end: 2.1, text: "primera línea"}, ...]
       ↓
Song.lyrics_timestamps = timestamps    [guardado en PostgreSQL]
       ↓
Frontend lee lyrics_timestamps via API  [GET /api/songs/{id}/detail/]
       ↓
Letra sincronizada en tiempo real con el audio ✅
```

**Por qué ffmpeg es necesario:**
Whisper es una red neuronal que procesa muestras de audio en crudo (arrays de floats). Para leer un archivo MP3 o WAV, necesita que **ffmpeg** decodifique el archivo primero. Es como necesitar Pillow para que PIL pueda abrir imágenes antes de procesarlas. Sin ffmpeg, Whisper no puede leer el archivo de audio.

**Para instalar ffmpeg en Windows:**
```powershell
winget install --id Gyan.FFmpeg
# luego reiniciar terminal
```

---

### Recomendación para la defensa

Presentar **ambos modelos**: el RandomForest como "ya en producción" y Whisper como "ya implementado, se activa con ffmpeg". Si pueden demostrar la letra sincronizada en vivo, mejor.

Para verificar que Whisper está corriendo en una canción existente, ejecutar desde Django shell:
```python
# python manage.py shell
from apps.songs.tasks import compute_lyrics_timestamps
compute_lyrics_timestamps('uuid-de-una-cancion-existente')
```

Luego abrir esa canción en `/library`, reproducirla y abrir "Letra" — debe sincronizar con el audio real.

---

## PREGUNTA 5 — ¿Tienen documentación SCRUM/UML 2.5?

### Si tienen los documentos
Mostrar directamente:
- Sprints del proyecto (ver `docs/01_division_trabajo.md`, `06_division_trabajo_sprint23.md`, `09_division_trabajo_sprint4.md`)
- Diagramas UML 2.5 si los tienen: casos de uso, diagrama de clases, secuencia
- Historias de usuario y backlog

### Argumentos para SCRUM
"Trabajamos con sprints definidos. Cada sprint tiene división de trabajo documentada (ver docs de sprints). Usamos branches por feature, PRs para revisión, y reuniones de sincronización."

### Argumentos para UML 2.5
Si tienen diagramas, mostrar:
- **Diagrama de clases**: `BaseModel → Song, User, AuditLog, Credits`
- **Diagrama de secuencia**: flujo de generación (Usuario → Frontend → Django → Celery → Modal → S3 → DB)
- **Caso de uso**: actores (Usuario, Admin, Sistema Celery, Modal GPU)

---

## Tabla resumen de evidencia técnica

| Concepto | Archivo | Línea/sección |
|---|---|---|
| ACE-Step (generación IA) | `ml/modal_client.py` | `call_modal_endpoint()` |
| RandomForest local | `ml/predictor.py` | `predict_from_description()` |
| Whisper local | `apps/songs/tasks.py` | línea 157-176 |
| Sincronización de letra | `components/song/lyrics-view.tsx` | useEffect línea 69 |
| Créditos atómicos | `credits/services/credit_service.py` | `transaction.atomic()` |
| Reintentos Celery | `apps/songs/tasks.py` | `max_retries=2, countdown=60` |
| Soft delete | `core/models.py` | `BaseModel.soft_delete()` |
| JWT blacklist | `apps/users/views.py` | `token.blacklist()` |
| Audit log | `apps/audit/models.py` | `AuditLog` |
| Lazy loading React | `router/index.tsx` | `lazy(() => import(...))` |
| SSL producción | `config/settings.py` | `sslmode: 'require'` |
| Recomendaciones ML | `recommendations/views.py` | bloque `is_model_available()` |

---

## Script de defensa (5 minutos)

**Apertura (30s):**
"Nuestra aplicación permite generar canciones originales con IA, escucharlas con letra sincronizada por Whisper, y recibir recomendaciones personalizadas por un modelo de machine learning local. Todo en producción."

**Demo en vivo (2 min):**
1. Mostrar `/create` — los 3 modos de generación
2. Mostrar `/library` — reproducir una canción, abrir "Letra" → sincronización en tiempo real
3. Mostrar `/for-you` — "recomendado por el modelo musical"

**Respuesta a IA local (1 min):**
"Tenemos dos modelos locales: RandomForest para recomendaciones (ya en producción) y Whisper para sincronización de letra (implementado, requiere ffmpeg). Ambos corren sin API externa."

**Calidad (1 min):**
"JWT con blacklist, soft delete, audit log, créditos atómicos, reintentos automáticos en Celery, lazy loading en React. Ver doc `08_calidad_software.md` para cada factor con el archivo y línea exacta."

**Cierre (30s):**
"El proyecto está completo, en producción real con PostgreSQL en Neon, Cola Celery con Redis, Storage en S3 y GPU en Modal. Los 7 factores de calidad están implementados y documentados."
