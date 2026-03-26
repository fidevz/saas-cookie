# EXPERIMENTS

> A/B tests and hypotheses the agent is actively running or has run.
> The agent updates this file after every experiment concludes.

---

## Active Experiments

### EXP-001 — [Name]
- **Hypothesis:** If we [change X], then [metric Y] will improve because [reason]
- **What we're testing:** [Description — e.g. two different ad headlines]
- **Control:** [What the current version is]
- **Variant:** [What we're testing against it]
- **Platform:** [Meta Ads / Google Ads / Email / Organic]
- **Start date:** [YYYY-MM-DD]
- **End date:** [YYYY-MM-DD] (minimum 7 days for ads, 14 for email)
- **Success metric:** [Primary metric to declare a winner]
- **Minimum detectable effect:** [e.g. 15% improvement in CTR]
- **Status:** Running

---

## Completed Experiments

### EXP-000 — Example Template
- **Hypothesis:** —
- **Result:** [Winner / No winner / Inconclusive]
- **Winner:** [Control / Variant]
- **Impact:** [Metric before vs. after]
- **Decision:** [What we changed as a result]
- **Learnings:** [What this tells us about our audience]
- **Date concluded:** [YYYY-MM-DD]

---

## Experiment Backlog (ideas to test next)

| Idea | Category | Expected impact | Priority |
|------|----------|----------------|----------|
| [Test idea 1] | [Ads/Email/Organic] | [High/Medium/Low] | [1/2/3] |
| [Test idea 2] | [Ads/Email/Organic] | [High/Medium/Low] | [1/2/3] |
| [Test idea 3] | [Ads/Email/Organic] | [High/Medium/Low] | [1/2/3] |

---

## Experiment Rules

1. **One variable at a time.** Never test multiple changes simultaneously in a single experiment.
2. **Minimum sample size:** 1,000 impressions or 100 clicks before declaring a winner for ads. 500 sends for email.
3. **Minimum duration:** 7 days for ads, 14 days for email (to account for day-of-week variance).
4. **Statistical significance:** Only declare a winner at 90%+ confidence.
5. **Document everything:** Even failed experiments teach us something. Always write learnings.
6. **One active experiment per channel** at a time to avoid interference.
