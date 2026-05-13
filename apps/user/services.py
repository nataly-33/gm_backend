from django.contrib.auth.hashers import make_password, check_password
from rest_framework.exceptions import ValidationError, AuthenticationFailed, NotFound
from .models import Usuario
from apps.role.models import Rol
from apps.user_role.models import UsuarioRol
from utils.jwt import generate_token


def register_usuario(data, nombre_rol='cliente'):
    if Usuario.objects.filter(email=data['email']).exists():
        raise ValidationError('El email ya está registrado')

    usuario = Usuario.objects.create(
        nombreCompleto=data['nombreCompleto'],
        email=data['email'],
        passwordHash=make_password(data['password']),
        credito=10,
    )

    try:
        rol = Rol.objects.get(nombre=nombre_rol)
        UsuarioRol.objects.create(usuario=usuario, rol=rol)
    except Rol.DoesNotExist:
        pass

    return usuario


def login_usuario(data):
    try:
        usuario = Usuario.objects.get(email=data['email'])
    except Usuario.DoesNotExist:
        raise AuthenticationFailed('Credenciales inválidas')

    if not check_password(data['password'], usuario.passwordHash):
        raise AuthenticationFailed('Credenciales inválidas')

    tokens = generate_token(usuario)
    return tokens, usuario


def obtener_perfil(usuario_id):
    try:
        return Usuario.objects.get(id=usuario_id)
    except Usuario.DoesNotExist:
        raise NotFound('Usuario no encontrado')


def modificar_perfil(usuario_id, data):
    try:
        usuario = Usuario.objects.get(id=usuario_id)
    except Usuario.DoesNotExist:
        raise NotFound('Usuario no encontrado')

    if data.get('nombreCompleto'):
        usuario.nombreCompleto = data['nombreCompleto']

    if data.get('email'):
        if Usuario.objects.filter(email=data['email']).exclude(id=usuario_id).exists():
            raise ValidationError('El email ya está en uso')
        usuario.email = data['email']

    if data.get('password'):
        usuario.passwordHash = make_password(data['password'])

    if data.get('biografia') is not None:
        usuario.biografia = data['biografia']

    if data.get('fotoBase64') is not None:
        usuario.fotoBase64 = data['fotoBase64']

    if data.get('credito') is not None:
        usuario.credito = data['credito']

    rolIds = data.get('rolIds')
    if rolIds is not None:
        UsuarioRol.objects.filter(usuario=usuario).delete()
        for rolId in rolIds:
            try:
                rol = Rol.objects.get(id=rolId)
                UsuarioRol.objects.create(usuario=usuario, rol=rol)
            except Rol.DoesNotExist:
                pass

    usuario.save()
    return usuario