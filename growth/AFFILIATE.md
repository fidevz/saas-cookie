# AFFILIATE PROGRAM

> Affiliates are different from referrals. Referrals are users sharing with friends.
> Affiliates are partners (creators, agencies, consultants) who promote you for a recurring commission.
> A well-run affiliate program can generate 20–30% of MRR with near-zero CAC.

---

## Program Structure

### Commission model
- **Type:** Recurring (not one-time) — this is the highest-converting offer for affiliates
- **Rate:** [X]% of MRR per referred customer, for [X] months / lifetime
- **Minimum payout:** $[X] (to avoid micro-payments)
- **Payout frequency:** Monthly, on the [X]th
- **Payout method:** PayPal / Wise / Stripe (choose one)
- **Cookie duration:** [90] days — if someone clicks their link and buys within 90 days, affiliate gets credit

### Who can be an affiliate
- Content creators in our niche
- Agencies and consultants who serve our ICP
- Newsletter authors
- Course creators
- Power users with an audience

### Who cannot be an affiliate
- Employees or contractors of [COMPANY]
- Users who refer themselves
- Anyone using paid ads to promote their affiliate link (conflicts with our own ads)

---

## Tracking & Attribution

### How it works
1. Affiliate gets a unique link: `yourdomain.com?ref=affiliateslug`
2. Visitor clicks → cookie set for [90] days
3. Visitor signs up → referral attributed to affiliate
4. Visitor pays → commission recorded
5. Payout triggered after [30]-day refund window passes

### Technical implementation options
- **[Rewardful](https://rewardful.com)** — best Stripe-native affiliate tracking, $49/mo
- **[Tapfiliate](https://tapfiliate.com)** — more flexible, $89/mo
- **[PartnerStack](https://partnerstack.com)** — enterprise, good for agency networks
- **Custom:** track via UTM params stored in DB on signup, reconcile with Stripe MRR

### UTM tracking (minimum viable)
If not using a dedicated tool, use UTMs:
```
yourdomain.com?utm_source=affiliate&utm_medium=referral&utm_campaign=affiliateslug
```
Store `utm_campaign` on User model at signup. Attribute MRR manually monthly.

---

## Recruiting Affiliates

### Who to target
- Look for creators with [X,000]+ followers in [niche]
- Check who is already talking about the problem we solve
- Find consultants/agencies who serve our ICP — they're the highest quality affiliates
- Check competitor affiliate programs for overlap

### Outreach template
```
Subject: Partnership opportunity — earn [X]% recurring on every customer you refer

Hi [Name],

I've been following your content on [platform] — [specific genuine compliment].

We built [PRODUCT] for [ICP description]. Your audience of [their audience description] is a natural fit.

Our affiliate program pays [X]% recurring commission for every customer you refer. With our average customer paying $[X]/month, that's $[X] per referral per month, recurring.

We'd love to have you in the program. Here's the signup: [link]

Happy to answer any questions.

[Name]
[COMPANY]
```

### Where to post the program
- Affiliate directories: ShareASale, Impact, PartnerStack marketplace
- Your own website: `/affiliates` landing page
- Email to power users: "Earn money recommending us"
- Mention in app for power users (segment by usage)

---

## Affiliate Portal

Affiliates need a dashboard where they can:
- Get their unique link
- See clicks, signups, and conversions
- See earnings and payout history
- Download promotional materials (banners, copy)

**Self-hosted options:** Rewardful and Tapfiliate both provide affiliate-facing dashboards.

---

## Marketing Materials for Affiliates

Provide affiliates with:
- [ ] 3-5 banner sizes (use DESIGN_SYSTEM.md specs)
- [ ] Pre-written email copy (use COMMUNICATION.md hooks)
- [ ] Social media caption templates
- [ ] A brief product demo video they can share
- [ ] Key stats and social proof they can cite

Store these in a shared folder (Notion, Google Drive) and link from their affiliate dashboard.

---

## Compliance

- Affiliates must disclose their relationship per FTC guidelines (US) and equivalent in other regions
- Include in affiliate agreement: no trademark bidding, no misleading claims, disclosure required
- Provide affiliates with a template disclosure: *"Disclosure: I may earn a commission if you sign up through my link, at no extra cost to you."*

---

## Performance Metrics

| Metric | Target | Review cadence |
|--------|--------|---------------|
| Active affiliates | [X] | Monthly |
| Affiliate-attributed MRR | [X]% of total MRR | Monthly |
| Average commission per affiliate | $[X]/month | Monthly |
| Top affiliate MRR contribution | — | Monthly |
| Affiliate application → approval rate | [X]% | Quarterly |

---

## Monthly Affiliate Tasks

1. Process payouts for previous month's commissions
2. Email affiliates with: their stats, new materials, product updates they can share
3. Recruit [X] new potential affiliates
4. Review fraud: any suspicious click patterns or self-referrals?
5. Recognize top affiliate publicly (newsletter, social) — builds loyalty
