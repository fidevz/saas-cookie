// Locale configuration (without i18n routing — no [locale] folder in app/)
// See: https://next-intl.dev/docs/getting-started/app-router/without-i18n-routing
export const locales = ["en", "es"] as const;
export const defaultLocale = "en" as const;
export type Locale = (typeof locales)[number];
