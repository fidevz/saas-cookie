# ONBOARDING

> The first 7 days determine whether a user stays forever or churns.
> This file defines what activation looks like and how to get every user there.

---

## The Aha Moment

> The single action that correlates most strongly with a user becoming a long-term customer.

**Our Aha Moment:** [Describe the specific action — e.g. "User publishes their first X" or "User connects their first integration"]

**Time to Aha target:** < [X] minutes from signup

**How we know they reached it:** [Specific event in PostHog/analytics — e.g. `first_project_created`]

---

## Activation Funnel

Track drop-off at each step. If a step has < [X]% completion, it needs fixing.

| Step | Event name | Target completion | Current |
|------|-----------|------------------|---------|
| 1. Signup completed | `user_registered` | 100% | — |
| 2. Email verified | `email_verified` | >[X]% | — |
| 3. Profile completed | `profile_completed` | >[X]% | — |
| 4. [First key action] | `[event]` | >[X]% | — |
| 5. Aha moment reached | `[aha_event]` | >[X]% | — |
| 6. Returned day 3 | `session_day_3` | >[X]% | — |
| 7. Returned day 7 | `session_day_7` | >[X]% | — |

---

## First 7 Days Playbook

### Day 0 — Signup
- Welcome email sent immediately (see `marketing/playbooks/EMAIL.md` — Welcome Sequence)
- In-app: show setup checklist (progress bar drives completion)
- Goal: get them to first meaningful action before they close the tab

### Day 1
- Email #2: "One thing to do today" — single focused action
- In-app: tooltip or coach mark on the most important feature
- Trigger: if user hasn't completed [step X] → show contextual prompt

### Day 3
- Email #3: Check-in — "Are you getting value?"
- If user hasn't reached Aha Moment → send targeted help content
- If user HAS reached Aha Moment → send expansion prompt (next feature)

### Day 5
- Email #4: Case study or social proof relevant to their use case
- In-app: surface a feature they haven't tried yet

### Day 7
- Email #5: Trial conversion push (if on trial) OR week 1 milestone celebration
- Review activation cohort in analytics — users who didn't activate by day 7 rarely do

---

## Onboarding Friction Audit

Run this monthly. For each step where users drop off:
1. Watch session recordings (PostHog / Clarity)
2. Check support tickets for that step
3. Identify the friction — confusion, missing info, too many steps, slow load
4. Fix one thing at a time and measure impact

---

## Empty States

Every empty state in the product must:
- Explain what the feature does (1 sentence)
- Show what it looks like when populated (screenshot or illustration)
- Provide a single, obvious CTA to get started

Never show a blank page. Empty state = missed activation opportunity.

---

## Onboarding Checklist (in-product)

Show a progress checklist to new users with [X] items. Check them off as completed.
Recommended items:
- [ ] Complete your profile
- [ ] [First core action]
- [ ] [Second core action]
- [ ] Invite a teammate (if FEATURE_TEAMS enabled)
- [ ] Connect your [integration] (if applicable)

Completion reward: [e.g. unlock a feature, show a congratulations message, offer a discount]
