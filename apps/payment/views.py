from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from .serializers import PagoSerializer
from . import services


class RealizarPagoView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        usuarioId       = request.data.get('usuarioId')
        paymentMethodId = request.data.get('paymentMethodId')
        monto           = float(request.data.get('monto'))
        moneda          = request.data.get('moneda', 'usd')

        pago = services.realizar_pago(usuarioId, paymentMethodId, monto, moneda)
        return Response(PagoSerializer(pago).data, status=status.HTTP_201_CREATED)


class ObtenerPagosPorUsuarioView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, usuario_id):  # ✅ corregido
        pagos = services.obtenerPorUsuario(usuario_id)
        return Response(PagoSerializer(pagos, many=True).data)