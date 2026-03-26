"""
Management command: python manage.py sync_stripe_plans

Syncs every active Plan in the database to Stripe:
- Creates a Stripe Product if none exists yet.
- Creates a Stripe Price if none exists yet.
- If the price in the database differs from the live Stripe price, archives the
  old price and creates a new one attached to the same product, then updates the
  local stripe_price_id. Old prices are NEVER deleted from Stripe.

Usage:
    python manage.py sync_stripe_plans           # live run
    python manage.py sync_stripe_plans --dry-run # preview without touching Stripe
"""
import stripe
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from apps.subscriptions.models import Plan

# Placeholder IDs written by the seed command — treat these as "not configured".
_PLACEHOLDER_PREFIXES = ("price_starter", "price_pro", "prod_starter", "prod_pro")


def _is_placeholder(value: str) -> bool:
    return not value or any(value.startswith(p) for p in _PLACEHOLDER_PREFIXES)


class Command(BaseCommand):
    help = (
        "Sync plans to Stripe: create products/prices as needed and rotate prices "
        "when the amount changes. Old prices are archived, never deleted."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Preview what would happen without calling Stripe.",
        )

    def handle(self, *args, **options):
        dry_run: bool = options["dry_run"]

        if not settings.STRIPE_SECRET_KEY:
            raise CommandError(
                "STRIPE_SECRET_KEY is not set. Configure it in your .env before running this command."
            )

        stripe.api_key = settings.STRIPE_SECRET_KEY

        if dry_run:
            self.stdout.write(self.style.WARNING("DRY RUN — no changes will be made to Stripe or the database.\n"))

        plans = Plan.objects.filter(is_active=True).order_by("amount")

        if not plans.exists():
            self.stdout.write("No active plans found. Run `make seed` first.")
            return

        created_count = 0
        updated_count = 0
        skipped_count = 0

        for plan in plans:
            self.stdout.write(f"\n{'─' * 50}")
            self.stdout.write(f"Plan: {self.style.MIGRATE_HEADING(plan.name)} (${plan.amount}/{plan.interval})")

            needs_product = _is_placeholder(plan.stripe_product_id)
            needs_price = _is_placeholder(plan.stripe_price_id)
            expected_unit_amount = int(plan.amount * 100)
            product_id = plan.stripe_product_id
            price_id = plan.stripe_price_id
            changed = False

            # ── 1. Product ────────────────────────────────────────────────────
            if needs_product:
                if dry_run:
                    self.stdout.write(f"  Would create Stripe product: name='{plan.name}'")
                else:
                    try:
                        product = stripe.Product.create(
                            name=plan.name,
                            metadata={"plan_id": str(plan.pk)},
                        )
                        product_id = product.id
                        self.stdout.write(f"  ✓ Created product: {product_id}")
                        changed = True
                    except stripe.StripeError as exc:
                        self.stdout.write(self.style.ERROR(f"  ✗ Failed to create product: {exc}"))
                        continue
            else:
                self.stdout.write(f"  · Product OK: {product_id}")

            # ── 2. Price ──────────────────────────────────────────────────────
            if needs_price:
                # No price yet — create one.
                if dry_run:
                    self.stdout.write(
                        f"  Would create Stripe price: "
                        f"amount={expected_unit_amount} {plan.currency.upper()}/{plan.interval}"
                        + (f", trial={plan.trial_days}d" if plan.trial_days else "")
                    )
                else:
                    price_id = self._create_price(plan, product_id, expected_unit_amount)
                    if price_id is None:
                        continue
                    changed = True
                created_count += 1
            else:
                # Price exists — check if amount matches.
                if dry_run:
                    # Fetch from Stripe to compare even in dry-run (read-only).
                    try:
                        live_price = stripe.Price.retrieve(price_id)
                        live_amount = live_price.unit_amount
                    except stripe.StripeError as exc:
                        self.stdout.write(self.style.ERROR(f"  ✗ Could not fetch price from Stripe: {exc}"))
                        continue

                    if live_amount != expected_unit_amount:
                        self.stdout.write(
                            f"  Would create new price ({expected_unit_amount} cents), "
                            f"old price {price_id} ({live_amount} cents) left untouched"
                        )
                        updated_count += 1
                    else:
                        self.stdout.write(f"  · Price OK: {price_id} ({live_amount} cents)")
                        skipped_count += 1
                    continue
                else:
                    try:
                        live_price = stripe.Price.retrieve(price_id)
                        live_amount = live_price.unit_amount
                    except stripe.StripeError as exc:
                        self.stdout.write(self.style.ERROR(f"  ✗ Could not fetch price from Stripe: {exc}"))
                        continue

                    if live_amount == expected_unit_amount:
                        self.stdout.write(f"  · Price OK: {price_id} ({live_amount} cents)")
                        skipped_count += 1
                        continue

                    # Amount changed — create new price, leave old one untouched.
                    self.stdout.write(
                        f"  ! Price mismatch: live={live_amount} cents, expected={expected_unit_amount} cents"
                    )
                    new_price_id = self._create_price(plan, product_id, expected_unit_amount)
                    if new_price_id is None:
                        continue
                    price_id = new_price_id
                    changed = True
                    updated_count += 1

            # ── 3. Persist to DB ──────────────────────────────────────────────
            if changed:
                plan.stripe_product_id = product_id
                plan.stripe_price_id = price_id
                plan.save(update_fields=["stripe_product_id", "stripe_price_id", "updated_at"])
                self.stdout.write(self.style.SUCCESS("  ✓ Plan updated in database"))

        self.stdout.write(f"\n{'─' * 50}")
        if dry_run:
            self.stdout.write(
                self.style.WARNING(
                    f"Dry run complete: {created_count} to create, {updated_count} price(s) to rotate, "
                    f"{skipped_count} already in sync."
                )
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(
                    f"Done: {created_count} created, {updated_count} price(s) rotated, {skipped_count} skipped."
                )
            )

    def _create_price(self, plan: "Plan", product_id: str, unit_amount: int) -> str | None:
        price_params = {
            "product": product_id,
            "unit_amount": unit_amount,
            "currency": plan.currency,
            "recurring": {"interval": plan.interval},
            "nickname": f"{plan.name} {plan.interval.capitalize()}ly",
            "metadata": {"plan_id": str(plan.pk)},
        }
        if plan.trial_days:
            price_params["recurring"]["trial_period_days"] = plan.trial_days

        try:
            price = stripe.Price.create(**price_params)
            self.stdout.write(f"  ✓ Created price: {price.id}")
            return price.id
        except stripe.StripeError as exc:
            self.stdout.write(self.style.ERROR(f"  ✗ Failed to create price: {exc}"))
            return None
