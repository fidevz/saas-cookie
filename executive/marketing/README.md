# Autonomous Marketing System

> This system runs autonomously via Claude on a cron schedule.
> Before executing any task, read this file completely.

---

## How This System Works

This is a self-operating marketing system. Claude reads these files to understand the product, audience, strategy, and rules — then executes marketing tasks autonomously with minimal human involvement.

**Humans define:** strategy, limits, goals, product context
**Claude executes:** content creation, ad management, email scheduling, analytics, decisions within defined thresholds

---

## First Run Checklist

Before the system can operate, the following files must be completed:

- [ ] `context/PRODUCT.md` — fill all product details
- [ ] `context/AUDIENCE.md` — define at least one ICP
- [ ] `context/COMPETITORS.md` — add at least 2 competitors
- [ ] `context/BRAND.md` — define voice, tone, and writing rules
- [ ] `context/DESIGN_SYSTEM.md` — add brand colors, fonts, and visual specs
- [ ] `context/COMMUNICATION.md` — add at least 5 proven hooks
- [ ] `strategy/GOALS.md` — set KPIs and targets for current period
- [ ] `strategy/BUDGET.md` — set hard spending limits
- [ ] `strategy/CHANNELS.md` — define which channels are active
- [ ] `decisions/THRESHOLDS.md` — fill in all `[X]` values with real numbers
- [ ] `decisions/ESCALATION.md` — add Telegram Bot credentials

---

## System Architecture

```
context/          → WHO we are and WHO we talk to
  PRODUCT.md      → what we sell
  AUDIENCE.md     → who we sell to
  COMPETITORS.md  → who we compete against
  BRAND.md        → how we sound
  DESIGN_SYSTEM.md → how we look
  COMMUNICATION.md → what we say

strategy/         → WHAT we want to achieve
  GOALS.md        → KPIs and targets
  CHANNELS.md     → which channels and why
  BUDGET.md       → financial limits
  EXPERIMENTS.md  → active A/B tests

playbooks/        → HOW we execute
  CONTENT.md      → organic content creation
  PAID_ADS.md     → ad campaign management
  SEO.md          → organic search
  EMAIL.md        → email sequences

decisions/        → WHEN to do what
  CADENCE.md      → daily/weekly/monthly schedule
  THRESHOLDS.md   → metric-based decision rules
  KILL_CRITERIA.md → when to stop something
  ESCALATION.md   → what requires human approval

state/            → WHAT has happened
  LOG.md          → append-only action log
  WINS.md         → what worked and why
  LOSSES.md       → what failed and why
```

---

## Tool Stack

| Tool | Purpose | Auth required |
|------|---------|--------------|
| Meta Ads API | Campaign management | Meta Business access token |
| Google Ads API | Campaign management | Google Ads OAuth |
| Google Analytics 4 API | Website analytics | GA4 API key |
| Google Search Console API | SEO monitoring | Search Console OAuth |
| Publer API | Social media publishing (all channels) | Publer Business API key |
| Ideogram API | AI image generation | Ideogram API key |
| Resend API | Email marketing | Resend API key |
| DataForSEO API | Keyword research | DataForSEO credentials |
| Telegram Bot API | Human notifications | Bot token + chat ID |

---

## Execution Flow (every run)

```
1. Read README.md (this file)
2. Read decisions/CADENCE.md → determine what run type this is
3. Read state/LOG.md → check recent history and pending items
4. Read strategy/BUDGET.md → verify spend headroom
5. Execute tasks for this run type (DAILY / WEEKLY / MONTHLY)
6. For each action: check decisions/THRESHOLDS.md before acting
7. For escalations: follow decisions/ESCALATION.md exactly
8. Append all actions to state/LOG.md
9. Send Telegram summary if required by this run type
```

---

## Core Rules (never violate)

1. **Budget is a hard limit.** Never spend above the ceiling in `strategy/BUDGET.md`.
2. **When in doubt, escalate.** Use `decisions/ESCALATION.md` if unsure.
3. **Never delete content.** Pause, archive, or flag — but never delete without human approval.
4. **Log everything.** Every action goes in `state/LOG.md` before moving to the next task.
5. **Brand first.** No content goes out that violates `context/BRAND.md` or `context/COMMUNICATION.md`.
6. **Learn from history.** Always check `state/WINS.md` and `state/LOSSES.md` before creating new campaigns or content.
7. **One thing at a time.** Complete each cadence task fully before moving to the next.
