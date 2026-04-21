import csv
from django.core.management.base import BaseCommand
from resilience_app.models import ConsentFormInvitation, TeacherProfile
from resilience_app.teacher_ids import generate_teacher_id, normalize_teacher_email


class Command(BaseCommand):
    help = "Import teachers from CSV file and create ConsentFormInvitation records"

    def add_arguments(self, parser):
        parser.add_argument(
            "csv_file",
            type=str,
            help="Path to CSV file with columns: teacher_email, full_name, optional teacher_id",
        )
        parser.add_argument(
            "--skip-duplicates",
            action="store_true",
            help="Skip teachers that already exist",
        )

    def handle(self, *args, **options):
        csv_file = options["csv_file"]
        skip_duplicates = options.get("skip_duplicates", False)

        created_count = 0
        skipped_count = 0
        error_count = 0

        try:
            with open(csv_file, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)

                for row_num, row in enumerate(reader, start=2):  # start=2 (header is 1)
                    try:
                        teacher_email = normalize_teacher_email(row.get("teacher_email", ""))
                        teacher_id = row.get("teacher_id", "").strip() or generate_teacher_id(
                            teacher_email=teacher_email
                        )
                        full_name = row.get("full_name", "").strip()

                        if not teacher_email:
                            self.stdout.write(
                                self.style.WARNING(
                                    f"Row {row_num}: Missing teacher_email, skipping"
                                )
                            )
                            error_count += 1
                            continue

                        TeacherProfile.objects.get_or_create(
                            teacher_id=teacher_id,
                            defaults={
                                "teacher_email": teacher_email,
                                "full_name": full_name or teacher_id,
                            },
                        )

                        # Check if already exists
                        if ConsentFormInvitation.objects.filter(
                            teacher_id=teacher_id
                        ).exists():
                            if skip_duplicates:
                                skipped_count += 1
                                continue
                            else:
                                # Update existing
                                invitation = ConsentFormInvitation.objects.get(
                                    teacher_id=teacher_id
                                )
                                invitation.teacher_email = teacher_email
                                invitation.full_name = full_name
                                invitation.save()
                                self.stdout.write(
                                    self.style.WARNING(
                                        f"Row {row_num}: Updated {teacher_id}"
                                    )
                                )
                                continue

                        # Create new
                        ConsentFormInvitation.objects.create(
                            teacher_id=teacher_id,
                            teacher_email=teacher_email,
                            full_name=full_name,
                        )
                        created_count += 1
                        self.stdout.write(
                            self.style.SUCCESS(f"Row {row_num}: Created {teacher_id}")
                        )

                    except Exception as e:
                        self.stdout.write(
                            self.style.ERROR(f"Row {row_num}: Error - {str(e)}")
                        )
                        error_count += 1

        except FileNotFoundError:
            self.stdout.write(self.style.ERROR(f"File not found: {csv_file}"))
            return

        # Summary
        self.stdout.write("\n" + "=" * 60)
        self.stdout.write(self.style.SUCCESS(f"✓ Created: {created_count}"))
        self.stdout.write(self.style.WARNING(f"⊘ Skipped: {skipped_count}"))
        self.stdout.write(self.style.ERROR(f"✗ Errors: {error_count}"))
        self.stdout.write("=" * 60)
