from django.db import transaction


def check_balance(user, required: int = 1) -> bool:
    """Persona B importa esto para validar antes de generar."""
    return user.credit_balance >= required


def deduct_credits(user, amount: int, reference_id: str = None, reference_type: str = None):
    """Descuenta créditos y registra la transacción. Operación atómica."""
    from apps.credits.models import CreditTransaction
    with transaction.atomic():
        user.credit_balance -= amount
        user.save(update_fields=['credit_balance'])
        CreditTransaction.objects.create(
            user=user,
            amount=-amount,
            balance_after=user.credit_balance,
            type=reference_type or 'generation',
            reference_id=reference_id,
        )


def grant_credits(user, amount: int, type: str = 'monthly_grant', description: str = None):
    """Agrega créditos al usuario. Se llama desde el webhook de Stripe."""
    from apps.credits.models import CreditTransaction
    with transaction.atomic():
        user.credit_balance += amount
        user.save(update_fields=['credit_balance'])
        CreditTransaction.objects.create(
            user=user,
            amount=amount,
            balance_after=user.credit_balance,
            type=type,
            description=description,
        )
