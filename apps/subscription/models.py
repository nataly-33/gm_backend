from django.db import models
from apps.user.models import Usuario
from apps.plan.models import Plan

class Suscripcion(models.Model):
    usuario              = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name='suscripciones')
    plan                 = models.ForeignKey(Plan,    on_delete=models.CASCADE, related_name='suscripciones')
    stripeSubscriptionId = models.CharField(max_length=255, null=True, blank=True)
    estado               = models.CharField(max_length=50, default='activa')
    currentPeriodStart   = models.DateTimeField(null=True, blank=True)
    currentPeriodEnd     = models.DateTimeField(null=True, blank=True)
    createdAt            = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'suscripciones'

    def __str__(self):
        return f"Suscripcion {self.usuario} - {self.plan} - {self.estado}"