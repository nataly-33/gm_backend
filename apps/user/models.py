from django.db import models

class Usuario(models.Model):
    nombreCompleto   = models.CharField(max_length=255)
    email            = models.EmailField(unique=True)
    passwordHash     = models.CharField(max_length=255)
    credito          = models.IntegerField(default=10)
    fotoBase64       = models.TextField(null=True, blank=True)
    biografia        = models.TextField(null=True, blank=True)
    stripeCustomerId = models.CharField(max_length=255, null=True, blank=True)
    createdAt        = models.DateTimeField(auto_now_add=True)
    updatedAt        = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'usuarios'

    def __str__(self):
        return self.email

    @property
    def is_authenticated(self):
        return True

    @property
    def is_anonymous(self):
        return False