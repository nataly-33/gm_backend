from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from .serializers import TarjetaSerializer
from . import services


class CrearTarjetaView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        usuarioId       = request.data.get('usuarioId')
        paymentMethodId = request.data.get('paymentMethodId')
        tarjeta = services.crear(usuarioId, paymentMethodId)
        return Response(TarjetaSerializer(tarjeta).data, status=status.HTTP_201_CREATED)


class ListarTarjetasView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, usuario_id):  # ✅ corregido
        tarjetas = services.listar(usuario_id)
        return Response(TarjetaSerializer(tarjetas, many=True).data)


class TarjetaDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        tarjeta = services.obtener(pk)
        return Response(TarjetaSerializer(tarjeta).data)

    def delete(self, request, pk):
        services.eliminar(pk)
        return Response(status=status.HTTP_204_NO_CONTENT)