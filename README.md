# MusicGen — Backend

Django 5 + Django REST Framework + Celery + PostgreSQL. API REST para generación musical con IA.

## Stack

| Tecnología | Uso |
| :--- | :--- |
| Django 5.0 + DRF 3.15 | Framework y API REST |
| SimpleJWT | Autenticación con tokens JWT |
| PostgreSQL | Base de datos principal |
| Celery + Redis | Cola de tareas asíncronas |
| AWS S3 + boto3 | Almacenamiento de audio e imágenes |
| Stripe | Pagos y suscripciones |
| Modal | Generación de música con IA |

## Scripts

```bash
# Desarrollo
python manage.py runserver

# Migraciones
python manage.py makemigrations
python manage.py migrate

# Seed inicial (roles, admin, planes, tags)
python manage.py shell < scripts/seed_db.py

# Worker de Celery
celery -A workers.celery worker -l info
```

## Variables de entorno

Copiar `.env.example` a `.env` y completar los valores:

```env
SECRET_KEY=...
DEBUG=True
DB_NAME=musicgen  DB_USER=...  DB_PASSWORD=...  DB_HOST=localhost  DB_PORT=5432
REDIS_URL=redis://localhost:6379/0
AWS_ACCESS_KEY_ID=...  AWS_SECRET_ACCESS_KEY=...  AWS_STORAGE_BUCKET_NAME=...
MODAL_ENDPOINT_URL=...  MODAL_API_KEY=...
STRIPE_SECRET_KEY=...  STRIPE_WEBHOOK_SECRET=...
```

---

## Documentos clave — **leer antes de escribir código**

| Archivo | Qué define |
| :--- | :--- |
| [`docs/API_CONTRACT.md`](docs/API_CONTRACT.md) | **Contrato de la API**: todos los endpoints, verbos HTTP, bodies y respuestas esperadas. Fuente de verdad para el frontend. |
| [`docs/database_schema.md`](docs/database_schema.md) | Esquema completo de la base de datos: tablas, columnas, índices, relaciones y justificaciones de diseño. |
| [`docs/01_division_trabajo.md`](docs/01_division_trabajo.md) | División de tareas por sprint (A/B/C) y checklist de implementación. |

---

## Estructura de carpetas

```
gm_backend/
├── apps/                  # Apps Django (una por dominio de negocio)
│   ├── core/              # BaseModel abstracto, permisos compartidos
│   ├── users/             # Auth, modelo User personalizado, roles
│   ├── songs/             # Generación de canciones, biblioteca, tags
│   ├── stems/             # Separación de stems de audio
│   ├── credits/           # Planes, pagos Stripe, transacciones
│   ├── community/         # Feed público, likes, reproducciones
│   ├── notifications/     # Notificaciones de usuario
│   ├── audit/             # Log de actividad del sistema
│   └── ...
├── config/
│   ├── settings.py        # Configuración Django (dev + prod)
│   └── urls.py            # URLs raíz del proyecto
├── workers/
│   └── celery.py          # Configuración de Celery
├── ml/                    # Clientes IA (Modal, Demucs, LLM)
├── scripts/
│   └── seed_db.py         # Datos iniciales (roles, admin, planes, tags)
└── docs/                  # Documentación del proyecto
```

---

## Reglas del proyecto

1. **Lógica de negocio en `services.py`** — nunca en views ni modelos.
2. **BaseModel** (`apps.core.models.BaseModel`) para todos los modelos de negocio: incluye UUID, `created_at`, `updated_at` y soft delete.
3. **`AUTH_USER_MODEL = 'users.User'`** — nunca usar el User de Django por defecto.
4. **Permisos DRF:** usar `IsAdmin` o `IsOwnerOrAdmin` de `apps.core.permissions`.
5. **Tareas asíncronas** van en `tasks.py` de cada app y se encolan con Celery.
6. **Los endpoints deben coincidir exactamente** con lo definido en `docs/API_CONTRACT.md`.
7. **Soft delete:** no borrar registros de negocio con `DELETE` de SQL. Usar el método `.soft_delete()` del BaseModel.
