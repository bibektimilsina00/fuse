---
name: db-migrate
description: "Generate an Alembic migration from current SQLAlchemy model changes and optionally apply it. Usage: /db-migrate <short description of the change>"
disable-model-invocation: true
---

# db-migrate skill

## Steps

1. **Get description** — if not provided as an argument, ask for a short snake_case description (e.g. `add_execution_tags`, `add_user_id_to_credential`)

2. **Generate migration** — run from `apps/api/`:
   ```bash
   cd apps/api && alembic revision --autogenerate -m "<description>"
   ```

3. **Show the generated file** — read and display the new migration file from `apps/api/alembic/versions/`. Point out:
   - What tables/columns are being added/modified/dropped
   - Any nullable issues (columns added to existing tables should have server_default or nullable=True)
   - Whether the downgrade() is correct

4. **Confirm before applying** — ask the user: "Apply this migration now? (yes/no)"

5. **If yes** — run:
   ```bash
   cd apps/api && alembic upgrade head
   ```
   Report success or show the full error if it fails.

6. **If no** — tell the user the file is saved and they can run `alembic upgrade head` manually when ready, or `alembic downgrade -1` to revert.

## Common issues to flag

- Adding a NOT NULL column to an existing table without a default → will fail on non-empty DB
- Dropping a column that has data → warn the user
- Migration imports a model that isn't in `apps/api/app/models/__init__.py` → will cause mapper errors

## Working directory

Always run alembic commands from `apps/api/` (not the repo root) since that's where `alembic.ini` lives.
