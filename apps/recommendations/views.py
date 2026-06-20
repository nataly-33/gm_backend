from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from apps.recommendations.models import UserTasteProfile
from apps.songs.models import Song, Tag
from apps.songs.serializers import SongLibrarySerializer


class ForYouView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        from ml.predictor import predict_from_description, is_model_available

        user = request.user
        tag_names = set()

        # 1. Tags del historial de escucha del usuario
        try:
            profile = UserTasteProfile.objects.get(user=user)
            tag_names.update(t['name'] for t in profile.top_tags[:5])
        except UserTasteProfile.DoesNotExist:
            pass

        # 2. Predicción ML sobre descripciones de canciones que creó el usuario.
        #    El modelo local (music_classifier.pkl) infiere qué géneros y moods
        #    caracterizan las canciones que le interesan al usuario.
        if is_model_available():
            recent_descriptions = (
                Song.objects.filter(user=user, description__isnull=False)
                .exclude(description='')
                .values_list('description', flat=True)[:5]
            )
            for desc in recent_descriptions:
                try:
                    pred = predict_from_description(str(desc))
                    tag_names.update(pred['suggested_tags'])
                except Exception:
                    pass

        # 3. Canciones públicas de OTROS usuarios que coincidan con esos tags
        if tag_names:
            songs = (
                Song.objects.filter(
                    is_public=True,
                    status='ready',
                    tags__name__in=tag_names,
                )
                .exclude(user=user)
                .distinct()
                .order_by('-play_count')[:20]
            )
        else:
            songs = (
                Song.objects.filter(is_public=True, status='ready')
                .exclude(user=user)
                .order_by('-play_count')[:20]
            )

        return Response(SongLibrarySerializer(songs, many=True).data)


class SuggestedTagsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        from ml.predictor import predict_from_description, is_model_available

        user = request.user
        tag_names = set()

        # Tags del historial
        try:
            profile = UserTasteProfile.objects.get(user=user)
            tag_names.update(t['name'] for t in profile.top_tags[:5])
        except UserTasteProfile.DoesNotExist:
            pass

        # ML amplía los tags con predicciones sobre las descripciones del usuario
        if is_model_available():
            recent_descriptions = (
                Song.objects.filter(user=user, description__isnull=False)
                .exclude(description='')
                .values_list('description', flat=True)[:3]
            )
            for desc in recent_descriptions:
                try:
                    pred = predict_from_description(str(desc))
                    tag_names.update(pred['suggested_tags'])
                except Exception:
                    pass

        if not tag_names:
            return Response([])

        tags = Tag.objects.filter(name__in=tag_names)
        return Response([{'id': t.id, 'name': t.name} for t in tags])
