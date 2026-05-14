from django.db import models
from django.conf import settings
from apps.core.models import BaseModel


class CreditPlan(models.Model):
    slug              = models.CharField(max_length=20, unique=True)
    name              = models.CharField(max_length=80)
    credits_per_month = models.IntegerField()
    price_usd         = models.DecimalField(max_digits=8, decimal_places=2)
    stripe_price_id   = models.CharField(max_length=255, blank=True, default='')
    features          = models.JSONField(default=list)
    is_active         = models.BooleanField(default=True)

    class Meta:
        db_table = 'credit_plans'

    def __str__(self):
        return self.name


class UserSubscription(BaseModel):
    user                   = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='subscriptions')
    plan                   = models.ForeignKey(CreditPlan, on_delete=models.PROTECT, related_name='subscriptions')
    stripe_subscription_id = models.CharField(max_length=255, null=True, blank=True)
    stripe_customer_id     = models.CharField(max_length=255, null=True, blank=True)
    status                 = models.CharField(max_length=20, default='active')
    current_period_start   = models.DateTimeField(null=True, blank=True)
    current_period_end     = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'user_subscriptions'

    def __str__(self):
        return f"{self.user} — {self.plan.name} ({self.status})"


class CreditTransaction(models.Model):
    user           = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='credit_transactions')
    amount         = models.IntegerField()
    balance_after  = models.IntegerField()
    type           = models.CharField(max_length=30)
    reference_id   = models.UUIDField(null=True, blank=True)
    reference_type = models.CharField(max_length=30, blank=True, default='')
    description    = models.TextField(blank=True, default='')
    created_at     = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'credit_transactions'
        ordering = ['-created_at']


class Payment(models.Model):
    user                     = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='payments')
    amount                   = models.DecimalField(max_digits=8, decimal_places=2)
    currency                 = models.CharField(max_length=10, default='usd')
    stripe_payment_intent_id = models.CharField(max_length=255)
    status                   = models.CharField(max_length=50)
    created_at               = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'payments'
        ordering = ['-created_at']


class PaymentMethod(models.Model):
    user                     = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='payment_methods')
    stripe_payment_method_id = models.CharField(max_length=255)
    stripe_customer_id       = models.CharField(max_length=255)
    brand                    = models.CharField(max_length=50)
    last4                    = models.CharField(max_length=4)
    exp_month                = models.IntegerField()
    exp_year                 = models.IntegerField()
    is_default               = models.BooleanField(default=False)
    created_at               = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'payment_methods'
