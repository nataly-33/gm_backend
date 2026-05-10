# Estructura de Repositorios — Generador Musical SaaS
> Backend: Django + Django REST Framework  
---

## BACKEND — `gm-backend`

```
gm-backend/
│
├── .github/
│   └── workflows/
│       ├── ci.yml               # Corre tests y linting en cada PR
│       └── deploy.yml           # Deploy automático al merge en main
│
├── config/                      # Configuración central de Django
│   ├── __init__.py
│   ├── settings/
│   │   ├── __init__.py
│   │   ├── base.py              # Configuración compartida (todas las env)
│   │   ├── development.py       # DEBUG=True, BD local, sin S3 real
│   │   └── production.py        # SECRET_KEY desde env, S3 real, Sentry
│   ├── urls.py                  # Enrutador raíz: incluye urls de cada módulo
│   ├── wsgi.py
│   └── asgi.py                  # Necesario para WebSockets (Channels)
│
├── apps/                        # TODOS los módulos van aquí
│   │
│   ├── core/                    # Utilidades globales compartidas
│   │   ├── __init__.py
│   │   ├── models.py            # BaseModel abstracto con id UUID, created_at, updated_at, deleted_at
│   │   ├── permissions.py       # Clases DRF de permisos (IsSuperAdmin, IsAdmin, HasPermission)
│   │   ├── pagination.py        # Paginación estándar del proyecto
│   │   ├── exceptions.py        # Excepciones personalizadas y handler global
│   │   ├── middleware.py        # TenantMiddleware: inyecta tenant en cada request
│   │   ├── storage.py           # Wrapper de S3/R2 para subir/bajar archivos
│   │   └── utils.py             # Funciones helper (generar tokens, validar audio, etc.)
│   │
│   ├── users/                   # Módulo: autenticación y usuarios
│   │   ├── __init__.py
│   │   ├── models.py            # User, Role, Permission, RolePermission, UserRole
│   │   ├── serializers.py       # RegisterSerializer, LoginSerializer, UserSerializer, RoleSerializer
│   │   ├── views.py             # Register, Login, Logout, Profile, ChangePassword, RolesCRUD
│   │   ├── urls.py
│   │   ├── services.py          # auth_service: crear usuario, asignar rol, verificar permiso
│   │   ├── backends.py          # Backend de autenticación personalizado (email + password)
│   │   └── tests/
│   │       ├── test_auth.py
│   │       └── test_roles.py
│   │
│   ├── songs/                   # Módulo: generación musical y biblioteca
│   │   ├── __init__.py
│   │   ├── models.py            # Song, Tag, SongTag, GenerationJob, LyricsJob
│   │   ├── serializers.py
│   │   ├── views.py             # SongCRUD, GenerateView, LyricsGenerateView, LibraryView
│   │   ├── urls.py
│   │   ├── services/
│   │   │   ├── __init__.py
│   │   │   ├── generation_service.py   # Orquesta: valida créditos → crea job → encola tarea
│   │   │   ├── lyrics_service.py       # Llama al LLM para generar letra
│   │   │   └── tag_service.py          # Gestión de tags y sugerencias
│   │   ├── tasks.py             # Celery tasks: process_generation_job, process_lyrics_job
│   │   └── tests/
│   │       ├── test_generation.py
│   │       └── test_songs.py
│   │
│   ├── stems/                   # Módulo: karaoke y separación de pistas
│   │   ├── __init__.py
│   │   ├── models.py            # StemJob, StemFile
│   │   ├── serializers.py
│   │   ├── views.py             # UploadAudioView, StemJobView, StemFilesView, ProgressView
│   │   ├── urls.py
│   │   ├── services/
│   │   │   ├── __init__.py
│   │   │   ├── stem_service.py         # Valida archivo → encola → llama Demucs
│   │   │   └── demucs_client.py        # Wrapper de Demucs (local o Modal)
│   │   ├── tasks.py             # Celery task: process_stem_job
│   │   └── tests/
│   │       └── test_stems.py
│   │
│   ├── credits/                 # Módulo: créditos, planes y pagos
│   │   ├── __init__.py
│   │   ├── models.py            # CreditPlan, UserSubscription, CreditTransaction
│   │   ├── serializers.py
│   │   ├── views.py             # PlansView, SubscribeView, TransactionsView, WebhookView
│   │   ├── urls.py
│   │   ├── services/
│   │   │   ├── __init__.py
│   │   │   ├── credit_service.py       # deduct_credits(), grant_credits(), check_balance()
│   │   │   └── polar_service.py        # Integración con Polar.sh webhook
│   │   └── tests/
│   │       └── test_credits.py
│   │
│   ├── community/               # Módulo: comunidad, likes, plays, tendencias
│   │   ├── __init__.py
│   │   ├── models.py            # SongLike, SongPlay
│   │   ├── serializers.py
│   │   ├── views.py             # TrendingView, LikeView, PlayView, PublicFeedView
│   │   ├── urls.py
│   │   ├── services.py          # Calcular trending, registrar play, toggle like
│   │   └── tests/
│   │       └── test_community.py
│   │
│   ├── recommendations/         # Módulo: recomendaciones personalizadas
│   │   ├── __init__.py
│   │   ├── models.py            # ListeningHistory, UserTasteProfile, UserSimilarity
│   │   ├── serializers.py
│   │   ├── views.py             # ForYouView, SuggestTagsView, SimilarUsersView
│   │   ├── urls.py
│   │   ├── services/
│   │   │   ├── __init__.py
│   │   │   ├── history_service.py      # Actualiza listening_history al registrar un play
│   │   │   ├── profile_service.py      # Recalcula user_taste_profile
│   │   │   └── similarity_service.py   # Calcula similitudes entre usuarios
│   │   ├── tasks.py             # Celery task: recalculate_profiles (cron diario)
│   │   └── tests/
│   │       └── test_recommendations.py
│   │
│   ├── playlists/               # Módulo: playlists manuales y automáticas
│   │   ├── __init__.py
│   │   ├── models.py            # Playlist, PlaylistSong
│   │   ├── serializers.py
│   │   ├── views.py             # PlaylistCRUD, AddSongView, ShareView, AutoPlaylistView
│   │   ├── urls.py
│   │   ├── services.py          # Generar playlists auto por mood/género, compartir
│   │   └── tests/
│   │       └── test_playlists.py
│   │
│   ├── mix/                     # Módulo: mix DJ (Sprint 4)
│   │   ├── __init__.py
│   │   ├── models.py            # MixProject, MixClip, MixExport
│   │   ├── serializers.py
│   │   ├── views.py             # MixProjectCRUD, ClipView, ExportView
│   │   ├── urls.py
│   │   ├── services/
│   │   │   ├── __init__.py
│   │   │   ├── mix_service.py          # Orquesta el armado del mix
│   │   │   └── audio_editor.py         # Cortes, fades, mezcla con pydub/ffmpeg
│   │   ├── tasks.py             # Celery task: render_mix
│   │   └── tests/
│   │       └── test_mix.py
│   │
│   ├── notifications/           # Módulo: notificaciones
│   │   ├── __init__.py
│   │   ├── models.py            # Notification
│   │   ├── serializers.py
│   │   ├── views.py             # ListNotifications, MarkReadView
│   │   ├── urls.py
│   │   └── services.py          # notify_user(), send_push() si se implementa
│   │
│   ├── audit/                   # Módulo: logs de auditoría (solo lectura para admins)
│   │   ├── __init__.py
│   │   ├── models.py            # AuditLog
│   │   ├── serializers.py
│   │   ├── views.py             # AuditLogListView (filtrable por acción/usuario/fecha)
│   │   ├── urls.py
│   │   └── services.py          # log_action() — función helper que llaman todos los módulos
│   │
│   └── reports/                 # Módulo: reportes para admins
│       ├── __init__.py
│       ├── views.py             # UsageReport, RevenueReport, TopSongsReport
│       ├── urls.py
│       └── services.py          # Queries agregadas para reportes
│
├── ml/                          # Clientes de modelos de IA (no son una app Django)
│   ├── __init__.py
│   ├── modal_client.py          # Llama a ACE-Step desplegado en Modal
│   ├── demucs_client.py         # Llama a Demucs (local o Modal)
│   └── llm_client.py            # Llama a OpenAI/Ollama para letras
│
├── workers/                     # Configuración de Celery
│   ├── __init__.py
│   ├── celery.py                # App Celery, configuración de brokers y colas
│   └── schedules.py             # Tareas periódicas: recalcular perfiles, hacer backups
│
├── requirements/
│   ├── base.txt                 # Dependencias comunes
│   ├── development.txt          # + pytest, factory-boy, coverage
│   └── production.txt           # + gunicorn, sentry-sdk
│
├── scripts/
│   ├── seed_db.py               # Datos iniciales: superadmin, tags, planes de crédito
│   └── create_tenant.py         # Script CLI para crear un nuevo tenant
│
├── .env.example                 # Variables de entorno de ejemplo (sin valores reales)
├── .gitignore
├── manage.py
├── pytest.ini
├── CONTRIBUTING.md              # Estándar de codificación, flujo de ramas, formato de commits
└── README.md
```


## Reglas de estructura que TODO el equipo debe seguir

### Backend
- **Un módulo = una app Django** dentro de `apps/`. Nunca mezclar lógica de dos módulos en el mismo archivo.
- **Lógica de negocio en `services.py`**, nunca en `views.py`. Las views solo reciben la request, validan con el serializer, llaman al service, y devuelven la response.
- **Tareas asíncronas en `tasks.py`** de cada módulo. Nunca hacer llamadas lentas (IA, S3, Demucs) dentro de una view.
- **Clientes de IA en `ml/`**. Los módulos no importan Modal o Demucs directamente; importan `ml.modal_client` o `ml.demucs_client`.
- **Auditoría**: toda acción importante llama `audit.services.log_action()` antes de retornar.

