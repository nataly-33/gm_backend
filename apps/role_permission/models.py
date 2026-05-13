from django.db import models
from apps.role.models import Rol
from apps.permission.models import Permiso

class RolPermiso(models.Model):
    rol        = models.ForeignKey(Rol,     on_delete=models.CASCADE, related_name='rol_permisos')
    permiso    = models.ForeignKey(Permiso, on_delete=models.CASCADE, related_name='rol_permisos')
    assignedAt = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table        = 'rol_permisos'
        unique_together = ('rol', 'permiso')