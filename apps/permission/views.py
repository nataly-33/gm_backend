from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from .serializers import PermisoSerializer
from . import services
from utils.permissions import IsAdmin

class PermisoListCreateView(APIView):
    permission_classes = [IsAuthenticated, IsAdmin]

    def get(self, request):
        permisos = services.listar_permisos()
        return Response(PermisoSerializer(permisos, many=True).data)

    def post(self, request):
        serializer = PermisoSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        permiso = services.crear_permiso(serializer.validated_data)
        return Response(PermisoSerializer(permiso).data, status=status.HTTP_201_CREATED)


class PermisoDetailView(APIView):
    permission_classes = [IsAuthenticated, IsAdmin]

    def put(self, request, pk):
        permiso = services.modificar_permiso(pk, request.data)
        return Response(PermisoSerializer(permiso).data)

    def delete(self, request, pk):
        services.eliminar_permiso(pk)
        return Response(status=status.HTTP_204_NO_CONTENT)