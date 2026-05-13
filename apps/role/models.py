from django.db import models

class Rol(models.Model):
    nombre      = models.CharField(max_length=100, unique=True)
    descripcion = models.TextField(null=True, blank=True)
    esSystem    = models.BooleanField(default=False)
    createdAt   = models.DateTimeField(auto_now_add=True)
    updatedAt   = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'roles'

    def __str__(self):
        return self.nombre