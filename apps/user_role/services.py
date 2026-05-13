from rest_framework.exceptions import NotFound
from .models import UsuarioRol
from apps.user.models import Usuario
from apps.role.models import Rol

def asignar_rol(usuario_id, rol_id):
    try:
        usuario = Usuario.objects.get(id=usuario_id)
        rol     = Rol.objects.get(id=rol_id)
    except (Usuario.DoesNotExist, Rol.DoesNotExist):
        raise NotFound('Usuario o Rol no encontrado')
    ur, _ = UsuarioRol.objects.get_or_create(usuario=usuario, rol=rol)
    return ur

def listar_roles_de_usuario(usuario_id):
    return UsuarioRol.objects.filter(usuario_id=usuario_id)

def revocar_rol(usuario_id, rol_id):
    deleted, _ = UsuarioRol.objects.filter(usuario_id=usuario_id, rol_id=rol_id).delete()
    if not deleted:
        raise NotFound('Asignación no encontrada')