import { getRequestConfig } from "next-intl/server";
import { cookies } from "next/headers";

const LOCALES = ["en", "es"] as const;
type Locale = (typeof LOCALES)[number];

function isValidLocale(locale: string | undefined): locale is Locale {
  return LOCALES.includes(locale as Locale);
}

export default getRequestConfig(async () => {
  const cookieStore = await cookies();
  const cookieLocale = cookieStore.get("NEXT_LOCALE")?.value;
  const locale: Locale = isValidLocale(cookieLocale) ? cookieLocale : "en";

  return {
    locale,
    messages: (await import(`../../messages/${locale}.json`)).default,
  };
});

export { LOCALES, isValidLocale };
