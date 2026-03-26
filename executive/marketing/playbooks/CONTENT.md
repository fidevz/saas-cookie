# PLAYBOOK: CONTENT CREATION & PUBLISHING

> Step-by-step process the agent follows to generate and publish organic content.

---

## Content Calendar Logic

The agent generates content based on:
1. **Pillar rotation** — cycle through message pillars from COMMUNICATION.md
2. **Funnel balance** — maintain ToFu/MoFu/BoFu ratio from CHANNELS.md
3. **Trending opportunities** — if a topic is trending and relevant, prioritize it
4. **Experiment assignments** — if an experiment is active, follow its content spec

---

## Step-by-Step: Creating a Post

### Step 1 — Select content angle
- Read STATE/LOG.md → check what was published in the last 7 days
- Choose a pillar not overused recently
- Read AUDIENCE.md → confirm the angle is relevant to current ICP
- Read COMMUNICATION.md → select or remix a proven hook

### Step 2 — Write the copy
- Apply tone and writing rules from BRAND.md
- Structure: Hook → Body → CTA
- Max caption length by platform:
  - Instagram: 2,200 chars (aim for 150–300 for feed, longer for carousels)
  - LinkedIn: 3,000 chars (aim for 1,000–1,500 for good reach)
  - X/Twitter: 280 chars (or thread format for longer content)
  - Facebook: no hard limit (aim for 80–250 chars for feed)
  - TikTok: 2,200 chars (caption matters less — focus on video hook)
- Always include relevant hashtags:
  - Instagram: 5–10 targeted hashtags
  - LinkedIn: 3–5 hashtags
  - X: 1–2 hashtags max
  - TikTok: 5–7 hashtags

### Step 3 — Generate visual
- Use Ideogram API with prompt style from DESIGN_SYSTEM.md
- Verify colors match brand palette
- Check logo placement if template requires it
- Generate in correct dimensions for each platform (see DESIGN_SYSTEM.md)

### Step 4 — Quality check (before publishing)
- [ ] Copy aligns with BRAND.md tone rules
- [ ] No claims that violate BRAND.md compliance section
- [ ] Visual matches DESIGN_SYSTEM.md specs
- [ ] CTA is present and links to correct URL
- [ ] No typos or grammar errors
- [ ] Hashtags are relevant, not banned

### Step 5 — Schedule via Publer API
- Use auto-schedule for optimal timing if no specific time required
- Cross-post to all relevant platforms with platform-specific captions
- Tag campaign in Publer for tracking

### Step 6 — Log the action
- Write to STATE/LOG.md: date, content type, platforms, angle used, Publer post ID

---

## Content Types & Formats

### Carousel (Instagram / LinkedIn)
- Slides: 5–10
- Slide 1: Hook (must make them swipe)
- Slides 2–8: Value delivery (one point per slide)
- Last slide: CTA + logo
- Best for: Educational content, lists, step-by-step

### Reel / TikTok / Short Video
- Duration: 15–60 seconds for highest reach
- Hook: First 2 seconds must stop the scroll
- Structure: Hook → Problem → Solution → CTA
- Captions/subtitles: Always (80% of people watch without sound)
- Best for: Tutorials, behind-the-scenes, trending formats

### Static Image
- One clear visual focus
- Minimal text on image (follow Meta 20% rule for ads)
- Best for: Quotes, announcements, product shots

### Text Post (LinkedIn / X)
- Lead with a one-line hook
- Use line breaks every 1–2 sentences
- No images needed if copy is strong
- Best for: Thought leadership, opinions, storytelling

---

## Content Frequency Targets

| Platform | Frequency | Best times (default — update from Publer analytics) |
|----------|-----------|-----------------------------------------------------|
| Instagram feed | 4–5x/week | Tue–Fri, 9–11am & 6–8pm local |
| Instagram Stories | Daily | 8am & 7pm local |
| Instagram Reels | 3x/week | Mon, Wed, Fri |
| LinkedIn | 3x/week | Tue–Thu, 8–10am local |
| X/Twitter | Daily | 9am–12pm local |
| TikTok | 3–5x/week | 7–9pm local |
| Facebook | 3x/week | 1–3pm local |

---

## Repurposing Rules
- A high-performing LinkedIn post → rewrite for X/Twitter thread
- A high-performing Instagram carousel → adapt for LinkedIn
- A blog post → extract 5 social posts
- A Reel that performs well → run as a Meta Ad (see PAID_ADS.md)
