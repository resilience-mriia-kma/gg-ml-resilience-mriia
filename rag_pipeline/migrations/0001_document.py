# Transfer Document model from resilience_app to rag_pipeline

import pgvector.django.indexes
import pgvector.django.vector
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("resilience_app", "0003_analysisrequest"),
    ]

    # State-only: register Document in this app's state.
    # The actual table already exists (owned by resilience_app),
    # and will be renamed in database_operations.
    operations = [
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.CreateModel(
                    name="Document",
                    fields=[
                        (
                            "id",
                            models.BigAutoField(
                                auto_created=True, primary_key=True, serialize=False, verbose_name="ID"
                            ),
                        ),
                        ("title", models.CharField(max_length=512)),
                        ("source", models.URLField(blank=True)),
                        ("content", models.TextField()),
                        ("embedding", pgvector.django.vector.VectorField(blank=True, dimensions=1536, null=True)),
                        ("created_at", models.DateTimeField(auto_now_add=True)),
                        ("updated_at", models.DateTimeField(auto_now=True)),
                    ],
                    options={
                        "indexes": [
                            pgvector.django.indexes.HnswIndex(
                                ef_construction=64,
                                fields=["embedding"],
                                m=16,
                                name="document_embedding_idx",
                                opclasses=["vector_cosine_ops"],
                            )
                        ],
                    },
                ),
            ],
            database_operations=[
                migrations.RunSQL(
                    sql="ALTER TABLE resilience_app_document RENAME TO rag_pipeline_document",
                    reverse_sql="ALTER TABLE rag_pipeline_document RENAME TO resilience_app_document",
                ),
            ],
        ),
    ]
