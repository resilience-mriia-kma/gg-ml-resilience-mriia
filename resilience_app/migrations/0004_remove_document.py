# Transfer Document model from resilience_app to rag_pipeline

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("resilience_app", "0003_analysisrequest"),
        ("rag_pipeline", "0001_document"),
    ]

    # State-only: remove Document from this app's state.
    # The actual table is kept and taken over by rag_pipeline.
    operations = [
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.DeleteModel(name="Document"),
            ],
            database_operations=[],
        ),
    ]
