from django.db import models
from apps.user.models import Usuario

class Pago(models.Model):
    usuario                = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name='pagos')
    monto                  = models.FloatField()
    moneda                 = models.CharField(max_length=10, default='usd')
    stripePaymentIntentId  = models.CharField(max_length=255)
    estado                 = models.CharField(max_length=50)
    createdAt              = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'pagos'

    def __str__(self):
        return f"Pago {self.id} - {self.estado}"