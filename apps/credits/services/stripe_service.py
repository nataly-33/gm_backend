import stripe
import datetime
from django.conf import settings
from rest_framework.exceptions import NotFound, ValidationError, APIException


class StripeError(APIException):
    status_code    = 500
    default_detail = 'Error al procesar operación de Stripe'


# ── Customer helpers ──────────────────────────────────────────────────────────

def _get_or_create_customer(user) -> str:
    """Obtiene o crea el Stripe Customer para el usuario."""
    if user.stripe_customer_id:
        return user.stripe_customer_id
    customer = stripe.Customer.create(email=user.email, name=user.full_name)
    user.stripe_customer_id = customer['id']
    user.save(update_fields=['stripe_customer_id'])
    return customer['id']


# ── Checkout Session (API_CONTRACT: POST /api/credits/checkout/) ──────────────

def create_checkout_session(user, plan_slug: str) -> str:
    """Crea una sesión de Stripe Checkout y devuelve la URL."""
    from apps.credits.models import CreditPlan
    stripe.api_key = settings.STRIPE_SECRET_KEY

    try:
        plan = CreditPlan.objects.get(slug=plan_slug, is_active=True)
    except CreditPlan.DoesNotExist:
        raise NotFound(f"Plan '{plan_slug}' no encontrado")

    if not plan.stripe_price_id:
        raise ValidationError(f"El plan '{plan_slug}' no tiene un precio de Stripe configurado")

    customer_id = _get_or_create_customer(user)

    try:
        session = stripe.checkout.Session.create(
            customer=customer_id,
            client_reference_id=str(user.id),
            mode='subscription',
            line_items=[{'price': plan.stripe_price_id, 'quantity': 1}],
            success_url=getattr(settings, 'STRIPE_SUCCESS_URL', 'http://localhost:5173/credits?success=1'),
            cancel_url=getattr(settings, 'STRIPE_CANCEL_URL', 'http://localhost:5173/credits?cancelled=1'),
            metadata={'user_id': str(user.id), 'plan_slug': plan_slug},
        )
        return session.url
    except stripe.error.StripeError as e:
        raise StripeError(detail=f'Error al crear sesión de pago: {str(e)}')


# ── Webhook ───────────────────────────────────────────────────────────────────

def handle_webhook(payload: bytes, sig_header: str) -> dict:
    """Procesa los eventos de Stripe (invoice.paid, etc.)."""
    from apps.credits.services.credit_service import grant_credits
    from apps.users.models import User

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
    except (ValueError, stripe.error.SignatureVerificationError) as e:
        raise ValidationError(f'Webhook inválido: {str(e)}')

    if event['type'] == 'invoice.paid':
        invoice = event['data']['object']
        meta    = invoice.get('subscription_details', {}).get('metadata', {})
        user_id = meta.get('user_id')
        plan_slug = meta.get('plan_slug', 'pro')

        if user_id:
            try:
                from apps.credits.models import CreditPlan
                user = User.objects.get(id=user_id)
                plan = CreditPlan.objects.get(slug=plan_slug)
                grant_credits(
                    user,
                    amount=plan.credits_per_month,
                    type='stripe_purchase',
                    description=f"Recarga mensual plan {plan.name}",
                )
            except (User.DoesNotExist, Exception):
                pass

    return {'received': True}


# ── Direct payment (POST /api/credits/pay/) ───────────────────────────────────

def process_payment(user, payment_method_id: str, amount: float, currency: str = 'usd'):
    """Cobra directamente con un PaymentIntent de Stripe."""
    from apps.credits.models import Payment
    stripe.api_key = settings.STRIPE_SECRET_KEY

    customer_id = _get_or_create_customer(user)

    try:
        intent = stripe.PaymentIntent.create(
            amount=int(amount * 100),
            currency=currency,
            customer=customer_id,
            payment_method=payment_method_id,
            confirm=True,
            automatic_payment_methods={'enabled': True, 'allow_redirects': 'never'},
        )
        return Payment.objects.create(
            user=user,
            amount=amount,
            currency=currency,
            stripe_payment_intent_id=intent['id'],
            status=intent['status'],
        )
    except stripe.error.StripeError as e:
        raise StripeError(detail=f'Error al realizar pago: {str(e)}')


def get_payments_by_user(user):
    from apps.credits.models import Payment
    return Payment.objects.filter(user=user)


# ── Payment methods / Cards ───────────────────────────────────────────────────

def save_payment_method(user, payment_method_id: str):
    """Adjunta un método de pago al Customer de Stripe y lo guarda en BD."""
    from apps.credits.models import PaymentMethod
    stripe.api_key = settings.STRIPE_SECRET_KEY

    customer_id = _get_or_create_customer(user)

    try:
        pm = stripe.PaymentMethod.retrieve(payment_method_id)
        stripe.PaymentMethod.attach(payment_method_id, customer=customer_id)
        card = pm['card']
        return PaymentMethod.objects.create(
            user=user,
            stripe_payment_method_id=payment_method_id,
            stripe_customer_id=customer_id,
            brand=card['brand'],
            last4=str(card['last4']),
            exp_month=int(card['exp_month']),
            exp_year=int(card['exp_year']),
        )
    except stripe.error.StripeError as e:
        raise StripeError(detail=f'Error al guardar método de pago: {str(e)}')


def get_payment_methods(user):
    from apps.credits.models import PaymentMethod
    return PaymentMethod.objects.filter(user=user)


def delete_payment_method(user, payment_method_id: int):
    from apps.credits.models import PaymentMethod
    stripe.api_key = settings.STRIPE_SECRET_KEY
    try:
        pm = PaymentMethod.objects.get(id=payment_method_id, user=user)
        stripe.PaymentMethod.detach(pm.stripe_payment_method_id)
        pm.delete()
    except PaymentMethod.DoesNotExist:
        raise NotFound('Método de pago no encontrado')
    except stripe.error.StripeError as e:
        raise StripeError(detail=f'Error al eliminar método de pago: {str(e)}')


# ── Plan management (admin) ───────────────────────────────────────────────────

def create_stripe_price(name: str, price_usd: float, interval: str = 'month') -> str:
    """Crea un Product + Price en Stripe y devuelve el price_id."""
    stripe.api_key = settings.STRIPE_SECRET_KEY
    try:
        product = stripe.Product.create(name=name)
        price   = stripe.Price.create(
            product=product.id,
            currency='usd',
            unit_amount=int(price_usd * 100),
            recurring={'interval': interval},
        )
        return price.id
    except stripe.error.StripeError as e:
        raise StripeError(detail=f'Error al crear precio en Stripe: {str(e)}')


def list_stripe_prices() -> list:
    stripe.api_key = settings.STRIPE_SECRET_KEY
    try:
        prices = stripe.Price.list(active=True, limit=100)
        return [
            {
                'price_id':   p.id,
                'product_id': p.product,
                'currency':   p.currency,
                'amount':     p.unit_amount,
                'interval':   p.recurring.interval if p.recurring else 'one_time',
                'active':     p.active,
            }
            for p in prices.auto_paging_iter()
        ]
    except stripe.error.StripeError as e:
        raise StripeError(detail=f'Error al listar precios: {str(e)}')


def deactivate_stripe_price(stripe_price_id: str) -> dict:
    stripe.api_key = settings.STRIPE_SECRET_KEY
    try:
        price = stripe.Price.modify(stripe_price_id, active=False)
        return {'price_id': price.id, 'active': price.active}
    except stripe.error.StripeError as e:
        raise StripeError(detail=f'Error al desactivar precio: {str(e)}')
