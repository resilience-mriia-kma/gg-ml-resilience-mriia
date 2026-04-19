# Raw Sources

This directory holds the raw knowledge-base documents (PDF, DOCX) that feed the
RAG pipeline. Contents are **not** tracked in VCS — only this README and
`.gitkeep` are.

## Where to get the files

Source PDFs live on the shared team drive (replace this line with your own
location: Google Drive folder, S3 bucket, internal share, etc.).

Drop the files directly into this directory, or point the pipeline at a
different location via `RAW_SOURCES_DIR` in `.env`.

## Ingesting

```bash
# Ingest all files in this directory
uv run python manage.py embed_docs

# Or a specific file
uv run python manage.py embed_docs raw_sources/Handout-27.pdf

# Tag all chunks with a specific resilience factor
uv run python manage.py embed_docs raw_sources/Optimism.pdf --factor optimism
```

Alternatively, upload files through the Django admin at
`/admin/rag_pipeline/knowledgesource/` and use the "Process selected sources"
action.

## Supported formats

- `.pdf` — parsed with `pypdf` (text-based PDFs only; scanned/image PDFs need OCR)
- `.docx` — parsed with `python-docx` (expects a table-structured layout for
  heading detection, otherwise falls back to page-level chunking)
