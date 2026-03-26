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
from apps.subscriptions.models import Plan, StripeWebhookEvent, Subscription
from apps.subscriptions.serializers import PlanSerializer, SubscriptionSerializer
from apps.subscriptions.webhooks import handle_webhook
from utils.audit import log_action
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


class CurrentSubscriptionView(APIView):
    """GET /api/v1/subscriptions/current/ — return the tenant's current subscription."""

    permission_classes = [IsAuthenticated]

    def get(self, request: Request) -> Response:
        _require_billing()
        tenant = getattr(request, "tenant", None)
        if not tenant:
            raise NotFound("No tenant context.")

        try:
            subscription = Subscription.objects.select_related("plan").get(
                tenant=tenant
            )
        except Subscription.DoesNotExist:
            raise NotFound("No subscription found.")

        return Response(SubscriptionSerializer(subscription).data)


class CreateCheckoutSessionView(APIView):
    """POST /api/v1/subscriptions/checkout/ — create a Stripe Checkout session."""

    permission_classes = [IsTenantAdmin]

    def post(self, request: Request) -> Response:
        _require_billing()
        tenant = getattr(request, "tenant", None)
        if not tenant:
            raise NotFound("No tenant context.")

        plan_id = request.data.get("plan_id")
        if not plan_id:
            raise ValidationError({"plan_id": "This field is required."})

        try:
            plan = Plan.objects.get(pk=plan_id, is_active=True)
        except Plan.DoesNotExist:
            raise ValidationError({"plan_id": "Invalid plan."})

        if not plan.stripe_price_id:
            raise ValidationError({"plan_id": "Plan has no Stripe price configured."})

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
            "line_items": [{"price": plan.stripe_price_id, "quantity": 1}],
            "success_url": success_url + "?session_id={CHECKOUT_SESSION_ID}",
            "cancel_url": cancel_url,
            "client_reference_id": str(tenant.pk),
            "metadata": {"tenant_slug": tenant.slug, "plan_id": str(plan.pk)},
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
            raise ValidationError(
                {"detail": "Payment processing failed. Please try again."}
            )

        log_action(
            actor=request.user,
            action="subscription.checkout_started",
            target=plan.name,
            metadata={"plan_id": plan.pk, "session_id": session.id},
            tenant=tenant,
        )
        return Response({"url": session.url, "session_id": session.id})


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
            raise ValidationError(
                {"detail": "No Stripe customer associated with this tenant."}
            )

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
            raise ValidationError(
                {"detail": "Failed to open billing portal. Please try again."}
            )

        log_action(
            actor=request.user,
            action="subscription.portal_accessed",
            target=subscription.stripe_customer_id,
            tenant=tenant,
        )
        return Response({"url": portal_session.url})


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
            raise ValidationError(
                {"detail": "Failed to cancel subscription. Please try again."}
            )

        subscription.status = Subscription.Status.CANCELLING
        subscription.save(update_fields=["status", "updated_at"])

        log_action(
            actor=request.user,
            action="subscription.cancelled",
            target=subscription.stripe_subscription_id,
            metadata={"source": "user_request"},
            tenant=tenant,
        )

        return Response({"detail": "Subscription will be cancelled at period end."})


class SelectFreePlanView(APIView):
    """POST /api/v1/subscriptions/select-free/ — activate the Free plan for the tenant."""

    permission_classes = [IsTenantAdmin]

    def post(self, request: Request) -> Response:
        _require_billing()
        tenant = getattr(request, "tenant", None)
        if not tenant:
            raise NotFound("No tenant context.")

        if Subscription.objects.filter(tenant=tenant).exists():
            raise ValidationError({"detail": "Tenant already has a subscription."})

        try:
            free_plan = Plan.objects.get(amount=0, is_active=True)
        except Plan.DoesNotExist:
            raise NotFound("No free plan is available.")

        subscription = Subscription.objects.create(
            tenant=tenant,
            plan=free_plan,
            status=Subscription.Status.ACTIVE,
            capabilities=free_plan.capabilities,  # snapshot at subscription time
        )

        log_action(
            actor=request.user,
            action="subscription.acquired",
            target=free_plan.name,
            metadata={"plan_id": free_plan.pk, "source": "free_plan_selection"},
            tenant=tenant,
        )

        return Response(
            SubscriptionSerializer(subscription).data, status=status.HTTP_201_CREATED
        )


class WebhookView(APIView):
    """POST /api/v1/subscriptions/webhook/ — receive and process Stripe webhook events."""

    permission_classes = [AllowAny]
    authentication_classes = []  # No JWT for webhooks

    def post(self, request: Request) -> Response:
        payload = request.body
        sig_header = request.META.get("HTTP_STRIPE_SIGNATURE", "")
        webhook_secret = settings.STRIPE_WEBHOOK_SECRET

        if not webhook_secret:
            logger.error(
                "STRIPE_WEBHOOK_SECRET is not configured. "
                "Set STRIPE_WEBHOOK_SECRET in the environment to enable webhook processing."
            )
            return Response(
                {"error": "Webhook not configured"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
        else:
            try:
                event = stripe.Webhook.construct_event(
                    payload, sig_header, webhook_secret
                )
            except stripe.error.SignatureVerificationError as exc:
                logger.warning("Stripe signature verification failed: %s", exc)
                return Response(
                    {"error": "Invalid signature"}, status=status.HTTP_400_BAD_REQUEST
                )
            except Exception as exc:
                logger.error("Stripe webhook payload error: %s", exc)
                return Response(
                    {"error": "Invalid payload"}, status=status.HTTP_400_BAD_REQUEST
                )

        _, created = StripeWebhookEvent.objects.get_or_create(
            event_id=event["id"],
            defaults={"event_type": event.get("type", "")},
        )
        if not created:
            logger.info("Duplicate Stripe event %s, skipping", event["id"])
            return Response({"received": True})

        try:
            handle_webhook(event)
        except Exception as exc:
            logger.exception("Webhook handler raised: %s", exc)
            return Response(
                {"error": "Webhook processing failed"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        return Response({"received": True})
