#!/usr/bin/env bash
# ----------------------------------------------------------------------
# Fuse — one-time VPS bootstrap
#
# Run ONCE, the first time after the VPS is provisioned. Sets up:
#   - Docker (official installer)
#   - ufw firewall (22 / 80 / 443 only)
#   - `/opt/fuse/deploy` target directory the deploy workflow writes to
#   - Authorized key for the GitHub Actions deploy user
#
# After this script finishes, the GitHub Actions deploy workflow takes
# over for every subsequent release — no manual SSH for ops.
#
# Usage on the VPS:
#     curl -fsSL https://raw.githubusercontent.com/bibektimilsina00/fuse_monorepo/main/deploy/bootstrap-vps.sh | bash -s -- "<paste your deploy_key.pub here>"
#
# Or, if you're already SSHed in and have the repo cloned:
#     ./bootstrap-vps.sh "<paste deploy_key.pub here>"
# ----------------------------------------------------------------------
set -euo pipefail

if [[ $EUID -ne 0 ]]; then
  echo "✗ Run as root (or via sudo)." >&2
  exit 1
fi

DEPLOY_KEY_PUB="${1:-}"
if [[ -z "${DEPLOY_KEY_PUB}" ]]; then
  echo "usage: $0 '<deploy_key.pub contents>'" >&2
  echo "       (generate locally with: ssh-keygen -t ed25519 -C fuse-deploy -f deploy_key -N \"\")" >&2
  exit 2
fi

echo "▶ Installing Docker…"
if ! command -v docker >/dev/null 2>&1; then
  curl -fsSL https://get.docker.com | sh
else
  echo "  Docker already installed; skipping."
fi

echo "▶ Confirming Docker + compose…"
docker --version
docker compose version

echo "▶ Configuring ufw (22 / 80 / 443 only)…"
if command -v ufw >/dev/null 2>&1; then
  ufw allow 22/tcp  || true
  ufw allow 80/tcp  || true
  ufw allow 443/tcp || true
  ufw --force enable || true
else
  echo "  ufw not installed; skipping firewall step."
fi

echo "▶ Creating /opt/fuse/deploy + /opt/fuse/deploy/pg-init…"
mkdir -p /opt/fuse/deploy/pg-init
chown -R root:root /opt/fuse
chmod 750 /opt/fuse /opt/fuse/deploy

echo "▶ Installing GitHub Actions deploy key…"
mkdir -p ~/.ssh
chmod 700 ~/.ssh
touch ~/.ssh/authorized_keys
chmod 600 ~/.ssh/authorized_keys

# Idempotent — don't append the same key twice.
if ! grep -qxF "${DEPLOY_KEY_PUB}" ~/.ssh/authorized_keys; then
  printf '%s\n' "${DEPLOY_KEY_PUB}" >> ~/.ssh/authorized_keys
  echo "  Added deploy key."
else
  echo "  Deploy key already present; skipping."
fi

echo
echo "✓ VPS bootstrap complete."
echo
echo "Next:"
echo "  1. In GitHub → Settings → Secrets and variables → Actions:"
echo "       Secrets:  VPS_SSH_PRIVATE_KEY, ENV_PRODUCTION (optional: GHCR_PAT)"
echo "       Variables: VPS_HOST, VPS_USER, VPS_DEPLOY_DIR"
echo "  2. Create the 'production' environment (Settings → Environments → New)."
echo "  3. Trigger the deploy workflow (push to main, or run 'deploy' from Actions)."
