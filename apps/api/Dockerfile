FROM python:3.13-slim

WORKDIR /app

# uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Workspace metadata + lockfile (the lock lives at the workspace root).
COPY pyproject.toml uv.lock ./
COPY apps/api/pyproject.toml ./apps/api/
COPY apps/worker/pyproject.toml ./apps/worker/

# Both apps: the API imports the worker's Celery task at module load to enqueue.
COPY apps/api ./apps/api
COPY apps/worker ./apps/worker

# Resolve the full workspace environment from the frozen lock.
RUN uv sync --frozen

ENV PYTHONPATH=/app
ENV PORT=8000
EXPOSE 8000

CMD ["uv", "run", "--no-sync", "uvicorn", "apps.api.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
