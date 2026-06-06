from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from apps.playlists.models import Playlist, PlaylistSong
from apps.playlists.serializers import PlaylistSerializer
from apps.songs.models import Song

class PlaylistListCreateView(generics.ListCreateAPIView):
    serializer_class = PlaylistSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Playlist.objects.filter(user=self.request.user, type='manual')

    def perform_create(self, serializer):
        serializer.save(user=self.request.user, type='manual')

class PlaylistDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = PlaylistSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Playlist.objects.filter(user=self.request.user)

class PlaylistSongsView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, id):
        try:
            playlist = Playlist.objects.get(id=id, user=request.user)
            song_id = request.data.get('song_id')
            position = request.data.get('position', playlist.song_count)
            song = Song.objects.get(id=song_id)

            PlaylistSong.objects.create(playlist=playlist, song=song, position=position)
            playlist.song_count = playlist.playlist_songs.count()
            playlist.save(update_fields=['song_count'])
            return Response({'status': 'ok'})
        except (Playlist.DoesNotExist, Song.DoesNotExist):
            return Response(status=status.HTTP_404_NOT_FOUND)

    def delete(self, request, id, song_id):
        try:
            playlist = Playlist.objects.get(id=id, user=request.user)
            PlaylistSong.objects.filter(playlist=playlist, song_id=song_id).delete()
            playlist.song_count = playlist.playlist_songs.count()
            playlist.save(update_fields=['song_count'])
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Playlist.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

class PlaylistShareView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, id):
        try:
            playlist = Playlist.objects.get(id=id, user=request.user)
            token = playlist.generate_share_token()
            playlist.is_public = True
            playlist.save(update_fields=['is_public'])
            return Response({'share_url': f'/playlists/public/{token}'})
        except Playlist.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

class PublicPlaylistView(generics.RetrieveAPIView):
    serializer_class = PlaylistSerializer
    permission_classes = [AllowAny]
    lookup_field = 'share_token'
    lookup_url_kwarg = 'token'

    def get_queryset(self):
        return Playlist.objects.filter(is_public=True)

class AutoPlaylistListView(generics.ListAPIView):
    serializer_class = PlaylistSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Playlist.objects.filter(user=self.request.user).exclude(type='manual')

class TriggerAutoPlaylistView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        from apps.playlists.services.auto_playlist_service import generate_mood_playlists, generate_genre_playlists
        generate_mood_playlists(request.user)
        generate_genre_playlists(request.user)
        return Response({'status': 'ok'})
