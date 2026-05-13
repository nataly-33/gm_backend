from rest_framework import serializers
from .models import Suscripcion

class SuscripcionSerializer(serializers.ModelSerializer):
    planNombre = serializers.SerializerMethodField()

    class Meta:
        model  = Suscripcion
        fields = '__all__'
        read_only_fields = ['id', 'createdAt']

    def get_planNombre(self, obj):
        return obj.plan.nombre if obj.plan else None