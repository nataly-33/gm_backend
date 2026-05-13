from django.db import models

class Plan(models.Model):
    nombre           = models.CharField(max_length=100, unique=True)
    precio           = models.FloatField(default=0)
    creditoPorMes    = models.IntegerField(default=0)
    creditoIlimitado = models.BooleanField(default=False)
    stripePriceId    = models.CharField(max_length=255, null=True, blank=True)

    class Meta:
        db_table = 'planes'

    def __str__(self):
        return self.nombre