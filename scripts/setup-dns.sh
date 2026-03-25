#!/usr/bin/env bash
# Creates all required DNS records in Cloudflare.
# Requires: CLOUDFLARE_TOKEN, CLOUDFLARE_ZONE_ID, SERVER_IP, DOMAIN

set -euo pipefail

: "${CLOUDFLARE_TOKEN:?CLOUDFLARE_TOKEN is required}"
: "${CLOUDFLARE_ZONE_ID:?CLOUDFLARE_ZONE_ID is required}"
: "${SERVER_IP:?SERVER_IP is required}"

API="https://api.cloudflare.com/client/v4/zones/$CLOUDFLARE_ZONE_ID/dns_records"
HEADERS=(-H "Authorization: Bearer $CLOUDFLARE_TOKEN" -H "Content-Type: application/json")

create_record() {
  local name=$1
  local content=$2
  local proxied=${3:-true}

  echo "→ Creating A record: $name → $content"

  result=$(curl -s -X POST "$API" "${HEADERS[@]}" \
    -d "{\"type\":\"A\",\"name\":\"$name\",\"content\":\"$content\",\"proxied\":$proxied,\"ttl\":1}")

  if echo "$result" | jq -e '.success' > /dev/null 2>&1; then
    echo "  ✅ Created"
  else
    # Check if already exists
    if echo "$result" | grep -q "already exists"; then
      echo "  ℹ️  Already exists — skipping"
    else
      echo "  ❌ Failed: $(echo "$result" | jq -r '.errors[0].message // "unknown error"')"
      exit 1
    fi
  fi
}

echo "Setting up DNS records for $SERVER_IP..."
echo ""

create_record "@"       "$SERVER_IP"   # Root domain → frontend
create_record "api"     "$SERVER_IP"   # API → backend
create_record "storage" "$SERVER_IP"   # MinIO console
create_record "*"       "$SERVER_IP"   # Wildcard → tenant subdomains

echo ""
echo "✅ DNS configured. Records may take up to 60s to propagate."
echo "   Verify at: https://dns.google/resolve?name=api.$DOMAIN&type=A"
