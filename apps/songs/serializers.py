from rest_framework import serializers

from .models import GenerationJob, Song, Tag


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ['id', 'name', 'category', 'emoji']


class SongGenerateSerializer(serializers.Serializer):
    title = serializers.CharField(max_length=200)
    description = serializers.CharField(required=False, allow_null=True, default=None)
    prompt = serializers.CharField(required=False, allow_null=True, default=None)
    lyrics = serializers.CharField(required=False, allow_null=True, default=None)
    described_lyrics = serializers.CharField(required=False, allow_null=True, default=None)
    instrumental = serializers.BooleanField(required=False, default=False)
    guidance_scale = serializers.FloatField(required=False, default=15.0, min_value=1.0, max_value=30.0)
    audio_duration = serializers.FloatField(required=False, default=180.0, min_value=10.0, max_value=300.0)

    def validate(self, data):
        description = data.get('description')
        prompt = data.get('prompt')
        lyrics = data.get('lyrics')
        described_lyrics = data.get('described_lyrics')

        if description:
            return data
        if prompt and lyrics:
            return data
        if prompt and described_lyrics:
            return data
        raise serializers.ValidationError(
            "Provide one of: (description) | (prompt + lyrics) | (prompt + described_lyrics)."
        )


class SongLibrarySerializer(serializers.ModelSerializer):
    tags = TagSerializer(many=True, read_only=True)
    audio_duration = serializers.FloatField(required=False, default=180.0, min_value=10.0, max_value=300.0)


    class Meta:
        model = Song
        fields = ['id', 'title', 'status', 'audio_duration', 'audio_s3_key', 'thumbnail_s3_key', 'tags', 'created_at']


class SongDetailSerializer(serializers.ModelSerializer):
    tags = TagSerializer(many=True, read_only=True)

    class Meta:
        model = Song
        fields = [
            'id', 'title', 'description', 'prompt', 'lyrics', 'described_lyrics',
            'lyrics_source', 'instrumental', 'guidance_scale', 'infer_step',
            'audio_duration', 'seed', 'audio_s3_key', 'thumbnail_s3_key',
            'status', 'is_public', 'play_count', 'like_count', 'tags',
            'created_at', 'updated_at',
        ]


class SongUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Song
        fields = ['title', 'is_public']


class GenerationJobSerializer(serializers.ModelSerializer):
    song_id = serializers.SerializerMethodField()

    class Meta:
        model = GenerationJob
        fields = ['id', 'status', 'song_id', 'error_message']

    def get_song_id(self, obj):
        # Use the raw FK column to avoid an extra query.
        return str(obj.song_id) if obj.song_id else None
