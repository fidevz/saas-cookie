# Changelog

All notable changes to this boilerplate will be documented here.

Format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).
Versioning follows [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

---

## [0.1.0] — 2026-03-22

### Added
- **Backend:** Django 5.1 REST API with DRF, JWT auth, Google OAuth, multi-tenancy, Celery, Django Channels
- **Frontend:** Next.js 15 app with Tailwind, shadcn/ui, Zustand, next-intl (en/es)
- **Billing:** Full Stripe integration — plans, checkout, customer portal, webhooks, trials
- **Auth:** Email/password + Google OAuth, JWT with HttpOnly refresh cookie, token rotation
- **Multi-tenancy:** Subdomain-based tenant resolution via `TenantMiddleware`
- **Real-time:** WebSocket notifications via Django Channels + Redis
- **Feature flags:** `FEATURE_TEAMS`, `FEATURE_BILLING`, `FEATURE_NOTIFICATIONS`
- **Email:** Custom Resend backend for Django
- **Testing:** Playwright E2E suite covering auth, billing, team, notifications
- **CI/CD:** GitHub Actions for backend (lint + test) and frontend (lint + type-check)
- **Marketing:** Autonomous AI marketing system in `marketing/`
- **Growth:** Onboarding, retention, PLG, NPS, and affiliate program playbooks
- **Legal:** Privacy Policy, Terms of Service, Cookie Policy templates
- **Ops:** Deployment guide, incident response, monitoring setup, launch checklist
- **Support:** FAQ, customer success playbook
- **Docs:** Architecture overview, ADRs
- `CLAUDE.md` — AI assistant context
- `SECURITY.md` — security policy and vulnerability reporting
- `new-project.sh` — bootstrap script to rename the boilerplate

---

<!--
Changelog entry types:
- Added: new features
- Changed: changes in existing functionality
- Deprecated: soon-to-be-removed features
- Removed: removed features
- Fixed: bug fixes
- Security: security-related fixes
-->
