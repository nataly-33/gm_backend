from rest_framework import serializers
from .models import Permiso

class PermisoSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Permiso
        fields = '__all__'
        read_only_fields = ['id']