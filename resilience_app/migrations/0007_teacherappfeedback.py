from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("resilience_app", "0006_backfill_teacherprofile_emails"),
    ]

    operations = [
        migrations.CreateModel(
            name="TeacherAppFeedback",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("responses", models.JSONField(default=dict)),
                ("comments", models.TextField(blank=True, default="")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "teacher_profile",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="app_feedback",
                        to="resilience_app.teacherprofile",
                    ),
                ),
            ],
        ),
    ]
