#!/usr/bin/env bash
# Pushes all required secrets to GitHub Actions.
# Requires: gh auth login, GITHUB_REPO, and all secret variables set.
# See ops/KAMAL_SETUP.md § 6 for the full list and descriptions.

set -euo pipefail

: "${GITHUB_REPO:?GITHUB_REPO is required (e.g. username/my-saas)}"
: "${VPS_SSH_PRIVATE_KEY:?VPS_SSH_PRIVATE_KEY is required}"
: "${KAMAL_REGISTRY_PASSWORD:?KAMAL_REGISTRY_PASSWORD is required (GitHub PAT with write:packages)}"
: "${TELEGRAM_BOT_TOKEN:?TELEGRAM_BOT_TOKEN is required}"
: "${TELEGRAM_CHAT_ID:?TELEGRAM_CHAT_ID is required}"

echo "Pushing secrets to GitHub repo: $GITHUB_REPO"
echo ""

set_secret() {
  local name=$1
  local value=$2
  echo "→ Setting $name"
  echo "$value" | gh secret set "$name" --repo "$GITHUB_REPO"
  echo "  ✅ Done"
}

# Kamal infrastructure
set_secret "VPS_SSH_PRIVATE_KEY"       "$VPS_SSH_PRIVATE_KEY"
set_secret "KAMAL_REGISTRY_PASSWORD"   "$KAMAL_REGISTRY_PASSWORD"

# Notifications
set_secret "TELEGRAM_BOT_TOKEN"        "$TELEGRAM_BOT_TOKEN"
set_secret "TELEGRAM_CHAT_ID"          "$TELEGRAM_CHAT_ID"

echo ""
echo "✅ Core CI/CD secrets configured."
echo "   Add application secrets (SECRET_KEY, DATABASE_URL, STRIPE_*, etc.) manually at:"
echo "   https://github.com/$GITHUB_REPO/settings/secrets/actions"
echo "   See ops/KAMAL_SETUP.md § 6 for the full list."
