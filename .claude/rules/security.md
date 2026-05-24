---
description: Security rules for API, auth, and middleware code
globs:
  - apps/api/app/middleware/**
  - apps/api/app/core/**
  - apps/api/app/features/auth/**
  - apps/api/app/dependencies/**
  - apps/api/app/permissions/**
---

# Security rules

- Never log secrets, tokens, or passwords — not even partially
- Auth tokens go in httpOnly cookies or Authorization header only — never response body storage
- All user input validated with Pydantic/SQLModel before hitting DB
- SQL: use SQLModel ORM only — no raw string interpolation in queries
- Credential secrets stored in `apps/api/app/credential_manager/` — never inline
- Rate limiting via `slowapi` on all public endpoints
- Never expose internal error details to API consumers — log internally, return generic message
