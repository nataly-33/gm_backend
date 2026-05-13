from rest_framework import serializers
from .models import Usuario

class UsuarioResponseSerializer(serializers.ModelSerializer):
    roles  = serializers.SerializerMethodField()
    rolIds = serializers.SerializerMethodField()

    class Meta:
        model  = Usuario
        fields = [
            'id', 'nombreCompleto', 'email', 'credito',
            'fotoBase64', 'biografia', 'stripeCustomerId',
            'createdAt', 'updatedAt', 'rolIds', 'roles'
        ]

    def get_roles(self, obj):
        return list(obj.usuario_roles.values_list('rol__nombre', flat=True))

    def get_rolIds(self, obj):
        return list(obj.usuario_roles.values_list('rol__id', flat=True))


class RegisterSerializer(serializers.Serializer):
    nombreCompleto = serializers.CharField()
    email          = serializers.EmailField()
    password       = serializers.CharField(write_only=True)


class LoginSerializer(serializers.Serializer):
    email    = serializers.EmailField()
    password = serializers.CharField(write_only=True)


class ModificarPerfilSerializer(serializers.Serializer):
    nombreCompleto   = serializers.CharField(required=False)
    email            = serializers.EmailField(required=False)
    password         = serializers.CharField(required=False, write_only=True)
    biografia        = serializers.CharField(required=False, allow_blank=True)
    fotoBase64       = serializers.CharField(required=False, allow_blank=True)
    credito          = serializers.IntegerField(required=False)
    rolIds           = serializers.ListField(
                           child=serializers.IntegerField(), required=False
                       )