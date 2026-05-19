from django.db.models import F
from django.shortcuts import get_object_or_404
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from ml.modal_client import get_presigned_url

from .models import GenerationJob, Song, Tag
from .serializers import (
    GenerationJobSerializer,
    SongDetailSerializer,
    SongGenerateSerializer,
    SongLibrarySerializer,
    SongUpdateSerializer,
    TagSerializer,
)
from .services.generation_service import InsufficientCreditsError, request_generation


class GenerateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = SongGenerateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        try:
            job = request_generation(
                request.user,
                title=data['title'],
                description=data.get('description'),
                prompt=data.get('prompt'),
                lyrics=data.get('lyrics'),
                described_lyrics=data.get('described_lyrics'),
                instrumental=data['instrumental'],
                guidance_scale=data['guidance_scale'],
                audio_duration=data['audio_duration'],
            )
        except InsufficientCreditsError as e:
            return Response({'detail': str(e)}, status=status.HTTP_402_PAYMENT_REQUIRED)
        except ValueError as e:
            return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(
            {'job_id': str(job.id), 'song_id': str(job.song.id), 'status': job.status},
            status=status.HTTP_202_ACCEPTED,
        )


class GenerationJobDetailView(generics.RetrieveAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = GenerationJobSerializer

    def get_queryset(self):
        return GenerationJob.objects.filter(user=self.request.user)


class SongLibraryView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = SongLibrarySerializer

    def get_queryset(self):
        return (
            Song.objects
            .filter(user=self.request.user, deleted_at__isnull=True)
            .prefetch_related('tags')
        )


class SongDetailView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = SongDetailSerializer
    http_method_names = ['get', 'patch', 'delete', 'head', 'options']

    def get_queryset(self):
        return (
            Song.objects
            .filter(user=self.request.user, deleted_at__isnull=True)
            .prefetch_related('tags')
        )

    def partial_update(self, request, *args, **kwargs):
        instance = self.get_object()
        in_ser = SongUpdateSerializer(instance, data=request.data, partial=True)
        in_ser.is_valid(raise_exception=True)
        in_ser.save()
        instance.refresh_from_db()
        return Response(SongDetailSerializer(instance, context={'request': request}).data)

    def perform_destroy(self, instance):
        instance.soft_delete()


class SongPlayUrlView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        song = get_object_or_404(Song, pk=pk, user=request.user, deleted_at__isnull=True)
        if not song.audio_s3_key:
            return Response({'detail': 'Audio not available yet.'}, status=status.HTTP_404_NOT_FOUND)
        return Response({'url': get_presigned_url(song.audio_s3_key, expiry_seconds=3600)})


class SongThumbnailUrlView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        song = get_object_or_404(Song, pk=pk, user=request.user, deleted_at__isnull=True)
        if not song.thumbnail_s3_key:
            return Response({'detail': 'Thumbnail not available yet.'}, status=status.HTTP_404_NOT_FOUND)
        return Response({'url': get_presigned_url(song.thumbnail_s3_key, expiry_seconds=3600)})


class SongLikeView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        # Per-user toggle requires a SongLike model; this atomically increments until then.
        get_object_or_404(Song, pk=pk, deleted_at__isnull=True)
        Song.objects.filter(pk=pk).update(like_count=F('like_count') + 1)
        return Response({'liked': True})


class TagListView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = TagSerializer
    queryset = Tag.objects.all().order_by('category', 'name')
    pagination_class = None
