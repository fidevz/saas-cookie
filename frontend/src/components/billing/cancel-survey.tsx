"use client";

import React, { useState } from "react";
import { useRouter } from "next/navigation";
import { useTranslations } from "next-intl";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group";
import { Label } from "@/components/ui/label";
import { cancelSubscription } from "@/lib/stripe";

const REASONS = [
  "tooExpensive",
  "missingFeatures",
  "notUsing",
  "foundAlternative",
  "other",
] as const;

export function CancelSurvey() {
  const t = useTranslations("billing.cancelConfirm");
  const router = useRouter();
  const [reason, setReason] = useState<string>("");
  const [loading, setLoading] = useState(false);
  const [cancelled, setCancelled] = useState(false);

  const handleCancel = async () => {
    if (!reason) {
      toast.error(t("selectReason"));
      return;
    }
    setLoading(true);
    try {
      await cancelSubscription(reason);
      setCancelled(true);
      toast.success(t("cancelled"));
    } catch (err) {
      toast.error(err instanceof Error ? err.message : t("failedToCancel"));
    } finally {
      setLoading(false);
    }
  };

  if (cancelled) {
    return (
      <div className="flex flex-col items-center gap-4 py-8 text-center">
        <div className="flex h-16 w-16 items-center justify-center rounded-full bg-muted">
          <span className="text-2xl">✓</span>
        </div>
        <h2 className="text-xl font-semibold">{t("cancelledTitle")}</h2>
        <p className="text-sm text-muted-foreground max-w-sm">
          {t("cancelledDescription")}
        </p>
        <Button variant="outline" onClick={() => router.push("/billing")}>
          {t("backToBilling")}
        </Button>
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-6 max-w-md">
      <div>
        <h2 className="text-lg font-semibold">{t("title")}</h2>
        <p className="mt-1 text-sm text-muted-foreground">{t("subtitle")}</p>
      </div>

      <RadioGroup value={reason} onValueChange={setReason} className="gap-3">
        {REASONS.map((r) => (
          <div key={r} className="flex items-center gap-3 rounded-lg border border-border p-4 cursor-pointer hover:bg-accent transition-colors">
            <RadioGroupItem value={r} id={r} />
            <Label htmlFor={r} className="cursor-pointer font-normal">
              {t(`reasons.${r}`)}
            </Label>
          </div>
        ))}
      </RadioGroup>

      <div className="flex flex-col gap-3 sm:flex-row">
        <Button
          variant="destructive"
          onClick={handleCancel}
          disabled={loading || !reason}
          className="flex-1"
        >
          {loading ? t("cancelling") : t("confirm")}
        </Button>
        <Button
          variant="outline"
          onClick={() => router.push("/billing")}
          disabled={loading}
          className="flex-1"
        >
          {t("keep")}
        </Button>
      </div>
    </div>
  );
}
