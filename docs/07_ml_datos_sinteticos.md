# Módulo ML — Datos Sintéticos + Modelo .pkl
> Satisface el requisito del Ing. Martínez de ML propio con datos sintéticos  
> Se integra con ACE-Step: el modelo predice parámetros ANTES de llamar a Modal  
> Le sirve a Nicol para mejorar las recomendaciones

---

## Flujo completo con ML propio + ACE-Step

```
Descripción del usuario
        ↓
[ml/predictor.py — carga music_classifier.pkl]
  → predice: género, mood, BPM estimado, tags sugeridos
        ↓
Esos parámetros se pasan a ACE-Step en Modal
        ↓
ACE-Step genera el audio con parámetros optimizados
        ↓
[ml/predictor.py — valida resultado]
  → confirma que los tags generados coinciden con la predicción
        ↓
Canción guardada con tags validados
```

El modelo propio tiene un rol real: **optimiza los parámetros de ACE-Step** y **valida el resultado**. No es decorativo.

---

## Archivos a crear

```
gm-backend/
└── ml/
    ├── data/
    │   └── dataset_sintetico.csv      ← ~1GB, generado por dataset_generator.py
    ├── models/
    │   └── music_classifier.pkl       ← modelo entrenado, generado por train_model.py
    ├── dataset_generator.py           ← genera el dataset sintético
    ├── train_model.py                 ← entrena y guarda el .pkl
    ├── predictor.py                   ← carga el .pkl y expone predict_from_description()
    ├── TRAINING_REPORT.md             ← documenta accuracy, precision, recall
    ├── modal_music_server.py          ← ya existe (del ZIP)
    ├── modal_client.py                ← ya existe
    └── prompts.py                     ← ya existe (del ZIP)
```

> El `dataset_sintetico.csv` y `music_classifier.pkl` van en `.gitignore`.  
> Se regeneran corriendo los scripts. Solo se commitea el código, no los datos ni el modelo.  
> En el documento del proyecto se explica cómo regenerarlos: `python ml/dataset_generator.py && python ml/train_model.py`

---

## Paso 1 — Generar el dataset sintético

### `ml/dataset_generator.py`

```python
"""
Generador de dataset sintético para entrenamiento del modelo de clasificación musical.
Genera ~3 millones de filas → aproximadamente 1GB en CSV.
Ejecutar: python ml/dataset_generator.py
"""
import csv
import random
import os
from pathlib import Path

random.seed(42)  # Reproducible: misma seed → mismo dataset siempre

# ── Vocabulario de plantillas ───────────────────────────────────────────────

DESCRIPTION_TEMPLATES_ES = [
    "quiero una canción {mood_adj} de {genre}",
    "necesito algo {mood_adj} para {context}",
    "una canción {tempo_adj} que transmita {emotion}",
    "música {genre} con ritmo {tempo_adj} y ambiente {mood_adj}",
    "quiero algo que suene a {genre}, {mood_adj} y {tempo_adj}",
    "canción para {context}, estilo {genre}, que sea {mood_adj}",
    "algo {mood_adj} con influencias de {genre}",
    "una melodía {tempo_adj} de {genre} con letra sobre {topic}",
]

DESCRIPTION_TEMPLATES_EN = [
    "I want a {mood_adj} {genre} song",
    "something {mood_adj} for {context}",
    "a {tempo_adj} track that transmits {emotion}",
    "{genre} music with a {tempo_adj} rhythm and {mood_adj} vibe",
    "I need something that sounds like {genre}, {mood_adj} and {tempo_adj}",
    "a song for {context}, {genre} style, {mood_adj}",
    "something {mood_adj} with {genre} influences",
    "a {tempo_adj} {genre} melody about {topic}",
]

GENRES = ['reggaeton', 'lofi', 'techno', 'pop', 'rock', 'hip-hop', 'jazz',
          'classical', 'salsa', 'cumbia', 'electronic', 'r&b', 'country', 'folk']

MOODS = ['sad', 'happy', 'energetic', 'chill', 'romantic', 'angry', 'nostalgic', 'hopeful']

MOOD_ADJ_MAP = {
    'sad':       ['triste', 'melancólica', 'sad', 'melancholic', 'heartbreaking'],
    'happy':     ['alegre', 'feliz', 'happy', 'joyful', 'upbeat'],
    'energetic': ['energética', 'potente', 'energetic', 'powerful', 'intense'],
    'chill':     ['relajante', 'tranquila', 'chill', 'relaxing', 'calm'],
    'romantic':  ['romántica', 'amorosa', 'romantic', 'loving', 'tender'],
    'angry':     ['intensa', 'fuerte', 'angry', 'aggressive', 'raw'],
    'nostalgic': ['nostálgica', 'retro', 'nostalgic', 'vintage', 'throwback'],
    'hopeful':   ['esperanzadora', 'motivadora', 'hopeful', 'uplifting', 'inspiring'],
}

TEMPO_ADJ = {
    'slow':   ['lenta', 'pausada', 'slow', 'mellow', 'laid-back'],
    'medium': ['moderada', 'fluida', 'moderate', 'steady', 'flowing'],
    'fast':   ['rápida', 'veloz', 'fast', 'quick', 'uptempo'],
}

BPM_RANGES = {
    'slow':   (60, 90),
    'medium': (90, 120),
    'fast':   (120, 160),
}

CONTEXTS = ['trabajar', 'estudiar', 'el gym', 'una fiesta', 'relajarme',
            'work', 'study', 'the gym', 'a party', 'relaxing', 'a workout',
            'una cena romántica', 'conducir', 'meditar', 'bailar']

EMOTIONS = ['alegría', 'tristeza', 'nostalgia', 'esperanza', 'amor',
            'joy', 'sadness', 'nostalgia', 'hope', 'love', 'power', 'peace']

TOPICS = ['el amor perdido', 'la libertad', 'el verano', 'la ciudad de noche',
          'lost love', 'freedom', 'summer', 'the city at night', 'growing up',
          'la amistad', 'el tiempo', 'los sueños', 'la vida', 'el futuro']

TAG_MAP = {
    'reggaeton': ['reggaeton', 'urban', 'latin'],
    'lofi':      ['lofi', 'chill', 'study'],
    'techno':    ['techno', 'electronic', 'dance'],
    'pop':       ['pop', 'commercial', 'radio'],
    'rock':      ['rock', 'guitar', 'band'],
    'hip-hop':   ['hip-hop', 'rap', 'urban'],
    'jazz':      ['jazz', 'instrumental', 'swing'],
    'classical': ['classical', 'orchestral', 'instrumental'],
    'salsa':     ['salsa', 'latin', 'tropical'],
    'cumbia':    ['cumbia', 'latin', 'tropical'],
    'electronic':['electronic', 'synth', 'edm'],
    'r&b':       ['r&b', 'soul', 'smooth'],
    'country':   ['country', 'folk', 'acoustic'],
    'folk':      ['folk', 'acoustic', 'indie'],
}


def generate_description(genre: str, mood: str, tempo: str) -> str:
    templates = DESCRIPTION_TEMPLATES_ES + DESCRIPTION_TEMPLATES_EN
    template = random.choice(templates)
    return template.format(
        genre=genre,
        mood_adj=random.choice(MOOD_ADJ_MAP[mood]),
        tempo_adj=random.choice(TEMPO_ADJ[tempo]),
        context=random.choice(CONTEXTS),
        emotion=random.choice(EMOTIONS),
        topic=random.choice(TOPICS),
    )


def generate_row(genre: str, mood: str, tempo: str) -> dict:
    bpm_min, bpm_max = BPM_RANGES[tempo]
    bpm = random.randint(bpm_min, bpm_max)
    tags = TAG_MAP.get(genre, [genre]) + [mood, tempo]
    tags = list(set(tags))  # eliminar duplicados
    instrumental = random.random() < 0.2  # 20% instrumental

    return {
        'description': generate_description(genre, mood, tempo),
        'genre': genre,
        'mood': mood,
        'tempo': tempo,
        'bpm': bpm,
        'tags': '|'.join(tags),  # separados por pipe para CSV
        'instrumental': int(instrumental),
        'duration_seconds': random.randint(60, 240),
    }


def generate_dataset(output_path: str, target_rows: int = 3_000_000):
    print(f"Generando {target_rows:,} filas en {output_path}...")
    os.makedirs(Path(output_path).parent, exist_ok=True)

    fieldnames = ['description', 'genre', 'mood', 'tempo', 'bpm', 'tags', 'instrumental', 'duration_seconds']
    tempos = list(BPM_RANGES.keys())

    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        for i in range(target_rows):
            genre = random.choice(GENRES)
            mood = random.choice(MOODS)
            tempo = random.choice(tempos)
            writer.writerow(generate_row(genre, mood, tempo))

            if (i + 1) % 100_000 == 0:
                size_mb = os.path.getsize(output_path) / (1024 * 1024)
                print(f"  {i+1:,} filas escritas — {size_mb:.1f} MB")

    size_gb = os.path.getsize(output_path) / (1024 ** 3)
    print(f"\nDataset generado: {output_path} ({size_gb:.2f} GB)")


if __name__ == '__main__':
    generate_dataset('ml/data/dataset_sintetico.csv', target_rows=3_000_000)
```

---

## Paso 2 — Entrenar el modelo

### `ml/train_model.py`

```python
"""
Entrena el clasificador musical con el dataset sintético.
Genera ml/models/music_classifier.pkl
Ejecutar DESPUÉS de dataset_generator.py:
  python ml/train_model.py
"""
import pandas as pd
import numpy as np
import joblib
import os
from pathlib import Path
from sklearn.pipeline import Pipeline
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.ensemble import RandomForestClassifier
from sklearn.multioutput import MultiOutputClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report
from sklearn.preprocessing import LabelEncoder

DATA_PATH   = 'ml/data/dataset_sintetico.csv'
OUTPUT_DIR  = 'ml/models'
MODEL_PATH  = f'{OUTPUT_DIR}/music_classifier.pkl'
REPORT_PATH = 'ml/TRAINING_REPORT.md'

print("Cargando dataset...")
# Cargar solo 500k filas para entrenamiento rápido (muestra representativa)
df = pd.read_csv(DATA_PATH, nrows=500_000)
print(f"  {len(df):,} filas cargadas")

X = df['description'].values

# Encoders para cada target
genre_encoder = LabelEncoder().fit(df['genre'])
mood_encoder  = LabelEncoder().fit(df['mood'])
tempo_encoder = LabelEncoder().fit(df['tempo'])

y_genre = genre_encoder.transform(df['genre'])
y_mood  = mood_encoder.transform(df['mood'])
y_tempo = tempo_encoder.transform(df['tempo'])

# Split
X_train, X_test, yg_train, yg_test, ym_train, ym_test, yt_train, yt_test = train_test_split(
    X, y_genre, y_mood, y_tempo, test_size=0.2, random_state=42
)

print("Entrenando modelo de género...")
genre_pipeline = Pipeline([
    ('tfidf', TfidfVectorizer(max_features=10_000, ngram_range=(1, 2))),
    ('clf',   RandomForestClassifier(n_estimators=100, random_state=42, n_jobs=-1))
])
genre_pipeline.fit(X_train, yg_train)

print("Entrenando modelo de mood...")
mood_pipeline = Pipeline([
    ('tfidf', TfidfVectorizer(max_features=10_000, ngram_range=(1, 2))),
    ('clf',   RandomForestClassifier(n_estimators=100, random_state=42, n_jobs=-1))
])
mood_pipeline.fit(X_train, ym_train)

print("Entrenando modelo de tempo...")
tempo_pipeline = Pipeline([
    ('tfidf', TfidfVectorizer(max_features=5_000, ngram_range=(1, 2))),
    ('clf',   RandomForestClassifier(n_estimators=50, random_state=42, n_jobs=-1))
])
tempo_pipeline.fit(X_train, yt_train)

# Evaluar
genre_report = classification_report(yg_test, genre_pipeline.predict(X_test),
                                     target_names=genre_encoder.classes_)
mood_report  = classification_report(ym_test, mood_pipeline.predict(X_test),
                                     target_names=mood_encoder.classes_)
tempo_report = classification_report(yt_test, tempo_pipeline.predict(X_test),
                                     target_names=tempo_encoder.classes_)

print("\n=== Reporte Género ===")
print(genre_report)

# Guardar todo en el .pkl
os.makedirs(OUTPUT_DIR, exist_ok=True)
model_bundle = {
    'genre_pipeline':  genre_pipeline,
    'mood_pipeline':   mood_pipeline,
    'tempo_pipeline':  tempo_pipeline,
    'genre_encoder':   genre_encoder,
    'mood_encoder':    mood_encoder,
    'tempo_encoder':   tempo_encoder,
    'version': '1.0',
}
joblib.dump(model_bundle, MODEL_PATH)
print(f"\nModelo guardado en {MODEL_PATH} ({os.path.getsize(MODEL_PATH) / 1024 / 1024:.1f} MB)")

# Escribir reporte de entrenamiento
with open(REPORT_PATH, 'w') as f:
    f.write("# Training Report — music_classifier.pkl\n\n")
    f.write(f"Dataset: {DATA_PATH} (500k filas de muestra de 3M)\n\n")
    f.write("## Género\n```\n" + genre_report + "\n```\n\n")
    f.write("## Mood\n```\n" + mood_report + "\n```\n\n")
    f.write("## Tempo\n```\n" + tempo_report + "\n```\n\n")

print(f"Reporte guardado en {REPORT_PATH}")
```

---

## Paso 3 — Integrar en Django

### `ml/predictor.py`

```python
"""
Carga el modelo .pkl una sola vez al arrancar Django.
Expone predict_from_description() para usar en generation_service y recommendations.
"""
import joblib
from pathlib import Path
from functools import lru_cache

MODEL_PATH = Path(__file__).parent / 'models' / 'music_classifier.pkl'

_model_bundle = None

def _load_model():
    global _model_bundle
    if _model_bundle is None:
        if not MODEL_PATH.exists():
            raise FileNotFoundError(
                f"Modelo no encontrado en {MODEL_PATH}. "
                f"Ejecutar: python ml/train_model.py"
            )
        _model_bundle = joblib.load(MODEL_PATH)
    return _model_bundle


def predict_from_description(description: str) -> dict:
    """
    Dado el texto de descripción del usuario, predice los parámetros musicales.

    Retorna:
    {
        'genre':          'lofi',
        'mood':           'sad',
        'tempo':          'slow',
        'bpm_range':      (60, 90),
        'suggested_tags': ['lofi', 'sad', 'slow', 'chill'],
        'confidence': {
            'genre': 0.87,
            'mood':  0.92,
            'tempo': 0.78,
        }
    }
    """
    bundle = _load_model()
    X = [description]

    genre_pred  = bundle['genre_pipeline'].predict(X)[0]
    genre_proba = bundle['genre_pipeline'].predict_proba(X)[0].max()

    mood_pred  = bundle['mood_pipeline'].predict(X)[0]
    mood_proba = bundle['mood_pipeline'].predict_proba(X)[0].max()

    tempo_pred  = bundle['tempo_pipeline'].predict(X)[0]
    tempo_proba = bundle['tempo_pipeline'].predict_proba(X)[0].max()

    genre_name = bundle['genre_encoder'].inverse_transform([genre_pred])[0]
    mood_name  = bundle['mood_encoder'].inverse_transform([mood_pred])[0]
    tempo_name = bundle['tempo_encoder'].inverse_transform([tempo_pred])[0]

    BPM_RANGES = {'slow': (60, 90), 'medium': (90, 120), 'fast': (120, 160)}

    return {
        'genre': genre_name,
        'mood':  mood_name,
        'tempo': tempo_name,
        'bpm_range': BPM_RANGES.get(tempo_name, (90, 120)),
        'suggested_tags': list({genre_name, mood_name, tempo_name}),
        'confidence': {
            'genre': round(float(genre_proba), 3),
            'mood':  round(float(mood_proba), 3),
            'tempo': round(float(tempo_proba), 3),
        }
    }
```

### Integrar en `apps/songs/services/generation_service.py`

Agregar antes de llamar a Modal:

```python
def request_generation(user, *, title, description=None, prompt=None,
                       lyrics=None, described_lyrics=None,
                       instrumental=False, guidance_scale=15.0):
    from apps.credits.services.credit_service import check_balance
    from ml.predictor import predict_from_description

    if not check_balance(user, required=1):
        raise InsufficientCreditsError("Sin créditos disponibles.")

    # ── NUEVO: usar el modelo .pkl para predecir parámetros ──────────────
    ml_prediction = None
    if description:
        ml_prediction = predict_from_description(description)
        # Si el usuario no especificó prompt, usar el del modelo
        if not prompt:
            prompt = ', '.join(ml_prediction['suggested_tags'])

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
        # Guardar la predicción del modelo para el dashboard
        ml_predicted_genre=ml_prediction['genre'] if ml_prediction else None,
        ml_predicted_mood=ml_prediction['mood']  if ml_prediction else None,
        ml_confidence=ml_prediction['confidence'] if ml_prediction else None,
        status='draft',
    )
    # ...resto igual
```

> Agregar al modelo `Song` los campos: `ml_predicted_genre`, `ml_predicted_mood`, `ml_confidence (JSONField)`.  
> Requiere una migración nueva: `python manage.py makemigrations songs && python manage.py migrate`

---

## Cómo le sirve a Nicol (recomendaciones)

Nicol puede importar `predict_from_description()` directamente en su módulo de recomendaciones:

```python
# apps/recommendations/services/profile_service.py — mejora para Nicol

def get_recommendations_for_user(user, limit=20):
    """
    Combina historial de escucha CON predicción del modelo para recomendar
    canciones que el usuario no ha escuchado pero probablemente le gusten.
    """
    from ml.predictor import predict_from_description
    from apps.songs.models import Song

    # 1. Tags del historial (lo que ya hace Nicol)
    from apps.recommendations.models import UserTasteProfile
    try:
        profile = UserTasteProfile.objects.get(user=user)
        top_tag_names = [t['name'] for t in profile.top_tags[:5]]
    except UserTasteProfile.DoesNotExist:
        top_tag_names = []

    # 2. Si el usuario describió canciones recientemente, predecir sus gustos latentes
    from apps.songs.models import Song as SongModel
    recent_descriptions = SongModel.objects.filter(
        user=user, description__isnull=False
    ).values_list('description', flat=True)[:5]

    predicted_tags = set(top_tag_names)
    for desc in recent_descriptions:
        pred = predict_from_description(desc)
        predicted_tags.update(pred['suggested_tags'])

    # 3. Recomendar canciones públicas con esos tags que el usuario no haya escuchado
    listened_ids = user.song_plays.values_list('song_id', flat=True)
    recommendations = Song.objects.filter(
        is_public=True, status='ready', deleted_at__isnull=True,
        tags__name__in=predicted_tags
    ).exclude(
        id__in=listened_ids
    ).distinct().order_by('-play_count')[:limit]

    return recommendations
```

---

## Qué va en `.gitignore`

```gitignore
# Datos y modelos ML (muy pesados — se regeneran con los scripts)
ml/data/
ml/models/*.pkl
```

## Qué va en el README del repo

```markdown
## Generar dataset y modelo ML

# 1. Generar el dataset sintético (~1GB, tarda ~5-10 minutos)
python ml/dataset_generator.py

# 2. Entrenar el modelo (tarda ~3-5 minutos)
python ml/train_model.py

# El modelo queda en ml/models/music_classifier.pkl
# El reporte de entrenamiento queda en ml/TRAINING_REPORT.md
```

---

## Tiempo estimado

| Tarea | Tiempo |
|---|---|
| Escribir `dataset_generator.py` | 3-4 horas |
| Correr la generación del dataset | 5-10 min (automático) |
| Escribir `train_model.py` | 2-3 horas |
| Correr el entrenamiento | 3-5 min (automático) |
| Escribir `predictor.py` e integrar en `generation_service` | 2-3 horas |
| Escribir la migración nueva de Song | 30 min |
| **Total trabajo humano** | **~1.5 días** |
