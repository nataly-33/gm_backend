import stripe
from django.conf import settings
from rest_framework.exceptions import NotFound, APIException
from .models import Tarjeta
from apps.user.models import Usuario


class StripeTarjetaError(APIException):
    status_code    = 500
    default_detail = 'Error al procesar tarjeta'


def _obtenerOCrearCustomer(usuario):
    if usuario.stripeCustomerId:
        return usuario.stripeCustomerId

    customer = stripe.Customer.create(
        email=usuario.email,
        name=usuario.nombreCompleto,
    )
    usuario.stripeCustomerId = customer['id']
    usuario.save()
    return customer['id']


def crear(usuarioId, paymentMethodId):
    stripe.api_key = settings.STRIPE_SECRET_KEY

    try:
        usuario = Usuario.objects.get(id=usuarioId)
    except Usuario.DoesNotExist:
        raise NotFound('Usuario no encontrado')

    try:
        customerId = _obtenerOCrearCustomer(usuario)

        pm = stripe.PaymentMethod.retrieve(paymentMethodId)

        stripe.PaymentMethod.attach(
            paymentMethodId,
            customer=customerId,
        )

        card = pm['card']

        tarjeta = Tarjeta.objects.create(
            usuario=usuario,
            stripePaymentMethodId=paymentMethodId,
            stripeCustomerId=customerId,
            brand=card['brand'],
            last4=int(card['last4']),
            expMonth=int(card['exp_month']),
            expYear=int(card['exp_year']),
        )

        return tarjeta

    except stripe.error.StripeError as e:
        raise StripeTarjetaError(detail=f'Error al agregar tarjeta: {str(e)}')


def listar(usuarioId):
    return Tarjeta.objects.filter(usuario_id=usuarioId)


def obtener(tarjetaId):
    try:
        return Tarjeta.objects.get(id=tarjetaId)
    except Tarjeta.DoesNotExist:
        raise NotFound('Tarjeta no encontrada')


def eliminar(tarjetaId):
    stripe.api_key = settings.STRIPE_SECRET_KEY

    try:
        tarjeta = obtener(tarjetaId)

        stripe.PaymentMethod.detach(tarjeta.stripePaymentMethodId)

        tarjeta.delete()

    except stripe.error.StripeError as e:
        raise StripeTarjetaError(detail=f'Error al eliminar tarjeta: {str(e)}')