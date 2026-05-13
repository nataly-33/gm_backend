from django.urls import path
from . import views

urlpatterns = [
    path('suscripciones/usuario/<int:usuario_id>', views.ObtenerSuscripcionesView.as_view()),
]