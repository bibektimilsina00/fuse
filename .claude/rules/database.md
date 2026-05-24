---
description: Database and migration rules
globs:
  - apps/api/alembic/**
  - apps/api/app/domains/**
  - apps/api/app/features/**/models.py
  - apps/api/app/features/**/repository.py
---

# Database rules

- ORM: SQLModel only. No raw SQLAlchemy Core or string SQL.
- Migrations: always generate via `uv run alembic revision --autogenerate -m "description"` — never hand-write migration files
- Apply: `uv run alembic upgrade head`
- Repositories do DB queries only — no business logic
- Services own transactions — repositories never commit independently
- Timestamps: use `utc_now_naive()` for all model timestamp fields (timezone-agnostic)
- Never drop columns in a migration without a deprecation migration first
