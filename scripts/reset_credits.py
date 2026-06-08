"""
Resetea a 0 el balance de créditos de TODOS los usuarios y limpia las
transacciones generadas por el seeder.

Ejecutar desde gm_backend/:
    python scripts/reset_credits.py

Flags opcionales:
    --only-clientes   Solo resetea cliente1-40 (deja intacto al admin)
    --dry-run         Muestra qué haría sin tocar nada
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.users.models import User
from apps.credits.models import CreditTransaction

DRY_RUN        = '--dry-run'      in sys.argv
ONLY_CLIENTES  = '--only-clientes' in sys.argv

print()
print("=" * 55)
print("  RESET DE CRÉDITOS")
if DRY_RUN:
    print("  MODO DRY-RUN: no se escribe nada")
print("=" * 55)

# ── 1. Seleccionar usuarios a resetear ────────────────────────────────────────
if ONLY_CLIENTES:
    users = User.objects.filter(email__startswith='cliente', is_staff=False)
    print(f"\n>>> Solo clientes: {users.count()} usuarios")
else:
    users = User.objects.all()
    print(f"\n>>> Todos los usuarios: {users.count()} usuarios")

# ── 2. Mostrar estado actual ───────────────────────────────────────────────────
non_zero = users.exclude(credit_balance=0)
print(f"    Con balance > 0 : {non_zero.count()}")
for u in non_zero:
    print(f"      {u.email:40s}  balance actual: {u.credit_balance}")

# ── 3. Borrar transacciones del seeder ────────────────────────────────────────
# Solo borramos las que tienen reference_type='seed' para no tocar las de Stripe
seed_txs = CreditTransaction.objects.filter(
    user__in=users,
    reference_type='seed',
)
print(f"\n>>> Transacciones de seeder a borrar: {seed_txs.count()}")

# ── 4. Aplicar cambios ────────────────────────────────────────────────────────
if DRY_RUN:
    print("\n  [DRY-RUN] Sin cambios. Corré sin --dry-run para aplicar.")
else:
    deleted, _ = seed_txs.delete()
    print(f"    ✓ {deleted} transacciones de seeder borradas")

    updated = users.update(credit_balance=0)
    print(f"    ✓ {updated} usuarios reseteados a 0 créditos")

# ── 5. Resumen final ───────────────────────────────────────────────────────────
print()
if not DRY_RUN:
    still_non_zero = User.objects.exclude(credit_balance=0).count()
    print(f"  Usuarios con balance != 0 después del reset: {still_non_zero}")
    if still_non_zero:
        print("  ⚠  Estos tienen saldo de transacciones Stripe reales — no se tocaron.")

print()
print("  Ahora cada usuario llega a 0. Para obtener créditos deben comprar")
print("  un plan desde la app usando las tarjetas de test de Stripe:")
print()
print("  Tarjeta Visa test (pago exitoso) : 4242 4242 4242 4242")
print("  Tarjeta que falla               : 4000 0000 0000 0002")
print("  CVC cualquiera · Fecha futura cualquiera · ZIP 00000")
print("=" * 55)
