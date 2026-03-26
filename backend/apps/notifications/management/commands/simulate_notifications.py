"""
Management command to simulate random in-app notifications for testing.

Usage:
    python manage.py simulate_notifications <email>
    python manage.py simulate_notifications <email> --count 10
    python manage.py simulate_notifications <email> --min-delay 2 --max-delay 8
    python manage.py simulate_notifications <email> --count 5 --min-delay 1 --max-delay 3
"""

import random
import time

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError

from apps.notifications.models import Notification
from apps.notifications.signals import _push_to_websocket

User = get_user_model()

SAMPLE_NOTIFICATIONS = [
    (
        Notification.Type.INFO,
        "Your export is ready",
        "The CSV export you requested has been generated and is ready to download.",
    ),
    (
        Notification.Type.INFO,
        "New team member joined",
        "Alex Johnson just accepted their invitation and joined your team.",
    ),
    (
        Notification.Type.INFO,
        "Weekly summary available",
        "Your weekly activity report for the past 7 days is now available.",
    ),
    (
        Notification.Type.WARNING,
        "Storage limit approaching",
        "You've used 85% of your storage quota. Consider upgrading your plan.",
    ),
    (
        Notification.Type.WARNING,
        "Subscription renewal in 3 days",
        "Your subscription will automatically renew on March 28. Make sure your payment method is up to date.",
    ),
    (
        Notification.Type.WARNING,
        "Unusual login detected",
        "A login was detected from a new device or location. If this wasn't you, please change your password.",
    ),
    (
        Notification.Type.ERROR,
        "Payment failed",
        "We were unable to charge your payment method. Please update your billing information to avoid service interruption.",
    ),
    (
        Notification.Type.ERROR,
        "Sync failed",
        "The last data sync encountered an error. Retrying automatically in 10 minutes.",
    ),
    (
        Notification.Type.WELCOME,
        "Feature spotlight: Teams",
        "Did you know you can invite team members and collaborate in real time? Try it from the Team settings page.",
    ),
    (
        Notification.Type.INFO,
        "Profile updated",
        "Your profile information was successfully updated.",
    ),
    (
        Notification.Type.INFO,
        "Password changed",
        "Your account password was changed successfully. If you didn't do this, contact support immediately.",
    ),
    (
        Notification.Type.WARNING,
        "API rate limit reached",
        "You've hit the API rate limit for this hour. Requests will resume at the top of the next hour.",
    ),
]


class Command(BaseCommand):
    help = "Simulate random in-app notifications for a user (useful for testing the notification system)"

    def add_arguments(self, parser):
        parser.add_argument(
            "email", type=str, help="Email of the user to send notifications to"
        )
        parser.add_argument(
            "--count",
            type=int,
            default=0,
            help="Number of notifications to send (0 = run indefinitely until Ctrl+C)",
        )
        parser.add_argument(
            "--min-delay",
            type=float,
            default=3.0,
            help="Minimum seconds between notifications (default: 3)",
        )
        parser.add_argument(
            "--max-delay",
            type=float,
            default=10.0,
            help="Maximum seconds between notifications (default: 10)",
        )

    def handle(self, *args, **options):
        email = options["email"]
        count = options["count"]
        min_delay = options["min_delay"]
        max_delay = options["max_delay"]

        if min_delay <= 0 or max_delay <= 0:
            raise CommandError("Delay values must be positive.")
        if min_delay > max_delay:
            raise CommandError("--min-delay cannot be greater than --max-delay.")

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            raise CommandError(f"No user found with email '{email}'.")

        mode = f"{count} notification(s)" if count else "indefinitely (Ctrl+C to stop)"
        self.stdout.write(
            self.style.SUCCESS(
                f"Simulating notifications for {user.email} — {mode} "
                f"[delay: {min_delay}–{max_delay}s]"
            )
        )

        sent = 0
        try:
            while True:
                notif_type, title, body = random.choice(SAMPLE_NOTIFICATIONS)
                notification = Notification.objects.create(
                    user=user,
                    type=notif_type,
                    title=title,
                    body=body,
                )
                _push_to_websocket(user.pk, notification)

                sent += 1
                self.stdout.write(f"  [{sent}] [{notif_type.upper()}] {title}")

                if count and sent >= count:
                    break

                delay = random.uniform(min_delay, max_delay)
                self.stdout.write(f"       next in {delay:.1f}s…")
                time.sleep(delay)

        except KeyboardInterrupt:
            pass

        self.stdout.write(
            self.style.SUCCESS(f"\nDone. Sent {sent} notification(s) to {user.email}.")
        )
