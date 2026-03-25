# Release Playbook

> Claude reads this file to execute releases end-to-end.
> To trigger: tell Claude "do a patch/minor/major release" or "release version X.Y.Z".

---

## One-Time Setup (human does this once)

```bash
# 1. Install GitHub CLI
brew install gh

# 2. Authenticate
gh auth login
# → choose GitHub.com → HTTPS → authenticate via browser

# 3. Verify
gh auth status
gh repo view   # should show your repo

# 4. Confirm git identity is set
git config user.name   # must not be empty
git config user.email  # must not be empty
```

That's it. After this, Claude can do all future releases autonomously.

---

## Release Types

| Command | When to use | Example: 0.1.0 → |
|---------|------------|-----------------|
| patch release | Bug fixes, small changes | 0.1.1 |
| minor release | New features, backwards compatible | 0.2.0 |
| major release | Breaking changes | 1.0.0 |

---

## Claude's Release Steps

When asked to do a release, Claude executes these steps **in order**. Stop immediately if any step fails.

### Step 1 — Verify clean state
```bash
git status                    # must show nothing to commit
git checkout main
git pull origin main          # must be up to date
```
If there are uncommitted changes → stop and tell the user.

### Step 2 — Run all tests
```bash
cd backend && make test       # pytest must pass
cd ../frontend && npm run type-check  # tsc must pass
cd ../frontend && npm run lint        # eslint must pass
```
If any test fails → stop. Do not release broken code.

### Step 3 — Calculate new version
Read current version from `backend/pyproject.toml`.
Calculate new version based on release type (patch/minor/major).

### Step 4 — Update version in both files
- `backend/pyproject.toml` → `version = "X.Y.Z"`
- `frontend/package.json` → `"version": "X.Y.Z"`

Both must always be in sync.

### Step 5 — Update CHANGELOG.md
Move items from `## [Unreleased]` to a new `## [X.Y.Z] — YYYY-MM-DD` section.
If `## [Unreleased]` is empty, summarize what changed based on git log since last tag:
```bash
git log $(git describe --tags --abbrev=0)..HEAD --oneline
```

### Step 6 — Commit the release
```bash
git add backend/pyproject.toml frontend/package.json CHANGELOG.md
git commit -m "chore: release vX.Y.Z"
```

### Step 7 — Tag and push
```bash
git tag vX.Y.Z
git push origin main
git push origin vX.Y.Z
```

### Step 8 — Create GitHub Release
```bash
gh release create vX.Y.Z \
  --title "vX.Y.Z" \
  --notes "$(sed -n '/## \[X.Y.Z\]/,/## \[/p' CHANGELOG.md | head -n -1)" \
  --latest
```

Extract the release notes from `CHANGELOG.md` for the specific version section.

### Step 9 — Confirm
```bash
gh release view vX.Y.Z   # confirm it's live
```

Report back: release URL, version, and that the deploy workflow was triggered.

---

## What Happens After

1. GitHub Release is published
2. `.github/workflows/deploy.yml` triggers automatically
3. Coolify pulls latest code and rebuilds all containers
4. You receive a Telegram notification with the result

The whole process from "do a patch release" to "running in production" takes ~5 minutes.

---

## Rollback

If the deploy causes a problem after release:

```bash
# Option 1: Rollback in Coolify UI (one click, fastest)
# Coolify → Application → Deployments → previous deploy → Redeploy

# Option 2: Create a fix and do a new patch release
# Fix the issue → "do a patch release"

# Option 3: Revert the release commit
git revert vX.Y.Z
git push origin main
# Then do a new patch release
```
