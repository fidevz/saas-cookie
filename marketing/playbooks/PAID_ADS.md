# PLAYBOOK: PAID ADVERTISING

> How the agent manages Meta Ads and Google Ads — from campaign creation to optimization.

---

## Campaign Structure

### Meta Ads — Account Structure
```
Campaign (objective)
  └── Ad Set (audience + budget)
        └── Ad (creative + copy)
```

**Naming convention:**
- Campaign: `[OBJECTIVE]-[FUNNEL STAGE]-[DATE]`
  - Example: `CONV-COLD-2025-03`
- Ad Set: `[AUDIENCE TYPE]-[PLATFORM]-[AGE RANGE]`
  - Example: `LOOKALIKE-IG-25-45`
- Ad: `[FORMAT]-[HOOK]-[VERSION]`
  - Example: `VIDEO-PAIN-V1`

### Google Ads — Account Structure
```
Campaign (network + goal)
  └── Ad Group (theme / intent)
        └── Ads (headlines + descriptions)
```

**Naming convention:**
- Campaign: `[NETWORK]-[INTENT]-[DATE]`
  - Example: `SEARCH-BRANDED-2025-03`
- Ad Group: `[KEYWORD THEME]`
  - Example: `COMPETITOR-COMPARISON`

---

## Step-by-Step: Launching a New Campaign

### Step 1 — Define the goal
- What funnel stage? TOFU / MOFU / BOFU
- What action do we want? Trial signup / Demo request / Purchase
- What's the target CPA? (must align with BUDGET.md)

### Step 2 — Define the audience (Meta)
**Cold audiences:**
- Interest targeting based on AUDIENCE.md ICP profile
- Lookalike 1–3% from customer list
- Broad + demographics only (let Meta optimize)

**Warm audiences:**
- Website visitors (last 30 / 60 / 90 days)
- Video viewers (50%+ watch time)
- Instagram engagers (last 30 days)

**Hot audiences:**
- Trial users who didn't convert
- Abandoned checkout / signup
- Past customers (win-back)

### Step 3 — Create the creative
- Follow DESIGN_SYSTEM.md for visuals
- Use hooks from COMMUNICATION.md
- Generate image with Ideogram API
- A/B test minimum 2 creatives per ad set
- Always create platform-native formats (see DESIGN_SYSTEM.md specs)

### Step 4 — Write the ad copy
- Primary text: Hook → Problem → Solution → CTA (max 125 chars visible before "more")
- Headline: Benefit-driven, max 40 chars
- Description: Supporting detail, max 30 chars
- CTA button: "Sign Up" / "Learn More" / "Try Free" — match funnel stage

### Step 5 — Configure campaign settings
- Optimization event: Purchase or Trial Start (never clicks or reach for conversion campaigns)
- Attribution: 7-day click, 1-day view
- Budget: Start at $[X]/day (see BUDGET.md for limits)
- Schedule: Run always (no dayparting until we have data)

### Step 6 — Launch and log
- Record campaign in STATE/LOG.md
- Set reminder to review after 3 days

---

## Optimization Cadence

### Every 3 days (automated check):
- Pull CTR, CPC, CPA per ad
- Kill ads with CTR < [X]% after 1,000 impressions (see THRESHOLDS.md)
- Flag ads with CPA > 1.5x target for review

### Every 7 days (automated review):
- Compare performance by audience, creative, placement
- Scale winning ad sets by 10–20%
- Pause ad sets below threshold
- Launch at least 1 new creative per active campaign

### Every 30 days (monthly review):
- Refresh all creative (avoid ad fatigue)
- Review audience performance and adjust targeting
- Update lookalike sources if customer list has grown
- Report results in Telegram

---

## Creative Rotation Rules
- Rotate creatives every **2–4 weeks** (earlier if frequency > 3)
- Never run fewer than **2 active ads per ad set**
- When adding new creative: launch alongside winner, don't replace until new one proves better
- High-performing organic content → test as ad immediately

---

## Google Ads Specifics

### Search campaigns
- Match types: Start with phrase match, add exact match for top converters
- Negatives: Build negative keyword list from search terms report weekly
- Ad copy: 3 headlines min, 2 descriptions min, use all extensions
- Bid strategy: Target CPA (once 30+ conversions/month) / Manual CPC (early stage)

### Responsive Search Ads
- Write 10–15 headlines (variety of angles: feature, benefit, urgency, brand)
- Write 4 descriptions
- Pin headline 1 only if brand name must appear there
- Review asset performance monthly — remove "Poor" rated assets

---

## TikTok Ads Specifics

### Account Structure
```
Campaign (objective)
  └── Ad Group (audience + placement + budget)
        └── Ad (video creative + copy)
```

**Naming convention:**
- Campaign: `TT-[OBJECTIVE]-[FUNNEL STAGE]-[DATE]` → Example: `TT-CONV-COLD-2025-03`
- Ad Group: `TT-[AUDIENCE TYPE]-[AGE]` → Example: `TT-INTEREST-18-34`
- Ad: `TT-[HOOK TYPE]-[VERSION]` → Example: `TT-PROBLEM-V1`

### Audience Options
- **Interest + behavior targeting** — based on AUDIENCE.md ICP
- **Custom audiences** — website visitors via TikTok Pixel, customer list upload
- **Lookalike audiences** — 1–5% from customer list (minimum 1,000 seed users)
- **Broad** — demographics only, let TikTok algorithm optimize

### Creative Rules (critical — TikTok is different)
- Hook within **first 2 seconds** — no logo intros, no slow builds
- **Native feel wins** — UGC-style and lo-fi outperform polished studio ads
- **Always add captions** — 80% watch without sound
- Video length: **15–34 seconds** for best completion rates
- Use trending audio when relevant (check TikTok Creative Center)
- Text on screen should reinforce, not repeat, the voiceover
- End with a clear CTA on screen + voiceover

### Campaign Settings
- Objective: Website Conversions (install TikTok Pixel first)
- Optimization goal: Complete Payment or Registration
- Bidding: Cost Cap (once data exists) / Lowest Cost (early stage)
- Placement: TikTok only (not Pangle network) until proven
- Attribution: 7-day click, 1-day view

### Optimization
- Review after **48h** — TikTok's learning phase is faster than Meta
- Kill creatives with < 15% video completion rate after 500 views
- Kill ad groups with CPA > [X]x target after 5 days
- Refresh creatives every **2 weeks** minimum (TikTok fatigue is faster than Meta)

---

## Reddit Ads Specifics

### Account Structure
```
Campaign (objective)
  └── Ad Group (targeting + budget)
        └── Ad (format + copy)
```

**Naming convention:**
- Campaign: `RD-[OBJECTIVE]-[DATE]` → Example: `RD-CONV-2025-03`
- Ad Group: `RD-[TARGETING TYPE]-[COMMUNITY]` → Example: `RD-SUBREDDIT-STARTUPS`
- Ad: `RD-[FORMAT]-[ANGLE]-[VERSION]` → Example: `RD-POST-PAIN-V1`

### Audience Options (Reddit's superpower)
- **Subreddit targeting** — most powerful; target communities where ICP lives
  - Research relevant subreddits from AUDIENCE.md ICP profile
  - Examples for SaaS: r/startups, r/entrepreneur, r/SaaS, r/webdev, r/marketing, r/smallbusiness
- **Interest targeting** — broader, less precise than subreddit
- **Keyword targeting** — target users who searched/engaged with specific keywords
- **Custom audiences** — retarget website visitors via Reddit Pixel

### Creative Rules (Reddit tone is everything)
- **Write like a Reddit post, not an ad** — corporate language gets downvoted mentally
- Be direct and honest — Redditors have very high BS detectors
- Lead with value or insight, not a pitch
- Promoted Post format: headline is critical (same weight as a post title)
- Image: simple, informative — meme format can work if relevant to community
- Video: optional — static posts often outperform on Reddit
- **Never use**: buzzwords, "revolutionary", "game-changing", excessive exclamation marks

### Ad Formats
- **Promoted Post (image)** — most common, works like a native post
- **Promoted Post (video)** — 15–60s, use for demos
- **Conversation Ad** — appears within comment threads, very native feel

### Campaign Settings
- Objective: Conversions (install Reddit Pixel)
- Bidding: CPM for awareness / CPC for conversion campaigns
- Daily budget: Start low ($[X]/day) — CPCs are lower than Meta/Google
- Run 24/7 initially — Reddit usage peaks vary by community

### Optimization
- Review after **5 days** (lower volume than Meta, needs more time)
- A/B test subreddit groups — performance varies dramatically by community
- Kill ad groups with CTR < 0.3% after 10,000 impressions
- Monitor comment sentiment — Reddit users comment on ads; respond professionally or escalate per ESCALATION.md

---

## Pinterest Ads Specifics

### Account Structure
```
Campaign (objective)
  └── Ad Group (targeting + budget)
        └── Pin (creative)
```

**Naming convention:**
- Campaign: `PT-[OBJECTIVE]-[DATE]` → Example: `PT-CONV-2025-03`
- Ad Group: `PT-[TARGETING TYPE]` → Example: `PT-KEYWORD-PRODUCTIVITY`
- Ad: `PT-[FORMAT]-[ANGLE]-[VERSION]` → Example: `PT-STANDARD-BENEFIT-V1`

### Audience Options
- **Keyword targeting** — Pinterest has strong search intent; target problem + solution keywords
- **Interest targeting** — broad but useful for awareness
- **Actalike audiences** — Pinterest's lookalike (needs 100+ customer seed)
- **Customer list retargeting** — upload email list

### Creative Rules
- Format: **2:3 vertical (1000×1500px)** — takes more screen space, higher visibility
- Text overlay **works on Pinterest** (unlike Meta) — add benefit headline on image
- Lifestyle imagery performs best — show the outcome, not the product
- Branding: add logo subtly (bottom corner) — Pinterest is a discovery platform, brand recall matters
- Video Pins: 6–15 seconds, loop well, no audio dependency

### Campaign Settings
- Objective: Conversions (install Pinterest Tag)
- Bidding: Automatic bidding initially, then Target CPA
- Budget: Start conservative — Pinterest converts slower than Meta (longer consideration)

### Optimization
- Review after **7 days** — Pinterest has a longer attribution window (30-day click is standard)
- Pinterest attribution: use 30-day click / 1-day engagement
- Kill Pins with save rate < 0.5% after 5,000 impressions
- Winning Pins can stay active for months — Pinterest content has longer shelf life than Meta

---

## Ad Copy Templates

### For TOFU (cold audience):
```
[Attention hook — problem or curiosity]
[Body — why this matters to them]
[Social proof — quick stat or "Join X customers"]
[CTA — free, low risk]
```

### For MOFU (warm audience):
```
[Acknowledge they've seen us — or use benefit lead]
[Specific feature or use case relevant to them]
[Remove objection]
[CTA — trial or demo]
```

### For BOFU (hot audience):
```
[Urgency or personalization]
[Testimonial or result]
[Offer or guarantee]
[Direct CTA]
```
