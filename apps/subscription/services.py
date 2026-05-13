from rest_framework.exceptions import NotFound
from .models import Suscripcion


def obtener_por_usuario(usuario_id):
    return Suscripcion.objects.filter(usuario_id=usuario_id).select_related('plan')


def obtener_activa(usuario_id):
    try:
        return Suscripcion.objects.get(usuario_id=usuario_id, estado='activa')
    except Suscripcion.DoesNotExist:
        raise NotFound('Suscripción activa no encontrada')