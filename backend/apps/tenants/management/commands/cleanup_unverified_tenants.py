from django.core.management.base import BaseCommand

from apps.tenants.tasks import cleanup_unverified_tenants


class Command(BaseCommand):
    help = "Delete tenants and users whose email was never verified after the grace period."

    def handle(self, *args, **options):
        cleanup_unverified_tenants()
        self.stdout.write(self.style.SUCCESS("Done."))
