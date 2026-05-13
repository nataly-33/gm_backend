from django.urls import path
from . import views

urlpatterns = [
    path('roles',           views.RolListCreateView.as_view()),
    path('roles/<int:pk>',  views.RolDetailView.as_view()),
]