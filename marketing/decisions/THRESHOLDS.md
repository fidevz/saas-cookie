# THRESHOLDS

> Metric-based decision rules. The agent checks these on every DAILY run.
> When a condition is met, the action is executed autonomously — no human needed (unless flagged).

---

## Meta Ads Thresholds

### Ad-Level

| Condition | After | Action | Notify? |
|-----------|-------|--------|---------|
| CTR < [X]% | 1,000 impressions | Pause ad | No |
| CTR < [X]% | 500 impressions AND cost > $[X] | Pause ad | No |
| CPA > [X]x target | 3 days | Reduce ad set budget by 30% | Yes |
| CPA > [X]x target | 5 days | Pause campaign | Yes |
| ROAS > [X]x target | 3 days | Scale budget +15% | Yes |
| Frequency > 4 | — | Flag creative for refresh | Yes |
| Frequency > 6 | — | Pause ad, trigger new creative creation | No |

### Campaign-Level

| Condition | After | Action | Notify? |
|-----------|-------|--------|---------|
| Daily spend < 50% of budget | 3 days | Check delivery, expand audience or bid | Yes |
| Daily spend > 110% of budget | 1 day | Pause until next day, investigate | Yes |
| No conversions | 7 days AND spend > $[X] | Pause campaign | Yes (urgent) |

---

## Google Ads Thresholds

| Condition | After | Action | Notify? |
|-----------|-------|--------|---------|
| CTR < [X]% (search) | 2 weeks | Review and update ad copy | No |
| Quality Score < 5 | — | Review landing page + ad relevance | Yes |
| CPA > [X]x target | 5 days | Reduce bids by 20% | No |
| CPA > [X]x target | 10 days | Pause ad group | Yes |
| Impression share < 30% | — | Increase bids or budget | Yes |
| ROAS > [X]x | 7 days | Increase budget by 20% | Yes |

---

## TikTok Ads Thresholds

| Condition | After | Action | Notify? |
|-----------|-------|--------|---------|
| Video completion rate < 15% | 500 views | Pause ad | No |
| CTR < [X]% | 1,000 impressions | Pause ad | No |
| CPA > [X]x target | 5 days | Pause ad group | Yes |
| ROAS > [X]x target | 3 days | Scale budget +15% | Yes |
| Same creative running > 14 days | — | Flag for refresh | No |

---

## Reddit Ads Thresholds

| Condition | After | Action | Notify? |
|-----------|-------|--------|---------|
| CTR < 0.3% | 10,000 impressions | Pause ad group | No |
| CPA > [X]x target | 7 days | Pause ad group | Yes |
| Negative comment ratio > 30% | — | Flag for human review | Yes |
| ROAS > [X]x target | 5 days | Scale budget +15% | Yes |

---

## Pinterest Ads Thresholds

| Condition | After | Action | Notify? |
|-----------|-------|--------|---------|
| Save rate < 0.5% | 5,000 impressions | Pause Pin | No |
| CTR < [X]% | 10,000 impressions | Pause Pin | No |
| CPA > [X]x target | 10 days | Pause ad group | Yes |
| ROAS > [X]x target | 7 days | Scale budget +15% | Yes |

---

## Organic Content Thresholds

| Condition | Action | Notify? |
|-----------|--------|---------|
| Post gets > [X] engagements in 24h | Boost post with $[X] via Meta Ads | Yes |
| Post gets > [X] engagements in 24h | Add it to WINS.md | No |
| 3 consecutive posts below [X] engagements | Switch content angle/format | No |
| Follower count drops for 7 days straight | Flag for strategy review | Yes |

---

## Email Thresholds

| Condition | Action | Notify? |
|-----------|--------|---------|
| Open rate < 20% (sequence email) | Flag for subject line rewrite | No |
| Open rate < 15% (sequence email) | Pause sequence, notify | Yes |
| Unsubscribe rate > 0.5% (single send) | Pause newsletter, review content | Yes |
| Spam complaint rate > 0.08% | Stop all sends immediately | Yes (urgent) |
| List growth < [X] subscribers/week | Flag acquisition gap | Yes |

---

## Budget Thresholds

| Condition | Action | Notify? |
|-----------|--------|---------|
| Monthly spend reaches 75% of ceiling | Send budget status update | Yes |
| Monthly spend reaches 90% of ceiling | Pause lowest-ROAS campaigns | Yes (urgent) |
| Monthly spend reaches 95% of ceiling | Pause ALL paid campaigns | Yes (urgent) |
| Daily spend > daily limit | Pause all ads for the day | Yes (urgent) |

---

## Website / Analytics Thresholds (from GA4)

| Condition | After | Action | Notify? |
|-----------|-------|--------|---------|
| Trial signups drop > 30% week-over-week | 1 week | Flag — check paid + organic traffic | Yes |
| Bounce rate increases > 20% | 1 week | Flag landing page for review | Yes |
| Conversion rate drops > 15% | 1 week | Flag — check funnel in GA4 | Yes (urgent) |

---

## Threshold Update Rules

- Thresholds should be reviewed monthly (part of MONTHLY run)
- Update targets as performance improves — never leave them static forever
- Any threshold change > 20% must be logged in STATE/LOG.md with reason
- If unsure about a threshold, keep it conservative and tighten over time
