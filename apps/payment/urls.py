from django.urls import path
from . import views

urlpatterns = [
    path('pagos/realizar',                        views.RealizarPagoView.as_view()),
    path('pagos/usuario/<int:usuario_id>',        views.ObtenerPagosPorUsuarioView.as_view()),
]