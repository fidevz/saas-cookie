"""
Subscription views.
"""
import logging

import stripe
from django.conf import settings
from rest_framework import status
from rest_framework.exceptions import NotFound, PermissionDenied, ValidationError
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.features import FeatureFlags
from apps.subscriptions.models import Plan, Subscription
from apps.subscriptions.serializers import PlanSerializer, SubscriptionSerializer
from apps.subscriptions.webhooks import handle_webhook
from utils.permissions import IsTenantAdmin

logger = logging.getLogger(__name__)

stripe.api_key = settings.STRIPE_SECRET_KEY


def _require_billing() -> None:
    if not FeatureFlags.billing_enabled():
        raise PermissionDenied("Billing feature is not enabled.")


class ListPlansView(APIView):
    """GET /api/v1/subscriptions/plans/ — public list of available plans."""

    permission_classes = [AllowAny]

    def get(self, request: Request) -> Response:
        plans = Plan.objects.filter(is_active=True).order_by("amount")
        return Response(PlanSerializer(plans, many=True).data)


class CreateCheckoutSessionView(APIView):
    """POST /api/v1/subscriptions/checkout/ — create a Stripe Checkout session."""

    permission_classes = [IsTenantAdmin]

    def post(self, request: Request) -> Response:
        _require_billing()
        tenant = getattr(request, "tenant", None)
        if not tenant:
            raise NotFound("No tenant context.")

        price_id = request.data.get("price_id")
        if not price_id:
            raise ValidationError({"price_id": "This field is required."})

        try:
            plan = Plan.objects.get(stripe_price_id=price_id, is_active=True)
        except Plan.DoesNotExist:
            raise ValidationError({"price_id": "Invalid plan."})

        success_url = request.data.get(
            "success_url", f"https://{settings.BASE_DOMAIN}/billing/success"
        )
        cancel_url = request.data.get(
            "cancel_url", f"https://{settings.BASE_DOMAIN}/billing/cancel"
        )

        # Retrieve or create Stripe customer
        subscription_obj = Subscription.objects.filter(tenant=tenant).first()
        customer_id = subscription_obj.stripe_customer_id if subscription_obj else None

        session_params = {
            "mode": "subscription",
            "payment_method_types": ["card"],
            "line_items": [{"price": price_id, "quantity": 1}],
            "success_url": success_url + "?session_id={CHECKOUT_SESSION_ID}",
            "cancel_url": cancel_url,
            "client_reference_id": str(tenant.pk),
            "metadata": {"tenant_slug": tenant.slug},
        }

        if customer_id:
            session_params["customer"] = customer_id
        else:
            session_params["customer_email"] = request.user.email

        if plan.trial_days:
            session_params["subscription_data"] = {"trial_period_days": plan.trial_days}

        try:
            session = stripe.checkout.Session.create(**session_params)
        except stripe.StripeError as exc:
            logger.error("Stripe checkout error: %s", exc)
            raise ValidationError({"detail": str(exc)})

        return Response({"checkout_url": session.url, "session_id": session.id})


class CustomerPortalView(APIView):
    """POST /api/v1/subscriptions/portal/ — create a Stripe Customer Portal session."""

    permission_classes = [IsTenantAdmin]

    def post(self, request: Request) -> Response:
        _require_billing()
        tenant = getattr(request, "tenant", None)
        if not tenant:
            raise NotFound("No tenant context.")

        try:
            subscription = Subscription.objects.get(tenant=tenant)
        except Subscription.DoesNotExist:
            raise NotFound("No active subscription found.")

        if not subscription.stripe_customer_id:
            raise ValidationError({"detail": "No Stripe customer associated with this tenant."})

        return_url = request.data.get(
            "return_url", f"https://{settings.BASE_DOMAIN}/billing/"
        )

        try:
            portal_session = stripe.billing_portal.Session.create(
                customer=subscription.stripe_customer_id,
                return_url=return_url,
            )
        except stripe.StripeError as exc:
            logger.error("Stripe portal error: %s", exc)
            raise ValidationError({"detail": str(exc)})

        return Response({"portal_url": portal_session.url})


class CancelSubscriptionView(APIView):
    """POST /api/v1/subscriptions/cancel/ — cancel at period end."""

    permission_classes = [IsTenantAdmin]

    def post(self, request: Request) -> Response:
        _require_billing()
        tenant = getattr(request, "tenant", None)
        if not tenant:
            raise NotFound("No tenant context.")

        try:
            subscription = Subscription.objects.get(tenant=tenant)
        except Subscription.DoesNotExist:
            raise NotFound("No active subscription found.")

        if not subscription.stripe_subscription_id:
            raise ValidationError({"detail": "No Stripe subscription found."})

        try:
            stripe.Subscription.modify(
                subscription.stripe_subscription_id,
                cancel_at_period_end=True,
            )
        except stripe.StripeError as exc:
            logger.error("Stripe cancel error: %s", exc)
            raise ValidationError({"detail": str(exc)})

        subscription.status = Subscription.Status.CANCELLING
        subscription.save(update_fields=["status", "updated_at"])

        return Response({"detail": "Subscription will be cancelled at period end."})


class WebhookView(APIView):
    """POST /api/v1/subscriptions/webhook/ — receive and process Stripe webhook events."""

    permission_classes = [AllowAny]
    authentication_classes = []  # No JWT for webhooks

    def post(self, request: Request) -> Response:
        payload = request.body
        sig_header = request.META.get("HTTP_STRIPE_SIGNATURE", "")
        webhook_secret = settings.STRIPE_WEBHOOK_SECRET

        if not webhook_secret:
            logger.warning("STRIPE_WEBHOOK_SECRET is not set — skipping signature check")
            import json

            try:
                event = json.loads(payload)
            except Exception:
                return Response({"error": "Invalid payload"}, status=status.HTTP_400_BAD_REQUEST)
        else:
            try:
                event = stripe.Webhook.construct_event(payload, sig_header, webhook_secret)
            except stripe.error.SignatureVerificationError as exc:
                logger.warning("Stripe signature verification failed: %s", exc)
                return Response(
                    {"error": "Invalid signature"}, status=status.HTTP_400_BAD_REQUEST
                )
            except Exception as exc:
                logger.error("Stripe webhook payload error: %s", exc)
                return Response({"error": "Invalid payload"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            handle_webhook(event)
        except Exception as exc:
            logger.exception("Webhook handler raised: %s", exc)
            return Response(
                {"error": "Webhook processing failed"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        return Response({"received": True})
