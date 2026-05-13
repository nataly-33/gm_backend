from rest_framework import serializers
from .models import Rol

class RolSerializer(serializers.ModelSerializer):
    class Meta:
        model            = Rol
        fields           = '__all__'
        read_only_fields = ['id', 'createdAt', 'updatedAt']