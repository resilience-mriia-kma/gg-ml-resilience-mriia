from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("resilience_app", "0004_teacherprofile_alter_analysisrequest_scores_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="teacherprofile",
            name="teacher_email",
            field=models.EmailField(blank=True, max_length=254, null=True),
        ),
    ]
