from rest_framework.exceptions import NotFound
from .models import RolPermiso
from apps.role.models import Rol
from apps.permission.models import Permiso

def asignar_permiso(rolId, permisoId):
    try:
        rol     = Rol.objects.get(id=rolId)
        permiso = Permiso.objects.get(id=permisoId)
    except (Rol.DoesNotExist, Permiso.DoesNotExist):
        raise NotFound('Rol o Permiso no encontrado')
    rp, _ = RolPermiso.objects.get_or_create(rol=rol, permiso=permiso)
    return rp

def listar_permisos_de_rol(rolId):
    return RolPermiso.objects.filter(rol_id=rolId)

def revocar_permiso(rolId, permisoId):
    deleted, _ = RolPermiso.objects.filter(rol_id=rolId, permiso_id=permisoId).delete()
    if not deleted:
        raise NotFound('Asignación no encontrada')