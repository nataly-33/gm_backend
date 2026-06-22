from django.db.models import Q
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.karaoke.models import KaraokeTrack, UserKaraokeAccess
from apps.karaoke.serializers import (
    KaraokeCatalogSongSerializer,
    KaraokeGenerateResponseSerializer,
    KaraokeLibrarySerializer,
    KaraokePlaySerializer,
    KaraokeStatusSerializer,
)
from apps.karaoke.services.karaoke_service import (
    InsufficientCreditsError,
    SongNotEligibleError,
    request_karaoke,
)
from apps.songs.models import Song


class CatalogView(APIView):
    """GET /api/karaoke/catalog/ — canciones disponibles para karaoke."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        songs = (
            Song.objects.filter(
                status='ready',
                instrumental=False,
            )
            .filter(Q(is_public=True) | Q(user=request.user))
            .select_related('karaoke_track')
            .order_by('-play_count', '-created_at')
        )
        serializer = KaraokeCatalogSongSerializer(songs, many=True, context={'request': request})
        return Response(serializer.data)


class GenerateKaraokeView(APIView):
    """POST /api/karaoke/songs/<song_id>/generate/ — inicia o paga el karaoke."""

    permission_classes = [IsAuthenticated]

    def post(self, request, song_id):
        try:
            track, already_owned = request_karaoke(request.user, str(song_id))
        except Song.DoesNotExist:
            return Response(
                {'error': 'Canción no encontrada.'},
                status=status.HTTP_404_NOT_FOUND,
            )
        except SongNotEligibleError as exc:
            return Response({'error': str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        except InsufficientCreditsError as exc:
            return Response({'error': str(exc)}, status=status.HTTP_402_PAYMENT_REQUIRED)
        except Exception as exc:
            return Response({'error': str(exc)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        serializer = KaraokeGenerateResponseSerializer(
            track,
            context={'already_owned': already_owned, 'request': request},
        )
        http_status = status.HTTP_200_OK if already_owned else status.HTTP_201_CREATED
        return Response(serializer.data, status=http_status)


class KaraokeStatusView(APIView):
    """GET /api/karaoke/<id>/status/ — estado del track para polling."""

    permission_classes = [IsAuthenticated]

    def get(self, request, id):
        try:
            track = KaraokeTrack.objects.get(id=id)
        except KaraokeTrack.DoesNotExist:
            return Response({'error': 'Karaoke no encontrado.'}, status=status.HTTP_404_NOT_FOUND)

        serializer = KaraokeStatusSerializer(track)
        return Response(serializer.data)


class KaraokePlayView(APIView):
    """GET /api/karaoke/<id>/play/ — URL prefirmada + timestamps (requiere acceso)."""

    permission_classes = [IsAuthenticated]

    def get(self, request, id):
        try:
            track = KaraokeTrack.objects.select_related('song').get(id=id)
        except KaraokeTrack.DoesNotExist:
            return Response({'error': 'Karaoke no encontrado.'}, status=status.HTTP_404_NOT_FOUND)

        if track.status != 'ready':
            return Response(
                {'error': 'El karaoke todavía no está listo.', 'status': track.status},
                status=status.HTTP_409_CONFLICT,
            )

        has_access = UserKaraokeAccess.objects.filter(
            user=request.user, karaoke_track=track
        ).exists()
        if not has_access:
            return Response(
                {'error': 'No tenés acceso a este karaoke.'},
                status=status.HTTP_403_FORBIDDEN,
            )

        serializer = KaraokePlaySerializer(track, context={'request': request})
        return Response(serializer.data)


class KaraokeLibraryView(APIView):
    """GET /api/karaoke/my-library/ — karaokes que el usuario ya tiene."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        accesses = (
            UserKaraokeAccess.objects.filter(user=request.user)
            .select_related('karaoke_track', 'karaoke_track__song')
            .order_by('-granted_at')
        )
        serializer = KaraokeLibrarySerializer(accesses, many=True)
        return Response(serializer.data)
