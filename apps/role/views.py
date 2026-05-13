from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from .serializers import RolSerializer
from . import services
from utils.permissions import IsAdmin

class RolListCreateView(APIView):
    permission_classes = [IsAuthenticated, IsAdmin]

    def get(self, request):
        roles = services.listar_roles()
        return Response(RolSerializer(roles, many=True).data)

    def post(self, request):
        serializer = RolSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        rol = services.crear_rol(serializer.validated_data)
        return Response(RolSerializer(rol).data, status=status.HTTP_201_CREATED)


class RolDetailView(APIView):
    permission_classes = [IsAuthenticated, IsAdmin]

    def put(self, request, pk):
        rol = services.modificar_rol(pk, request.data)
        return Response(RolSerializer(rol).data)

    def delete(self, request, pk):
        services.eliminar_rol(pk)
        return Response(status=status.HTTP_204_NO_CONTENT)