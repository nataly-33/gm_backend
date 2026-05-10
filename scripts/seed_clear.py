import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

import pandas as pd
from django.db import connection

# ── Modelos actuales ──────────────────────────────────────────────────────────
from apps.users.models import User, Role, UserRole
from rest_framework_simplejwt.token_blacklist.models import OutstandingToken, BlacklistedToken
from django.contrib.admin.models import LogEntry
from django.contrib.sessions.models import Session

# ── Confirmación ──────────────────────────────────────────────────────────────
print()
print("=" * 55)
print("  ⚠   SEED CLEAR — eliminación de todos los registros")
print("=" * 55)
print()
print("  Tablas que se van a limpiar:")
print("    - BlacklistedToken / OutstandingToken (JWT)")
print("    - UserRole / User / Role")
print("    - LogEntry (admin logs) / Session")
print()
print("  Las tablas de sistema (ContentType, Permission)")
print("  NO se tocan — Django las necesita para funcionar.")
print()

confirm = input("  Escribí 'si' para continuar o cualquier otra cosa para cancelar: ")
if confirm.strip().lower() != 'si':
    print("\n  Operación cancelada. No se eliminó nada.")
    sys.exit(0)

print()

# ── Función helper ────────────────────────────────────────────────────────────
results = []

def clear_table(label: str, manager):
    count = manager.count()
    manager.all().delete()
    results.append({'Tabla': label, 'Eliminados': count})
    estado = f"  ✓ {label:<35} {count} registros"
    print(estado)

# ── Borrado en orden (respetar foreign keys) ──────────────────────────────────
print(">>> Limpiando...")
clear_table('BlacklistedToken (JWT)',         BlacklistedToken.objects)
clear_table('OutstandingToken (JWT)',          OutstandingToken.objects)
clear_table('UserRole',                        UserRole.objects)
clear_table('User',                            User.objects)
clear_table('Role',                            Role.objects)
clear_table('LogEntry (admin logs)',           LogEntry.objects)
clear_table('Session',                         Session.objects)

# Agregar aquí cuando los modelos existan:
# from apps.songs.models import SongLike, GenerationJob, Song, Tag
# from apps.credits.models import CreditTransaction, UserSubscription, CreditPlan
# from apps.community.models import Play
# clear_table('SongLike',         SongLike.objects)
# clear_table('Play',             Play.objects)
# clear_table('GenerationJob',    GenerationJob.objects)
# clear_table('Song',             Song.objects)
# clear_table('Tag',              Tag.objects)
# clear_table('CreditTransaction',CreditTransaction.objects)
# clear_table('UserSubscription', UserSubscription.objects)
# clear_table('CreditPlan',       CreditPlan.objects)

# ── Resetear secuencias de autoincremento (PostgreSQL) ────────────────────────
SEQUENCES = [
    'users_role_id_seq',
    'users_userrole_id_seq',
    'admin_logentry_id_seq',
]
try:
    with connection.cursor() as cursor:
        for seq in SEQUENCES:
            cursor.execute(f"ALTER SEQUENCE IF EXISTS {seq} RESTART WITH 1;")
    print()
    print("  ✓ Secuencias de ID reseteadas a 1")
except Exception as e:
    print(f"\n  ⚠  No se pudieron resetear secuencias: {e}")

# ── Resumen ───────────────────────────────────────────────────────────────────
df = pd.DataFrame(results)
total = df['Eliminados'].sum()

print()
print("=" * 55)
print("  RESUMEN")
print("=" * 55)
print(df.to_string(index=False))
print("-" * 55)
print(f"  Total registros eliminados: {total}")
print("=" * 55)
print()
print("  Base de datos limpia.")
print("  Ejecutá 'python scripts/seed_db.py' para volver a poblarla.")
print()
