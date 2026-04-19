"""
Management command to send consent form invitations to teachers.

Usage:
    python manage.py send_consent_invitations [--limit 100]
    python manage.py send_consent_invitations --retry-failed
"""

import logging

from django.core.management.base import BaseCommand
from django.utils import timezone

from ...models import ConsentFormInvitation
from ...notifications import NotificationService, queue_consent_form_notification

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Send pending consent form invitations to teachers."

    def add_arguments(self, parser):
        parser.add_argument(
            "--limit",
            type=int,
            default=100,
            help="Maximum number of invitations to send",
        )
        parser.add_argument(
            "--retry-failed",
            action="store_true",
            help="Retry failed invitations",
        )

    def handle(self, *args, **options):
        limit = options.get("limit", 100)
        retry_failed = options.get("retry_failed", False)

        if retry_failed:
            invitations = ConsentFormInvitation.objects.filter(
                status=ConsentFormInvitation.Status.FAILED,
                invitation_sent=False,
            ).order_by("updated_at")[:limit]
        else:
            invitations = ConsentFormInvitation.objects.filter(
                status=ConsentFormInvitation.Status.PENDING,
                invitation_sent=False,
            ).order_by("created_at")[:limit]

        self.stdout.write(f"Found {invitations.count()} invitations to send")

        service = NotificationService()
        sent_count = 0
        failed_count = 0

        for invitation in invitations:
            try:
                notification = queue_consent_form_notification(
                    teacher_email=invitation.teacher_email,
                )

                service.send(notification)

                invitation.mark_sent()
                sent_count += 1

                self.stdout.write(
                    self.style.SUCCESS(
                        f"✓ Sent to {invitation.teacher_email}"
                    )
                )

            except Exception as exc:
                logger.exception("Failed to send invitation to %s", invitation.teacher_email)
                invitation.mark_failed(str(exc))
                failed_count += 1

                self.stdout.write(
                    self.style.ERROR(
                        f"✗ Failed to send to {invitation.teacher_email}: {str(exc)[:50]}"
                    )
                )

        self.stdout.write(
            self.style.SUCCESS(
                f"\nSummary: {sent_count} sent, {failed_count} failed"
            )
        )
