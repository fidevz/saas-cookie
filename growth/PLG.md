# PRODUCT-LED GROWTH (PLG)

> PLG means the product itself drives acquisition, conversion, and expansion.
> Users experience value before paying. The product markets itself.

---

## PLG Motion

**Our primary motion:** [Free Trial / Freemium / Free Tier + Paid upgrade]

**How the product sells itself:**
[Describe the natural viral or self-serve mechanism — e.g. "Users share outputs that contain our branding", "Inviting teammates brings new users", "Published work is publicly indexable"]

---

## Viral Loops

### Loop 1 — [Name, e.g. Collaboration invite]
```
User gets value → invites teammate → teammate signs up → teammate gets value → invites another...
```
- **Trigger:** [What prompts the share/invite?]
- **Incentive:** [Why would they invite? Intrinsic value / reward / social proof]
- **Friction to remove:** [What makes this loop slow or leaky?]
- **Viral coefficient target:** K > [X] (K > 1 = exponential growth)

### Loop 2 — [Name, e.g. Public output / branding]
```
User publishes output → viewer sees our brand → viewer signs up...
```
- **Trigger:** [When does sharing happen?]
- **Where our brand appears:** [e.g. footer, watermark, "Made with X"]
- **CTA to new viewer:** [What do they see and what action do we want?]

---

## Referral Program

### Structure
- **Who can refer:** [All users / paid users only]
- **Reward for referrer:** [e.g. 1 month free, $X credit, upgrade for X days]
- **Reward for referred:** [e.g. extended trial, discount on first month]
- **Payout trigger:** [When referred user pays for X months]

### Rules
- Referrals tracked via unique referral link (UTM + DB attribution)
- Self-referral detection: same payment method or IP → disqualified
- Reward applied automatically via Stripe credit or plan extension

### Metrics to track
- Referral signup rate: % of new signups from referral links
- Referral conversion rate: % of referred users who become paid
- Referral CAC: reward cost / converted customers
- Top referrers: identify and nurture them (potential affiliates)

---

## Free → Paid Conversion Levers

### In-product paywalls
Position limits strategically — users should hit them after experiencing value, not before.

| Feature / Limit | Free tier | Paid tier | Paywall message |
|----------------|-----------|-----------|----------------|
| [Feature 1] | [limit] | Unlimited | "[Benefit] — upgrade to unlock" |
| [Feature 2] | [limit] | Unlimited | "[Benefit] — upgrade to unlock" |
| [Feature 3] | Locked | Included | "[Feature] is a paid feature" |

### Upgrade prompt rules
- Show prompt at moment of hitting limit (not on a timer)
- Always show the benefit of upgrading, not just "you hit the limit"
- Include social proof: "Join [X] teams who upgraded for this"
- One-click path to upgrade — never make them search for pricing

### Trial optimization
- Trial length: [X] days — long enough to see value, short enough to create urgency
- Show countdown in-app from day [X] of trial (not from day 1 — creates anxiety too early)
- Day before trial ends: in-app banner + email
- Trial end: don't immediately kill access — give [X] day grace period

---

## Product Analytics Setup

Track these events in PostHog for PLG insights:

### Acquisition
- `user_registered` — source, channel, referral
- `trial_started`

### Activation
- `[aha_moment_event]` — the Aha Moment (see ONBOARDING.md)
- `feature_[name]_first_use` — first use of each core feature

### Engagement
- `session_started` — daily/weekly active user tracking
- `feature_[name]_used` — feature adoption rates

### Monetization
- `upgrade_prompt_shown` — how often paywalls appear
- `upgrade_prompt_clicked` — paywall CTR
- `subscription_started` — conversion
- `subscription_cancelled` — churn

### Virality
- `invite_sent` — referral/team invites
- `invite_accepted` — successful viral spread
- `referral_link_shared`

---

## Growth Experiments Backlog

| Experiment | Hypothesis | Metric | Priority |
|-----------|-----------|--------|----------|
| [idea] | If we [X] then [Y] because [Z] | [metric] | High/Med/Low |
| [idea] | If we [X] then [Y] because [Z] | [metric] | High/Med/Low |

Log results in `marketing/strategy/EXPERIMENTS.md` when run.
