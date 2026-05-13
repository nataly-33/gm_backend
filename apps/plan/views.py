from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from .serializers import PlanSerializer
from . import services
from utils.permissions import IsAdmin


class PlanListCreateView(APIView):
    def get_permissions(self):
        if self.request.method == 'GET':
            return [IsAuthenticated()]
        return [IsAuthenticated(), IsAdmin()]

    def get(self, request):
        planes = services.listar()
        return Response(PlanSerializer(planes, many=True).data)

    def post(self, request):
        serializer = PlanSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        plan = services.crear(serializer.validated_data)
        return Response(PlanSerializer(plan).data, status=status.HTTP_201_CREATED)


class PlanDetailView(APIView):
    permission_classes = [IsAuthenticated, IsAdmin]

    def put(self, request, pk):
        plan = services.modificar(pk, request.data)
        return Response(PlanSerializer(plan).data)

    def delete(self, request, pk):
        services.eliminar(pk)
        return Response(status=status.HTTP_204_NO_CONTENT)


class CrearStripePriceView(APIView):
    permission_classes = [IsAuthenticated, IsAdmin]

    def post(self, request):
        nombre    = request.data.get('nombre')
        precio    = float(request.data.get('precio'))
        intervalo = request.data.get('intervalo', 'month')
        priceId   = services.crearStripePriceId(nombre, precio, intervalo)
        return Response({'stripePriceId': priceId})


class ListarStripePricesView(APIView):
    permission_classes = [IsAuthenticated, IsAdmin]

    def get(self, request):
        prices = services.listarStripePrices()
        return Response(prices)


class EliminarStripePriceView(APIView):
    permission_classes = [IsAuthenticated, IsAdmin]

    def delete(self, request, priceId):
        resultado = services.eliminarStripePrice(priceId)
        return Response(resultado)