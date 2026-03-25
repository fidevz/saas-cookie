#!/usr/bin/env bash
# Configures Coolify via API: creates project, app, sets env vars and domains.
# Requires: COOLIFY_URL, COOLIFY_TOKEN, GITHUB_REPO, DOMAIN, and all env vars.

set -euo pipefail

: "${COOLIFY_URL:?COOLIFY_URL is required (e.g. http://SERVER_IP:8000)}"
: "${COOLIFY_TOKEN:?COOLIFY_TOKEN is required}"
: "${GITHUB_REPO:?GITHUB_REPO is required}"
: "${DOMAIN:?DOMAIN is required}"

API="$COOLIFY_URL/api/v1"
HEADERS=(-H "Authorization: Bearer $COOLIFY_TOKEN" -H "Content-Type: application/json")

echo "Configuring Coolify at $COOLIFY_URL"
echo ""

# ─── Helper ───────────────────────────────────────────────────────────────────
coolify_post() {
  local path=$1
  local data=$2
  curl -s -X POST "$API$path" "${HEADERS[@]}" -d "$data"
}

coolify_get() {
  local path=$1
  curl -s -X GET "$API$path" "${HEADERS[@]}"
}

# ─── 1. Get server UUID ───────────────────────────────────────────────────────
echo "→ Getting server info..."
SERVER_UUID=$(coolify_get "/servers" | jq -r '.[0].uuid')
echo "  Server UUID: $SERVER_UUID"

# ─── 2. Create project ────────────────────────────────────────────────────────
echo "→ Creating project..."
PROJECT_UUID=$(coolify_post "/projects" \
  "{\"name\":\"$APP_NAME\",\"description\":\"$APP_NAME production\"}" \
  | jq -r '.uuid')
echo "  Project UUID: $PROJECT_UUID"

# ─── 3. Get production environment ────────────────────────────────────────────
ENVIRONMENT_NAME=$(coolify_get "/projects/$PROJECT_UUID/environments" \
  | jq -r '.[0].name')
echo "  Environment: $ENVIRONMENT_NAME"

# ─── 4. Add GitHub source ─────────────────────────────────────────────────────
echo "→ Note: Connect GitHub source manually in Coolify UI if not already done."
echo "  (Coolify → Sources → GitHub App → install on $GITHUB_REPO)"
echo ""

# ─── 5. Create Docker Compose application ─────────────────────────────────────
echo "→ Creating Docker Compose application..."
APP_RESPONSE=$(coolify_post "/applications/dockercompose" "{
  \"project_uuid\": \"$PROJECT_UUID\",
  \"environment_name\": \"$ENVIRONMENT_NAME\",
  \"server_uuid\": \"$SERVER_UUID\",
  \"git_repository\": \"https://github.com/$GITHUB_REPO\",
  \"git_branch\": \"main\",
  \"docker_compose_location\": \"/docker-compose.yml\",
  \"name\": \"$APP_NAME\",
  \"description\": \"$APP_NAME full stack\"
}")

APP_UUID=$(echo "$APP_RESPONSE" | jq -r '.uuid')
echo "  App UUID: $APP_UUID"

if [ -z "$APP_UUID" ] || [ "$APP_UUID" = "null" ]; then
  echo "  ❌ Failed to create app. Response:"
  echo "$APP_RESPONSE" | jq .
  exit 1
fi

# ─── 6. Get deploy webhook ────────────────────────────────────────────────────
echo "→ Getting deploy webhook..."
WEBHOOK_URL=$(coolify_get "/applications/$APP_UUID" | jq -r '.webhook_url // empty')

if [ -n "$WEBHOOK_URL" ]; then
  echo "  Webhook URL: $COOLIFY_URL$WEBHOOK_URL"
  export COOLIFY_WEBHOOK_URL="$COOLIFY_URL$WEBHOOK_URL"
else
  echo "  ℹ️  Webhook URL not available yet — get it from Coolify UI after first deploy"
fi

echo ""
echo "✅ Coolify configured."
echo ""
echo "Next steps:"
echo "  1. Open $COOLIFY_URL and set environment variables in the app settings"
echo "  2. Configure domains: $DOMAIN (frontend), api.$DOMAIN (backend), storage.$DOMAIN (MinIO port 9001)"
echo "  3. Click Deploy"
echo ""
echo "App UUID: $APP_UUID (save this)"
