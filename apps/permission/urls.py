from django.urls import path
from . import views

urlpatterns = [
    path('permisos/',           views.PermisoListCreateView.as_view()),
    path('permisos/<int:pk>/',  views.PermisoDetailView.as_view()),
]