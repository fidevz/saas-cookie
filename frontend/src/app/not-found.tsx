import Link from "next/link";
import { getTranslations } from "next-intl/server";
import { Header } from "@/components/layout/header";
import { Footer } from "@/components/layout/footer";
import { Button } from "@/components/ui/button";

export default async function NotFound() {
  const t = await getTranslations("errors.notFound");

  return (
    <div className="flex min-h-screen flex-col">
      <Header />
      <main className="flex flex-1 flex-col items-center justify-center px-4 text-center">
        <p className="text-sm font-medium uppercase tracking-widest text-muted-foreground">
          404
        </p>
        <h1 className="mt-4 text-3xl font-bold tracking-tight">{t("title")}</h1>
        <p className="mt-3 text-base text-muted-foreground max-w-sm">
          {t("description")}
        </p>
        <div className="mt-8 flex gap-3">
          <Button asChild>
            <Link href="/">{t("goHome")}</Link>
          </Button>
          <Button asChild variant="outline">
            <Link href="/support">{t("contactSupport")}</Link>
          </Button>
        </div>
      </main>
      <Footer />
    </div>
  );
}
