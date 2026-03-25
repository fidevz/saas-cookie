# NPS & FEEDBACK

> Continuous feedback loops that tell us what to build, fix, and stop doing.

---

## NPS (Net Promoter Score)

### Survey setup
- **Question:** "How likely are you to recommend [Product] to a friend or colleague?" (0–10)
- **Follow-up:** "What's the main reason for your score?" (open text)
- **When to send:** After [X] days of active use (not too early — they need to have experienced value)
- **Frequency:** Every [X] months per user (don't over-survey)
- **Channel:** In-app modal + email fallback

### Scoring
- **Promoters** (9–10): Happy customers — ask for reviews, referrals
- **Passives** (7–8): Satisfied but not enthusiastic — identify what would make them a 9
- **Detractors** (0–6): At-risk — immediate follow-up to understand and fix

**NPS = % Promoters − % Detractors**

| Score | Interpretation |
|-------|---------------|
| > 50 | Excellent |
| 30–50 | Good |
| 0–30 | Needs improvement |
| < 0 | Critical |

### Response playbook

**Promoters (9–10):**
1. Thank them personally
2. Ask for a G2 / Capterra / Product Hunt review
3. Ask if they'd be a case study or testimonial
4. Invite to referral program

**Passives (7–8):**
1. Ask: "What would make this a 10 for you?"
2. Log their answer in product feedback tracker
3. Follow up if/when that feature ships

**Detractors (0–6):**
1. Personal reply within 24 hours
2. Understand root cause — ask clarifying questions
3. Escalate to founder/CS if churning or high-value account
4. Log issue and track resolution
5. Follow up after fix is deployed

---

## Other Feedback Channels

### In-product feedback widget
- Always-visible "Share feedback" button
- Freeform text + optional category (bug / idea / other)
- Goes to [Notion / Linear / email — choose one]

### Exit survey (on cancellation)
Required before cancellation completes. Options:
- [ ] Too expensive
- [ ] Missing a feature I need
- [ ] Not using it enough
- [ ] Switching to a competitor → which one?
- [ ] Technical issues
- [ ] Other (open text)

Data from this feeds directly into `marketing/state/LOSSES.md` and product roadmap.

### Customer interviews
- Schedule [X] user interviews per month
- Mix of: new users (activation friction), power users (what they love), churned users (why they left)
- Record with permission, extract insights to product decisions

---

## Feedback → Action Loop

1. **Collect** — NPS, exit surveys, support tickets, interviews
2. **Categorize** — tag by theme: UX, performance, missing feature, pricing, etc.
3. **Prioritize** — frequency × impact × strategic alignment
4. **Build** — add to roadmap if threshold of requests met
5. **Close the loop** — notify users who requested the feature when it ships

**Close the loop template:**
> "Hey [name], you mentioned [X] a while back. We just shipped it. Here's how to use it: [link]. Thanks for the feedback — it shaped this directly."

---

## Review Sites

Proactively collect reviews on:
- **G2** — most important for B2B SaaS
- **Capterra** — strong for SMB buyers
- **Product Hunt** — for launches and visibility
- **Trustpilot** — consumer trust signal
- **App Store / Play Store** — if mobile app exists

**When to ask for a review:** right after an NPS Promoter response, or after a successful support resolution (customer is happy in that moment).
