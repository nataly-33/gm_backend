# Ejecutar con: python manage.py shell < scripts/seed_db.py
from apps.users.models import User, Role
from apps.credits.models import CreditPlan
from apps.songs.models import Tag

# Roles del sistema
for name in ['admin', 'user', 'dj']:
    Role.objects.get_or_create(name=name, defaults={'is_system': True})

# Superadmin
if not User.objects.filter(email='admin@gm.com').exists():
    u = User.objects.create_superuser(email='admin@gm.com', password='admin1234', full_name='Super Admin')
    print(f"Superadmin creado: {u.email}")

# Planes de crédito
CreditPlan.objects.get_or_create(slug='free',   defaults={'name': 'Free',   'credits_per_month': 5,   'price_usd': 0.00})
CreditPlan.objects.get_or_create(slug='pro',    defaults={'name': 'Pro',    'credits_per_month': 50,  'price_usd': 9.00})
CreditPlan.objects.get_or_create(slug='studio', defaults={'name': 'Studio', 'credits_per_month': 200, 'price_usd': 25.00})

# Tags iniciales
tags = [
    ('reggaeton', 'genre'), ('lofi', 'genre'), ('techno', 'genre'), ('pop', 'genre'),
    ('rock', 'genre'), ('hip-hop', 'genre'), ('jazz', 'genre'), ('classical', 'genre'),
    ('sad', 'mood'), ('happy', 'mood'), ('energetic', 'mood'), ('chill', 'mood'),
    ('romantic', 'mood'), ('angry', 'mood'),
    ('fast', 'tempo'), ('slow', 'tempo'), ('120bpm', 'tempo'),
]
for name, cat in tags:
    Tag.objects.get_or_create(name=name, defaults={'category': cat})

print("Seed completado.")
