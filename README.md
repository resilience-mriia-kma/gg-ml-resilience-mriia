# ml-resilience-mriia

Django project with PostgreSQL and FAISS for RAG-based document retrieval.

## Prerequisites

- Python 3.13+
- [uv](https://docs.astral.sh/uv/)
- Docker & Docker Compose

## Setup

1. Clone the repository and install dependencies:

```bash
git clone <repo-url>
cd ml-resilience-mriia
uv sync
```

2. Create `.env` from the sample:

```bash
cp .env.sample .env
```

Edit `.env` and set your values (all variables are required).

3. Start PostgreSQL:

```bash
docker compose up -d
```

4. Run migrations:

```bash
uv run python manage.py migrate
```

5. Create a superuser:

```bash
uv run python manage.py createsuperuser
```

6. Run the development server:

```bash
uv run python manage.py runserver
```

Visit http://localhost:8000/admin to access the admin panel.

## Project structure

```
config/          Django project settings
resilience_app/  Backend API (Document model with pgvector embeddings)
docker-compose.yml   PostgreSQL with pgvector extension
```
