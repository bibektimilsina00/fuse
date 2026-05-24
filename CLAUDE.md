# Fuse — Project Instructions

## Commands

**Frontend** (`apps/web_v2`):
- Dev: `pnpm --filter web_v2 dev`
- Build: `pnpm --filter web_v2 build`
- Lint: `pnpm --filter web_v2 lint`
- Typecheck: `pnpm --filter web_v2 typecheck`

**Backend** (`apps/api`):
- Dev: `cd apps/api && uv run uvicorn app.main:app --reload`
- Test: `cd apps/api && uv run pytest`
- Lint/format: `uvx ruff check . && uvx ruff format .`
- Migrations: `cd apps/api && uv run alembic upgrade head`

## Fix discipline (mandatory)

Before fixing any bug:
1. State root cause (where wrong thing originates, not where it surfaces)
2. State lazy fix rejected
3. State correct fix + files touched
4. Fix at source. Never at consumer.

Banned: `as any`, `@ts-ignore`, `# type: ignore`, node-type checks in generic code,
`try/except: pass`, null checks hiding missing values, duplicated logic.

## Architecture

- **Nodes**: `CustomNode` fixed-output, `ConditionNode` dynamic handles. No node-type checks inside either.
- **Inspector**: Field visibility logic in `panels/inspector/visibility.ts` only.
- **Theming**: CSS variables (`var(--token)`) or Tailwind tokens. No hardcoded hex.
- **Components**: Reuse `components/ui/`. Never re-implement inline.
- **Backend**: Router → Service → Repository → Model. Logic in Service. ORM: SQLModel.
