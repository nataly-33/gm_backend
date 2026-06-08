from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAdminUser

class UsageReportView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request):
        from apps.songs.models import Song, GenerationJob
        from apps.users.models import User
        from django.utils import timezone
        from datetime import timedelta

        now = timezone.now()
        last_30 = now - timedelta(days=30)

        return Response({
            'total_users': User.objects.filter(deleted_at__isnull=True).count(),
            'new_users_30d': User.objects.filter(created_at__gte=last_30).count(),
            'total_songs_generated': Song.objects.filter(status='ready').count(),
            'songs_last_30d': Song.objects.filter(status='ready', created_at__gte=last_30).count(),
            'failed_jobs_30d': GenerationJob.objects.filter(status='failed', created_at__gte=last_30).count(),
            'public_songs': Song.objects.filter(is_public=True, status='ready').count(),
        })

class TopSongsView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request):
        from apps.songs.models import Song
        from apps.songs.serializers import SongLibrarySerializer
        songs = Song.objects.filter(status='ready', is_public=True).order_by('-play_count')[:20]
        return Response(SongLibrarySerializer(songs, many=True).data)

class AuditLogView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request):
        from apps.audit.models import AuditLog
        from apps.audit.serializers import AuditLogSerializer
        logs = AuditLog.objects.all().order_by('-created_at')

        action = request.query_params.get('action')
        user_id = request.query_params.get('user_id')

        if action:
            logs = logs.filter(action=action)
        if user_id:
            logs = logs.filter(user_id=user_id)

        return Response(AuditLogSerializer(logs[:100], many=True).data)


class UsersListView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request):
        from apps.users.models import User
        from django.db.models import Q
        search = request.query_params.get('search', '')
        users = User.objects.filter(deleted_at__isnull=True).order_by('-created_at')
        if search:
            users = users.filter(Q(full_name__icontains=search) | Q(email__icontains=search))

        data = [
            {
                'id': str(u.id),
                'full_name': u.full_name,
                'email': u.email,
                'credit_balance': u.credit_balance,
                'is_active': u.is_active,
                'is_staff': u.is_staff,
                'created_at': u.created_at,
            }
            for u in users[:200]
        ]
        return Response(data)
