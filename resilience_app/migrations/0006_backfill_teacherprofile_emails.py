from django.db import migrations


def backfill_teacherprofile_emails(apps, schema_editor):
    TeacherProfile = apps.get_model("resilience_app", "TeacherProfile")
    ConsentFormInvitation = apps.get_model("resilience_app", "ConsentFormInvitation")

    invitations_by_teacher_id = {
        invitation.teacher_id: invitation
        for invitation in ConsentFormInvitation.objects.exclude(teacher_email="")
    }

    for profile in TeacherProfile.objects.all():
        invitation = invitations_by_teacher_id.get(profile.teacher_id)
        if invitation is None:
            continue

        updated_fields = []
        if not profile.teacher_email and invitation.teacher_email:
            profile.teacher_email = invitation.teacher_email
            updated_fields.append("teacher_email")
        if not profile.full_name and invitation.full_name:
            profile.full_name = invitation.full_name
            updated_fields.append("full_name")
        if updated_fields:
            profile.save(update_fields=updated_fields)


class Migration(migrations.Migration):

    dependencies = [
        ("resilience_app", "0005_teacherprofile_teacher_email"),
    ]

    operations = [
        migrations.RunPython(
            backfill_teacherprofile_emails,
            migrations.RunPython.noop,
        ),
    ]
