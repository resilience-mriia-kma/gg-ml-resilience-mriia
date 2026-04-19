import csv
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from resilience_app.notifications import NotificationService, queue_consent_form_notification


class Command(BaseCommand):
    help = "Send consent form emails in bulk from CSV file"

    def add_arguments(self, parser):
        parser.add_argument("csv_file", type=str, help="Path to CSV file with teacher email data")
        parser.add_argument(
            "--dry-run", action="store_true", help="Show what would be sent without actually sending"
        )
        parser.add_argument("--send-now", action="store_true", help="Send emails immediately (default: queue only)")

    def handle(self, **options):
        csv_file = Path(options["csv_file"])
        dry_run = options["dry_run"]
        send_now = options["send_now"]

        if not csv_file.exists():
            raise CommandError(f"CSV file not found: {csv_file}")

        self.stdout.write(f"Processing bulk consent emails from: {csv_file}")
        if dry_run:
            self.stdout.write("DRY RUN MODE - no emails will be sent")

        notifications_created = 0
        notifications_sent = 0
        errors = []

        try:
            with open(csv_file, "r", encoding="utf-8") as file:
                reader = csv.DictReader(file)
                required_fields = {"teacher_email"}

                if not required_fields.issubset(reader.fieldnames or []):
                    missing = required_fields - set(reader.fieldnames or [])
                    raise CommandError(f"Missing required CSV columns: {missing}")

                for row_num, row in enumerate(reader, start=2):
                    try:
                        self.process_row(row, row_num, dry_run, send_now)
                        notifications_created += 1

                        if send_now and not dry_run:
                            notifications_sent += 1

                    except Exception as e:
                        error_msg = f"Row {row_num} ({row.get('teacher_email', 'unknown')}): {str(e)}"
                        errors.append(error_msg)
                        self.stdout.write(self.style.ERROR(f"  Error: {error_msg}"))

        except Exception as e:
            raise CommandError(f"Failed to process CSV file: {str(e)}")

        self.show_summary(notifications_created, notifications_sent, errors, dry_run, send_now)

    def process_row(self, row, row_num, dry_run, send_now):
        teacher_email = row["teacher_email"].strip()

        if not teacher_email:
            raise ValueError("teacher_email is required")

        if dry_run:
            self.stdout.write(f"  Would send consent email to: {teacher_email}")
            return

        notification = queue_consent_form_notification(
            teacher_email=teacher_email,
        )

        self.stdout.write(f"  Queued consent notification for: {teacher_email}")

        if send_now:
            notification_service = NotificationService()
            notification_service.send(notification)
            self.stdout.write(f"    Sent immediately to: {teacher_email}")

    def show_summary(self, notifications_created, notifications_sent, errors, dry_run, send_now):
        self.stdout.write("\n" + "=" * 60)

        if dry_run:
            self.stdout.write(self.style.SUCCESS(f"DRY RUN: Would create {notifications_created} notifications"))
        else:
            self.stdout.write(self.style.SUCCESS(f"Successfully created {notifications_created} notifications"))

            if send_now:
                self.stdout.write(f"Sent immediately: {notifications_sent}")
            else:
                self.stdout.write("Notifications queued (use NotificationService.send() to process)")

        if errors:
            self.stdout.write(self.style.WARNING(f"Errors encountered: {len(errors)}"))
            for error in errors:
                self.stdout.write(f"  - {error}")

        if not dry_run and not send_now:
            self.stdout.write("\nNext steps:")
            self.stdout.write("  - Check queued notifications in admin or database")
            self.stdout.write("  - Process notifications with NotificationService.send()")