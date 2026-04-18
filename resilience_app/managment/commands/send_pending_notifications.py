from django.core.management.base import BaseCommand
from django.utils import timezone

from resilience_app.models import Notification
from resilience_app.notifications import NotificationService


class Command(BaseCommand):
    help = "Send all pending notifications scheduled up to now."

    def add_arguments(self, parser):
        parser.add_argument("--limit", type=int, default=100)

    def handle(self, *args, **options):
        limit = options["limit"]

        notifications = Notification.objects.filter(
            status=Notification.Status.PENDING,
            scheduled_at__lte=timezone.now(),
        ).order_by("scheduled_at", "pk")[:limit]

        service = NotificationService()
        sent_count = 0
        failed_count = 0

        for notification in notifications:
            service.send(notification)
            notification.refresh_from_db()

            if notification.status == Notification.Status.SENT:
                sent_count += 1
            elif notification.status == Notification.Status.FAILED:
                failed_count += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Processed {len(notifications)} notifications. "
                f"Sent: {sent_count}. Failed: {failed_count}."
            )
        )