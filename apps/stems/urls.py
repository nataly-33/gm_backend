from django.urls import path
from apps.stems.views import UploadAndSeparateView, StemJobStatusView, StemJobListView, StemFileDownloadView

urlpatterns = [
    path('separate/', UploadAndSeparateView.as_view(), name='stem-separate'),
    path('jobs/', StemJobListView.as_view(), name='stem-job-list'),
    path('jobs/<uuid:id>/', StemJobStatusView.as_view(), name='stem-job-status'),
    path('files/<uuid:id>/download-url/', StemFileDownloadView.as_view(), name='stem-file-download'),
]
