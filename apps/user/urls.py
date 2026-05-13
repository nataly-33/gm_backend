from django.urls import path
from . import views

urlpatterns = [
    path('auth/register-cliente', views.RegisterClienteView.as_view()),
    path('auth/register-admin',   views.RegisterAdminView.as_view()),
    path('auth/login',            views.LoginView.as_view()),
    path('auth/perfil/obtener',   views.ObtenerPerfilView.as_view()),
    path('auth/perfil/modificar', views.ModificarPerfilView.as_view()),
]