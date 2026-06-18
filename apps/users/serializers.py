from django.contrib.auth import authenticate
from rest_framework import serializers

from apps.users.models import User


class RegisterSerializer(serializers.ModelSerializer):
    """
    Serializer para el registro de nuevos usuarios.

    Valida los datos de entrada y delega la creación del usuario al servicio
    correspondiente, garantizando que la contraseña sea hasheada correctamente.
    """

    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = User
        fields = ["email", "password", "full_name"]

    def create(self, validated_data):
        from apps.users.services import create_user

        return create_user(
            email=validated_data["email"],
            password=validated_data["password"],
            full_name=validated_data["full_name"],
        )


class LoginSerializer(serializers.Serializer):
    """
    Serializer para la autenticación de usuarios existentes.

    Valida las credenciales de email y contraseña, e inyecta la instancia
    del usuario autenticado en los datos validados bajo la clave 'user'.
    """

    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        user = authenticate(email=data["email"], password=data["password"])
        if not user:
            raise serializers.ValidationError("Credenciales inválidas.")
        if not user.is_active:
            raise serializers.ValidationError("Cuenta desactivada.")
        data["user"] = user
        return data


class UserProfileSerializer(serializers.ModelSerializer):
    """
    Serializer de solo lectura para exponer el perfil público del usuario.

    Incluye el nombre del rol principal del usuario calculado mediante un
    campo de método.
    """

    role = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ["id", "email", "full_name", "avatar_url", "credit_balance", "role", "created_at"]
        read_only_fields = ["id", "email", "credit_balance", "created_at"]

    def get_role(self, obj):
        user_role = obj.user_roles.select_related("role").first()
        return user_role.role.name if user_role else "user"
