# RETENTION

> Retention is the foundation of SaaS growth. A leaky bucket can't be filled with more acquisition.
> This file defines how we measure retention and what we do when it slips.

---

## Retention Metrics

### Primary metric: Monthly Retention Rate
`MRR retained = (MRR at end of month - new MRR) / MRR at start of month`

| Metric | Current | Target | Alert threshold |
|--------|---------|--------|----------------|
| Monthly retention rate | [X]% | >[X]% | <[X]% |
| Monthly churn rate | [X]% | <[X]% | >[X]% |
| Net Revenue Retention (NRR) | [X]% | >[X]% | <100% |
| Logo churn (customer count) | [X]% | <[X]% | >[X]% |

### Leading indicators (predict churn before it happens)
| Signal | Definition | Action threshold |
|--------|-----------|-----------------|
| Login frequency drop | User logged in < [X]x in last 14 days | Trigger re-engagement |
| Feature usage drop | Core feature usage down [X]% vs. prior month | Send tips email |
| Support ticket spike | [X]+ tickets in [X] days | Proactive outreach |
| Failed payment | Payment method declined | Dunning sequence |

---

## Churn Reasons (update from exit surveys)

| Reason | % of churns | Fix |
|--------|------------|-----|
| Too expensive | [X]% | Offer downgrade option before cancel |
| Missing feature | [X]% | Capture in roadmap, follow up when shipped |
| Not using it enough | [X]% | Re-activation campaign |
| Found alternative | [X]% | Win-back after 30 days |
| Business closed / project ended | [X]% | Nothing to do |

---

## Retention Playbooks

### Playbook 1 — At-risk user detection
**Trigger:** User shows 2+ leading indicators above threshold
**Action:**
1. Tag user as "at-risk" in CRM / PostHog
2. Send personal-feeling email from founder: "Hey [name], noticed you haven't been around lately..."
3. Offer a 15-min call or async help
4. If no response in 7 days → add to win-back sequence

### Playbook 2 — Failed payment (dunning)
**Trigger:** Stripe webhook `invoice.payment_failed`
**Email sequence:**
- Day 0: "Your payment didn't go through" — update payment link
- Day 3: Reminder + consequences of not updating
- Day 7: Final warning — account will pause
- Day 10: Account paused — reactivation CTA
- Day 30: Win-back offer (discount or bonus)

### Playbook 3 — Cancel intent
**Trigger:** User visits cancellation page
**Action:**
1. Show cancellation survey — capture reason (required before cancel)
2. Based on reason, show targeted save offer:
   - Too expensive → offer downgrade or pause
   - Missing feature → show roadmap / workaround
   - Not using it → offer to help / reset trial
   - Leaving for competitor → show comparison
3. If they still cancel → confirm, send exit email, start win-back sequence

### Playbook 4 — Monthly health check
Run on the 1st of every month:
1. Identify users with no login in last 30 days → re-engagement sequence
2. Identify users who haven't used [core feature] → tips email
3. Identify users near plan limits → upsell email
4. Review cohort retention curves — any month showing accelerated churn?

---

## Expansion Revenue

NRR > 100% means growth even without new customers.

### Upsell triggers
| Trigger | Upsell offer |
|---------|-------------|
| User hits [X]% of plan limit | Upgrade CTA in-app + email |
| Team has [X]+ members | Suggest team plan |
| User uses [advanced feature] 5+ times | Offer plan with full access |

### How to upsell without being annoying
- In-app: show upgrade prompt at the moment of hitting a limit (not randomly)
- Email: send once per trigger, not repeatedly
- Never interrupt their workflow — show the prompt after they complete an action

---

## Retention Reviews

### Monthly (internal)
- Churn rate vs. target
- Cohort analysis: are newer cohorts retaining better than older ones?
- Top churn reasons from exit surveys
- At-risk user count and actions taken

### Quarterly
- Full NRR calculation
- Feature usage vs. retention correlation (which features predict staying?)
- Price sensitivity analysis — is pricing driving churn?
