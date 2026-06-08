from django.urls import path
from apps.reports.views import UsageReportView, TopSongsView, AuditLogView, UsersListView

urlpatterns = [
    path('usage/', UsageReportView.as_view(), name='reports-usage'),
    path('top-songs/', TopSongsView.as_view(), name='reports-top-songs'),
    path('audit-logs/', AuditLogView.as_view(), name='reports-audit-logs'),
    path('users/', UsersListView.as_view(), name='reports-users'),
]
