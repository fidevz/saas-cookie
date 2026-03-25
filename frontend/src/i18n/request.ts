import { getRequestConfig } from "next-intl/server";

const LOCALES = ["en", "es"] as const;
type Locale = (typeof LOCALES)[number];

function isValidLocale(locale: string | undefined): locale is Locale {
  return LOCALES.includes(locale as Locale);
}

export default getRequestConfig(async () => {
  // Without i18n routing: locale comes from cookie or defaults to "en"
  // Cookie-based locale switching can be added later
  const locale: Locale = "en";

  return {
    locale,
    messages: (await import(`../../messages/${locale}.json`)).default,
  };
});

export { LOCALES, isValidLocale };
