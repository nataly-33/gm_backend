from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from .serializers import RolPermisoSerializer
from . import services
from utils.permissions import IsAdmin

class RolPermisoListView(APIView):
    permission_classes = [IsAuthenticated, IsAdmin]

    def get(self, request, rolId):
        items = services.listar_permisos_de_rol(rolId)
        return Response(RolPermisoSerializer(items, many=True).data)

    def post(self, request, rolId):
        permisoId = request.data.get('permisoId')
        rp = services.asignar_permiso(rolId, permisoId)
        return Response(RolPermisoSerializer(rp).data, status=status.HTTP_201_CREATED)


class RolPermisoDetailView(APIView):
    permission_classes = [IsAuthenticated, IsAdmin]

    def delete(self, request, rolId, permisoId):
        services.revocar_permiso(rolId, permisoId)
        return Response(status=status.HTTP_204_NO_CONTENT)