# Fuse — Operator runbook

Production deploy on `fuse.bibektimilsina.tech` (DigitalOcean droplet
`139.59.71.226`). Companion to `docs/devops-plan.md`.

Deployment model: **fully automatic**. Every push to `main` triggers
`build-publish` → `deploy` workflows on GitHub Actions. The CI/CD
pipeline ships compose YAML + scripts + `.env` to the VPS over SSH,
pulls newly-built images from ghcr.io, restarts changed services,
and health-checks the live URL.

Sections:

- [§1 One-time VPS + GitHub bootstrap](#1-one-time-vps--github-bootstrap)
- [§2 Everyday operations](#2-everyday-operations)
- [§3 Incident playbooks](#3-incident-playbooks)
- [§4 Off-VPS backups (Phase 1 add-on)](#4-off-vps-backups-phase-1-add-on)
- [§5 What lives where](#5-what-lives-where)

---

## 1. One-time VPS + GitHub bootstrap

Run once. About 20 minutes total.

### 1.1 DNS

On the registrar that owns `bibektimilsina.tech`:

| Type | Name | Value | TTL |
|------|------|-------|-----|
| A    | fuse | 139.59.71.226 | 300 |

Verify:

```
dig +short fuse.bibektimilsina.tech    # should print 139.59.71.226
```

### 1.2 Generate the GitHub deploy SSH key (on your laptop)

```
ssh-keygen -t ed25519 -C "fuse-deploy" -f ~/.ssh/fuse_deploy_key -N ""
# Produces:  ~/.ssh/fuse_deploy_key   (private — goes into GitHub Secret)
#            ~/.ssh/fuse_deploy_key.pub (public — goes into VPS authorized_keys)
```

Print the public key and copy it; you'll feed it to the bootstrap
script in step 1.3:

```
cat ~/.ssh/fuse_deploy_key.pub
```

### 1.3 Run the VPS bootstrap script

SSH into the VPS using your normal admin key (the `fv` alias). Run:

```
curl -fsSL https://raw.githubusercontent.com/bibektimilsina00/fuse_monorepo/main/deploy/bootstrap-vps.sh \
  | bash -s -- "ssh-ed25519 AAAA...your-pub-key-here... fuse-deploy"
```

What this does (idempotent — safe to re-run):

1. Installs Docker via the official one-liner if missing.
2. Opens ufw 22 / 80 / 443 only.
3. Creates `/opt/fuse/deploy/pg-init/`.
4. Appends the deploy public key to `/root/.ssh/authorized_keys`.

### 1.4 Set GitHub Secrets + Variables

GitHub → repo → Settings:

**Secrets and variables → Actions → Secrets:**

| Name | Value |
|------|-------|
| `VPS_SSH_PRIVATE_KEY` | Full contents of `~/.ssh/fuse_deploy_key` (the private file). Paste exactly, including the `BEGIN OPENSSH PRIVATE KEY` and `END` lines. |
| `ENV_PRODUCTION` | Full contents of `deploy/.env` (see §1.5 below). Paste exactly, one `KEY=value` per line. |
| `GHCR_PAT` *(optional)* | Personal Access Token with `read:packages` scope. **Only needed if you keep the ghcr packages private.** Public packages don't need any auth — leave the secret unset. |

**Settings → Secrets and variables → Actions → Variables:**

| Name | Value |
|------|-------|
| `VPS_HOST` | `139.59.71.226` |
| `VPS_USER` | `root` |
| `VPS_DEPLOY_DIR` | `/opt/fuse/deploy` |

**Settings → Environments → New environment** → name it `production`.
Optionally add yourself as a Required Reviewer if you want a manual
gate before every deploy. (Otherwise deploys go out on every green build.)

### 1.5 Build the production `.env`

Copy the template locally:

```
cp deploy/.env.production.example deploy/.env
# Generate the three required secrets:
echo "SECRET_KEY=$(openssl rand -hex 32)"
echo "ENCRYPTION_KEY=$(python3 -c 'from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())')"
echo "POSTGRES_PASSWORD=$(openssl rand -base64 24 | tr -d '/+=')"
# Paste those + your OAuth / AI provider keys into deploy/.env
nano deploy/.env

# Copy the whole file into the ENV_PRODUCTION GitHub secret:
cat deploy/.env | pbcopy   # macOS
# (Linux: cat deploy/.env | xclip -selection clipboard)
```

> ⚠️ Never commit `deploy/.env`. It's already covered by `.gitignore`.
> The local copy can stay on your laptop as a backup — it's just the
> source of truth for `ENV_PRODUCTION` until you rotate secrets.

### 1.6 (Only if you kept ghcr private) Make ghcr packages public

Public packages = no PAT needed = simpler workflow. Recommended:

GitHub → your profile → Packages → **fuse-api** → Package settings →
Change visibility → Public. Repeat for `fuse-worker` and `fuse-web`.

### 1.7 First deploy

Push any commit to `main` — or trigger manually:

```
Actions → deploy → Run workflow → Run
```

Watch the run:

- `Install SSH key`             — sets up agent
- `Sync compose stack to VPS`   — scp's the deploy/ files
- `Write production .env on VPS`— from the GitHub secret
- `Deploy (pull + up + prune)`  — docker compose runs the stack
- `Smoke-test the deploy`       — hits `https://fuse.bibektimilsina.tech/api/v1/health` until it returns 200

On first run the API container does `alembic upgrade head` before
opening the port — give it ~45 s.

### 1.8 Update OAuth redirect URIs (one-time)

Now that HTTPS is live, every OAuth provider needs the callback URL
updated. For each provider you actually use:

| Provider | Console path | URL to add |
|---|---|---|
| Google Cloud | APIs & Services → Credentials → OAuth client → Authorized redirect URIs | `https://fuse.bibektimilsina.tech/api/v1/credentials/oauth/google/callback` |
| Meta | App Dashboard → Use cases → settings → Valid OAuth Redirect URIs | `https://fuse.bibektimilsina.tech/api/v1/credentials/oauth/facebook/callback` |
| Slack | api.slack.com/apps → OAuth & Permissions → Redirect URLs | `https://fuse.bibektimilsina.tech/api/v1/credentials/oauth/slack/callback` |
| GitHub | Settings → Developer settings → OAuth Apps → Callback URL | `https://fuse.bibektimilsina.tech/api/v1/credentials/oauth/github/callback` |
| Notion | Integration settings → Redirect URIs | `https://fuse.bibektimilsina.tech/api/v1/credentials/oauth/notion/callback` |
| Discord | Developer Portal → app → OAuth2 → Redirects | `https://fuse.bibektimilsina.tech/api/v1/credentials/oauth/discord/callback` |
| Linear | Workspace settings → API → Application | `https://fuse.bibektimilsina.tech/api/v1/credentials/oauth/linear/callback` |

Until you do this, every OAuth flow returns `redirect_uri mismatch`.

### 1.9 Smoke test

- Open `https://fuse.bibektimilsina.tech` → app loads.
- Log in. Create a workspace. Connect a Google credential → confirm
  OAuth bounce works. Run a simple workflow.

Done.

---

## 2. Everyday operations

### Deploy a new build

```
git push origin main          # triggers build-publish then deploy
```

Watch in Actions tab. ~3 min cold, ~90s warm-cache. No SSH needed.

### Roll back to a previous build

Actions → `deploy` → Run workflow → **Image tag** = `sha-abc1234`
(grab from a recent `build-publish` run) → Run.

Or for a longer-lived pin: set `FUSE_IMAGE_TAG=sha-abc1234` in the
`ENV_PRODUCTION` GitHub secret and re-trigger.

### Tail logs (via SSH)

```
fv                                   # admin SSH alias
cd /opt/fuse/deploy
docker compose -f docker-compose.production.yml logs -f api worker
docker compose -f docker-compose.production.yml logs --tail=200 web
```

### Service health check

```
docker compose -f docker-compose.production.yml ps
```

Expected: every row says `(healthy)`. `Up x minutes` without
`(healthy)` is still booting; `unhealthy` is broken.

### Restart one service manually

```
docker compose -f docker-compose.production.yml restart api
```

### Run an ad-hoc Alembic command

```
docker compose -f docker-compose.production.yml exec api \
  uv run --no-sync alembic -c apps/api/alembic.ini history --verbose
```

### Open a psql shell

```
docker compose -f docker-compose.production.yml exec db \
  psql -U fuse -d fuse
```

### Rotate a secret

1. Edit the `ENV_PRODUCTION` GitHub secret with the new value.
2. Trigger the `deploy` workflow → new `.env` is shipped + services
   restart with the updated env.

(Or to test fast: SSH in, edit `/opt/fuse/deploy/.env`, run
`./deploy.sh`. Remember to update the GitHub secret afterward or the
next CI deploy overwrites your change.)

---

## 3. Incident playbooks

### "API is 5xx"

```
fv
cd /opt/fuse/deploy

# 1. What does the API say?
docker compose -f docker-compose.production.yml logs --tail=200 api

# 2. Is the DB up?
docker compose -f docker-compose.production.yml ps db
docker compose -f docker-compose.production.yml exec db pg_isready -U fuse

# 3. Is Redis up?
docker compose -f docker-compose.production.yml exec redis redis-cli ping

# 4. If migrations failed, the entrypoint log shows it.
docker compose -f docker-compose.production.yml restart api

# 5. Still broken — roll back from Actions (see §2).
```

### "Workflow executions stop firing"

Most likely the polling scheduler (`beat`) crashed:

```
docker compose -f docker-compose.production.yml ps beat
docker compose -f docker-compose.production.yml logs --tail=200 beat
docker compose -f docker-compose.production.yml restart beat
```

If `worker` shows `consumer.Connection.OperationalError`, it's a Redis
issue — restart Redis and the workers.

### "Caddy can't get a certificate"

```
docker compose -f docker-compose.production.yml logs --tail=200 web
```

Common causes:

- DNS isn't pointing at the VPS yet (`dig +short fuse.bibektimilsina.tech`).
- Port 80 is closed (Let's Encrypt's HTTP-01 challenge needs it open).
- LE rate limit — 5 certs per 7 days per registered domain. Wait or
  use the staging tier (edit Caddyfile: add `acme_ca https://acme-staging-v02.api.letsencrypt.org/directory`
  inside the global `{}` block).

### "Disk is full"

```
docker system df         # see what's eating it
docker image prune -af   # nuke dangling + unused (won't touch running)
docker volume ls
ls -lh /var/lib/docker/volumes/fuse_pg_backups/_data | tail
```

If `pg_backups` is huge: drop retention in `deploy/backup.sh` from 14
to 7 days; the next push to `main` re-syncs the script and the
`backup` container picks it up on its next loop.

### "Need to restore the DB"

See `deploy/restore.sh`. **Test on a scratch DB first.**

```
ls -lh /var/lib/docker/volumes/fuse_pg_backups/_data
./restore.sh /var/lib/docker/volumes/fuse_pg_backups/_data/latest.dump.gz
```

### "Deploy workflow failed at the smoke test"

The compose stack is up but the public URL isn't responding within
~60 s. Likely causes:

- Alembic migration is taking longer than the timeout — SSH in,
  watch `docker compose logs -f api`.
- Caddy is still getting the LE cert (first deploy after DNS change).
- A `.env` key is wrong — check `docker compose logs api` for
  `pydantic_settings` errors.

The smoke-test job tails the last 80 lines of api + web logs on
failure — start there.

---

## 4. Off-VPS backups (Phase 1 add-on)

Until set up, the only backup is on the same VPS that holds the live
data. Acceptable for testing, *not* for real launch.

Recommended: rsync the `pg_backups` volume to Backblaze B2 (~$0.005/GB/mo)
or DO Spaces nightly. Cron entry on the VPS:

```
# /etc/cron.d/fuse-offsite-backup
30 3 * * * root /usr/local/bin/rclone sync \
  /var/lib/docker/volumes/fuse_pg_backups/_data \
  b2:fuse-backups/$(date -u +\%Y\%m) --quiet
```

Requires `rclone` installed and configured with B2 credentials. Doc
the rclone setup separately when you wire this up.

---

## 5. What lives where

| Thing | Location |
|---|---|
| Compose stack | `/opt/fuse/deploy/docker-compose.production.yml` (CI overwrites on each deploy) |
| `.env` | `/opt/fuse/deploy/.env` (CI writes from `ENV_PRODUCTION` secret) |
| Postgres data | volume `fuse_postgres_data` → `/var/lib/docker/volumes/fuse_postgres_data/_data` |
| DB backups | volume `fuse_pg_backups` → `/var/lib/docker/volumes/fuse_pg_backups/_data` |
| Caddy certs | volume `fuse_caddy_data` → `/var/lib/docker/volumes/fuse_caddy_data/_data/caddy/certificates` |
| Images | `ghcr.io/bibektimilsina00/fuse-{api,worker,web}:<tag>` |
| Source of truth | `git@github.com:bibektimilsina00/fuse_monorepo.git` (main branch) |
