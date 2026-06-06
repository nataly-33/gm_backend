from django.urls import path
from apps.playlists.views import (
    PlaylistListCreateView, PlaylistDetailView, PlaylistSongsView, 
    PlaylistShareView, PublicPlaylistView, AutoPlaylistListView, TriggerAutoPlaylistView
)

urlpatterns = [
    path('', PlaylistListCreateView.as_view(), name='playlist-list-create'),
    path('<uuid:pk>/', PlaylistDetailView.as_view(), name='playlist-detail'),
    path('<uuid:id>/songs/', PlaylistSongsView.as_view(), name='playlist-songs'),
    path('<uuid:id>/songs/<uuid:song_id>/', PlaylistSongsView.as_view(), name='playlist-songs-delete'),
    path('<uuid:id>/share/', PlaylistShareView.as_view(), name='playlist-share'),
    path('public/<str:token>/', PublicPlaylistView.as_view(), name='playlist-public'),
    path('auto/', AutoPlaylistListView.as_view(), name='playlist-auto-list'),
    path('auto/generate/', TriggerAutoPlaylistView.as_view(), name='playlist-auto-generate'),
]
