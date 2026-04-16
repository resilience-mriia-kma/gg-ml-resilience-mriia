# Deployment: Embedding Pipeline

## Prerequisites

- Python 3.13+
- [uv](https://docs.astral.sh/uv/getting-started/installation/) package manager
- Docker (for PostgreSQL)
- OpenAI API key with access to `text-embedding-3-small` and `gpt-4o-mini`

## 1. Clone and install

```bash
git clone <repo-url> && cd ml-resilience-mriia
git checkout feat/llm-retrieval
uv sync
```

## 2. Start PostgreSQL

```bash
docker compose up -d
```

This starts a Postgres 18 container (`resilience-app-db`) on port 5432.

## 3. Configure environment

```bash
cp .env.sample .env
```

Edit `.env` — the only value you **must** change is the OpenAI key:

```
OPENAI_API_KEY=sk-...          # required — used for embedding and LLM calls
```

Other defaults work as-is for local/dev:

| Variable | Default | Notes |
|---|---|---|
| `DJANGO_SECRET_KEY` | insecure placeholder | change in production |
| `DJANGO_DEBUG` | `True` | set `False` in production |
| `DJANGO_ALLOWED_HOSTS` | `localhost,127.0.0.1` | add your server host |
| `POSTGRES_*` | `postgres/postgres@localhost:5432/ml_resilience` | matches docker-compose |
| `OPENAI_LLM_MODEL` | `gpt-4o-mini` | model for RAG answer generation |

## 4. Apply migrations

```bash
uv run python manage.py migrate
```

## 5. Create admin user (optional, for Django admin panel)

```bash
uv run python manage.py createsuperuser
```

Admin panel is at `http://localhost:8000/admin/` — you can upload and process
KnowledgeSources there as an alternative to the CLI commands below.

## 6. Embed documents

### From CLI (recommended for initial bulk load)

```bash
# Embed all PDFs in raw_sources/ (auto-detects resilience factor from headings)
uv run python manage.py embed_docs raw_sources/*.pdf

# Embed a specific file with an explicit resilience factor
uv run python manage.py embed_docs raw_sources/Handout-27.pdf --factor family_support
```

Supported file types: `.pdf`, `.docx`

Supported `--factor` values: `family_support`, `optimism`, `goal_directedness`,
`social_connections`, `health`. If omitted, the parser attempts to detect factors
from document headings.

### From Django admin

1. Go to **Raw Knowledge Base Sources** → **Add**
2. Fill in title, source type, upload file, set resilience factor/category
3. Select the source(s) → Actions → **Process selected sources**

This runs the same parse → chunk → embed → index pipeline.

### What happens during embedding

1. File is parsed and split into token-bounded chunks (max 512 tokens, 50-token overlap)
2. A `Document` + `DocumentChunk` rows are created in PostgreSQL
3. Each chunk is sent to OpenAI `text-embedding-3-small` (512-dimensional vectors)
4. Vectors are added to the FAISS index at `faiss_store/index.bin`
5. Document status is set to `indexed`

## 7. Verify

### Check retrieval (no LLM call)

```bash
uv run python manage.py debug_retrieve --no-llm "How to support family resilience?"
```

Shows matched chunks with similarity scores. If you see results, embedding worked.

### Full RAG query (retrieval + LLM)

```bash
uv run python manage.py debug_retrieve "What interventions help with low optimism?"
```

### Check index health

```bash
uv run python manage.py check_index_drift
```

Reports any mismatch between FAISS index and PostgreSQL. Add `--repair` to fix.

## 8. Run the server

```bash
uv run python manage.py runserver
```

### API endpoint

```
POST /rag/query/
Content-Type: application/json

{"query": "How to help a student with low social connections?", "top_k": 5}
```

## Maintenance commands

| Command | Purpose |
|---|---|
| `embed_docs <files> [--factor X]` | Parse, chunk, embed and index new documents |
| `rebuild_index [--status pending\|indexed\|stale]` | Re-embed all documents (or filtered by status) |
| `check_index_drift [--repair]` | Detect/fix FAISS ↔ PostgreSQL mismatches |
| `debug_retrieve <question> [--no-llm] [--top-k N]` | Test retrieval pipeline from CLI |

## Architecture overview

```
raw_sources/*.pdf
       │
       ▼
  file_importer    parse + chunk (tiktoken token boundaries)
       │
       ▼
  PostgreSQL       Document + DocumentChunk rows
       │
       ▼
  OpenAI API       text-embedding-3-small (512-dim vectors)
       │
       ▼
  FAISS index      faiss_store/index.bin (IndexFlatIP, inner product)
       │
       ▼
  RetrievalService    query → embed → FAISS search → hydrate from DB
       │
       ▼
  RAGService          retrieved chunks + LLM prompt → OpenAI gpt-4o-mini → answer
```

## Troubleshooting

**`tiktoken` SSL error on first run** — tiktoken downloads its encoding on first
use. If your server has restricted outbound HTTPS, run once on a machine with
internet access or pre-cache the encoding:
```bash
uv run python -c "import tiktoken; tiktoken.encoding_for_model('text-embedding-3-small')"
```

**`FAISS index not initialized`** — the index is created automatically on first
`embed_docs` run. If the file is missing, re-run embedding or `rebuild_index`.

**Duplicate documents after re-running `embed_docs`** — the command creates new
Document rows each run. If you need to re-embed the same files, delete the old
documents first (via admin panel) or use `rebuild_index --status stale`.
