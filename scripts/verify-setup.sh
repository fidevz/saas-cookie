#!/usr/bin/env bash
# Verifies the full stack is running correctly after initial deploy.
# Requires: DOMAIN

set -euo pipefail

: "${DOMAIN:?DOMAIN is required}"

PASS=0
FAIL=0

check() {
  local description=$1
  local url=$2
  local expected=${3:-200}

  status=$(curl -s -o /dev/null -w "%{http_code}" --max-time 10 "$url" || echo "000")

  if [ "$status" = "$expected" ]; then
    echo "  ✅ $description ($url)"
    PASS=$((PASS + 1))
  else
    echo "  ❌ $description — got HTTP $status, expected $expected ($url)"
    FAIL=$((FAIL + 1))
  fi
}

check_json() {
  local description=$1
  local url=$2
  local field=$3
  local expected_value=$4

  result=$(curl -s --max-time 10 "$url" || echo "{}")
  value=$(echo "$result" | jq -r "$field" 2>/dev/null || echo "error")

  if [ "$value" = "$expected_value" ]; then
    echo "  ✅ $description"
    PASS=$((PASS + 1))
  else
    echo "  ❌ $description — $field = '$value', expected '$expected_value'"
    FAIL=$((FAIL + 1))
  fi
}

echo "Verifying setup for $DOMAIN..."
echo ""

echo "── Frontend"
check "Landing page" "https://$DOMAIN"

echo ""
echo "── Backend"
check_json "Health check — status" "https://api.$DOMAIN/health/" ".status" "ok"
check_json "Health check — db"     "https://api.$DOMAIN/health/" ".db"     "ok"
check_json "Health check — redis"  "https://api.$DOMAIN/health/" ".redis"  "ok"
check     "API docs (Swagger)"    "https://api.$DOMAIN/api/docs/"

echo ""
echo "── Storage"
check "MinIO console" "https://storage.$DOMAIN" "200"

echo ""
echo "── API endpoints"
check "Plans endpoint (public)" "https://api.$DOMAIN/api/v1/subscriptions/plans/"

echo ""
echo "────────────────────────────────"
echo "Results: $PASS passed, $FAIL failed"
echo ""

if [ "$FAIL" -gt 0 ]; then
  echo "❌ Setup incomplete — fix the failing checks above."
  exit 1
else
  echo "✅ All checks passed. Your app is live at https://$DOMAIN"
  echo ""
  echo "Next steps:"
  echo "  1. Log in at https://$DOMAIN"
  echo "  2. Change the superuser password"
  echo "  3. Register Stripe webhook at https://dashboard.stripe.com/webhooks"
  echo "     URL: https://api.$DOMAIN/api/v1/subscriptions/webhook/"
  echo "  4. Add STRIPE_WEBHOOK_SECRET to GitHub secrets and redeploy via `make deploy`"
  echo "  5. Configure Google OAuth callback: https://api.$DOMAIN/api/v1/auth/google/"
fi
