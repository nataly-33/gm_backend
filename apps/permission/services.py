from rest_framework.exceptions import NotFound
from .models import Permiso

def crear_permiso(data):
    return Permiso.objects.create(**data)

def listar_permisos():
    return Permiso.objects.all()

def modificar_permiso(permiso_id, data):
    try:
        permiso = Permiso.objects.get(id=permiso_id)
    except Permiso.DoesNotExist:
        raise NotFound('Permiso no encontrado')
    for field, value in data.items():
        setattr(permiso, field, value)
    permiso.save()
    return permiso

def eliminar_permiso(permiso_id):
    try:
        permiso = Permiso.objects.get(id=permiso_id)
    except Permiso.DoesNotExist:
        raise NotFound('Permiso no encontrado')
    permiso.delete()