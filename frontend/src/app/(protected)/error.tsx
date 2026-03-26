"use client";

import { useEffect } from "react";
import Link from "next/link";
import { useTranslations } from "next-intl";
import { Button } from "@/components/ui/button";

export default function ProtectedError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  const t = useTranslations("errors.generic");

  useEffect(() => {
    if (process.env.NODE_ENV === "development") {
      console.error(error);
    }
  }, [error]);

  return (
    <div className="flex flex-1 flex-col items-center justify-center px-4 text-center py-16">
      <div className="flex h-16 w-16 items-center justify-center rounded-full bg-destructive/10 mb-6">
        <span className="text-2xl font-bold text-destructive">!</span>
      </div>
      <h1 className="text-2xl font-bold tracking-tight">{t("title")}</h1>
      <p className="mt-3 text-base text-muted-foreground max-w-sm">
        {t("description")}
      </p>
      {error.digest && (
        <p className="mt-2 text-xs text-muted-foreground font-mono">
          {t("errorId", { id: error.digest })}
        </p>
      )}
      <div className="mt-8 flex gap-3">
        <Button onClick={reset}>{t("tryAgain")}</Button>
        <Button asChild variant="outline">
          <Link href="/dashboard">{t("goToDashboard")}</Link>
        </Button>
      </div>
    </div>
  );
}
