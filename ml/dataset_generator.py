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
    'reggaeton':  ['reggaeton', 'urban', 'latin'],
    'lofi':       ['lofi', 'chill', 'study'],
    'techno':     ['techno', 'electronic', 'dance'],
    'pop':        ['pop', 'commercial', 'radio'],
    'rock':       ['rock', 'guitar', 'band'],
    'hip-hop':    ['hip-hop', 'rap', 'urban'],
    'jazz':       ['jazz', 'instrumental', 'swing'],
    'classical':  ['classical', 'orchestral', 'instrumental'],
    'salsa':      ['salsa', 'latin', 'tropical'],
    'cumbia':     ['cumbia', 'latin', 'tropical'],
    'electronic': ['electronic', 'synth', 'edm'],
    'r&b':        ['r&b', 'soul', 'smooth'],
    'country':    ['country', 'folk', 'acoustic'],
    'folk':       ['folk', 'acoustic', 'indie'],
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
    tags = list(set(tags))
    instrumental = random.random() < 0.2

    return {
        'description':      generate_description(genre, mood, tempo),
        'genre':            genre,
        'mood':             mood,
        'tempo':            tempo,
        'bpm':              bpm,
        'tags':             '|'.join(tags),
        'instrumental':     int(instrumental),
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
            mood  = random.choice(MOODS)
            tempo = random.choice(tempos)
            writer.writerow(generate_row(genre, mood, tempo))

            if (i + 1) % 100_000 == 0:
                size_mb = os.path.getsize(output_path) / (1024 * 1024)
                print(f"  {i+1:,} filas escritas — {size_mb:.1f} MB")

    size_gb = os.path.getsize(output_path) / (1024 ** 3)
    print(f"\nDataset generado: {output_path} ({size_gb:.2f} GB)")


if __name__ == '__main__':
    generate_dataset('ml/data/dataset_sintetico.csv', target_rows=3_000_000)
