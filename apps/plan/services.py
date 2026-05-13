import stripe
from django.conf import settings
from rest_framework.exceptions import NotFound, APIException
from .models import Plan


class StripePlanError(APIException):
    status_code    = 500
    default_detail = 'Error al procesar plan en Stripe'


def crear(data):
    return Plan.objects.create(**data)


def listar():
    return Plan.objects.all()


def modificar(planId, data):
    try:
        plan = Plan.objects.get(id=planId)
    except Plan.DoesNotExist:
        raise NotFound('Plan no encontrado')
    for field, value in data.items():
        setattr(plan, field, value)
    plan.save()
    return plan


def eliminar(planId):
    try:
        plan = Plan.objects.get(id=planId)
    except Plan.DoesNotExist:
        raise NotFound('Plan no encontrado')
    plan.delete()


# ── Stripe Price ──────────────────────────────────────────────────────────────

def crearStripePriceId(nombre, precioUsd, intervalo='month'):
    stripe.api_key = settings.STRIPE_SECRET_KEY
    try:
        product = stripe.Product.create(name=nombre)

        price = stripe.Price.create(
            product=product.id,
            currency='usd',
            unit_amount=int(precioUsd * 100),
            recurring={'interval': intervalo},
        )
        return price.id

    except stripe.error.StripeError as e:
        raise StripePlanError(detail=f'Error al crear precio en Stripe: {str(e)}')


def listarStripePrices():
    stripe.api_key = settings.STRIPE_SECRET_KEY
    try:
        prices    = stripe.Price.list(active=True, limit=100)
        resultado = []
        for price in prices.auto_paging_iter():
            recurring = price.recurring
            resultado.append({
                'priceId':   price.id,
                'productId': price.product,
                'currency':  price.currency,
                'amount':    price.unit_amount,
                'intervalo': recurring.interval if recurring else 'one_time',
                'activo':    price.active,
            })
        return resultado

    except stripe.error.StripeError as e:
        raise StripePlanError(detail=f'Error al listar precios de Stripe: {str(e)}')


def eliminarStripePrice(stripePriceId):
    stripe.api_key = settings.STRIPE_SECRET_KEY
    try:
        price = stripe.Price.modify(stripePriceId, active=False)
        return {
            'priceId': price.id,
            'activo':  price.active,
            'mensaje': 'Price desactivado correctamente',
        }

    except stripe.error.StripeError as e:
        raise StripePlanError(detail=f'Error al desactivar precio en Stripe: {str(e)}')