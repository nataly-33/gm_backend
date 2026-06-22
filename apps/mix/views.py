from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from apps.mix.models import MixProject, MixClip, MixExport
from apps.mix.serializers import MixProjectSerializer, MixClipSerializer, MixExportSerializer
from apps.mix.services.mix_service import (
    create_mix_project, add_clip, reorder_clips, remove_clip,
)


class MixProjectListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        qs = MixProject.objects.filter(user=request.user, deleted_at__isnull=True)
        return Response(MixProjectSerializer(qs, many=True).data)

    def post(self, request):
        mix = create_mix_project(
            user=request.user,
            title=request.data.get('title', 'Nuevo mix'),
            description=request.data.get('description'),
            bpm=request.data.get('bpm'),
        )
        return Response(MixProjectSerializer(mix).data, status=status.HTTP_201_CREATED)


class MixProjectDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def _get_mix(self, request, mix_id):
        try:
            return MixProject.objects.get(id=mix_id, user=request.user, deleted_at__isnull=True)
        except MixProject.DoesNotExist:
            return None

    def get(self, request, mix_id):
        mix = self._get_mix(request, mix_id)
        if not mix:
            return Response(status=status.HTTP_404_NOT_FOUND)
        return Response(MixProjectSerializer(mix).data)

    def patch(self, request, mix_id):
        mix = self._get_mix(request, mix_id)
        if not mix:
            return Response(status=status.HTTP_404_NOT_FOUND)

        for field in ['title', 'description', 'bpm']:
            if field in request.data:
                setattr(mix, field, request.data[field])
        mix.save()

        if 'tag_ids' in request.data:
            from apps.songs.models import Tag
            tag_ids = request.data['tag_ids']
            mix.tags.set(Tag.objects.filter(id__in=tag_ids))

        return Response(MixProjectSerializer(mix).data)

    def delete(self, request, mix_id):
        mix = self._get_mix(request, mix_id)
        if not mix:
            return Response(status=status.HTTP_404_NOT_FOUND)
        mix.soft_delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class MixClipView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, mix_id):
        try:
            mix = MixProject.objects.get(id=mix_id, user=request.user, deleted_at__isnull=True)
        except MixProject.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

        end_time_ms = request.data.get('end_time_ms')
        if end_time_ms is None:
            return Response({'detail': 'end_time_ms es requerido.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            clip = add_clip(
                mix_project=mix,
                position=int(request.data.get('position', mix.clips.count())),
                song_id=request.data.get('song_id'),
                stem_file_id=request.data.get('stem_file_id'),
                start_time_ms=int(request.data.get('start_time_ms', 0)),
                end_time_ms=int(end_time_ms),
                fade_in_ms=int(request.data.get('fade_in_ms', 0)),
                fade_out_ms=int(request.data.get('fade_out_ms', 0)),
                volume=float(request.data.get('volume', 1.0)),
            )
        except ValueError as e:
            return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(MixClipSerializer(clip).data, status=status.HTTP_201_CREATED)


class MixClipDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def _get_clip(self, request, mix_id, clip_id):
        try:
            return MixClip.objects.select_related('mix_project').get(
                id=clip_id,
                mix_project__id=mix_id,
                mix_project__user=request.user,
                mix_project__deleted_at__isnull=True,
            )
        except MixClip.DoesNotExist:
            return None

    def patch(self, request, mix_id, clip_id):
        clip = self._get_clip(request, mix_id, clip_id)
        if not clip:
            return Response(status=status.HTTP_404_NOT_FOUND)

        for field in ['start_time_ms', 'end_time_ms', 'fade_in_ms', 'fade_out_ms', 'volume', 'position']:
            if field in request.data:
                setattr(clip, field, request.data[field])

        if clip.end_time_ms <= clip.start_time_ms:
            return Response(
                {'detail': 'end_time_ms debe ser mayor que start_time_ms.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        clip.save()
        return Response(MixClipSerializer(clip).data)

    def delete(self, request, mix_id, clip_id):
        clip = self._get_clip(request, mix_id, clip_id)
        if not clip:
            return Response(status=status.HTTP_404_NOT_FOUND)
        clip.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class MixReorderView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, mix_id):
        try:
            mix = MixProject.objects.get(id=mix_id, user=request.user, deleted_at__isnull=True)
        except MixProject.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

        clip_ids = request.data.get('clip_ids', [])
        if not clip_ids:
            return Response({'detail': 'clip_ids es requerido.'}, status=status.HTTP_400_BAD_REQUEST)

        reorder_clips(mix, clip_ids)
        return Response({'status': 'ok'})


class MixExportView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, mix_id):
        try:
            mix = MixProject.objects.get(id=mix_id, user=request.user, deleted_at__isnull=True)
        except MixProject.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

        if not mix.clips.exists():
            return Response({'detail': 'El mix no tiene clips.'}, status=status.HTTP_400_BAD_REQUEST)

        export = MixExport.objects.create(
            mix_project=mix,
            format=request.data.get('format', 'mp3'),
            quality=request.data.get('quality', '320k'),
            status='queued',
        )

        from apps.mix.tasks import render_mix
        tag_ids = list(mix.tags.values_list('id', flat=True))
        render_mix.delay(str(export.id), tag_ids=tag_ids)

        return Response({'export_id': str(export.id)}, status=status.HTTP_202_ACCEPTED)


class MixExportStatusView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, export_id):
        try:
            export = MixExport.objects.select_related('mix_project').get(
                id=export_id,
                mix_project__user=request.user,
            )
        except MixExport.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

        data = {
            'status':        export.status,
            'format':        export.format,
            'error_message': export.error_message,
        }

        if export.status == 'ready' and export.output_s3_key:
            from ml.modal_client import get_presigned_url
            data['download_url'] = get_presigned_url(export.output_s3_key, expiry_seconds=3600)

        return Response(data)