from django.urls import path
from . import views

urlpatterns = [
    path('roles/<int:rol_id>/permisos/',                      views.RolPermisoListView.as_view()),
    path('roles/<int:rol_id>/permisos/<int:permiso_id>/',     views.RolPermisoDetailView.as_view()),
]