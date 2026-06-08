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
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report
from sklearn.preprocessing import LabelEncoder

DATA_PATH   = 'ml/data/dataset_sintetico.csv'
OUTPUT_DIR  = 'ml/models'
MODEL_PATH  = f'{OUTPUT_DIR}/music_classifier.pkl'
REPORT_PATH = 'ml/TRAINING_REPORT.md'

print("Cargando dataset...")
# 500k filas para entrenamiento rápido (muestra representativa del dataset de 3M)
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

# Split estratificado por género
X_train, X_test, yg_train, yg_test, ym_train, ym_test, yt_train, yt_test = train_test_split(
    X, y_genre, y_mood, y_tempo, test_size=0.2, random_state=42
)

print("Entrenando modelo de género...")
genre_pipeline = Pipeline([
    ('tfidf', TfidfVectorizer(max_features=10_000, ngram_range=(1, 2))),
    ('clf',   RandomForestClassifier(n_estimators=100, random_state=42, n_jobs=-1)),
])
genre_pipeline.fit(X_train, yg_train)

print("Entrenando modelo de mood...")
mood_pipeline = Pipeline([
    ('tfidf', TfidfVectorizer(max_features=10_000, ngram_range=(1, 2))),
    ('clf',   RandomForestClassifier(n_estimators=100, random_state=42, n_jobs=-1)),
])
mood_pipeline.fit(X_train, ym_train)

print("Entrenando modelo de tempo...")
tempo_pipeline = Pipeline([
    ('tfidf', TfidfVectorizer(max_features=5_000, ngram_range=(1, 2))),
    ('clf',   RandomForestClassifier(n_estimators=50, random_state=42, n_jobs=-1)),
])
tempo_pipeline.fit(X_train, yt_train)

# Evaluar los tres modelos
genre_report = classification_report(
    yg_test, genre_pipeline.predict(X_test),
    target_names=genre_encoder.classes_
)
mood_report = classification_report(
    ym_test, mood_pipeline.predict(X_test),
    target_names=mood_encoder.classes_
)
tempo_report = classification_report(
    yt_test, tempo_pipeline.predict(X_test),
    target_names=tempo_encoder.classes_
)

print("\n=== Reporte Género ===")
print(genre_report)
print("=== Reporte Mood ===")
print(mood_report)
print("=== Reporte Tempo ===")
print(tempo_report)

# Guardar todo en un único .pkl
os.makedirs(OUTPUT_DIR, exist_ok=True)
model_bundle = {
    'genre_pipeline': genre_pipeline,
    'mood_pipeline':  mood_pipeline,
    'tempo_pipeline': tempo_pipeline,
    'genre_encoder':  genre_encoder,
    'mood_encoder':   mood_encoder,
    'tempo_encoder':  tempo_encoder,
    'version':        '1.0',
}
joblib.dump(model_bundle, MODEL_PATH)
print(f"\nModelo guardado en {MODEL_PATH} ({os.path.getsize(MODEL_PATH) / 1024 / 1024:.1f} MB)")

# Escribir reporte de entrenamiento
with open(REPORT_PATH, 'w', encoding='utf-8') as f:
    f.write("# Training Report — music_classifier.pkl\n\n")
    f.write(f"Dataset: {DATA_PATH} (500k filas de muestra de 3M)\n\n")
    f.write("## Género\n```\n" + genre_report + "\n```\n\n")
    f.write("## Mood\n```\n" + mood_report + "\n```\n\n")
    f.write("## Tempo\n```\n" + tempo_report + "\n```\n\n")

print(f"Reporte guardado en {REPORT_PATH}")
