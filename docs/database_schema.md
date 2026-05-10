# Base de Datos — Generador Musical SaaS (B2C)
> Versión 2.0 · Sin multitenancy — modelo B2C con suscripciones tipo Spotify  
> Motor: PostgreSQL · ORM: Django ORM  
> Soft delete en todas las tablas de negocio · UUID como PK

---

## Por qué no hay multitenancy

Este sistema es **B2C**: los usuarios se registran individualmente y pagan una suscripción mensual personal. No hay organizaciones ni empresas cliente. Forzar multitenancy sería añadir complejidad innecesaria que no corresponde al problema.

Los dos niveles del sistema son:
- **Admin**: el equipo desarrollador/dueño de la plataforma. Un solo panel global.
- **Usuario**: cualquier persona que se registra.

---

## Mapa de módulos y tablas

```
USUARIOS Y AUTH
  └── users, roles, user_roles

GENERACIÓN MUSICAL
  └── songs, song_tags, tags, generation_jobs, lyrics_jobs

KARAOKE / STEMS (Sprint 2)
  └── stem_jobs, stem_files

CRÉDITOS Y SUSCRIPCIONES
  └── credit_plans, user_subscriptions, credit_transactions

COMUNIDAD
  └── song_likes, song_plays

RECOMENDACIONES (Sprint 3)
  └── listening_history, user_taste_profiles, user_similarities

PLAYLISTS (Sprint 3)
  └── playlists, playlist_songs

MIX / DJ (Sprint 4)
  └── mix_projects, mix_clips, mix_exports

SISTEMA
  └── audit_logs, notifications
```

---

## 1. USUARIOS Y AUTH

### `users` (tabla de Django — AUTH_USER_MODEL personalizado)
| Campo | Tipo | Descripción |
|---|---|---|
| `id` | UUID PK | |
| `email` | VARCHAR(255) UNIQUE | Identificador principal |
| `password` | VARCHAR(255) | Hash Django |
| `full_name` | VARCHAR(200) | |
| `avatar_url` | TEXT NULL | |
| `is_active` | BOOLEAN DEFAULT true | |
| `is_staff` | BOOLEAN DEFAULT false | Acceso al panel de admin Django |
| `is_superuser` | BOOLEAN DEFAULT false | Superadmin — acceso total |
| `credit_balance` | INT DEFAULT 0 | Créditos disponibles ahora mismo |
| `email_verified_at` | TIMESTAMPTZ NULL | |
| `last_login_at` | TIMESTAMPTZ NULL | |
| `stripe_customer_id` | VARCHAR(100) NULL | ID del cliente en Stripe |
| `created_at` | TIMESTAMPTZ | |
| `updated_at` | TIMESTAMPTZ | |
| `deleted_at` | TIMESTAMPTZ NULL | Soft delete |

---

### `roles`
Solo dos roles fijos del sistema: `admin` y `user`. Se pueden agregar más en el futuro (ej: `dj`, `moderator`).

| Campo | Tipo | Descripción |
|---|---|---|
| `id` | UUID PK | |
| `name` | VARCHAR(40) UNIQUE | `admin` / `user` / `dj` |
| `description` | TEXT NULL | |
| `is_system` | BOOLEAN DEFAULT false | Roles predefinidos del sistema |

---

### `user_roles`
| Campo | Tipo | Descripción |
|---|---|---|
| `id` | UUID PK | |
| `user_id` | UUID FK → users | |
| `role_id` | UUID FK → roles | |
| `assigned_at` | TIMESTAMPTZ | |
| UNIQUE(`user_id`, `role_id`) | | |

---

## 2. GENERACIÓN MUSICAL

### `tags`
| Campo | Tipo | Descripción |
|---|---|---|
| `id` | INT PK auto | |
| `name` | VARCHAR(60) UNIQUE | `reggaeton`, `lofi`, `sad` |
| `category` | VARCHAR(20) | `genre` / `mood` / `tempo` |
| `emoji` | VARCHAR(10) NULL | |

---

### `songs`
| Campo | Tipo | Descripción |
|---|---|---|
| `id` | UUID PK | |
| `user_id` | UUID FK → users | |
| `title` | VARCHAR(200) | |
| `description` | TEXT NULL | Descripción libre (full_described_song del ZIP) |
| `prompt` | TEXT NULL | Tags de estilo generados o escritos |
| `lyrics` | TEXT NULL | Letra final usada |
| `described_lyrics` | TEXT NULL | Descripción de letra para el LLM |
| `lyrics_source` | VARCHAR(20) | `user` / `ai_generated` / `described` |
| `instrumental` | BOOLEAN DEFAULT false | |
| `guidance_scale` | FLOAT DEFAULT 15.0 | Parámetro de ACE-Step |
| `infer_step` | INT DEFAULT 60 | Parámetro de ACE-Step |
| `audio_duration` | FLOAT DEFAULT 180.0 | Duración en segundos |
| `seed` | INT DEFAULT -1 | Semilla para reproducibilidad |
| `audio_s3_key` | TEXT NULL | Clave del archivo WAV en S3 |
| `thumbnail_s3_key` | TEXT NULL | Clave de la imagen de portada en S3 |
| `status` | VARCHAR(20) | `draft`/`queued`/`processing`/`ready`/`failed`/`no_credits` |
| `is_public` | BOOLEAN DEFAULT false | Si aparece en el feed de comunidad |
| `play_count` | INT DEFAULT 0 | Contador desnormalizado |
| `like_count` | INT DEFAULT 0 | Contador desnormalizado |
| `created_at` | TIMESTAMPTZ | |
| `updated_at` | TIMESTAMPTZ | |
| `deleted_at` | TIMESTAMPTZ NULL | Soft delete |

---

### `song_tags`
| Campo | Tipo | |
|---|---|---|
| `song_id` | UUID FK → songs | |
| `tag_id` | INT FK → tags | |
| PK(`song_id`, `tag_id`) | | |

---

### `generation_jobs`
| Campo | Tipo | Descripción |
|---|---|---|
| `id` | UUID PK | |
| `user_id` | UUID FK → users | |
| `song_id` | UUID FK → songs NULL | Se llena al crear la canción |
| `mode` | VARCHAR(30) | `from_description` / `with_lyrics` / `with_described_lyrics` |
| `modal_endpoint_used` | VARCHAR(200) | URL del endpoint de Modal que se llamó |
| `status` | VARCHAR(20) | `queued`/`processing`/`completed`/`failed`/`no_credits` |
| `error_message` | TEXT NULL | |
| `credits_used` | INT DEFAULT 0 | |
| `started_at` | TIMESTAMPTZ NULL | |
| `completed_at` | TIMESTAMPTZ NULL | |
| `created_at` | TIMESTAMPTZ | |

---

### `lyrics_jobs`
| Campo | Tipo | Descripción |
|---|---|---|
| `id` | UUID PK | |
| `user_id` | UUID FK → users | |
| `song_id` | UUID FK → songs NULL | |
| `description_prompt` | TEXT | Lo que el usuario describió |
| `generated_lyrics` | TEXT NULL | Resultado del LLM |
| `status` | VARCHAR(20) | `queued`/`completed`/`failed` |
| `created_at` | TIMESTAMPTZ | |

---

## 3. KARAOKE / STEMS (Sprint 2)

### `stem_jobs`
| Campo | Tipo | Descripción |
|---|---|---|
| `id` | UUID PK | |
| `user_id` | UUID FK → users | |
| `source_audio_url` | TEXT | Audio subido por el usuario |
| `source_filename` | VARCHAR(255) | Nombre del archivo original |
| `source_file_size_bytes` | BIGINT | |
| `model_used` | VARCHAR(40) DEFAULT `demucs-v4` | |
| `status` | VARCHAR(20) | `queued`/`processing`/`completed`/`failed` |
| `progress_pct` | INT DEFAULT 0 | 0–100 |
| `error_message` | TEXT NULL | |
| `credits_used` | INT DEFAULT 2 | La separación cuesta 2 créditos |
| `started_at` | TIMESTAMPTZ NULL | |
| `completed_at` | TIMESTAMPTZ NULL | |
| `created_at` | TIMESTAMPTZ | |

---

### `stem_files`
| Campo | Tipo | Descripción |
|---|---|---|
| `id` | UUID PK | |
| `stem_job_id` | UUID FK → stem_jobs | |
| `stem_type` | VARCHAR(20) | `vocals` / `no_vocals` / `bass` / `drums` |
| `audio_s3_key` | TEXT | Clave en S3 |
| `duration_seconds` | INT NULL | |
| `file_size_bytes` | BIGINT NULL | |
| `created_at` | TIMESTAMPTZ | |

---

## 4. CRÉDITOS Y SUSCRIPCIONES

### `credit_plans`
| Campo | Tipo | Descripción |
|---|---|---|
| `id` | INT PK auto | |
| `slug` | VARCHAR(20) UNIQUE | `free` / `pro` / `studio` |
| `name` | VARCHAR(80) | Nombre visible: "Free", "Pro", "Studio" |
| `credits_per_month` | INT | Créditos que se otorgan cada mes |
| `price_usd` | DECIMAL(8,2) | 0 para free |
| `stripe_price_id` | VARCHAR(100) NULL | ID del precio en Stripe |
| `features` | JSONB | Lista de features en el plan |
| `is_active` | BOOLEAN DEFAULT true | |

**Datos iniciales:**
- Free: 5 créditos/mes, $0
- Pro: 50 créditos/mes, $9/mes
- Studio: 200 créditos/mes, $25/mes

---

### `user_subscriptions`
| Campo | Tipo | Descripción |
|---|---|---|
| `id` | UUID PK | |
| `user_id` | UUID FK → users | |
| `plan_id` | INT FK → credit_plans | |
| `stripe_subscription_id` | VARCHAR(100) NULL | ID de la suscripción en Stripe |
| `stripe_customer_id` | VARCHAR(100) NULL | |
| `status` | VARCHAR(20) | `active`/`cancelled`/`past_due`/`trialing` |
| `current_period_start` | TIMESTAMPTZ NULL | |
| `current_period_end` | TIMESTAMPTZ NULL | |
| `created_at` | TIMESTAMPTZ | |
| `updated_at` | TIMESTAMPTZ | |

---

### `credit_transactions`
| Campo | Tipo | Descripción |
|---|---|---|
| `id` | UUID PK | |
| `user_id` | UUID FK → users | |
| `amount` | INT | Positivo = recarga, negativo = consumo |
| `balance_after` | INT | Balance resultante |
| `type` | VARCHAR(30) | `monthly_grant`/`stripe_purchase`/`generation`/`stem`/`mix`/`refund` |
| `reference_id` | UUID NULL | ID del job que consumió o del pago |
| `reference_type` | VARCHAR(30) NULL | `generation_job`/`stem_job`/`stripe_invoice` |
| `description` | TEXT NULL | |
| `created_at` | TIMESTAMPTZ | |

---

## 5. COMUNIDAD

### `song_likes`
Igual que la tabla `Like` del ZIP (prisma/schema.prisma).

| Campo | Tipo | |
|---|---|---|
| `user_id` | UUID FK → users | |
| `song_id` | UUID FK → songs | |
| `created_at` | TIMESTAMPTZ | |
| PK(`user_id`, `song_id`) | | |

---

### `song_plays`
| Campo | Tipo | Descripción |
|---|---|---|
| `id` | UUID PK | |
| `user_id` | UUID FK → users NULL | |
| `song_id` | UUID FK → songs | |
| `seconds_played` | INT DEFAULT 0 | |
| `completed` | BOOLEAN DEFAULT false | Si escuchó >80% |
| `source` | VARCHAR(30) | `trending`/`library`/`recommendation`/`playlist` |
| `created_at` | TIMESTAMPTZ | |

---

## 6. RECOMENDACIONES (Sprint 3)

### `listening_history`
Agrega el historial por usuario y tag para calcular preferencias.

| Campo | Tipo | Descripción |
|---|---|---|
| `id` | UUID PK | |
| `user_id` | UUID FK → users | |
| `tag_id` | INT FK → tags | |
| `play_count` | INT DEFAULT 0 | |
| `total_seconds` | INT DEFAULT 0 | |
| `last_played_at` | TIMESTAMPTZ NULL | |
| `updated_at` | TIMESTAMPTZ | |
| UNIQUE(`user_id`, `tag_id`) | | |

---

### `user_taste_profiles`
| Campo | Tipo | Descripción |
|---|---|---|
| `id` | UUID PK | |
| `user_id` | UUID FK → users UNIQUE | |
| `top_tags` | JSONB | `[{"tag_id": 5, "score": 0.95}, ...]` |
| `top_genres` | JSONB | |
| `top_moods` | JSONB | |
| `calculated_at` | TIMESTAMPTZ | |

---

### `user_similarities`
| Campo | Tipo | Descripción |
|---|---|---|
| `id` | UUID PK | |
| `user_a_id` | UUID FK → users | |
| `user_b_id` | UUID FK → users | |
| `similarity_score` | FLOAT | 0.0–1.0 |
| `calculated_at` | TIMESTAMPTZ | |
| UNIQUE(`user_a_id`, `user_b_id`) | | |

---

## 7. PLAYLISTS (Sprint 3)

### `playlists`
| Campo | Tipo | Descripción |
|---|---|---|
| `id` | UUID PK | |
| `user_id` | UUID FK → users | |
| `title` | VARCHAR(200) | |
| `description` | TEXT NULL | |
| `cover_url` | TEXT NULL | |
| `type` | VARCHAR(20) | `manual`/`auto_mood`/`auto_genre`/`recommended` |
| `is_public` | BOOLEAN DEFAULT false | |
| `share_token` | VARCHAR(64) UNIQUE NULL | Token para link público |
| `song_count` | INT DEFAULT 0 | Desnormalizado |
| `created_at` | TIMESTAMPTZ | |
| `updated_at` | TIMESTAMPTZ | |
| `deleted_at` | TIMESTAMPTZ NULL | |

---

### `playlist_songs`
| Campo | Tipo | |
|---|---|---|
| `id` | UUID PK | |
| `playlist_id` | UUID FK → playlists | |
| `song_id` | UUID FK → songs | |
| `position` | INT | Orden |
| `added_at` | TIMESTAMPTZ | |
| UNIQUE(`playlist_id`, `song_id`) | | |

---

## 8. MIX / DJ (Sprint 4)

### `mix_projects`
| Campo | Tipo | |
|---|---|---|
| `id` | UUID PK | |
| `user_id` | UUID FK → users | |
| `title` | VARCHAR(200) | |
| `bpm` | INT NULL | |
| `status` | VARCHAR(20) | `draft`/`processing`/`ready`/`failed` |
| `output_s3_key` | TEXT NULL | |
| `duration_seconds` | INT NULL | |
| `created_at` | TIMESTAMPTZ | |
| `updated_at` | TIMESTAMPTZ | |
| `deleted_at` | TIMESTAMPTZ NULL | |

---

### `mix_clips`
| Campo | Tipo | |
|---|---|---|
| `id` | UUID PK | |
| `mix_project_id` | UUID FK → mix_projects | |
| `song_id` | UUID FK → songs NULL | |
| `stem_file_id` | UUID FK → stem_files NULL | |
| `position` | INT | |
| `start_time_ms` | INT DEFAULT 0 | |
| `end_time_ms` | INT | |
| `fade_in_ms` | INT DEFAULT 0 | |
| `fade_out_ms` | INT DEFAULT 0 | |
| `volume` | FLOAT DEFAULT 1.0 | |
| `created_at` | TIMESTAMPTZ | |

---

### `mix_exports`
| Campo | Tipo | |
|---|---|---|
| `id` | UUID PK | |
| `mix_project_id` | UUID FK → mix_projects | |
| `format` | VARCHAR(10) | `mp3`/`wav` |
| `output_s3_key` | TEXT NULL | |
| `status` | VARCHAR(20) | |
| `credits_used` | INT DEFAULT 3 | |
| `created_at` | TIMESTAMPTZ | |

---

## 9. SISTEMA

### `audit_logs`
| Campo | Tipo | Descripción |
|---|---|---|
| `id` | UUID PK | |
| `user_id` | UUID FK → users NULL | NULL = acción del sistema |
| `action` | VARCHAR(100) | `user.login` / `song.generate` / `credits.deduct` |
| `entity_type` | VARCHAR(60) NULL | `Song` / `User` / `Subscription` |
| `entity_id` | UUID NULL | |
| `old_value` | JSONB NULL | |
| `new_value` | JSONB NULL | |
| `ip_address` | INET NULL | |
| `created_at` | TIMESTAMPTZ | Nunca se borra ni modifica |

---

### `notifications`
| Campo | Tipo | Descripción |
|---|---|---|
| `id` | UUID PK | |
| `user_id` | UUID FK → users | |
| `type` | VARCHAR(40) | `song_ready`/`credits_low`/`job_failed`/`subscription_expired` |
| `title` | VARCHAR(200) | |
| `body` | TEXT | |
| `is_read` | BOOLEAN DEFAULT false | |
| `reference_id` | UUID NULL | |
| `reference_type` | VARCHAR(40) NULL | |
| `created_at` | TIMESTAMPTZ | |

---

## Índices recomendados

```sql
-- Canciones del usuario (biblioteca personal)
CREATE INDEX idx_songs_user ON songs(user_id, created_at DESC) WHERE deleted_at IS NULL;

-- Feed público de tendencias
CREATE INDEX idx_songs_public ON songs(play_count DESC, created_at DESC)
  WHERE is_public = true AND status = 'ready' AND deleted_at IS NULL;

-- Jobs pendientes de procesar (Celery los busca por status)
CREATE INDEX idx_genjobs_status ON generation_jobs(status, created_at);

-- Notificaciones no leídas
CREATE INDEX idx_notif_unread ON notifications(user_id) WHERE is_read = false;

-- Auditoría por entidad
CREATE INDEX idx_audit_entity ON audit_logs(entity_type, entity_id);

-- Historial de escucha por usuario
CREATE INDEX idx_listhist_user ON listening_history(user_id, play_count DESC);
```

---

> Este esquema se implementa por sprints:
> - **Sprint 0-1**: users, roles, user_roles, songs, song_tags, tags, generation_jobs, credit_plans, user_subscriptions, credit_transactions, song_likes, song_plays, audit_logs, notifications
> - **Sprint 2**: stem_jobs, stem_files
> - **Sprint 3**: listening_history, user_taste_profiles, user_similarities, playlists, playlist_songs
> - **Sprint 4**: mix_projects, mix_clips, mix_exports
