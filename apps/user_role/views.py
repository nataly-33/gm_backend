from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from .serializers import UsuarioRolSerializer
from . import services
from utils.permissions import IsAdmin

class UsuarioRolListView(APIView):
    permission_classes = [IsAuthenticated, IsAdmin]

    def get(self, request, usuarioId):
        items = services.listar_roles_de_usuario(usuarioId)
        return Response(UsuarioRolSerializer(items, many=True).data)

    def post(self, request, usuarioId):
        rolId = request.data.get('rolId')
        ur = services.asignar_rol(usuarioId, rolId)
        return Response(UsuarioRolSerializer(ur).data, status=status.HTTP_201_CREATED)


class UsuarioRolDetailView(APIView):
    permission_classes = [IsAuthenticated, IsAdmin]

    def delete(self, request, usuarioId, rolId):
        services.revocar_rol(usuarioId, rolId)
        return Response(status=status.HTTP_204_NO_CONTENT)