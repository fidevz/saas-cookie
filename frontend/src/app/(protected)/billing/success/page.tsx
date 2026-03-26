"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useTranslations } from "next-intl";
import { CheckCircle } from "lucide-react";
import { Button } from "@/components/ui/button";

export default function BillingSuccessPage() {
  const t = useTranslations("billing.success");
  const router = useRouter();

  // Redirect to billing after 5 seconds
  useEffect(() => {
    const timer = setTimeout(() => router.replace("/billing"), 5000);
    return () => clearTimeout(timer);
  }, [router]);

  return (
    <div className="mx-auto max-w-md py-16 text-center animate-fade-in">
      <div className="flex justify-center mb-6">
        <CheckCircle className="h-16 w-16 text-emerald-500" />
      </div>
      <h1 className="text-2xl font-bold tracking-tight mb-2">{t("title")}</h1>
      <p className="text-muted-foreground mb-8">
        {t("description")}
      </p>
      <Button onClick={() => router.replace("/billing")}>
        {t("goToBilling")}
      </Button>
    </div>
  );
}
