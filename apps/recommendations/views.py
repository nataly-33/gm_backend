from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from apps.recommendations.models import UserTasteProfile
from apps.songs.models import Song
from apps.songs.serializers import SongLibrarySerializer

class ForYouView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            profile = UserTasteProfile.objects.get(user=request.user)
            top_tag_ids = [t['tag_id'] for t in profile.top_tags]
            songs = Song.objects.filter(is_public=True, status='ready', tags__in=top_tag_ids).exclude(user=request.user).distinct()[:20]
        except UserTasteProfile.DoesNotExist:
            songs = Song.objects.filter(is_public=True, status='ready').order_by('-play_count')[:20]
        
        return Response(SongLibrarySerializer(songs, many=True).data)

class SuggestedTagsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            profile = UserTasteProfile.objects.get(user=request.user)
            tags = profile.top_tags[:5]
            return Response([{'id': t['tag_id'], 'name': t['name']} for t in tags])
        except UserTasteProfile.DoesNotExist:
            return Response([])
