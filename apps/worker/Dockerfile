FROM python:3.13-slim

WORKDIR /app

# uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Workspace metadata + lockfile (the lock lives at the workspace root).
COPY pyproject.toml uv.lock ./
COPY apps/api/pyproject.toml ./apps/api/
COPY apps/worker/pyproject.toml ./apps/worker/

# Both apps: the worker executes via apps.api (engine, models, credential manager).
COPY apps/api ./apps/api
COPY apps/worker ./apps/worker

# Resolve the full workspace environment from the frozen lock.
RUN uv sync --frozen

ENV PYTHONPATH=/app

CMD ["uv", "run", "--no-sync", "celery", "-A", "apps.worker.app.jobs.tasks", "worker", "--loglevel=info"]
