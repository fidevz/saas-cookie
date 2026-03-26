# DESIGN SYSTEM

> This file tells the agent exactly how to generate visual content — ads, social posts, thumbnails — to maintain brand consistency across all channels.

---

## Colors

### Primary Palette
| Name | HEX | RGB | Usage |
|------|-----|-----|-------|
| Primary | `#[HEX]` | rgb([R],[G],[B]) | CTAs, key elements |
| Secondary | `#[HEX]` | rgb([R],[G],[B]) | Accents, highlights |
| Background | `#[HEX]` | rgb([R],[G],[B]) | Main backgrounds |
| Surface | `#[HEX]` | rgb([R],[G],[B]) | Cards, containers |

### Text Colors
| Name | HEX | Usage |
|------|-----|-------|
| Primary text | `#[HEX]` | Headlines, body |
| Secondary text | `#[HEX]` | Subtitles, captions |
| On dark | `#[HEX]` | Text over dark backgrounds |

### Do Not Use
- [Color 1] — [reason]
- [Color 2] — [reason]

---

## Typography

### Fonts
- **Headlines:** [Font name] — Weight: [Bold/Black] — Size range: [32px–72px]
- **Body:** [Font name] — Weight: [Regular/Medium] — Size range: [14px–18px]
- **Captions / Labels:** [Font name] — Weight: [Light/Regular] — Size range: [11px–13px]

### Text Rules for Visuals
- Maximum characters in a headline: [e.g. 60]
- Maximum words on a single image: [e.g. 12]
- Text must always pass contrast ratio [4.5:1 minimum for accessibility]

---

## Visual Style

### Overall Aesthetic
[Describe the visual style in 2-3 sentences. E.g. "Clean and minimal with bold typography. We use real photography over illustrations. Dark mode preferred."]

### Photography / Imagery
- Style: [e.g. authentic lifestyle, studio product, flat lay, UGC-style]
- Subjects: [e.g. people at work, product screenshots, abstract concepts]
- Avoid: [e.g. stock photo clichés, staged corporate photos, generic handshakes]

### Illustration / Icons
- Style: [e.g. line icons, filled, isometric, none]
- Library: [e.g. custom, Feather Icons, Heroicons]

### Logos & Watermarks
- Logo position on content: [Bottom right / Bottom left / Top right]
- Minimum logo size: [e.g. 80px wide]
- Clear space around logo: [e.g. 16px all sides]
- Logo on dark backgrounds: [use white version / color version]

---

## Ad Creative Specifications

### Meta Ads
| Format | Size | Aspect Ratio | Text limit |
|--------|------|--------------|------------|
| Feed image | 1080×1080px | 1:1 | 20% rule |
| Feed video | 1080×1350px | 4:5 | — |
| Story / Reel | 1080×1920px | 9:16 | — |

### TikTok Ads
| Format | Size | Duration | Notes |
|--------|------|----------|-------|
| In-Feed Video | 1080×1920px | 15–60s | 9:16 required, captions mandatory |
| TopView | 1080×1920px | 5–60s | Premium placement, use for launches |

### Reddit Ads
| Format | Size | Notes |
|--------|------|-------|
| Promoted Post (image) | 1200×628px or 1:1 | 16:9 or square |
| Promoted Post (video) | 1920×1080px | 16:9, 15–60s |

### Pinterest Ads
| Format | Size | Notes |
|--------|------|-------|
| Standard Pin | 1000×1500px | 2:3 — takes most screen space |
| Video Pin | 1000×1500px | 2:3, 6–15s recommended |
| Carousel Pin | 1000×1500px per card | 2–5 cards |

### Google Display
| Format | Size |
|--------|------|
| Leaderboard | 728×90px |
| Medium rectangle | 300×250px |
| Large rectangle | 336×280px |

---

## Image Generation Prompts (for Ideogram / DALL-E)

### Base prompt style for social content:
```
[Brand aesthetic description], [color palette], [subject], professional marketing image,
[platform format], no text overlay, high quality, [style keywords]
```

### Base prompt style for ad creatives:
```
[Product/service visual], clean background [primary color hex], minimal,
modern, professional, suitable for digital advertising, [aspect ratio]
```

### Keywords to always include:
[list of style keywords that define the brand visual]

### Keywords to always exclude (negative prompts):
[list of elements to avoid — e.g. watermarks, people with 6 fingers, blurry, dark]
