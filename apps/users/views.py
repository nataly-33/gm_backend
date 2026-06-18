from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from apps.users.serializers import LoginSerializer, RegisterSerializer, UserProfileSerializer


class RegisterView(APIView):
    """
    Endpoint de registro de nuevos usuarios.

    POST /api/users/register/
    Crea un usuario y retorna tokens JWT de acceso y refresco.
    """

    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        refresh = RefreshToken.for_user(user)
        return Response(
            {
                "user": UserProfileSerializer(user).data,
                "access": str(refresh.access_token),
                "refresh": str(refresh),
            },
            status=status.HTTP_201_CREATED,
        )


class LoginView(APIView):
    """
    Endpoint de autenticación de usuarios existentes.

    POST /api/users/login/
    Valida credenciales y retorna tokens JWT de acceso y refresco.
    """

    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]
        refresh = RefreshToken.for_user(user)
        return Response(
            {
                "access": str(refresh.access_token),
                "refresh": str(refresh),
            }
        )


class MeView(APIView):
    """
    Endpoint para obtener el perfil del usuario autenticado.

    GET /api/users/me/
    Requiere autenticación JWT. Retorna los datos del perfil del usuario actual.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(UserProfileSerializer(request.user).data)


class LogoutView(APIView):
    """
    Endpoint de cierre de sesión.

    POST /api/users/logout/
    Invalida el refresh token JWT del usuario para impedir su reutilización.
    """

    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            token = RefreshToken(request.data.get("refresh"))
            token.blacklist()
        except Exception:
            pass
        return Response(status=status.HTTP_204_NO_CONTENT)


class ChangePasswordView(APIView):
    """
    Endpoint para cambiar la contraseña del usuario autenticado.

    POST /api/users/change-password/
    Requiere la contraseña actual y la nueva contraseña.
    """

    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        old_password = request.data.get("old_password")
        new_password = request.data.get("new_password")
        if not user.check_password(old_password):
            return Response(
                {"detail": "Contraseña actual incorrecta."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        user.set_password(new_password)
        user.save()
        return Response({"detail": "Contraseña actualizada."})
