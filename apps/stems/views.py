from rest_framework import status
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.stems.models import StemFile, StemJob
from apps.stems.services.stem_service import (
    FileTooLargeError,
    InsufficientCreditsError,
    request_stem_separation,
)
from ml.modal_client import get_presigned_url


class UploadAndSeparateView(APIView):
    """
    Endpoint para subir un archivo de audio e iniciar la separación de stems.

    POST /api/stems/upload/
    Acepta un archivo multipart. Valida el tamaño y los créditos disponibles,
    sube el archivo a S3 y encola el job de separación. Retorna el job_id.
    """

    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        file = request.FILES.get("file")
        if not file:
            return Response({"error": "No file provided"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            job = request_stem_separation(request.user, file, file.name)
            return Response({"job_id": str(job.id)}, status=status.HTTP_201_CREATED)
        except FileTooLargeError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except InsufficientCreditsError as e:
            return Response({"error": str(e)}, status=status.HTTP_402_PAYMENT_REQUIRED)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class StemJobStatusView(APIView):
    """
    Endpoint para consultar el estado de un job de separación de stems.

    GET /api/stems/jobs/<id>/
    Retorna el estado, porcentaje de progreso, lista de archivos generados
    y mensaje de error si corresponde.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request, id):
        try:
            job = StemJob.objects.prefetch_related("stem_files").get(id=id, user=request.user)
            stem_files = [
                {"stem_type": sf.stem_type, "id": str(sf.id)} for sf in job.stem_files.all()
            ]
            return Response(
                {
                    "status": job.status,
                    "progress_pct": job.progress_pct,
                    "stem_files": stem_files,
                    "error_message": job.error_message,
                }
            )
        except StemJob.DoesNotExist:
            return Response({"error": "Job not found"}, status=status.HTTP_404_NOT_FOUND)


class StemJobListView(APIView):
    """
    Endpoint para listar todos los jobs de separación del usuario autenticado.

    GET /api/stems/jobs/
    Retorna los jobs ordenados por fecha de creación descendente.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        jobs = StemJob.objects.filter(user=request.user).order_by("-created_at")
        data = [
            {
                "id": str(job.id),
                "source_filename": job.source_filename,
                "status": job.status,
                "progress_pct": job.progress_pct,
                "created_at": job.created_at,
                "completed_at": job.completed_at,
            }
            for job in jobs
        ]
        return Response(data)


class StemFileDownloadView(APIView):
    """
    Endpoint para obtener una URL prefirmada de descarga de un stem individual.

    GET /api/stems/files/<id>/download/
    Verifica que el archivo pertenece a un job del usuario autenticado y
    retorna una URL temporal de S3 para reproducir o descargar el stem.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request, id):
        try:
            # First check if the file belongs to a job owned by the user
            stem_file = StemFile.objects.select_related("stem_job").get(
                id=id, stem_job__user=request.user
            )
            url = get_presigned_url(stem_file.audio_s3_key)
            return Response({"url": url})
        except StemFile.DoesNotExist:
            return Response({"error": "File not found"}, status=status.HTTP_404_NOT_FOUND)
