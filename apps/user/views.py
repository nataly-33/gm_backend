from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from .serializers import (
    RegisterSerializer, LoginSerializer,
    ModificarPerfilSerializer, UsuarioResponseSerializer
)
from . import services

class RegisterClienteView(APIView):
    permission_classes = []

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        usuario = services.register_usuario(serializer.validated_data, 'cliente')
        return Response(UsuarioResponseSerializer(usuario).data, status=status.HTTP_201_CREATED)


class RegisterAdminView(APIView):
    permission_classes = []

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        usuario = services.register_usuario(serializer.validated_data, 'admin')
        return Response(UsuarioResponseSerializer(usuario).data, status=status.HTTP_201_CREATED)


class LoginView(APIView):
    permission_classes = []

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        tokens, usuario = services.login_usuario(serializer.validated_data)
        return Response({
            'token':   tokens['access'],
            'refresh': tokens['refresh'],
            'usuario': UsuarioResponseSerializer(usuario).data
        })


class ObtenerPerfilView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        usuario = services.obtener_perfil(request.data.get('id'))
        return Response(UsuarioResponseSerializer(usuario).data)


class ModificarPerfilView(APIView):
    permission_classes = [IsAuthenticated]

    def put(self, request):
        serializer = ModificarPerfilSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        usuario_id = request.data.get('id')
        usuario = services.modificar_perfil(usuario_id, serializer.validated_data)
        return Response(UsuarioResponseSerializer(usuario).data)