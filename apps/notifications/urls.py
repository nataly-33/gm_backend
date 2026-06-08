from django.urls import path
from apps.notifications.views import (
    NotificationListView, NotificationMarkReadView, NotificationMarkAllReadView,
)

urlpatterns = [
    path('',                      NotificationListView.as_view(),       name='notifications-list'),
    path('<int:notif_id>/read/',  NotificationMarkReadView.as_view(),    name='notification-read'),
    path('read-all/',             NotificationMarkAllReadView.as_view(), name='notifications-read-all'),
]
