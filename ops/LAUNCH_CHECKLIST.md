# LAUNCH CHECKLIST

> Run through this before going live. Check every box — don't skip.

---

## Product

- [ ] Core user journey works end-to-end: signup → onboarding → aha moment → upgrade
- [ ] Email/password registration works
- [ ] Google OAuth works
- [ ] Password reset flow works
- [ ] Trial signup and conversion to paid works
- [ ] Stripe checkout completes successfully (test mode first, then live)
- [ ] Subscription cancellation works
- [ ] Team invitation works (if FEATURE_TEAMS=True)
- [ ] Real-time notifications work (if FEATURE_NOTIFICATIONS=True)
- [ ] All feature flags configured correctly for launch
- [ ] Mobile-responsive on iOS Safari and Android Chrome

## Content & Legal

- [ ] Landing page is complete with clear value proposition
- [ ] Pricing page is accurate with current plan details
- [ ] Privacy Policy published and linked in footer
- [ ] Terms of Service published and linked in footer
- [ ] Cookie Policy published and cookie consent banner working
- [ ] Legal pages linked from signup flow
- [ ] All placeholder content (`[PLACEHOLDER]`) replaced
- [ ] No lorem ipsum anywhere in the product

## Infrastructure & Security

- [ ] Production environment fully configured (see `ops/DEPLOYMENT.md`)
- [ ] `DEBUG=False` in production
- [ ] All secrets in environment variables (not in code)
- [ ] SSL/TLS active on all domains including wildcard
- [ ] CORS locked to production domains only
- [ ] Admin URL changed from default
- [ ] Rate limiting active and tested
- [ ] Uptime monitoring configured (UptimeRobot / Better Uptime / etc.)
- [ ] Sentry configured and receiving events
- [ ] Database backups configured and tested (restore at least once)

## Payments

- [ ] Stripe live keys configured (not test)
- [ ] Stripe webhook endpoint registered for production domain
- [ ] Webhook events configured: `customer.subscription.*`, `invoice.*`, `checkout.session.completed`
- [ ] Test a real payment with a real card
- [ ] Refund flow works in Stripe dashboard
- [ ] Failed payment dunning emails configured

## Email

- [ ] Resend domain verified (DNS records added)
- [ ] From email is a real, monitored inbox
- [ ] Welcome email sends correctly
- [ ] Password reset email sends correctly
- [ ] All email templates reviewed for formatting on mobile
- [ ] Unsubscribe link works in all marketing emails
- [ ] SPF, DKIM, DMARC records configured for your domain

## Analytics & Tracking

- [ ] Google Analytics 4 connected and receiving events
- [ ] PostHog configured (if using)
- [ ] Stripe revenue visible in dashboard
- [ ] Key events tracked: signup, trial_start, subscription_start, subscription_cancel

## Marketing

- [ ] Marketing folder (`marketing/`) fully configured with product details
- [ ] `marketing/context/PRODUCT.md` — complete
- [ ] `marketing/context/AUDIENCE.md` — at least 1 ICP defined
- [ ] `marketing/strategy/BUDGET.md` — real numbers set
- [ ] `marketing/decisions/THRESHOLDS.md` — all `[X]` values filled
- [ ] `marketing/decisions/ESCALATION.md` — Telegram bot configured
- [ ] Publer account connected to all social channels
- [ ] Meta Ads account connected and pixel installed
- [ ] Google Ads account connected and tag installed
- [ ] First content batch scheduled in Publer

## Support

- [ ] Support email configured and monitored
- [ ] Support page live (or at minimum, contact email visible)
- [ ] FAQ draft ready
- [ ] `support/FAQ.md` completed with common questions
- [ ] Team knows how to handle first support requests

## Growth

- [ ] `growth/ONBOARDING.md` — Aha Moment defined
- [ ] In-product onboarding checklist implemented
- [ ] Email welcome sequence active in Resend
- [ ] NPS survey configured to send at day [X]
- [ ] At least one review site profile claimed (G2 or Product Hunt)

---

## Launch Day

- [ ] Announce on all owned channels (social, email list)
- [ ] Product Hunt launch (if planned)
- [ ] Monitor Sentry for new errors in real-time for first 2 hours
- [ ] Watch Stripe for first payments
- [ ] Be available for support responses within 1 hour
- [ ] Capture feedback from first users immediately

---

## Post-Launch (first 48h)

- [ ] Review activation funnel — where are users dropping off?
- [ ] Respond to all support tickets personally
- [ ] Fix any P0/P1 bugs discovered
- [ ] Send follow-up email to first users asking for feedback
- [ ] Write down what surprised you (good and bad)
