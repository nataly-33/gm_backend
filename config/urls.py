"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from rest_framework_simplejwt.views import TokenRefreshView

urlpatterns = [
    path('admin/', admin.site.urls),

    # Auth y usuario
    path('api/', include('apps.user.urls')),

    # Roles y permisos
    path('api/', include('apps.role.urls')),
    path('api/', include('apps.permission.urls')),
    path('api/', include('apps.role_permission.urls')),
    path('api/', include('apps.user_role.urls')),

    # Pagos y tarjetas
    path('api/', include('apps.payment.urls')),
    path('api/', include('apps.card.urls')),

    # Planes y suscripciones
    path('api/', include('apps.plan.urls')),
    path('api/', include('apps.subscription.urls')),

    # Refresh token
    path('api/auth/token/refresh', TokenRefreshView.as_view()),
]