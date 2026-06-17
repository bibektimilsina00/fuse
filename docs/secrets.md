# Fuse — Secrets inventory

Where every secret lives, who generates it, and what breaks if it's missing
or rotated.

## Local development

- `.env` at the repo root, copied from `.env.example`.
- Not committed.

## Production runtime

- `/opt/fuse/deploy/.env` on the VPS, `chmod 600`.
- **Written by the `deploy` GitHub Actions workflow** from the
  `ENV_PRODUCTION` secret on every deploy. Do not edit the VPS copy
  directly — the next CI run overwrites it.
- Source of truth = the `ENV_PRODUCTION` GitHub Actions secret.

## GitHub Actions secrets + variables

The CI/CD pipeline ships `.env` and the compose stack to the VPS over
SSH. All deploy-time credentials live in GitHub.

### Secrets (Settings → Secrets and variables → Actions → Secrets)

| Name | Required? | Purpose | Source |
|---|---|---|---|
| `VPS_SSH_PRIVATE_KEY` | yes | Private SSH key the deploy workflow uses to log into the VPS. | `ssh-keygen -t ed25519 -C fuse-deploy -f deploy_key -N ""` locally. Paste the `deploy_key` file (private half) here. |
| `ENV_PRODUCTION` | yes | Full contents of `deploy/.env`. Written verbatim onto the VPS at `/opt/fuse/deploy/.env`. | Build locally from `deploy/.env.production.example`, then `cat deploy/.env \| pbcopy` and paste. |
| `GHCR_PAT` | optional | Personal Access Token with `read:packages` scope. Only needed if you keep the ghcr packages private. | github.com → Settings → Developer settings → PATs (classic) → check `read:packages`. Leave the secret empty when packages are public. |
| `GITHUB_TOKEN` | auto | Provided by Actions. Used by `build-publish` to push images to ghcr. | n/a |

### Variables (Settings → Secrets and variables → Actions → Variables)

| Name | Value | Why a variable, not a secret |
|---|---|---|
| `VPS_HOST` | `139.59.71.226` | Public IP, not sensitive. |
| `VPS_USER` | `root` | Public, not sensitive. |
| `VPS_DEPLOY_DIR` | `/opt/fuse/deploy` | Path constant. |

### Environment

Create a `production` GitHub Environment (Settings → Environments → New).
Optionally add Required Reviewers to gate every deploy on a click.

---

## Secret-by-secret reference (the .env contents)

These values live inside the `ENV_PRODUCTION` GitHub secret. The table
documents what each one does and what breaks if it's missing or rotated.

| Var | Generator | Used by | Rotation impact |
|---|---|---|---|
| `SECRET_KEY` | `openssl rand -hex 32` | JWT signing for user sessions | All existing JWTs invalidated — every user is logged out. |
| `ENCRYPTION_KEY` | `python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"` | Fernet encrypting credential blobs at rest in Postgres | **Existing credentials become un-decryptable.** Rotating means every connection (Google, Meta, Slack, etc) must be re-connected by every user. Treat as forever-immutable in v1; design a key-versioned scheme before changing. |
| `POSTGRES_PASSWORD` | `openssl rand -base64 24 \| tr -d '/+='` | Postgres auth | Compose recreate restarts API + worker (they reload the env). pgdump backups remain readable — they don't store the password. |
| `GOOGLE_CLIENT_ID` / `_SECRET` | Google Cloud Console → OAuth client | Every Google node (gmail, gcal, gdrive, gsheets, gdocs, gtasks, gforms, gpeople, gyt, gslides, gchat, ga4, gsc, gcs) | Rotating breaks new OAuth flows until users reconnect (existing tokens still work until refresh). |
| `META_APP_ID` / `_SECRET` | Meta App Dashboard | Instagram, Facebook, WhatsApp, Lead Ads | Same as Google. |
| OAuth secrets (Slack/GitHub/Notion/Discord/Linear) | Each provider's app dashboard | The corresponding node | Same. |
| AI provider API keys | Each provider's dashboard | LLM, Embeddings, Vision, TTS, STT, Image gen nodes | Workflow runs that use the rotated provider fail until the key is updated. |
| `SMTP_*` | Your SMTP provider (SendGrid / SES / etc) | Workspace invites, password resets | Without SMTP, those emails are logged to stdout instead of sent. |
| `SENTRY_DSN` | sentry.io project | Error tracking on backend + frontend | Optional; missing = no Sentry events emitted. |

---

## Rotating a secret

1. Generate the new value locally.
2. Edit your local `deploy/.env` to match (so your laptop copy is in
   sync) — optional but recommended.
3. Edit the `ENV_PRODUCTION` GitHub secret with the new value (paste
   the whole file).
4. Trigger the `deploy` workflow (Actions → deploy → Run workflow).
   The new `.env` is shipped + services restart with updated env.
5. For OAuth secret rotations: update the OAuth provider console with
   the new secret **before** running the deploy.

### Fast-path for testing (don't forget to round-trip)

For quick experimentation you can SSH into the VPS, edit
`/opt/fuse/deploy/.env`, and run `./deploy.sh`. Then update the
`ENV_PRODUCTION` GitHub secret — the next CI deploy overwrites the
VPS copy from the secret. If you skip the secret update, the next
push undoes your change.
