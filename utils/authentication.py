from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
from utils.jwt import decode_token
from apps.user.models import Usuario


class JWTAuthentication(BaseAuthentication):
    def authenticate(self, request):
        auth_header = request.META.get('HTTP_AUTHORIZATION', '')

        if not auth_header.startswith('Bearer '):
            return None  # sin token → anónimo

        token = auth_header[7:]

        try:
            payload = decode_token(token)
        except Exception:
            raise AuthenticationFailed('Token inválido o expirado')

        try:
            usuario = Usuario.objects.get(id=payload['user_id'])
        except Usuario.DoesNotExist:
            raise AuthenticationFailed('Usuario no encontrado')

        return (usuario, token)