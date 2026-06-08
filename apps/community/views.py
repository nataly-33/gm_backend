from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from django.shortcuts import get_object_or_404

from apps.songs.models import Song
from apps.community.serializers import CommunitySongSerializer
from apps.community.services import toggle_like, record_play, get_trending


class CommunityFeedView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Feed paginado de canciones públicas, más recientes primero."""
        search = request.query_params.get('search', '')
        tag    = request.query_params.get('tag', '')
        page   = max(int(request.query_params.get('page', 1)), 1)
        limit  = 20
        offset = (page - 1) * limit

        qs = Song.objects.filter(
            is_public=True, status='ready', deleted_at__isnull=True
        ).prefetch_related('tags', 'liked_by').select_related('user').order_by('-created_at')

        if search:
            qs = qs.filter(title__icontains=search)
        if tag:
            qs = qs.filter(tags__name__iexact=tag)

        total   = qs.count()
        songs   = list(qs[offset: offset + limit])
        serializer = CommunitySongSerializer(songs, many=True, context={'request': request})

        return Response({
            'results':  serializer.data,
            'count':    total,
            'page':     page,
            'has_next': offset + limit < total,
        })


class CommunityTrendingView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Top canciones por reproducciones en las últimas 48h."""
        songs = get_trending(limit=20)
        serializer = CommunitySongSerializer(songs, many=True, context={'request': request})
        return Response(serializer.data)


class CommunityStatsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        from apps.songs.models import Song
        from apps.users.models import User
        from apps.community.models import SongPlay
        from django.utils import timezone
        from datetime import timedelta

        today = timezone.now().date()
        return Response({
            'public_songs': Song.objects.filter(is_public=True, status='ready').count(),
            'active_users': User.objects.filter(is_active=True, deleted_at__isnull=True).count(),
            'plays_today':  SongPlay.objects.filter(played_at__date=today).count(),
        })


class SongLikeToggleView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, song_id):
        song = get_object_or_404(Song, pk=song_id, is_public=True, deleted_at__isnull=True)
        result = toggle_like(request.user, song)
        return Response(result)


class SongPlayView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, song_id):
        song = get_object_or_404(Song, pk=song_id, deleted_at__isnull=True)
        duration = int(request.data.get('duration_seconds', 0))
        record_play(request.user, song, duration)
        return Response({'status': 'ok'})
