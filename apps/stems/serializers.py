from rest_framework import serializers
from apps.stems.models import StemJob, StemFile


class StemFileSerializer(serializers.ModelSerializer):
    class Meta:
        model = StemFile
        fields = ['id', 'stem_type', 'duration_seconds', 'file_size_bytes', 'created_at']


class StemJobSerializer(serializers.ModelSerializer):
    class Meta:
        model = StemJob
        fields = [
            'id', 'source_filename', 'source_file_size_bytes',
            'status', 'progress_pct', 'credits_used',
            'created_at', 'started_at', 'completed_at', 'error_message',
        ]


class StemJobDetailSerializer(serializers.ModelSerializer):
    stem_files = StemFileSerializer(many=True, read_only=True)

    class Meta:
        model = StemJob
        fields = [
            'id', 'source_filename', 'source_file_size_bytes', 'model_used',
            'status', 'progress_pct', 'credits_used',
            'created_at', 'started_at', 'completed_at', 'error_message',
            'stem_files',
        ]
