from django.urls import path
from . import views

urlpatterns = [
    path('planes',                               views.PlanListCreateView.as_view()),  # ← sin barra
    path('planes/',                              views.PlanListCreateView.as_view()),  # ← con barra
    path('planes/stripe/prices',                 views.ListarStripePricesView.as_view()),
    path('planes/stripe/price',                  views.CrearStripePriceView.as_view()),
    path('planes/stripe/price/<str:price_id>',   views.EliminarStripePriceView.as_view()),
    path('planes/<int:pk>',                      views.PlanDetailView.as_view()),
]