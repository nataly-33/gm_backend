# Módulo ML — Modelo Local + ACE-Step vía API

> Documento de defensa técnica.  
> Responde directamente las dos preguntas del Ing. Martínez.

---

## Las dos preguntas del ingeniero

### ¿La aplicación usa una llamada a una API de IA?

**Sí.** Cuando el usuario genera una canción, el backend llama a **ACE-Step** corriendo en Modal (infraestructura en la nube). Esa llamada HTTP POST desde `ml/modal_client.py` es la "API de IA". ACE-Step es el modelo de generación de audio.

Archivo: `ml/modal_client.py` → función `call_modal_endpoint()`  
Endpoint configurado en `settings.py` → `MODAL_ENDPOINT_FROM_DESCRIPTION`, etc.

### ¿La aplicación usa algo más que esa llamada, es decir un modelo local?

**Sí.** La aplicación tiene un **clasificador propio** entrenado con datos sintéticos (`music_classifier.pkl`). Este modelo se ejecuta 100% en el servidor Django, sin llamadas externas. Su rol es **potenciar las recomendaciones**: analiza las canciones que el usuario describió y predice qué géneros y moods le interesan para recomendarle canciones de otros usuarios.

Archivo: `ml/predictor.py` → función `predict_from_description()`  
Usado en: `apps/recommendations/views.py` → `ForYouView` y `SuggestedTagsView`

---

## Flujo 1 — Generación de música (API de IA: ACE-Step)

```
Usuario llena el formulario en el frontend
        ↓
POST /songs/generate/
        ↓
apps/songs/services/generation_service.py
  · Valida créditos
  · Crea Song + GenerationJob en DB
  · Encola tarea Celery: process_generation_job
        ↓
apps/songs/tasks.py → process_generation_job
  · Construye el payload según el modo (descripción / letra exacta / letra descrita)
  · Llama a ml/modal_client.py → call_modal_endpoint()
        ↓
ml/modal_client.py
  · HTTP POST autenticado al endpoint de Modal
  · Timeout: 600 s (ACE-Step puede tardar varios minutos)
        ↓
Modal Cloud → ml/modal_music_server.py (ACE-Step)
  · Genera el audio WAV
  · Crea portada (thumbnail)
  · Sube ambos archivos a S3
  · Retorna: { s3_key, cover_image_s3_key, lyrics, categories }
        ↓
tasks.py guarda s3_key, thumbnail_s3_key, status='ready' en la Song
El frontend hace polling a /songs/jobs/{id}/ hasta que status='ready'
```

### Modos de generación (determinados por el payload)

| Modo frontend | Campo enviado | Endpoint Modal | Qué hace ACE-Step |
|---|---|---|---|
| Solo Descripción | `description` | `MODAL_ENDPOINT_FROM_DESCRIPTION` | La IA elige letra e instrumentos |
| Letra Exacta | `prompt` + `lyrics` | `MODAL_ENDPOINT_WITH_LYRICS` | Canta exactamente la letra dada |
| Letra Autogenerada | `prompt` + `described_lyrics` | `MODAL_ENDPOINT_FROM_DESCRIBED_LYRICS` | La IA redacta la letra basándose en la descripción |

---

## Flujo 2 — Recomendaciones (Modelo local: music_classifier.pkl)

```
Usuario abre la página "Para ti"
        ↓
GET /recommendations/for-you/
        ↓
apps/recommendations/views.py → ForYouView.get()

  SEÑAL 1: Historial de escucha
    · Busca UserTasteProfile del usuario
    · Extrae top_tags (géneros/moods que más escuchó)

  SEÑAL 2: Predicción ML (modelo local .pkl)
    · Toma hasta 5 descripciones de canciones que el usuario creó
    · Para cada descripción llama: ml/predictor.py → predict_from_description()
    · El modelo predice: género, mood, tempo
    · Agrega esos tags al conjunto de preferencias

  Combina ambas señales → conjunto de tag_names

        ↓
Filtra Song donde:
  · is_public=True, status='ready'
  · tags__name__in = {tag_names combinados}
  · user ≠ usuario actual  ← canciones de OTROS usuarios
  · ordenadas por play_count desc
        ↓
Retorna hasta 20 canciones (serialized)
```

### ¿Qué pasa si el usuario no tiene historial ni descripciones?

Retorna las 20 canciones públicas más reproducidas, excluyendo las propias del usuario. Sin ML y sin historial, el fallback es popularidad global.

---

## El modelo local — cómo funciona por dentro

### Paso 1: Dataset sintético (`ml/dataset_generator.py`)

Genera un CSV de 3 millones de filas. Cada fila es un ejemplo de entrenamiento:

| description | genre | mood | tempo |
|---|---|---|---|
| "quiero algo triste de lofi" | lofi | sad | slow |
| "I need energetic techno for the gym" | techno | energetic | fast |
| "música romántica con influencias de jazz" | jazz | romantic | medium |

El generador combina plantillas en español e inglés con vocabularios de géneros, moods, adjetivos y contextos. Seed fija (42) → siempre produce el mismo dataset, reproducible.

Ejecutar: `python ml/dataset_generator.py`  
Salida: `ml/data/dataset_sintetico.csv` (~1 GB, en .gitignore)

### Paso 2: Entrenamiento (`ml/train_model.py`)

Entrena **3 clasificadores independientes** (uno por target):

```
TF-IDF (texto → vector numérico)
    ↓
RandomForestClassifier
    ↓
Predice: género | mood | tempo
```

- Usa 500k filas de muestra (representativa del dataset de 3M)
- Split 80/20 para evaluación
- Genera `ml/TRAINING_REPORT.md` con accuracy, precision, recall por clase

Ejecutar después del generador: `python ml/train_model.py`  
Salida: `ml/models/music_classifier.pkl` (en .gitignore)

### Paso 3: Inferencia (`ml/predictor.py`)

Carga el `.pkl` una sola vez al arrancar Django (singleton). Expone:

```python
predict_from_description("quiero algo triste de lofi")
# Retorna:
{
  'genre':          'lofi',
  'mood':           'sad',
  'tempo':          'slow',
  'bpm_range':      (60, 90),
  'suggested_tags': ['lofi', 'sad', 'slow'],
  'confidence': {
    'genre': 0.87,
    'mood':  0.92,
    'tempo': 0.78,
  }
}
```

Si el `.pkl` no existe, `is_model_available()` retorna `False` y las recomendaciones funcionan igual usando solo el historial de escucha.

---

## Qué hace cada archivo de `ml/`

| Archivo | Rol | ¿Se usa en producción? |
|---|---|---|
| `dataset_generator.py` | Genera el CSV de entrenamiento | No (script manual, una vez) |
| `train_model.py` | Entrena y guarda el `.pkl` | No (script manual, una vez) |
| `predictor.py` | Carga el `.pkl` y clasifica descripciones | **Sí** — llamado en recomendaciones |
| `modal_client.py` | HTTP client para llamar a ACE-Step en Modal | **Sí** — llamado en cada generación |
| `modal_music_server.py` | Servidor ACE-Step desplegado en Modal | Corre en la nube (Modal) |
| `prompts.py` | Plantillas de prompt para ACE-Step | **Sí** — usado por el servidor Modal |
| `TRAINING_REPORT.md` | Métricas de accuracy del modelo | Referencia/documentación |
| `models/music_classifier.pkl` | Modelo entrenado | **Sí** — cargado por `predictor.py` |
| `data/dataset_sintetico.csv` | Dataset de entrenamiento | No (se regenera) |

---

## Cómo se ve desde el frontend

### Página "Para ti" (`/recommendations`)

1. Al abrir: llama a `GET /recommendations/for-you/` → backend corre el modelo + historial
2. Muestra chips de "Tus géneros detectados" (combina historial + predicciones ML)
3. Muestra grilla de canciones de **otros usuarios** que coincidan con esos géneros/moods
4. Botón **"Actualizar"** (esquina superior derecha): vuelve a llamar al endpoint para refrescar — útil cuando otros usuarios publican canciones nuevas
5. Si no hay recomendaciones todavía: mensaje "Crea canciones con descripción libre para que el modelo aprenda tus gustos"

### Página "Crear canción" (`/create`)

- La pestaña **"Solo Descripción"** guarda el texto en el campo `description` de la Song
- Esas descripciones son la materia prima que el modelo ML analiza después para las recomendaciones
- La generación en sí la hace ACE-Step vía Modal (sin intervención del modelo local)

---

## Qué va en `.gitignore`

```
ml/data/
ml/models/*.pkl
```

## Cómo regenerar el modelo

```bash
# 1. Generar el dataset sintético (~1 GB, ~5-10 minutos)
python ml/dataset_generator.py

# 2. Entrenar el modelo (~3-5 minutos)
python ml/train_model.py

# 3. Aplicar la migración de DB si es necesario
python manage.py migrate
```

---

## Resumen para la defensa

| Pregunta | Respuesta | Archivo clave |
|---|---|---|
| ¿Usa API de IA? | Sí — ACE-Step en Modal genera el audio | `ml/modal_client.py`, `ml/modal_music_server.py` |
| ¿Usa modelo local? | Sí — RandomForest entrenado con datos sintéticos potencia las recomendaciones | `ml/predictor.py`, `ml/train_model.py` |
| ¿Datos propios? | Sí — 3 millones de filas generadas con `dataset_generator.py` | `ml/dataset_generator.py` |
| ¿El modelo es decorativo? | No — sin él las recomendaciones solo usan historial; con él también infiere gustos de las descripciones | `apps/recommendations/views.py` |
| ¿Dónde se ven los resultados? | Página "Para ti" — géneros detectados + canciones recomendadas | `gm_frontend/.../for-you-page.tsx` |
