from rest_framework import serializers
from apps.audit.models import AuditLog


class AuditLogSerializer(serializers.ModelSerializer):
    user_email = serializers.SerializerMethodField()

    class Meta:
        model  = AuditLog
        fields = ['id', 'user_email', 'action', 'resource_type', 'resource_id', 'ip_address', 'details', 'created_at']

    def get_user_email(self, obj):
        return obj.user.email if obj.user else '—'
