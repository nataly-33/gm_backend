from django.db import models

class Permiso(models.Model):
    codigo      = models.CharField(max_length=100, unique=True)
    descripcion = models.TextField(null=True, blank=True)
    modulo      = models.CharField(max_length=100)

    class Meta:
        db_table = 'permisos'

    def __str__(self):
        return self.codigo