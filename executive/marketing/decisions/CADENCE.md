# CADENCE

> When the agent runs and what it does each time.
> The cron scheduler triggers these tasks. Each run, the agent checks this file first.

---

## Cron Schedule

| Frequency | Cron Expression | Task |
|-----------|----------------|------|
| Daily | `0 8 * * *` | DAILY run (8am) |
| Weekly | `0 9 * * 1` | WEEKLY run (Monday 9am) |
| Monthly | `0 9 1 * *` | MONTHLY run (1st of month, 9am) |

All times are in `[YOUR TIMEZONE — e.g. America/New_York]`.

---

## DAILY Run

**Estimated duration:** 15–30 minutes

### 1. Check system state
- Read STATE/LOG.md → verify nothing is broken or pending from yesterday
- Read BUDGET.md → verify we're within daily spend limits

### 2. Paid ads health check
- Pull Meta Ads metrics (spend, impressions, CTR, CPA, ROAS) for last 24h
- Pull Google Ads metrics for last 24h
- Compare against THRESHOLDS.md
- Execute actions required by thresholds (pause, scale, alert)
- Log results in STATE/LOG.md

### 3. Content publishing
- Check Publer queue — is it populated for the next 48 hours?
- If gaps exist: generate content following PLAYBOOKS/CONTENT.md
- Schedule missing posts via Publer API

### 4. Engagement scan (if applicable)
- Check for comments needing responses on scheduled posts
- Flag any negative comments for human review via Telegram

### 5. Log and close
- Write daily summary to STATE/LOG.md
- Send Telegram summary only if something requires attention

---

## WEEKLY Run (Monday)

**Estimated duration:** 45–90 minutes

### 1. Performance review — Paid Ads
- Pull 7-day data: Meta Ads + Google Ads
- Compare CTR, CPA, ROAS vs. targets in GOALS.md
- Apply KILL_CRITERIA.md to underperforming campaigns
- Scale winning campaigns per BUDGET.md rules
- Create new creative if any ad set has been running the same creative 14+ days

### 2. Performance review — Organic
- Pull Publer analytics: top posts by reach + engagement this week
- Update COMMUNICATION.md with what worked/didn't
- Add winning format to WINS.md if it significantly outperformed

### 3. Performance review — Email
- Pull Resend metrics: open rates, click rates, unsubscribes for the week
- Flag any sequence with open rate < 20% for copy review
- Check list growth

### 4. Content planning for the coming week
- Plan content themes for next 7 days (follow pillars from COMMUNICATION.md)
- Generate and schedule content for all platforms via Publer
- Ensure content mix matches ratios in CHANNELS.md

### 5. SEO check
- Pull Google Search Console: impressions, clicks, average position
- Note any significant movers (up or down)
- If any page dropped significantly: flag for content update

### 6. Competitor scan
- Check Meta Ad Library for competitor new ads
- Note any new messaging angles in COMPETITORS.md

### 7. Telegram weekly report
Send weekly performance summary via Telegram:
- Ad spend vs. budget
- Best performing ad / organic post
- Metrics vs. goals
- Actions taken this week
- Anything requiring human attention

---

## MONTHLY Run (1st of month)

**Estimated duration:** 2–3 hours

### 1. Full performance report
- All channels: GA4, Meta Ads, Google Ads, Publer, Resend, Search Console
- Compare vs. GOALS.md targets
- Calculate actual vs. planned budget spend

### 2. Creative refresh
- Archive all creatives running 30+ days
- Plan and generate fresh creative batch for the new month
- Update DESIGN_SYSTEM.md if any visual patterns performed notably

### 3. Experiment review
- Conclude any experiment running 30+ days
- Document result in EXPERIMENTS.md
- Implement winner and launch next experiment from backlog

### 4. Competitor update
- Review COMPETITORS.md and update pricing/positioning if changed
- Check their website and ad library for new angles

### 5. Goals review
- Compare results vs. GOALS.md
- Flag if behind — suggest budget or strategy adjustment via Telegram
- Update baseline metrics in GOALS.md for new month

### 6. State cleanup
- Archive last month's LOG.md entries to `state/archive/YYYY-MM.md`
- Clean up old experiments from EXPERIMENTS.md
- Consolidate WINS.md and LOSSES.md learnings

### 7. Telegram monthly report
Send full monthly report including:
- MRR impact summary
- Full channel breakdown
- Budget utilization
- What worked / what didn't
- Recommendations for next month
- Any decisions requiring human approval
