from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .serializers import SuscripcionSerializer
from . import services


class ObtenerSuscripcionesView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, usuario_id):
        suscripciones = services.obtener_por_usuario(usuario_id)
        return Response(SuscripcionSerializer(suscripciones, many=True).data)