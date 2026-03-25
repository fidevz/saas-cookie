# KILL CRITERIA

> Clear, unambiguous rules for when to kill an ad, campaign, channel, or sequence.
> No judgment needed — if the criteria is met, kill it.

---

## Kill an Ad (creative)

Kill a specific ad creative if ANY of the following:

- [ ] CTR < [X]% after 1,000 impressions
- [ ] CPA > [X]x the target after 5 days of spend
- [ ] Frequency > 6 (audience is exhausted)
- [ ] The ad has been running > 30 days with no creative refresh
- [ ] Ad contains a factual error, outdated pricing, or wrong link
- [ ] The ad was published violating brand rules (BRAND.md)

**Action when killed:**
1. Pause the ad via Meta Ads API / Google Ads API
2. Document in STATE/LOG.md: ad name, kill date, kill reason, final metrics
3. If it was the only active ad in an ad set → generate replacement creative immediately (CONTENT.md process)

---

## Kill an Ad Set (audience)

Kill an ad set if ALL of the following:

- [ ] Has been running for at least 7 days
- [ ] Spent at least $[X]
- [ ] CPA is > [X]x target OR zero conversions
- [ ] All creative within it has been refreshed at least once

**Action when killed:**
1. Pause the ad set
2. Document audience segment + performance in LOSSES.md
3. Do NOT rebuild the same audience — document why it failed first
4. Notify via Telegram if budget spent was > $[X]

---

## Kill a Campaign

Kill a campaign if:

- [ ] ALL ad sets within it have been killed, OR
- [ ] The campaign objective has been achieved and no longer needed, OR
- [ ] Monthly budget ceiling forces prioritization and this is lowest ROAS campaign, OR
- [ ] Campaign has spent > $[X] with zero conversions

**Action when killed:**
1. Pause campaign
2. Document in STATE/LOG.md + LOSSES.md
3. Send Telegram notification with spend summary and reason

---

## Kill an Email Sequence

Kill (pause) an email sequence if:

- [ ] Spam complaint rate > 0.1% on any email in the sequence
- [ ] Unsubscribe rate > 1% on any email in the sequence
- [ ] Open rate < 10% on the first email of the sequence for 30+ days
- [ ] The sequence is based on outdated product information

**Action when killed:**
1. Pause sequence in Resend
2. Notify via Telegram
3. Flag for human review — sequence needs rewrite before reactivating

---

## Kill a Channel (organic)

Pause all activity on an organic channel if:

- [ ] Platform has API issues blocking publishing for 7+ days (wait for fix)
- [ ] Account is flagged or restricted by the platform
- [ ] Channel shows 0 engagement growth for 60+ consecutive days despite content variations

**Action when paused:**
1. Document in STATE/LOG.md
2. Notify via Telegram with metrics summary
3. Do NOT delete content or account — await human decision

---

## Recovery Protocol

After killing any campaign/ad:

1. **Document the failure** → LOSSES.md (what metrics, what we learned)
2. **Wait 24h** before launching a replacement (unless urgent)
3. **Change at least one variable** in the replacement (audience, creative, copy angle, or offer)
4. **Set a tighter monitoring window** for the replacement — review at 48h instead of standard 3 days
