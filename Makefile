.PHONY: test lint fmt build release-patch release-minor release-major

# ─── Dev ──────────────────────────────────────────────────────────────────────

test:
	cd backend && make test
	cd frontend && npm run type-check
	cd frontend && npm run lint

lint:
	cd backend && make lint
	cd frontend && npm run lint

fmt:
	cd backend && make fmt

# ─── Docker ───────────────────────────────────────────────────────────────────

build:
	docker compose build

up:
	docker compose up

down:
	docker compose down

logs:
	docker compose logs -f

# ─── Release ──────────────────────────────────────────────────────────────────
# These are helpers — Claude reads RELEASE.md and uses these as building blocks.

release-patch:
	@echo "Starting patch release — Claude should follow RELEASE.md"
	@$(MAKE) _check-clean
	@$(MAKE) test
	@scripts/bump-version.sh patch

release-minor:
	@echo "Starting minor release — Claude should follow RELEASE.md"
	@$(MAKE) _check-clean
	@$(MAKE) test
	@scripts/bump-version.sh minor

release-major:
	@echo "Starting major release — Claude should follow RELEASE.md"
	@$(MAKE) _check-clean
	@$(MAKE) test
	@scripts/bump-version.sh major

_check-clean:
	@if [ -n "$$(git status --porcelain)" ]; then \
		echo "ERROR: Working tree is not clean. Commit or stash changes first."; \
		exit 1; \
	fi

_check-main:
	@if [ "$$(git branch --show-current)" != "main" ]; then \
		echo "ERROR: Not on main branch."; \
		exit 1; \
	fi
