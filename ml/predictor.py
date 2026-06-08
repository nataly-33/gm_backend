"""
Carga el modelo .pkl una sola vez al arrancar Django.
Expone predict_from_description() para usar en generation_service y recommendations.
"""
import joblib
from pathlib import Path

MODEL_PATH = Path(__file__).parent / 'models' / 'music_classifier.pkl'

_model_bundle = None

BPM_RANGES = {
    'slow':   (60, 90),
    'medium': (90, 120),
    'fast':   (120, 160),
}


def _load_model():
    global _model_bundle
    if _model_bundle is None:
        if not MODEL_PATH.exists():
            raise FileNotFoundError(
                f"Modelo no encontrado en {MODEL_PATH}. "
                f"Ejecutar: python ml/dataset_generator.py && python ml/train_model.py"
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
        'suggested_tags': ['lofi', 'sad', 'slow'],
        'confidence': {
            'genre': 0.87,
            'mood':  0.92,
            'tempo': 0.78,
        }
    }

    Lanza FileNotFoundError si el modelo no está entrenado todavía.
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

    return {
        'genre':          genre_name,
        'mood':           mood_name,
        'tempo':          tempo_name,
        'bpm_range':      BPM_RANGES.get(tempo_name, (90, 120)),
        'suggested_tags': list({genre_name, mood_name, tempo_name}),
        'confidence': {
            'genre': round(float(genre_proba), 3),
            'mood':  round(float(mood_proba), 3),
            'tempo': round(float(tempo_proba), 3),
        },
    }


def is_model_available() -> bool:
    """Devuelve True si el .pkl existe y puede cargarse."""
    return MODEL_PATH.exists()
