# BUDGET

> This file defines the financial limits the agent must NEVER exceed without human approval.
> These are hard constraints, not guidelines.

---

## Monthly Budget Ceiling

| Category | Monthly Limit | Notes |
|----------|--------------|-------|
| **Total marketing spend** | $[X]/month | Absolute ceiling |
| Meta Ads | $[X]/month | |
| Google Ads | $[X]/month | |
| Tools & subscriptions | $[X]/month | Publer, Ideogram, DataForSEO, etc. |
| Content creation | $[X]/month | Image generation API costs |
| Email | $[X]/month | Resend costs |

---

## Daily Limits (Paid Ads)

| Platform | Daily Budget | Max single campaign budget |
|----------|-------------|--------------------------|
| Meta Ads | $[X]/day | $[X]/campaign/day |
| Google Ads | $[X]/day | $[X]/campaign/day |

**Rule:** If the agent detects daily spend is approaching 90% of daily limit before 6pm local time, pause lowest-performing campaigns immediately.

---

## Autonomous Spending Authority

The agent can autonomously:
- ✅ Allocate budget between campaigns within approved totals
- ✅ Scale a winning campaign up by **maximum 20%** per week
- ✅ Pause campaigns that violate KILL_CRITERIA.md
- ✅ Spend on image generation (Ideogram API) up to $[X]/month

The agent must notify via Telegram and wait for approval to:
- ❌ Increase total monthly budget
- ❌ Launch a new campaign type not previously approved
- ❌ Scale any campaign by more than 20% in a single action
- ❌ Spend on any new tool not in the approved stack

---

## Budget Allocation Logic

### When ROAS > [X]x on a campaign:
→ Scale budget by 10–20%, notify via Telegram

### When ROAS < [X]x for 3+ consecutive days:
→ Reduce budget by 30%, flag in LOG.md

### When CPA > [X]x target for 5+ days:
→ Pause campaign, notify via Telegram, await approval

---

## Emergency Stop
If total monthly spend reaches **95% of ceiling** before month end:
1. Pause ALL paid campaigns immediately
2. Send Telegram alert with spend summary
3. Do not resume until human approves new budget or month resets

---

## Budget Review Cadence
- **Weekly:** Agent reports spend vs. budget in Telegram message
- **Monthly:** Agent generates full budget report and sends via Telegram

---

## Tool Costs (fixed monthly, for tracking)
| Tool | Cost | Billed |
|------|------|--------|
| Publer Business | $21/mo | Monthly |
| Ideogram API | ~$[X]/mo | Usage |
| DataForSEO API | ~$[X]/mo | Usage |
| Resend | ~$[X]/mo | Usage |
| Google Analytics | $0 | — |
| Meta Ads API | $0 | — |
| Google Ads API | $0 | — |

**Total fixed tool cost:** $[X]/month
