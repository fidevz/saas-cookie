import { getTranslations } from "next-intl/server";
import Link from "next/link";
import { Button } from "@/components/ui/button";

export default async function ProtectedNotFound() {
  const t = await getTranslations("errors.notFound");

  return (
    <div className="flex flex-1 flex-col items-center justify-center px-4 text-center py-16">
      <p className="text-sm font-medium uppercase tracking-widest text-muted-foreground">
        404
      </p>
      <h1 className="mt-4 text-3xl font-bold tracking-tight">{t("title")}</h1>
      <p className="mt-3 text-base text-muted-foreground max-w-sm">{t("description404")}</p>
      <div className="mt-8">
        <Button asChild>
          <Link href="/dashboard">{t("goToDashboard")}</Link>
        </Button>
      </div>
    </div>
  );
}
