#!/usr/bin/env bash
# Usage: scripts/bump-version.sh [patch|minor|major]
# Bumps version in pyproject.toml and package.json in sync.

set -euo pipefail

BUMP_TYPE="${1:-patch}"

# ─── Read current version ─────────────────────────────────────────────────────
CURRENT=$(grep '^version = ' backend/pyproject.toml | sed 's/version = "\(.*\)"/\1/')
echo "Current version: $CURRENT"

IFS='.' read -r MAJOR MINOR PATCH <<< "$CURRENT"

# ─── Calculate new version ────────────────────────────────────────────────────
case "$BUMP_TYPE" in
  patch) PATCH=$((PATCH + 1)) ;;
  minor) MINOR=$((MINOR + 1)); PATCH=0 ;;
  major) MAJOR=$((MAJOR + 1)); MINOR=0; PATCH=0 ;;
  *)
    echo "ERROR: Unknown bump type '$BUMP_TYPE'. Use patch, minor, or major."
    exit 1
    ;;
esac

NEW_VERSION="$MAJOR.$MINOR.$PATCH"
echo "New version:     $NEW_VERSION"

# ─── Update pyproject.toml ───────────────────────────────────────────────────
sed -i.bak "s/^version = \"$CURRENT\"/version = \"$NEW_VERSION\"/" backend/pyproject.toml
rm -f backend/pyproject.toml.bak

# ─── Update package.json ─────────────────────────────────────────────────────
sed -i.bak "s/\"version\": \"$CURRENT\"/\"version\": \"$NEW_VERSION\"/" frontend/package.json
rm -f frontend/package.json.bak

echo "✅ Bumped $CURRENT → $NEW_VERSION in pyproject.toml and package.json"
echo "   Next: update CHANGELOG.md, commit, tag, and push."
