from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, AllowAny

from apps.core.permissions import IsAdmin
from apps.credits.models import CreditPlan, CreditTransaction
from apps.credits.serializers import (
    CreditPlanSerializer, CreditTransactionSerializer,
    PaymentSerializer, PaymentMethodSerializer,
)
from apps.credits.services import stripe_service


# ── Balance ──────────────────────────────────────────────────────────────────

class BalanceView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        subscription = user.subscriptions.filter(status='active').select_related('plan').first()
        return Response({
            'balance': user.credit_balance,
            'plan':    CreditPlanSerializer(subscription.plan).data if subscription else None,
        })


# ── Plans ────────────────────────────────────────────────────────────────────

class PlanListView(APIView):
    def get_permissions(self):
        if self.request.method == 'POST':
            return [IsAuthenticated(), IsAdmin()]
        return [IsAuthenticated()]

    def get(self, request):
        plans = CreditPlan.objects.filter(is_active=True).order_by('price_usd')
        return Response(CreditPlanSerializer(plans, many=True).data)

    def post(self, request):
        serializer = CreditPlanSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        plan = CreditPlan.objects.create(**serializer.validated_data)
        return Response(CreditPlanSerializer(plan).data, status=status.HTTP_201_CREATED)


class PlanDetailView(APIView):
    permission_classes = [IsAuthenticated, IsAdmin]

    def put(self, request, pk):
        try:
            plan = CreditPlan.objects.get(pk=pk)
        except CreditPlan.DoesNotExist:
            return Response({'detail': 'Plan no encontrado'}, status=status.HTTP_404_NOT_FOUND)
        serializer = CreditPlanSerializer(plan, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    def delete(self, request, pk):
        try:
            CreditPlan.objects.get(pk=pk).delete()
        except CreditPlan.DoesNotExist:
            return Response({'detail': 'Plan no encontrado'}, status=status.HTTP_404_NOT_FOUND)
        return Response(status=status.HTTP_204_NO_CONTENT)


# ── Checkout (Stripe Checkout Session) ───────────────────────────────────────

class CheckoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        plan_slug = request.data.get('plan_slug')
        if not plan_slug:
            return Response({'detail': 'plan_slug es requerido'}, status=status.HTTP_400_BAD_REQUEST)
        checkout_url = stripe_service.create_checkout_session(request.user, plan_slug)
        return Response({'checkout_url': checkout_url})


# ── Stripe Webhook (sin JWT) ──────────────────────────────────────────────────

class StripeWebhookView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        sig_header = request.META.get('HTTP_STRIPE_SIGNATURE', '')
        result = stripe_service.handle_webhook(request.body, sig_header)
        return Response(result)


# ── Transactions ──────────────────────────────────────────────────────────────

class TransactionHistoryView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        txs = CreditTransaction.objects.filter(user=request.user)
        return Response(CreditTransactionSerializer(txs, many=True).data)


# ── Direct payment (PaymentIntent) ───────────────────────────────────────────

class PayView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        from apps.credits.models import CreditPlan, UserSubscription
        from apps.credits.services.credit_service import grant_credits
        from django.utils import timezone
        from datetime import timedelta

        payment_method_id = request.data.get('payment_method_id')
        amount            = request.data.get('amount')
        plan_slug         = request.data.get('plan_slug')
        currency          = request.data.get('currency', 'usd')

        if not payment_method_id or not amount:
            return Response({'detail': 'payment_method_id y amount son requeridos'}, status=status.HTTP_400_BAD_REQUEST)

        payment = stripe_service.process_payment(request.user, payment_method_id, float(amount), currency)

        if plan_slug:
            try:
                plan = CreditPlan.objects.get(slug=plan_slug)
                UserSubscription.objects.update_or_create(
                    user=request.user,
                    defaults={
                        'plan':                 plan,
                        'status':               'active',
                        'current_period_start': timezone.now(),
                        'current_period_end':   timezone.now() + timedelta(days=30),
                    }
                )
                grant_credits(
                    request.user,
                    amount=plan.credits_per_month,
                    type='stripe_purchase',
                    description=f"Recarga plan {plan.name}",
                )
            except CreditPlan.DoesNotExist:
                pass

        return Response(PaymentSerializer(payment).data, status=status.HTTP_201_CREATED)

    def get(self, request):
        payments = stripe_service.get_payments_by_user(request.user)
        return Response(PaymentSerializer(payments, many=True).data)


# ── Payment Methods / Cards ───────────────────────────────────────────────────

class PaymentMethodView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        methods = stripe_service.get_payment_methods(request.user)
        return Response(PaymentMethodSerializer(methods, many=True).data)

    def post(self, request):
        payment_method_id = request.data.get('payment_method_id')
        if not payment_method_id:
            return Response({'detail': 'payment_method_id es requerido'}, status=status.HTTP_400_BAD_REQUEST)
        pm = stripe_service.save_payment_method(request.user, payment_method_id)
        return Response(PaymentMethodSerializer(pm).data, status=status.HTTP_201_CREATED)


class PaymentMethodDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, pk):
        stripe_service.delete_payment_method(request.user, pk)
        return Response(status=status.HTTP_204_NO_CONTENT)


# ── Subscriptions ─────────────────────────────────────────────────────────────

class SubscriptionView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        from apps.credits.serializers import UserSubscriptionSerializer
        subs = request.user.subscriptions.select_related('plan').all()
        return Response(UserSubscriptionSerializer(subs, many=True).data)


# ── Stripe admin (prices) ─────────────────────────────────────────────────────

class StripePriceListView(APIView):
    permission_classes = [IsAuthenticated, IsAdmin]

    def get(self, request):
        return Response(stripe_service.list_stripe_prices())

    def post(self, request):
        name      = request.data.get('name')
        price_usd = float(request.data.get('price_usd', 0))
        interval  = request.data.get('interval', 'month')
        price_id  = stripe_service.create_stripe_price(name, price_usd, interval)
        return Response({'stripe_price_id': price_id})


class StripePriceDetailView(APIView):
    permission_classes = [IsAuthenticated, IsAdmin]

    def delete(self, request, price_id):
        result = stripe_service.deactivate_stripe_price(price_id)
        return Response(result)
