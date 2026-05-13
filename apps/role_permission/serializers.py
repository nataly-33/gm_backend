from rest_framework import serializers
from .models import RolPermiso

class RolPermisoSerializer(serializers.ModelSerializer):
    class Meta:
        model            = RolPermiso
        fields           = '__all__'
        read_only_fields = ['id', 'assignedAt']