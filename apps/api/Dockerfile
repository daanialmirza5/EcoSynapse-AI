# Build context is the REPO ROOT (see docker-compose.yml / `docker build -f
# apps/api/Dockerfile .`), not apps/api -- this image needs both the backend
# source and the top-level data/seed/ corpus, which live in different
# subtrees of the monorepo.
FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends gcc curl \
    && rm -rf /var/lib/apt/lists/*

COPY apps/api/pyproject.toml ./
COPY apps/api/app ./app
COPY apps/api/alembic ./alembic
COPY apps/api/alembic.ini ./
COPY data ./data

RUN pip install --no-cache-dir -e ".[postgres]"

ENV PYTHONUNBUFFERED=1 \
    DATABASE_URL=sqlite:///./ecosynapse.db \
    SEED_DATA_DIR=/app/data/seed

# Run as a non-root user. The default sqlite:// dev path writes the DB file
# into /app, so it must be writable by this user.
RUN useradd --create-home --uid 1000 appuser && chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

HEALTHCHECK --interval=15s --timeout=5s --start-period=10s --retries=5 \
    CMD curl -f http://localhost:8000/health || exit 1

CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000"]
