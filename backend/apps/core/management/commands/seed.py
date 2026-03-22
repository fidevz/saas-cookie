"""
Management command: python manage.py seed

Creates initial data for local development:
  - 2 Plans (Starter, Pro)
  - Admin test user
  - Test tenant + admin membership
"""
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

User = get_user_model()

PLANS = [
    {
        "name": "Starter",
        "stripe_price_id": "price_starter_monthly",
        "stripe_product_id": "prod_starter",
        "amount": "9.00",
        "currency": "usd",
        "interval": "month",
        "trial_days": 0,
        "is_active": True,
        "features": [
            "Up to 3 team members",
            "5 GB storage",
            "Email support",
        ],
    },
    {
        "name": "Pro",
        "stripe_price_id": "price_pro_monthly",
        "stripe_product_id": "prod_pro",
        "amount": "29.00",
        "currency": "usd",
        "interval": "month",
        "trial_days": 14,
        "is_active": True,
        "features": [
            "Unlimited team members",
            "50 GB storage",
            "Priority support",
            "Advanced analytics",
            "Custom integrations",
        ],
    },
]

TEST_USER_EMAIL = "admin@test.com"
TEST_USER_PASSWORD = "testpassword123"
TEST_TENANT_NAME = "Test Company"
TEST_TENANT_SLUG = "test-company"


class Command(BaseCommand):
    help = "Seed the database with initial development data."

    def handle(self, *args, **options):
        self._seed_plans()
        user = self._seed_user()
        self._seed_tenant(user)
        self.stdout.write(self.style.SUCCESS("Seeding complete."))

    def _seed_plans(self):
        from apps.subscriptions.models import Plan

        for plan_data in PLANS:
            plan, created = Plan.objects.update_or_create(
                stripe_price_id=plan_data["stripe_price_id"],
                defaults=plan_data,
            )
            verb = "Created" if created else "Updated"
            self.stdout.write(f"  {verb} plan: {plan.name}")

    def _seed_user(self):
        user, created = User.objects.get_or_create(
            email=TEST_USER_EMAIL,
            defaults={
                "first_name": "Admin",
                "last_name": "User",
                "is_staff": True,
                "is_superuser": True,
                "is_first_login": False,
            },
        )
        if created:
            user.set_password(TEST_USER_PASSWORD)
            user.save()
            self.stdout.write(f"  Created user: {TEST_USER_EMAIL} / {TEST_USER_PASSWORD}")
        else:
            self.stdout.write(f"  User already exists: {TEST_USER_EMAIL}")
        return user

    def _seed_tenant(self, user):
        from apps.tenants.models import Tenant, TenantMembership

        tenant, created = Tenant.objects.get_or_create(
            slug=TEST_TENANT_SLUG,
            defaults={"name": TEST_TENANT_NAME, "owner": user},
        )
        verb = "Created" if created else "Found"
        self.stdout.write(f"  {verb} tenant: {tenant.name} ({tenant.slug})")

        membership, mem_created = TenantMembership.objects.get_or_create(
            user=user,
            tenant=tenant,
            defaults={"role": TenantMembership.Role.ADMIN},
        )
        if mem_created:
            self.stdout.write(f"  Created admin membership for {user.email}")
