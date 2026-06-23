from django.urls import path

from .views import (
    CatalogView,
    GenerateKaraokeView,
    KaraokeLibraryView,
    KaraokePlayView,
    KaraokeStatusView,
)

urlpatterns = [
    path('catalog/',                       CatalogView.as_view(),        name='karaoke-catalog'),
    path('songs/<uuid:song_id>/generate/', GenerateKaraokeView.as_view(), name='karaoke-generate'),
    path('<uuid:id>/status/',              KaraokeStatusView.as_view(),  name='karaoke-status'),
    path('<uuid:id>/play/',                KaraokePlayView.as_view(),    name='karaoke-play'),
    path('my-library/',                    KaraokeLibraryView.as_view(), name='karaoke-library'),
]
