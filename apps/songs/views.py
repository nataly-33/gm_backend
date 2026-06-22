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
                title=data["title"],
                description=data.get("description"),
                prompt=data.get("prompt"),
                lyrics=data.get("lyrics"),
                described_lyrics=data.get("described_lyrics"),
                instrumental=data["instrumental"],
                vocal_type=data.get("vocal_type", "auto"),
                language=data.get("language", "auto"),
                guidance_scale=data["guidance_scale"],
                infer_step=data["infer_step"],
                audio_duration=data["audio_duration"],
            )
        except InsufficientCreditsError as e:
            return Response({"detail": str(e)}, status=status.HTTP_402_PAYMENT_REQUIRED)
        except ValueError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(
            {"job_id": str(job.id), "song_id": str(job.song.id), "status": job.status},
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
        return Song.objects.filter(
            user=self.request.user, deleted_at__isnull=True
        ).prefetch_related("tags")


class SongDetailView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = SongDetailSerializer
    http_method_names = ["get", "patch", "delete", "head", "options"]

    def get_queryset(self):
        user = self.request.user
        if self.request.method in ("PATCH", "DELETE"):
            return Song.objects.filter(user=user, deleted_at__isnull=True).prefetch_related("tags")
        from django.db.models import Q
        return Song.objects.filter(
            Q(user=user) | Q(is_public=True), deleted_at__isnull=True
        ).prefetch_related("tags")

    def partial_update(self, request, *args, **kwargs):
        instance = self.get_object()
        was_public = instance.is_public

        in_ser = SongUpdateSerializer(instance, data=request.data, partial=True)
        in_ser.is_valid(raise_exception=True)
        in_ser.save()
        instance.refresh_from_db()

        if not was_public and instance.is_public:
            from apps.notifications.firebase import send_push
            from apps.users.models import User

            tokens = list(
                User.objects.exclude(fcm_token__isnull=True)
                .exclude(fcm_token='')
                .values_list('fcm_token', flat=True)
            )


            for token in tokens:
                try:
                    send_push(
                        token=token,
                        title='🎵 Nueva canción en la comunidad',
                        body=f'"{instance.title}" ya está disponible',
                        data={'song_id': str(instance.id), 'type': 'song_published'}
                    )
                except Exception:
                    pass

        return Response(SongDetailSerializer(instance, context={"request": request}).data)

    def perform_destroy(self, instance):
        instance.soft_delete()


class SongPlayUrlView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        song = get_object_or_404(Song, pk=pk, deleted_at__isnull=True)
        if song.user != request.user and not song.is_public:
            return Response({"detail": "No autorizado."}, status=status.HTTP_403_FORBIDDEN)
        if not song.audio_s3_key:
            return Response(
                {"detail": "Audio not available yet."}, status=status.HTTP_404_NOT_FOUND
            )
        return Response({"url": get_presigned_url(song.audio_s3_key, expiry_seconds=3600)})


class SongThumbnailUrlView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        song = get_object_or_404(Song, pk=pk, deleted_at__isnull=True)
        if song.user != request.user and not song.is_public:
            return Response({"detail": "No autorizado."}, status=status.HTTP_403_FORBIDDEN)
        if not song.thumbnail_s3_key:
            return Response(
                {"detail": "Thumbnail not available yet."}, status=status.HTTP_404_NOT_FOUND
            )
        return Response({"url": get_presigned_url(song.thumbnail_s3_key, expiry_seconds=3600)})


class SongLikeView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        song = get_object_or_404(Song, pk=pk, deleted_at__isnull=True)
        from apps.community.services import toggle_like
        result = toggle_like(request.user, song)
        return Response(result)


class TagListView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = TagSerializer
    queryset = Tag.objects.all().order_by("category", "name")
    pagination_class = None