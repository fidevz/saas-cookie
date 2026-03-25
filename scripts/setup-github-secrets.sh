#!/usr/bin/env bash
# Pushes all required secrets to GitHub Actions.
# Requires: gh auth login, GITHUB_REPO, and all secret variables set.

set -euo pipefail

: "${GITHUB_REPO:?GITHUB_REPO is required (e.g. username/my-saas)}"
: "${COOLIFY_WEBHOOK_URL:?COOLIFY_WEBHOOK_URL is required}"
: "${COOLIFY_TOKEN:?COOLIFY_TOKEN is required}"
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

set_secret "COOLIFY_WEBHOOK_URL"  "$COOLIFY_WEBHOOK_URL"
set_secret "COOLIFY_TOKEN"        "$COOLIFY_TOKEN"
set_secret "TELEGRAM_BOT_TOKEN"   "$TELEGRAM_BOT_TOKEN"
set_secret "TELEGRAM_CHAT_ID"     "$TELEGRAM_CHAT_ID"

echo ""
echo "✅ All GitHub secrets configured."
echo "   Verify at: https://github.com/$GITHUB_REPO/settings/secrets/actions"
