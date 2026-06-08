from django.urls import path
from apps.community.views import (
    CommunityFeedView, CommunityTrendingView, CommunityStatsView,
    SongLikeToggleView, SongPlayView,
)

urlpatterns = [
    path('feed/',                      CommunityFeedView.as_view(),     name='community-feed'),
    path('trending/',                  CommunityTrendingView.as_view(), name='community-trending'),
    path('stats/',                     CommunityStatsView.as_view(),    name='community-stats'),
    path('songs/<uuid:song_id>/like/', SongLikeToggleView.as_view(),    name='community-like'),
    path('songs/<uuid:song_id>/play/', SongPlayView.as_view(),          name='community-play'),
]
