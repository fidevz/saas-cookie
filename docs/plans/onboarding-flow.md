# Onboarding Flow

## Context

This boilerplate lacks a guided onboarding experience for new users. We're adding a configurable, DB-driven onboarding checklist that renders as a dismissible card on the dashboard. Steps are managed via Django admin so each project scaffolded from this boilerplate can define its own flow without code changes.

`CustomUser` already has `is_first_login` — the onboarding card will show for all non-dismissed users (not gated by first login, since steps may be added later).

---

## Backend

### 1. Feature flag

- `backend/config/settings/base.py` — add `"ONBOARDING": config("FEATURE_ONBOARDING", default=True, cast=bool)` to `FEATURE_FLAGS`
- `backend/apps/core/features.py` — add `onboarding_enabled()` classmethod

### 2. New app `apps.onboarding`

Create with `uv run python manage.py startapp onboarding apps/onboarding`. Register in `LOCAL_APPS` in `base.py`.

**Models** (`apps/onboarding/models.py`), both inherit `BaseModel`:

`OnboardingStep`:
- `key` — CharField(max_length=100, unique=True), e.g. `"create_team"`
- `title` — CharField(max_length=255)
- `description` — TextField(blank=True, default="")
- `action_url` — CharField(max_length=255, blank=True, default=""), frontend route
- `order` — PositiveIntegerField(default=0)
- `is_active` — BooleanField(default=True)
- `required_feature` — CharField(max_length=50, blank=True, default=""), e.g. `"TEAMS"` — step only shown when that flag is on
- Meta: `ordering = ["order"]`

`UserOnboardingProgress`:
- `user` — FK to AUTH_USER_MODEL (CASCADE)
- `step` — FK to OnboardingStep (CASCADE)
- `completed` — BooleanField(default=False)
- `completed_at` — DateTimeField(null=True, blank=True)
- Meta: `unique_together = [("user", "step")]`

### 3. Add `onboarding_dismissed` BooleanField(default=False) to `CustomUser` in `backend/apps/users/models.py`

### 4. Serializers (`apps/onboarding/serializers.py`)

- `OnboardingStepSerializer` — ModelSerializer for step fields
- `OnboardingProgressSerializer` — nested, includes `step` + `completed` + `completed_at`
- `OnboardingStatusSerializer` — wraps `dismissed`, `steps`, `completed_count`, `total_count`

### 5. Views (`apps/onboarding/views.py`)

All require `IsAuthenticated`, gated by `FeatureFlags.onboarding_enabled()`:

| Method | Path | View | Behavior |
|--------|------|------|----------|
| GET | `/api/v1/onboarding/` | `OnboardingStatusView` | Returns all active steps with user progress. Lazily creates `UserOnboardingProgress` rows via `get_or_create`. Short-circuits if `user.onboarding_dismissed`. Filters out steps whose `required_feature` is disabled. |
| PATCH | `/api/v1/onboarding/<step_id>/complete/` | `CompleteStepView` | Marks step completed, sets `completed_at`. |
| POST | `/api/v1/onboarding/dismiss/` | `DismissOnboardingView` | Sets `user.onboarding_dismissed = True`. |

### 6. URLs & registration

- `apps/onboarding/urls.py` — three paths
- `config/urls.py` — add `path("onboarding/", include("apps.onboarding.urls"))` alongside existing app includes

### 7. Admin (`apps/onboarding/admin.py`)

- `OnboardingStepAdmin` — list_display: order, key, title, is_active, required_feature. list_editable: order, is_active.
- `UserOnboardingProgressAdmin` — list_display: user, step, completed, completed_at.

### 8. Seed data

Add `_seed_onboarding_steps()` to `backend/apps/core/management/commands/seed.py` with 4 default steps:
1. `complete_profile` — "Complete your profile" → `/settings` (no feature gate)
2. `create_team` — "Create a team" → `/settings/team` (requires `TEAMS`)
3. `invite_member` — "Invite a team member" → `/settings/team` (requires `TEAMS`)
4. `setup_billing` — "Set up billing" → `/billing` (requires `BILLING`)

Use `update_or_create(key=..., defaults=...)` for idempotency.

### 9. Migrations

Run `make migrations` — produces `apps/onboarding/migrations/0001_initial.py` + a users migration for `onboarding_dismissed`.

---

## Frontend

### 10. Types (`frontend/src/types/index.ts`)

Add `OnboardingStep`, `OnboardingProgress`, `OnboardingStatus` interfaces. Add `ONBOARDING: boolean` to `FeatureFlags`.

### 11. Feature store (`frontend/src/stores/feature-store.ts`)

Add `ONBOARDING: true` to defaults.

### 12. Onboarding store (`frontend/src/stores/onboarding-store.ts`)

Zustand store with:
- `status: OnboardingStatus | null`
- `isLoading: boolean`
- `fetchOnboarding()` — GET `/onboarding/`
- `completeStep(stepId)` — PATCH `/onboarding/{stepId}/complete/`, update local state
- `dismiss()` — POST `/onboarding/dismiss/`, set `status.dismissed = true`

### 13. Dashboard card (`frontend/src/components/onboarding-checklist.tsx`)

- Self-gates on `flags.ONBOARDING` and `status.dismissed`
- shadcn `Card` with progress bar, step list (check icon + title + description + arrow link)
- Completed steps get muted/struck-through style
- X button to dismiss (with confirmation)
- Congratulations state when all steps are done
- Icon map by `step.key` (Users, UserPlus, CreditCard, UserCog) with fallback

### 14. Dashboard integration (`frontend/src/app/(protected)/dashboard/page.tsx`)

Import `OnboardingChecklist`, render between greeting and account summary. Call `fetchOnboarding()` in useEffect. Component handles its own visibility logic.

### 15. i18n

Add `"onboarding"` key to `messages/en.json` and `messages/es.json` with: title, subtitle (with `{completed}/{total}` interpolation), dismiss, dismissConfirm, congratulations, congratulationsSubtitle.

---

## Backend tests

### 16. Tests (`backend/apps/onboarding/tests/`)

- `test_views.py` — status returns steps with progress, respects feature flag (403 when off), filters by `required_feature`, dismissed short-circuit, complete step, dismiss, unauthenticated 401
- `test_models.py` — unique_together constraint, ordering

---

## Verification

1. `make migrations && make migrate && make seed`
2. `make test` — all new + existing tests pass
3. `make run` + `pnpm dev` — dashboard shows checklist card for non-dismissed users
4. Click step links → navigates correctly
5. Complete a step → check icon updates, progress bar advances
6. Dismiss → card disappears, reload confirms it stays hidden
7. Toggle `FEATURE_ONBOARDING=False` → card doesn't render, API returns 403

---

## Files summary

**New (13 files):**
- `backend/apps/onboarding/__init__.py`, `apps.py`, `models.py`, `serializers.py`, `views.py`, `urls.py`, `admin.py`
- `backend/apps/onboarding/tests/__init__.py`, `test_views.py`, `test_models.py`
- `backend/apps/onboarding/migrations/0001_initial.py` (auto)
- `frontend/src/stores/onboarding-store.ts`
- `frontend/src/components/onboarding-checklist.tsx`

**Modified (8 files):**
- `backend/config/settings/base.py` — LOCAL_APPS + FEATURE_FLAGS
- `backend/config/urls.py` — onboarding URL include
- `backend/apps/core/features.py` — onboarding_enabled()
- `backend/apps/core/management/commands/seed.py` — seed steps
- `backend/apps/users/models.py` — onboarding_dismissed field
- `frontend/src/types/index.ts` — new types + FeatureFlags
- `frontend/src/stores/feature-store.ts` — ONBOARDING default
- `frontend/src/app/(protected)/dashboard/page.tsx` — render checklist
- `frontend/messages/en.json` + `frontend/messages/es.json` — i18n
