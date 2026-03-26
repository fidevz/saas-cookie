# ESCALATION

> Defines what the agent can do alone vs. what requires human approval.
> When in doubt, escalate. Never assume when money or reputation is at stake.

---

## Autonomy Levels

### 🟢 Fully Autonomous (no notification needed)
The agent executes without asking:

- Pause an ad that meets KILL_CRITERIA.md
- Generate and publish organic content (following BRAND.md + DESIGN_SYSTEM.md)
- Schedule posts via Publer
- Send automated email sequences (pre-approved sequences only)
- Reduce a campaign budget by up to 30%
- Generate image assets via Ideogram API
- Update STATE/LOG.md, WINS.md, LOSSES.md
- Run routine SEO checks and reports
- Refresh creatives within existing approved campaigns

---

### 🟡 Execute + Notify (do it, then tell me)
The agent executes immediately but sends a Telegram message:

- Pause any campaign (not just individual ads)
- Scale a campaign budget up by 10–20%
- Kill an audience/ad set that spent > $[X]
- Post is boosted (organic → paid)
- Email sequence paused due to poor metrics
- Any threshold breach from THRESHOLDS.md

**Telegram message format:**
```
🟡 [ACTION TAKEN]
Campaign: [name]
Reason: [threshold or criteria]
Impact: [what changed]
Metrics: [relevant numbers]
No action needed unless you disagree.
```

---

### 🔴 Ask Before Acting (hard stop — wait for approval)
The agent STOPS and sends a Telegram message, then waits:

- Increase total monthly budget
- Launch a brand new campaign type (not previously approved)
- Scale any campaign by more than 20% at once
- Spend on any tool not in the approved stack
- Respond to public negative feedback or controversy
- Post content that deviates from established messaging (new claims, new positioning)
- Send any email outside of pre-approved sequences to the full list
- Reactivate a campaign that was manually paused by the human
- Any action with spend implications > $[X] not covered by existing rules

**Telegram message format:**
```
🔴 APPROVAL NEEDED — [ACTION REQUESTED]
What I want to do: [description]
Why: [reason / opportunity]
Expected impact: [what we gain]
Cost / risk: [spend or downside]

Reply:
✅ Approved
❌ Rejected
Or: [alternative instructions]
```

---

## Crisis Escalation

If ANY of these occur, stop all marketing activity and alert immediately:

- A post receives significant viral negative attention
- An ad is flagged by Meta/Google for policy violation
- Account is suspended or restricted on any platform
- A data or privacy issue is reported
- Budget overrun detected (actual spend > limit)
- An automated action causes an unintended consequence

**Telegram message format:**
```
🚨 CRISIS ALERT — IMMEDIATE ATTENTION REQUIRED
Situation: [what happened]
Affected: [platforms/campaigns/channels]
Actions taken so far: [what the agent did]
Status: ALL ACTIVITY PAUSED

Please respond with instructions.
```

---

## Telegram Notification Setup

- **Bot:** [Telegram Bot username]
- **Chat ID:** [Chat ID to send messages to]
- **Format:** Always include emoji prefix (🟢/🟡/🔴/🚨) for quick visual scanning
- **Response handling:** Agent checks for human responses to 🔴 requests every [X] minutes before timing out

## Timeout Rules
If agent sends a 🔴 request and receives no response within:
- **4 hours** → send reminder
- **24 hours** → assume rejected, log in STATE/LOG.md, skip the action
