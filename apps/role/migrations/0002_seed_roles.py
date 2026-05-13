from django.db import migrations

def seed_roles(apps, schema_editor):
    Rol = apps.get_model('role', 'Rol')
    roles = [
        {'nombre': 'admin',   'descripcion': 'Administrador del sistema', 'esSystem': True},
        {'nombre': 'cliente', 'descripcion': 'Cliente estándar',          'esSystem': True},
    ]
    for rol in roles:
        Rol.objects.get_or_create(nombre=rol['nombre'], defaults=rol)

def unseed_roles(apps, schema_editor):
    Rol = apps.get_model('role', 'Rol')
    Rol.objects.filter(nombre__in=['admin', 'cliente']).delete()

class Migration(migrations.Migration):

    dependencies = [
        ('role', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(seed_roles, unseed_roles),
    ]