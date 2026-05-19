import uuid
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
from django.db import models


class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra):
        if not email:
            raise ValueError("El email es obligatorio")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra):
        extra.setdefault('is_staff', True)
        extra.setdefault('is_superuser', True)
        return self.create_user(email, password, **extra)


class User(AbstractBaseUser):
    id                = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email             = models.EmailField(unique=True)
    full_name         = models.CharField(max_length=200)
    avatar_url        = models.TextField(blank=True, default='')
    is_active         = models.BooleanField(default=True)
    is_staff          = models.BooleanField(default=False)
    is_superuser      = models.BooleanField(default=False)
    credit_balance    = models.IntegerField(default=0)
    stripe_customer_id = models.CharField(max_length=100, blank=True, default='')
    email_verified_at = models.DateTimeField(null=True, blank=True)
    last_login_at     = models.DateTimeField(null=True, blank=True)
    created_at        = models.DateTimeField(auto_now_add=True)
    updated_at        = models.DateTimeField(auto_now=True)
    deleted_at        = models.DateTimeField(null=True, blank=True)

    USERNAME_FIELD   = 'email'
    REQUIRED_FIELDS  = ['full_name']
    objects          = UserManager()

    def __str__(self):
        return self.email

    # Requerido por Django Admin sin PermissionsMixin
    def has_perm(self, perm, obj=None):
        return self.is_superuser

    def has_module_perms(self, app_label):
        return self.is_superuser


class Role(models.Model):
    name        = models.CharField(max_length=40, unique=True)
    description = models.TextField(blank=True, default='')
    is_system   = models.BooleanField(default=False)


class UserRole(models.Model):
    user        = models.ForeignKey(User, on_delete=models.CASCADE, related_name='user_roles')
    role        = models.ForeignKey(Role, on_delete=models.CASCADE)
    assigned_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [('user', 'role')]
