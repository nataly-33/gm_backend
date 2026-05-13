from django.urls import path
from . import views

urlpatterns = [
    path('usuarios/<int:usuario_id>/roles/',                  views.UsuarioRolListView.as_view()),
    path('usuarios/<int:usuario_id>/roles/<int:rol_id>/',     views.UsuarioRolDetailView.as_view()),
]