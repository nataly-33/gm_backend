import sys
import os

# Permite ejecutar el script directamente: python scripts/seed_db.py
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

# ── Imports de datos (se usarán más en sprints futuros) ──────────────────────
import pandas as pd
from faker import Faker

from apps.users.models import User, Role, UserRole

fake = Faker('es_ES')   # nombres en español
Faker.seed(42)          # reproducible: mismos nombres en cada máquina

# ── Configuración ─────────────────────────────────────────────────────────────
ADMIN_EMAIL     = 'admin@musicgen.com'
ADMIN_PASSWORD  = 'admin1234'
CLIENT_PASSWORD = 'cliente1234'
NUM_CLIENTS     = 40

# ── 1. Roles del sistema ──────────────────────────────────────────────────────
print("\n>>> [1/3] Roles del sistema")
for role_name in ['admin', 'user']:
    _, created = Role.objects.get_or_create(
        name=role_name,
        defaults={'is_system': True},
    )
    estado = "✓ creado  " if created else "- ya existe"
    print(f"    {estado}: {role_name}")

# ── 2. Superadmin ─────────────────────────────────────────────────────────────
print("\n>>> [2/3] Superadmin")
admin_role = Role.objects.get(name='admin')

if not User.objects.filter(email=ADMIN_EMAIL).exists():
    admin = User.objects.create_superuser(
        email=ADMIN_EMAIL,
        password=ADMIN_PASSWORD,
        full_name='Super Admin',
    )
    UserRole.objects.get_or_create(user=admin, role=admin_role)
    print(f"    ✓ Creado  → {ADMIN_EMAIL}  |  contraseña: {ADMIN_PASSWORD}")
else:
    print(f"    - Ya existe: {ADMIN_EMAIL}")

# ── 3. Clientes (40 usuarios con emails predecibles) ─────────────────────────
print(f"\n>>> [3/3] Clientes ({NUM_CLIENTS} usuarios)")
user_role = Role.objects.get(name='user')

# DataFrame con datos realistas — se extiende en sprints futuros
rows = [
    {
        'n':      i,
        'email':  f'cliente{i}@gmail.com',
        'nombre': fake.name(),
    }
    for i in range(1, NUM_CLIENTS + 1)
]
df = pd.DataFrame(rows).set_index('n')

created_count  = 0
existing_count = 0

for n, row in df.iterrows():
    email = row['email']
    if not User.objects.filter(email=email).exists():
        u = User.objects.create_user(
            email=email,
            password=CLIENT_PASSWORD,
            full_name=row['nombre'],
        )
        UserRole.objects.get_or_create(user=u, role=user_role)
        created_count += 1
    else:
        existing_count += 1

print(f"    ✓ {created_count} nuevos  |  {existing_count} ya existían")
print()
print("    Muestra (primeros 5):")
print(df[['email', 'nombre']].head(5).to_string())
if NUM_CLIENTS > 5:
    print(f"    ... ({NUM_CLIENTS} registros en total)")

# ── Resumen final ─────────────────────────────────────────────────────────────
print()
print("=" * 55)
print("  SEED COMPLETADO")
print("=" * 55)
print(f"  Total usuarios en BD : {User.objects.count()}")
print(f"  Total roles          : {Role.objects.count()}")
print()
print(f"  ADMIN")
print(f"    email    : {ADMIN_EMAIL}")
print(f"    password : {ADMIN_PASSWORD}")
print()
print(f"  CLIENTES ({NUM_CLIENTS})")
print(f"    emails   : cliente1@gmail.com … cliente{NUM_CLIENTS}@gmail.com")
print(f"    password : {CLIENT_PASSWORD}")
print("=" * 55)

# ── Sección para sprints futuros (descomentar cuando los modelos existan) ─────
# from apps.credits.models import CreditPlan
# planes = pd.DataFrame([
#     {'slug': 'free',   'name': 'Free',   'credits_per_month': 5,   'price_usd': 0.00},
#     {'slug': 'pro',    'name': 'Pro',    'credits_per_month': 50,  'price_usd': 9.00},
#     {'slug': 'studio', 'name': 'Studio', 'credits_per_month': 200, 'price_usd': 25.00},
# ])
# for _, p in planes.iterrows():
#     CreditPlan.objects.get_or_create(slug=p['slug'], defaults=p.to_dict())

# from apps.songs.models import Tag
# tags = pd.DataFrame([
#     {'name': 'reggaeton', 'category': 'genre'}, {'name': 'lofi',      'category': 'genre'},
#     {'name': 'techno',    'category': 'genre'}, {'name': 'pop',       'category': 'genre'},
#     {'name': 'sad',       'category': 'mood'},  {'name': 'happy',     'category': 'mood'},
#     {'name': 'energetic', 'category': 'mood'},  {'name': 'chill',     'category': 'mood'},
#     {'name': 'fast',      'category': 'tempo'}, {'name': 'slow',      'category': 'tempo'},
# ])
# for _, t in tags.iterrows():
#     Tag.objects.get_or_create(name=t['name'], defaults={'category': t['category']})
