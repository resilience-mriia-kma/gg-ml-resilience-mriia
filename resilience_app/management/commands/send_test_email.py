from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from resilience_app.models import AnalysisRequest, Notification, TeacherProfile
from resilience_app.notifications import NotificationService, enqueue_notification


class Command(BaseCommand):
    help = "Send test emails to verify email configuration"

    def add_arguments(self, parser):
        parser.add_argument("email", type=str, help="Email address to send test email to")
        parser.add_argument(
            "--type",
            choices=["consent", "report", "feedback", "simple"],
            default="simple",
            help="Type of test email to send (default: simple)",
        )
        parser.add_argument("--teacher-id", default="TEST001", help="Teacher ID for test context (default: TEST001)")
        parser.add_argument(
            "--student-id", default="STUDENT001", help="Student ID for test context (default: STUDENT001)"
        )

    def handle(self, *args, **options):
        email = options["email"]
        email_type = options["type"]
        teacher_id = options["teacher_id"]
        student_id = options["student_id"]

        self.stdout.write(f"Sending {email_type} test email to {email}...")

        try:
            if email_type == "simple":
                self.send_simple_test_email(email)
            elif email_type == "consent":
                self.send_consent_test_email(email, teacher_id, student_id)
            elif email_type == "report":
                self.send_report_test_email(email, teacher_id, student_id)
            elif email_type == "feedback":
                self.send_feedback_test_email(email, teacher_id)

            self.stdout.write(self.style.SUCCESS(f"Test email sent successfully to {email}"))

        except Exception as e:
            raise CommandError(f"Failed to send email: {str(e)}")

    def send_simple_test_email(self, email):
        notification_service = NotificationService()
        notification_service._send_email(
            subject="Test Email - ML Resilience System",
            body=(
                "This is a test email from the ML Resilience system.\n\n"
                "If you received this email, your email configuration is working correctly.\n\n"
                f"Sent at: {timezone.now()}\n"
                f"To: {email}\n\n"
                "Best regards,\nML Resilience System"
            ),
            recipient_email=email,
        )

    def send_consent_test_email(self, email, teacher_id, student_id):
        notification = enqueue_notification(
            notification_type=Notification.NotificationType.CONSENT_FORM,
            recipient_email=email,
            subject="TEST: Згода та форма оцінювання резільєнтності",
            context={
                "teacher_id": teacher_id,
                "teacher_email": email,
                "student_id": student_id,
                "student_age": 12,
                "student_gender": "М",
            },
            attachment_path="",  # No attachment for test
        )

        notification_service = NotificationService()
        notification_service.send(notification)

    def send_report_test_email(self, email, teacher_id, student_id):
        try:
            teacher_profile = TeacherProfile.objects.filter(teacher_id=teacher_id).first()
            if not teacher_profile:
                teacher_profile = TeacherProfile.objects.create(
                    teacher_id=teacher_id, full_name=f"Test Teacher {teacher_id}", consent_given=True
                )

            analysis_request = AnalysisRequest.objects.create(
                teacher_profile=teacher_profile,
                teacher_id=teacher_id,
                teacher_email=email,
                student_id=student_id,
                student_age=12,
                student_gender="М",
                scores={},
                profile={"factor1": "MEDIUM", "factor2": "HIGH"},
                recommendations="Test recommendation line 1.\nTest recommendation line 2.",
            )

            notification = enqueue_notification(
                notification_type=Notification.NotificationType.REPORT_READY,
                recipient_email=email,
                subject=f"TEST: Готовий звіт для учня {student_id}",
                context={"analysis_request_id": analysis_request.pk},
                analysis_request=analysis_request,
            )

            notification_service = NotificationService()
            notification_service.send(notification)

            # Clean up test data
            analysis_request.delete()
            if teacher_profile.analysis_requests.count() == 0:
                teacher_profile.delete()

        except Exception as e:
            self.stdout.write(self.style.WARNING(f"Note: Could not create full test context: {e}"))
            # Fall back to simple email
            self.send_simple_test_email(email)

    def send_feedback_test_email(self, email, teacher_id):
        notification = enqueue_notification(
            notification_type=Notification.NotificationType.FEEDBACK_REQUEST,
            recipient_email=email,
            subject="TEST: Поділіться коротким фідбеком про систему",
            context={
                "teacher_id": teacher_id,
                "teacher_email": email,
                "forms_completed": 10,
            },
        )

        notification_service = NotificationService()
        notification_service.send(notification)
