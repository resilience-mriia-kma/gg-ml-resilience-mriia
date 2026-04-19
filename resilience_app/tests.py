from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from .models import ConsentFormInvitation, TeacherProfile


class TeacherProfileAdminTests(TestCase):
    def setUp(self):
        self.admin_user = get_user_model().objects.create_superuser(
            username="admin",
            email="admin@example.com",
            password="password123",
        )
        self.client.force_login(self.admin_user)

    def test_changelist_shows_upload_and_send_form_actions(self):
        teacher = TeacherProfile.objects.create(
            teacher_id="teacher-001",
            teacher_email="teacher@example.com",
            full_name="Teacher One",
        )

        response = self.client.get(reverse("admin:resilience_app_teacherprofile_changelist"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Upload teachers from CSV")
        self.assertContains(
            response,
            reverse("admin:resilience_app_teacherprofile_send_form", args=[teacher.pk]),
        )

    def test_changelist_handles_teacher_without_email(self):
        TeacherProfile.objects.create(
            teacher_id="teacher-003",
            full_name="Teacher Three",
        )

        response = self.client.get(reverse("admin:resilience_app_teacherprofile_changelist"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Send form unavailable")

    @patch("resilience_app.admin.NotificationService.send")
    def test_send_form_view_creates_or_updates_invitation(self, mocked_send):
        teacher = TeacherProfile.objects.create(
            teacher_id="teacher-002",
            teacher_email="teacher2@example.com",
            full_name="Teacher Two",
        )

        def mark_notification_as_sent(notification):
            notification.mark_sent()

        mocked_send.side_effect = mark_notification_as_sent

        response = self.client.get(
            reverse("admin:resilience_app_teacherprofile_send_form", args=[teacher.pk])
        )

        self.assertEqual(response.status_code, 302)
        invitation = ConsentFormInvitation.objects.get(teacher_id=teacher.teacher_id)
        self.assertEqual(invitation.teacher_email, teacher.teacher_email)
        self.assertEqual(invitation.full_name, teacher.full_name)
        self.assertTrue(invitation.invitation_sent)
        self.assertEqual(invitation.status, ConsentFormInvitation.Status.SENT)

    @patch("resilience_app.admin.NotificationService.send")
    def test_send_form_uses_invitation_email_when_profile_email_missing(self, mocked_send):
        teacher = TeacherProfile.objects.create(
            teacher_id="teacher-004",
            full_name="Teacher Four",
        )
        ConsentFormInvitation.objects.create(
            teacher_id="teacher-004",
            teacher_email="teacher4@example.com",
            full_name="Teacher Four",
        )

        def mark_notification_as_sent(notification):
            notification.mark_sent()

        mocked_send.side_effect = mark_notification_as_sent

        response = self.client.get(
            reverse("admin:resilience_app_teacherprofile_send_form", args=[teacher.pk])
        )

        self.assertEqual(response.status_code, 302)
        teacher.refresh_from_db()
        invitation = ConsentFormInvitation.objects.get(teacher_id=teacher.teacher_id)
        self.assertEqual(teacher.teacher_email, "teacher4@example.com")
        self.assertEqual(invitation.status, ConsentFormInvitation.Status.SENT)
