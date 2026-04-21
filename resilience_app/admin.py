import csv
import io

from django.conf import settings
from django.contrib import admin, messages
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.urls import path, reverse
from django.utils.html import format_html

from .models import (
    AnalysisRequest,
    ConsentFormInvitation,
    Notification,
    TeacherAppFeedback,
    TeacherFeedback,
    TeacherProfile,
)
from .notifications import NotificationService, enqueue_notification
from .teacher_ids import generate_teacher_id, normalize_teacher_email


@admin.register(TeacherProfile)
class TeacherProfileAdmin(admin.ModelAdmin):
    change_list_template = "admin/resilience_app/teacherprofile/change_list.html"
    list_display = (
        "teacher_id",
        "teacher_email",
        "full_name",
        "consent_given",
        "completed_screenings_count",
        "feedback_status",
        "send_form_button",
        "consent_given_at",
    )
    search_fields = ("teacher_id", "teacher_email", "full_name")
    list_filter = ("consent_given", "feedback_status", "created_at")
    readonly_fields = ("created_at", "updated_at", "consent_given_at")
    actions = ["send_form_action"]

    def get_fields(self, request, obj=None):
        fields = list(super().get_fields(request, obj))
        if obj is None:
            return [field for field in fields if field != "teacher_id"]
        return fields

    def get_readonly_fields(self, request, obj=None):
        readonly_fields = list(super().get_readonly_fields(request, obj))
        if obj is not None:
            readonly_fields.append("teacher_id")
        return readonly_fields

    def save_model(self, request, obj, form, change):
        if not change and not obj.teacher_id:
            obj.teacher_id = generate_teacher_id(teacher_email=obj.teacher_email)
        super().save_model(request, obj, form, change)

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                "upload-csv/",
                self.admin_site.admin_view(self.upload_csv_view),
                name="resilience_app_teacherprofile_upload_csv",
            ),
            path(
                "<path:object_id>/send-form/",
                self.admin_site.admin_view(self.send_form_view),
                name="resilience_app_teacherprofile_send_form",
            ),
        ]
        return custom_urls + urls

    def upload_csv_view(self, request):
        if request.method == "POST" and request.FILES.get("csv_file"):
            csv_file = request.FILES["csv_file"]

            try:
                decoded_file = csv_file.read().decode("utf-8-sig")
                reader = csv.DictReader(io.StringIO(decoded_file))

                created_count = 0
                updated_count = 0
                errors = []

                for row_num, row in enumerate(reader, start=2):
                    try:
                        teacher_email = normalize_teacher_email(
                            row.get("teacher_email", "")
                        )
                        teacher_id = (
                            row.get("teacher_id", "").strip()
                            or generate_teacher_id(teacher_email=teacher_email)
                        )
                        full_name = row.get("full_name", "").strip()

                        profile, created = TeacherProfile.objects.get_or_create(
                            teacher_id=teacher_id,
                            defaults={
                                "full_name": full_name or teacher_id,
                                "teacher_email": teacher_email or None,
                            },
                        )

                        if created:
                            created_count += 1
                        else:
                            if full_name:
                                profile.full_name = full_name
                            if teacher_email:
                                profile.teacher_email = teacher_email
                            profile.save()
                            updated_count += 1

                        if teacher_email:
                            ConsentFormInvitation.objects.update_or_create(
                                teacher_id=teacher_id,
                                defaults={
                                    "teacher_email": teacher_email,
                                    "full_name": full_name,
                                },
                            )

                    except Exception as exc:
                        errors.append(f"Row {row_num}: {exc}")

                summary = f"Created: {created_count}, updated: {updated_count}"
                level = messages.SUCCESS

                if errors:
                    summary += f". Errors ({len(errors)}): {'; '.join(errors[:3])}"
                    level = messages.WARNING

                self.message_user(request, summary, level=level)

            except Exception as exc:
                self.message_user(
                    request,
                    f"Error reading file: {exc}",
                    level=messages.ERROR,
                )

            return HttpResponseRedirect(
                reverse("admin:resilience_app_teacherprofile_changelist")
            )

        return render(
            request,
            "admin/upload_csv.html",
            {
                "title": "Upload Teachers from CSV",
                "opts": self.model._meta,
            },
        )

    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        extra_context["upload_csv_url"] = reverse(
            "admin:resilience_app_teacherprofile_upload_csv"
        )
        return super().changelist_view(request, extra_context)

    def _send_form_for_teacher(self, teacher):
        invitation, _ = ConsentFormInvitation.objects.get_or_create(
            teacher_id=teacher.teacher_id,
            defaults={
                "teacher_email": teacher.teacher_email or "",
                "full_name": teacher.full_name,
                "status": ConsentFormInvitation.Status.PENDING,
            },
        )

        email = teacher.teacher_email or invitation.teacher_email
        if not email:
            raise ValueError("No email available")

        updated_fields = []

        if invitation.teacher_email != email:
            invitation.teacher_email = email
            updated_fields.append("teacher_email")

        if invitation.full_name != teacher.full_name:
            invitation.full_name = teacher.full_name
            updated_fields.append("full_name")

        if updated_fields:
            invitation.save(update_fields=updated_fields)

        if teacher.teacher_email != email:
            teacher.teacher_email = email
            teacher.save(update_fields=["teacher_email"])

        notification = self._queue_teacher_info_notification(teacher)
        NotificationService().send(notification)

        invitation.refresh_from_db()

        if notification.status == Notification.Status.SENT:
            if (
                invitation.status != ConsentFormInvitation.Status.SENT
                or not invitation.invitation_sent
            ):
                invitation.mark_sent()
            return

        error_message = notification.error_message or "Unknown error"
        invitation.mark_failed(error_message)

    def _queue_teacher_info_notification(self, teacher):
        teacher_info_url = (
            f"{settings.APP_BASE_URL}"
            f"{reverse('teacher_info_sheet')}?teacher_id={teacher.teacher_id}"
        )

        notification = enqueue_notification(
            notification_type=Notification.NotificationType.CONSENT_FORM,
            recipient_email=teacher.teacher_email,
            subject="Запрошення до участі у дослідженні стійкості",
            context={
                "teacher_id": teacher.teacher_id,
                "teacher_email": teacher.teacher_email,
                "teacher_info_url": teacher_info_url,
            },
        )

        return notification

    def send_form_view(self, request, object_id):
        teacher = get_object_or_404(TeacherProfile, pk=object_id)

        try:
            self._send_form_for_teacher(teacher)
            self.message_user(
                request,
                f"Form invitation sent to {teacher.teacher_id}.",
                level=messages.SUCCESS,
            )
        except Exception as exc:
            self.message_user(
                request,
                f"Failed to send form to {teacher.teacher_id}: {exc}",
                level=messages.ERROR,
            )

        return HttpResponseRedirect(
            reverse("admin:resilience_app_teacherprofile_changelist")
        )

    def send_form_button(self, obj):
        url = reverse("admin:resilience_app_teacherprofile_send_form", args=[obj.pk])
        has_email = bool(obj.teacher_email) or ConsentFormInvitation.objects.filter(
            teacher_id=obj.teacher_id,
            teacher_email__gt="",
        ).exists()

        if not has_email:
            return format_html(
                '<span style="color: #999;">{}</span>',
                "Send form unavailable",
            )

        return format_html('<a class="button" href="{}">Send form</a>', url)

    send_form_button.short_description = "Actions"

    @admin.action(description="Send form invitation for selected teachers")
    def send_form_action(self, request, queryset):
        sent_count = 0
        failed = []

        for teacher in queryset:
            try:
                self._send_form_for_teacher(teacher)
                sent_count += 1
            except Exception as exc:
                failed.append(f"{teacher.teacher_id}: {exc}")

        if sent_count:
            self.message_user(
                request,
                f"Sent {sent_count} form invitation(s).",
                level=messages.SUCCESS,
            )

        if failed:
            self.message_user(
                request,
                f"Failed ({len(failed)}): {'; '.join(failed[:3])}",
                level=messages.WARNING,
            )


@admin.register(ConsentFormInvitation)
class ConsentFormInvitationAdmin(admin.ModelAdmin):
    list_display = (
        "teacher_id",
        "teacher_email",
        "full_name",
        "status_badge",
        "sent_at",
        "created_at",
    )
    search_fields = ("teacher_id", "teacher_email", "full_name")
    list_filter = ("status", "invitation_sent", "created_at")
    readonly_fields = ("created_at", "updated_at", "sent_at", "error_message")
    actions = ["mark_as_pending"]

    fieldsets = (
        ("Teacher Info", {"fields": ("teacher_id", "teacher_email", "full_name")}),
        (
            "Invitation Status",
            {"fields": ("status", "invitation_sent", "sent_at", "error_message")},
        ),
        ("Metadata", {"fields": ("created_at", "updated_at")}),
    )

    def status_badge(self, obj):
        colors = {
            "pending": "#FFA500",
            "sent": "#28a745",
            "failed": "#dc3545",
        }
        color = colors.get(obj.status, "#6c757d")

        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; '
            'border-radius: 3px;">{}</span>',
            color,
            obj.get_status_display(),
        )

    status_badge.short_description = "Status"

    @admin.action(description="Mark selected invitations as pending")
    def mark_as_pending(self, request, queryset):
        count = queryset.update(
            status=ConsentFormInvitation.Status.PENDING,
            invitation_sent=False,
        )
        self.message_user(request, f"{count} invitations marked as pending.")


@admin.register(AnalysisRequest)
class AnalysisRequestAdmin(admin.ModelAdmin):
    list_display = (
        "pk",
        "teacher_id",
        "teacher_email",
        "student_id",
        "student_age",
        "created_at",
        "report_emailed_at",
    )
    search_fields = ("teacher_id", "teacher_email", "student_id")
    list_filter = ("created_at", "report_emailed_at")
    readonly_fields = ("created_at", "report_emailed_at")


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = (
        "pk",
        "type",
        "recipient_email",
        "status_badge",
        "scheduled_at",
        "sent_at",
    )
    search_fields = ("recipient_email", "subject", "dedupe_key")
    list_filter = ("type", "status", "scheduled_at", "sent_at")
    readonly_fields = ("sent_at", "error_message", "scheduled_at")

    def status_badge(self, obj):
        colors = {
            "pending": "#FFA500",
            "sent": "#28a745",
            "failed": "#dc3545",
        }
        color = colors.get(obj.status, "#6c757d")

        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; '
            'border-radius: 3px;">{}</span>',
            color,
            obj.get_status_display(),
        )

    status_badge.short_description = "Status"


@admin.register(TeacherFeedback)
class TeacherFeedbackAdmin(admin.ModelAdmin):
    list_display = (
        "pk",
        "teacher_id",
        "teacher_email",
        "forms_completed",
        "rating",
        "created_at",
    )
    search_fields = ("teacher_id", "teacher_email", "comments")
    list_filter = ("rating", "created_at")
    readonly_fields = ("created_at",)


@admin.register(TeacherAppFeedback)
class TeacherAppFeedbackAdmin(admin.ModelAdmin):
    list_display = (
        "teacher_profile",
        "created_at",
        "updated_at",
    )
    search_fields = (
        "teacher_profile__teacher_id",
        "teacher_profile__teacher_email",
        "teacher_profile__full_name",
        "comments",
    )
    readonly_fields = ("created_at", "updated_at")
