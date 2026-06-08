from rest_framework import serializers
from apps.playlists.models import Playlist, PlaylistSong
from apps.songs.serializers import SongLibrarySerializer

class PlaylistSongSerializer(serializers.ModelSerializer):
    song = SongLibrarySerializer(read_only=True)
    
    class Meta:
        model = PlaylistSong
        fields = ['id', 'song', 'position', 'added_at']

class PlaylistSerializer(serializers.ModelSerializer):
    playlist_songs = PlaylistSongSerializer(many=True, read_only=True)

    class Meta:
        model = Playlist
        fields = ['id', 'title', 'description', 'cover_url', 'type', 'is_public', 'share_token', 'song_count', 'playlist_songs', 'created_at', 'updated_at']
        read_only_fields = ['type', 'share_token', 'song_count', 'playlist_songs']
