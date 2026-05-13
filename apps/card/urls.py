from django.urls import path
from . import views

from django.urls import path
from . import views

urlpatterns = [
    path('tarjetas',                      views.CrearTarjetaView.as_view()),
    path('tarjetas/usuario/<int:usuario_id>', views.ListarTarjetasView.as_view()),
    path('tarjetas/<int:pk>',             views.TarjetaDetailView.as_view()),
]