from rest_framework import serializers

from apps.karaoke.models import KaraokeTrack, UserKaraokeAccess


class KaraokeGenerateResponseSerializer(serializers.ModelSerializer):
    """Respuesta del endpoint POST generate/."""
    karaoke_id   = serializers.UUIDField(source='id')
    already_owned = serializers.SerializerMethodField()

    class Meta:
        model  = KaraokeTrack
        fields = ['karaoke_id', 'status', 'already_owned']

    def get_already_owned(self, obj) -> bool:
        return self.context.get('already_owned', False)


class KaraokeStatusSerializer(serializers.ModelSerializer):
    """Respuesta del endpoint GET status/ (polling)."""
    class Meta:
        model  = KaraokeTrack
        fields = ['id', 'status', 'error_message']


class KaraokePlaySerializer(serializers.ModelSerializer):
    """Respuesta del endpoint GET play/ — incluye URL prefirmada y timestamps."""
    instrumental_url = serializers.SerializerMethodField()
    song             = serializers.SerializerMethodField()

    class Meta:
        model  = KaraokeTrack
        fields = ['id', 'instrumental_url', 'lyrics', 'lyrics_timestamps', 'song']

    def get_instrumental_url(self, obj) -> str | None:
        from ml.modal_client import get_presigned_url
        if obj.instrumental_s3_key:
            return get_presigned_url(obj.instrumental_s3_key, expiry_seconds=3600)
        return None

    def get_song(self, obj) -> dict:
        return {
            'id':       str(obj.song_id),
            'title':    obj.song.title,
            'duration': obj.song.audio_duration,
        }


class KaraokeCatalogSongSerializer(serializers.Serializer):
    """Un ítem del catálogo de canciones disponibles para karaoke."""
    song_id        = serializers.UUIDField(source='id')
    title          = serializers.CharField()
    duration       = serializers.FloatField(source='audio_duration')
    thumbnail_url  = serializers.SerializerMethodField()
    has_lyrics     = serializers.SerializerMethodField()
    karaoke_status = serializers.SerializerMethodField()

    def get_thumbnail_url(self, obj) -> str | None:
        from ml.modal_client import get_presigned_url
        if obj.thumbnail_s3_key:
            return get_presigned_url(obj.thumbnail_s3_key, expiry_seconds=3600)
        return None

    def get_has_lyrics(self, obj) -> bool:
        return bool(obj.lyrics)

    def get_karaoke_status(self, obj) -> str | None:
        try:
            return obj.karaoke_track.status
        except KaraokeTrack.DoesNotExist:
            return None


class KaraokeLibrarySerializer(serializers.ModelSerializer):
    """Un ítem de la biblioteca personal de karaokes del usuario."""
    karaoke_id    = serializers.UUIDField(source='karaoke_track.id')
    song_id       = serializers.UUIDField(source='karaoke_track.song.id')
    song_title    = serializers.CharField(source='karaoke_track.song.title')
    thumbnail_url = serializers.SerializerMethodField()
    status        = serializers.CharField(source='karaoke_track.status')

    class Meta:
        model  = UserKaraokeAccess
        fields = ['karaoke_id', 'song_id', 'song_title', 'thumbnail_url', 'status', 'granted_at']

    def get_thumbnail_url(self, obj) -> str | None:
        from ml.modal_client import get_presigned_url
        key = obj.karaoke_track.song.thumbnail_s3_key
        if key:
            return get_presigned_url(key, expiry_seconds=3600)
        return None
