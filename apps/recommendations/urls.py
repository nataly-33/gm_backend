from django.urls import path
from apps.recommendations.views import ForYouView, SuggestedTagsView

urlpatterns = [
    path('for-you/', ForYouView.as_view(), name='for-you'),
    path('suggested-tags/', SuggestedTagsView.as_view(), name='suggested-tags'),
]
