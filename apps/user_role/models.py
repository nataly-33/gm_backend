from django.db import models
from apps.user.models import Usuario
from apps.role.models import Rol

class UsuarioRol(models.Model):
    usuario    = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name='usuario_roles')
    rol        = models.ForeignKey(Rol,     on_delete=models.CASCADE, related_name='usuario_roles')
    assignedAt = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table        = 'usuario_roles'
        unique_together = ('usuario', 'rol')