from datetime import datetime, timedelta
from django.conf import settings
import jwt as pyjwt

def generate_token(usuario):
    now = datetime.utcnow()

    access_payload = {
        'user_id': usuario.id,
        'email':   usuario.email,
        'exp':     now + timedelta(hours=3),
        'iat':     now,
        'token_type': 'access',
    }

    refresh_payload = {
        'user_id': usuario.id,
        'email':   usuario.email,
        'exp':     now + timedelta(days=7),
        'iat':     now,
        'token_type': 'refresh',
    }

    secret = settings.SECRET_KEY

    return {
        'access':  pyjwt.encode(access_payload,  secret, algorithm='HS256'),
        'refresh': pyjwt.encode(refresh_payload, secret, algorithm='HS256'),
    }


def decode_token(token):
    return pyjwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])