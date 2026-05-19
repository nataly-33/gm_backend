from django.urls import path
from apps.credits import views

urlpatterns = [
    # API_CONTRACT endpoints
    path('balance/',          views.BalanceView.as_view(),          name='credits-balance'),
    path('plans/',            views.PlanListView.as_view(),          name='credits-plans'),
    path('plans/<int:pk>/',   views.PlanDetailView.as_view(),        name='credits-plan-detail'),
    path('checkout/',         views.CheckoutView.as_view(),          name='credits-checkout'),
    path('stripe-webhook/',   views.StripeWebhookView.as_view(),     name='credits-webhook'),
    path('transactions/',     views.TransactionHistoryView.as_view(),name='credits-transactions'),
    path('subscriptions/',    views.SubscriptionView.as_view(),      name='credits-subscriptions'),

    # Pago directo con PaymentIntent
    path('pay/',              views.PayView.as_view(),               name='credits-pay'),

    # Métodos de pago / tarjetas guardadas
    path('payment-methods/',          views.PaymentMethodView.as_view(),       name='credits-payment-methods'),
    path('payment-methods/<int:pk>/', views.PaymentMethodDetailView.as_view(), name='credits-payment-method-detail'),

    # Admin: gestión de precios en Stripe
    path('stripe/prices/',             views.StripePriceListView.as_view(),   name='credits-stripe-prices'),
    path('stripe/prices/<str:price_id>/', views.StripePriceDetailView.as_view(), name='credits-stripe-price-detail'),
]
