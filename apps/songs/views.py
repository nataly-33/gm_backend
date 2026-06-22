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
    """
    Endpoint para solicitar la generación de una nueva canción con IA.

    POST /api/songs/generate/
    Valida los parámetros de generación, descuenta créditos del usuario y
    encola el job de generación. Retorna el job_id, song_id y el estado inicial.
    """

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
    """
    Endpoint para consultar el estado de un job de generación de canción.

    GET /api/songs/jobs/<pk>/
    Solo retorna jobs pertenecientes al usuario autenticado.
    """

    permission_classes = [IsAuthenticated]
    serializer_class = GenerationJobSerializer

    def get_queryset(self):
        return GenerationJob.objects.filter(user=self.request.user)



class SongLibraryView(generics.ListAPIView):
    """
    Endpoint para listar la biblioteca de canciones del usuario autenticado.

    GET /api/songs/
    Retorna únicamente las canciones propias que no han sido eliminadas (soft delete).
    """

    permission_classes = [IsAuthenticated]
    serializer_class = SongLibrarySerializer

    def get_queryset(self):
        return Song.objects.filter(
            user=self.request.user, deleted_at__isnull=True
        ).prefetch_related("tags")


class SongDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Endpoint para obtener, actualizar parcialmente o eliminar una canción.

    GET /api/songs/<pk>/    - Retorna canciones propias o públicas de otros usuarios.
    PATCH /api/songs/<pk>/  - Actualiza título, tags u otros campos editables.
                              Solo el dueño puede modificar.
    DELETE /api/songs/<pk>/ - Realiza un soft delete. Solo el dueño puede eliminar.
    """

    permission_classes = [IsAuthenticated]
    serializer_class = SongDetailSerializer
    http_method_names = ["get", "patch", "delete", "head", "options"]

    def get_queryset(self):
        user = self.request.user
        if self.request.method in ("PATCH", "DELETE"):
            # Solo el dueño puede modificar o borrar
            return Song.objects.filter(user=user, deleted_at__isnull=True).prefetch_related("tags")
        # GET: propias o públicas de otros
        from django.db.models import Q

        return Song.objects.filter(
            Q(user=user) | Q(is_public=True), deleted_at__isnull=True
        ).prefetch_related("tags")

    def partial_update(self, request, *args, **kwargs):
        instance = self.get_object()
        in_ser = SongUpdateSerializer(instance, data=request.data, partial=True)
        in_ser.is_valid(raise_exception=True)
        in_ser.save()
        instance.refresh_from_db()
        return Response(SongDetailSerializer(instance, context={"request": request}).data)

    def perform_destroy(self, instance):
        instance.soft_delete()


class SongPlayUrlView(APIView):
    """
    Endpoint para obtener una URL temporal de reproducción del audio de una canción.

    GET /api/songs/<pk>/play/
    Retorna una URL prefirmada de S3 válida por 1 hora. Accesible para el
    dueño de la canción o cualquier usuario si la canción es pública.
    """

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
    """
    Endpoint para obtener una URL temporal de la imagen de portada de una canción.

    GET /api/songs/<pk>/thumbnail/
    Retorna una URL prefirmada de S3 válida por 1 hora. Accesible para el
    dueño de la canción o cualquier usuario si la canción es pública.
    """

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
    """
    Endpoint para dar o quitar like a una canción (toggle).

    POST /api/songs/<pk>/like/
    Si el usuario ya dio like, lo elimina. Si no lo había dado, lo agrega.
    Retorna el estado actual del like y el contador actualizado.
    """

    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        song = get_object_or_404(Song, pk=pk, deleted_at__isnull=True)
        from apps.community.services import toggle_like

        result = toggle_like(request.user, song)
        return Response(result)


class TagListView(generics.ListAPIView):
    """
    Endpoint para listar todos los tags disponibles en el sistema.

    GET /api/songs/tags/
    Retorna los tags ordenados por categoría y nombre. Sin paginación.
    """

    permission_classes = [IsAuthenticated]
    serializer_class = TagSerializer
    queryset = Tag.objects.all().order_by("category", "name")
    pagination_class = None
