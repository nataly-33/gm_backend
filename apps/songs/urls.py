from django.urls import path

from . import views

urlpatterns = [
    path('generate/', views.GenerateView.as_view(), name='song-generate'),
    path('jobs/<uuid:pk>/', views.GenerationJobDetailView.as_view(), name='song-job-detail'),
    path('library/', views.SongLibraryView.as_view(), name='song-library'),
    path('tags/', views.TagListView.as_view(), name='song-tags'),
    path('<uuid:pk>/', views.SongDetailView.as_view(), name='song-detail'),
    path('<uuid:pk>/play-url/', views.SongPlayUrlView.as_view(), name='song-play-url'),
    path('<uuid:pk>/thumbnail-url/', views.SongThumbnailUrlView.as_view(), name='song-thumbnail-url'),
    path('<uuid:pk>/like/', views.SongLikeView.as_view(), name='song-like'),
]
