from rest_framework import serializers
from .models import UsuarioRol

class UsuarioRolSerializer(serializers.ModelSerializer):
    class Meta:
        model            = UsuarioRol
        fields           = '__all__'
        read_only_fields = ['id', 'assignedAt']