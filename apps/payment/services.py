import stripe
import datetime
from django.conf import settings
from rest_framework.exceptions import NotFound, ValidationError, APIException
from .models import Pago
from apps.user.models import Usuario
from apps.plan.models import Plan
from apps.subscription.models import Suscripcion


class StripePaymentError(APIException):
    status_code    = 500
    default_detail = 'Error al realizar pago'


def realizar_pago(usuarioId, paymentMethodId, monto, moneda='usd'):
    stripe.api_key = settings.STRIPE_SECRET_KEY

    try:
        usuario = Usuario.objects.get(id=usuarioId)
    except Usuario.DoesNotExist:
        raise NotFound('Usuario no encontrado')

    if not usuario.stripeCustomerId:
        raise ValidationError('El usuario no tiene Stripe Customer asociado')

    try:
        intent = stripe.PaymentIntent.create(
            amount=int(monto * 100),
            currency=moneda,
            customer=usuario.stripeCustomerId,
            payment_method=paymentMethodId,
            confirm=True,
            automatic_payment_methods={
                'enabled':         True,
                'allow_redirects': 'never',
            },
        )

        pago = Pago.objects.create(
            usuario=usuario,
            monto=monto,
            moneda=moneda,
            stripePaymentIntentId=intent['id'],
            estado=intent['status'],
        )

        try:
            planPro = Plan.objects.get(nombre__iexact='pro')
            ahora   = datetime.datetime.now()
            unMes   = ahora + datetime.timedelta(days=30)

            sub, created = Suscripcion.objects.get_or_create(
                usuario=usuario,
                estado='activa',
                defaults={
                    'plan':               planPro,
                    'currentPeriodStart': ahora,
                    'currentPeriodEnd':   unMes,
                }
            )
            if not created:
                sub.plan               = planPro
                sub.currentPeriodStart = ahora
                sub.currentPeriodEnd   = unMes
                sub.save()
        except Plan.DoesNotExist:
            pass

        return pago

    except stripe.error.StripeError as e:
        print(f">>> ERROR STRIPE: {type(e).__name__} - {str(e)}")
        raise StripePaymentError(detail=f'Error al realizar pago: {str(e)}')


def obtenerPorUsuario(usuarioId):
    return Pago.objects.filter(usuario_id=usuarioId)