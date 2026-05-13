from django.db import models
from apps.user.models import Usuario

class Tarjeta(models.Model):
    usuario                = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name='tarjetas')
    stripePaymentMethodId  = models.CharField(max_length=255)
    stripeCustomerId       = models.CharField(max_length=255)
    brand                  = models.CharField(max_length=50)
    last4                  = models.IntegerField()
    expMonth               = models.IntegerField()
    expYear                = models.IntegerField()
    createdAt              = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'tarjetas'

    def __str__(self):
        return f"{self.brand} **** {self.last4}"