from rest_framework.exceptions import NotFound
from .models import Rol

def crear_rol(data):
    return Rol.objects.create(**data)

def listar_roles():
    return Rol.objects.all()

def modificar_rol(rolId, data):
    try:
        rol = Rol.objects.get(id=rolId)
    except Rol.DoesNotExist:
        raise NotFound('Rol no encontrado')
    for field, value in data.items():
        setattr(rol, field, value)
    rol.save()
    return rol

def eliminar_rol(rolId):
    try:
        rol = Rol.objects.get(id=rolId)
    except Rol.DoesNotExist:
        raise NotFound('Rol no encontrado')
    rol.delete()