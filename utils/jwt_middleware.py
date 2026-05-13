# utils/jwt_middleware.py  ← ya no se usa como middleware, queda de legacy
from utils.jwt import decode_token
from apps.user.models import Usuario


class JwtAuthMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        return self.get_response(request)