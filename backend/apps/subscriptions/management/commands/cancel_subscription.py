"""
Management command: python manage.py cancel_subscription <email>

Cancels the Stripe subscription for the tenant owned by the given user and
removes the Subscription record from the database.

If the user is only a member (not an owner) of any tenant, the command aborts
and prints the owner's email so you can re-run with the correct address.

Usage:
    python manage.py cancel_subscription user@example.com
    python manage.py cancel_subscription user@example.com --dry-run
"""
import stripe
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError

from apps.subscriptions.models import Subscription
from apps.tenants.models import Tenant, TenantMembership

User = get_user_model()


class Command(BaseCommand):
    help = "Cancel and delete the subscription for the tenant owned by the given user email."

    def add_arguments(self, parser):
        parser.add_argument("email", help="Email of the tenant owner whose subscription to cancel.")
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Preview what would happen without touching Stripe or the database.",
        )

    def handle(self, *args, **options):
        email: str = options["email"]
        dry_run: bool = options["dry_run"]

        if dry_run:
            self.stdout.write(self.style.WARNING("DRY RUN — no changes will be made.\n"))

        # ── 1. Find the user ──────────────────────────────────────────────────
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            raise CommandError(f"No user found with email: {email}")

        # ── 2. Check if they own a tenant ─────────────────────────────────────
        owned_tenants = Tenant.objects.filter(owner=user).select_related("subscription")

        if not owned_tenants.exists():
            # They might be a member somewhere — give a useful hint.
            memberships = TenantMembership.objects.filter(user=user).select_related("tenant__owner")
            if memberships.exists():
                lines = [
                    f"  • {m.tenant.slug} — owner: {m.tenant.owner.email} (role: {m.role})"
                    for m in memberships
                ]
                raise CommandError(
                    f"{email} is not the owner of any tenant.\n"
                    f"They are a member of:\n" + "\n".join(lines) + "\n\n"
                    f"Re-run the command with the owner's email to cancel the subscription."
                )
            raise CommandError(f"{email} is not the owner of any tenant and has no memberships.")

        # ── 3. Find tenant(s) with an active subscription ─────────────────────
        # Normally one user owns one tenant, but handle multiple gracefully.
        tenants_with_sub = [t for t in owned_tenants if hasattr(t, "subscription")]

        if not tenants_with_sub:
            tenant_slugs = ", ".join(t.slug for t in owned_tenants)
            raise CommandError(
                f"{email} owns tenant(s) [{tenant_slugs}] but none have an active subscription."
            )

        if len(tenants_with_sub) > 1:
            slugs = ", ".join(t.slug for t in tenants_with_sub)
            raise CommandError(
                f"{email} owns multiple tenants with subscriptions: {slugs}\n"
                f"Cannot cancel ambiguously — handle each tenant manually."
            )

        tenant = tenants_with_sub[0]
        subscription: Subscription = tenant.subscription

        self.stdout.write(f"Tenant:       {tenant.slug}")
        self.stdout.write(f"Subscription: {subscription.pk} (status: {subscription.status})")
        self.stdout.write(f"Stripe sub:   {subscription.stripe_subscription_id or '(none)'}")

        if dry_run:
            if subscription.stripe_subscription_id:
                self.stdout.write(f"  Would cancel Stripe subscription: {subscription.stripe_subscription_id}")
            self.stdout.write(f"  Would delete local Subscription record (pk={subscription.pk})")
            return

        # ── 4. Cancel in Stripe ───────────────────────────────────────────────
        if subscription.stripe_subscription_id:
            stripe.api_key = settings.STRIPE_SECRET_KEY
            try:
                stripe.Subscription.cancel(subscription.stripe_subscription_id)
                self.stdout.write(self.style.SUCCESS(f"  ✓ Cancelled in Stripe: {subscription.stripe_subscription_id}"))
            except stripe.StripeError as exc:
                raise CommandError(f"Stripe error: {exc}")
        else:
            self.stdout.write("  · No Stripe subscription ID — skipping Stripe cancellation.")

        # ── 5. Delete local record ────────────────────────────────────────────
        subscription.delete()
        self.stdout.write(self.style.SUCCESS(f"  ✓ Subscription record deleted from database."))
