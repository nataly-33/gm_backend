from __future__ import annotations

from typing import TYPE_CHECKING

from django.db import transaction

if TYPE_CHECKING:
    from apps.users.models import User


def check_balance(user: User, required: int = 1) -> bool:
    """
    Verifica si el usuario tiene suficientes créditos para una operación.

    Args:
        user: Usuario cuyo balance se desea comprobar.
        required: Cantidad mínima de créditos necesarios. Por defecto 1.

    Returns:
        True si el balance del usuario es mayor o igual al requerido,
        False en caso contrario.
    """
    return user.credit_balance >= required


def deduct_credits(
    user: User,
    amount: int,
    reference_id: str | None = None,
    reference_type: str | None = None,
) -> None:
    """
    Descuenta créditos del balance del usuario y registra la transacción.

    La operación es atómica: si falla el registro de la transacción se
    revierte también el cambio en el balance del usuario.

    Args:
        user: Usuario al que se le descontarán los créditos.
        amount: Cantidad de créditos a descontar (valor positivo).
        reference_id: Identificador del recurso que originó el descuento
            (p. ej. el ID de un job o canción). Opcional.
        reference_type: Tipo de operación que originó el descuento
            (p. ej. 'generation', 'stem'). Si no se proporciona se usa
            'generation'.
    """
    from apps.credits.models import CreditTransaction

    with transaction.atomic():
        user.credit_balance -= amount
        user.save(update_fields=["credit_balance"])
        CreditTransaction.objects.create(
            user=user,
            amount=-amount,
            balance_after=user.credit_balance,
            type=reference_type or "generation",
            reference_id=reference_id,
        )


def grant_credits(
    user: User,
    amount: int,
    type: str = "monthly_grant",
    description: str | None = None,
) -> None:
    """
    Agrega créditos al balance del usuario y registra la transacción.

    Se invoca principalmente desde el webhook de Stripe cuando se confirma
    un pago o al ejecutar el grant mensual programado.

    Args:
        user: Usuario al que se le acreditarán los créditos.
        amount: Cantidad de créditos a agregar (valor positivo).
        type: Tipo de transacción. Por defecto 'monthly_grant'.
        description: Descripción opcional de la razón del otorgamiento.
    """
    from apps.credits.models import CreditTransaction

    with transaction.atomic():
        user.credit_balance += amount
        user.save(update_fields=["credit_balance"])
        CreditTransaction.objects.create(
            user=user,
            amount=amount,
            balance_after=user.credit_balance,
            type=type,
            description=description,
        )
