.PHONY: test test-frontend test-frontend-watch test-frontend-coverage lint fmt build e2e e2e-ui e2e-debug e2e-headed release-patch release-minor release-major

# ─── Dev ──────────────────────────────────────────────────────────────────────

test:
	cd backend && make test
	cd frontend && pnpm test
	cd frontend && pnpm type-check
	cd frontend && pnpm lint

test-frontend:
	cd frontend && pnpm test $(ARGS)

test-frontend-watch:
	cd frontend && pnpm test:watch

test-frontend-coverage:
	cd frontend && pnpm test:coverage

lint:
	cd backend && make lint
	cd frontend && pnpm lint

fmt:
	cd backend && make fmt

# ─── E2E (Playwright) ─────────────────────────────────────────────────────────

e2e:
	cd testing && pnpm exec playwright test $(ARGS)

e2e-ui:
	cd testing && pnpm exec playwright test --ui

e2e-debug:
	cd testing && pnpm exec playwright test --debug $(ARGS)

e2e-headed:
	cd testing && pnpm exec playwright test --headed $(ARGS)

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
