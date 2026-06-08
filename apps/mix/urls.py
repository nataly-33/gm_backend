from django.urls import path
from apps.mix.views import (
    MixProjectListCreateView, MixProjectDetailView,
    MixClipView, MixClipDetailView, MixReorderView,
    MixExportView, MixExportStatusView,
)

urlpatterns = [
    path('projects/',                                    MixProjectListCreateView.as_view(), name='mix-projects'),
    path('projects/<uuid:mix_id>/',                      MixProjectDetailView.as_view(),     name='mix-project-detail'),
    path('projects/<uuid:mix_id>/clips/',                MixClipView.as_view(),              name='mix-clips'),
    path('projects/<uuid:mix_id>/clips/<uuid:clip_id>/', MixClipDetailView.as_view(),        name='mix-clip-detail'),
    path('projects/<uuid:mix_id>/reorder/',              MixReorderView.as_view(),           name='mix-reorder'),
    path('projects/<uuid:mix_id>/export/',               MixExportView.as_view(),            name='mix-export'),
    path('exports/<uuid:export_id>/',                    MixExportStatusView.as_view(),      name='mix-export-status'),
]
