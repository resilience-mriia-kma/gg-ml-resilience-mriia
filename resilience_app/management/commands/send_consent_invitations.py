"""
Management command to send consent form invitations to teachers.

Usage:
    python manage.py send_consent_invitations [--limit 100]
    python manage.py send_consent_invitations --retry-failed
"""

import logging

from django.core.management.base import BaseCommand

from ...models import ConsentFormInvitation, TeacherProfile
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
                teacher_profile, _ = TeacherProfile.objects.get_or_create(
                    teacher_id=invitation.teacher_id,
                    defaults={
                        "teacher_email": invitation.teacher_email,
                        "full_name": invitation.full_name or invitation.teacher_id,
                    },
                )
                updated_fields = []
                if teacher_profile.teacher_email != invitation.teacher_email:
                    teacher_profile.teacher_email = invitation.teacher_email
                    updated_fields.append("teacher_email")
                if invitation.full_name and teacher_profile.full_name != invitation.full_name:
                    teacher_profile.full_name = invitation.full_name
                    updated_fields.append("full_name")
                if updated_fields:
                    teacher_profile.save(update_fields=[*updated_fields, "updated_at"])

                notification = queue_consent_form_notification(
                    teacher_profile=teacher_profile,
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
