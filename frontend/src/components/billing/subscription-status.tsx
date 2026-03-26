"use client";

import React from "react";
import { useTranslations } from "next-intl";
import { Badge } from "@/components/ui/badge";
import { Subscription } from "@/types";

interface SubscriptionStatusProps {
  status: Subscription["status"];
}

const STATUS_VARIANTS: Record<Subscription["status"], "success" | "warning" | "destructive" | "info" | "secondary"> = {
  active: "success",
  trialing: "info",
  cancelling: "warning",
  cancelled: "destructive",
  past_due: "warning",
  unpaid: "destructive",
};

export function SubscriptionStatus({ status }: SubscriptionStatusProps) {
  const t = useTranslations("billing.subscriptionStatus");
  const labelKeys: Record<Subscription["status"], string> = {
    active: "active",
    trialing: "trialing",
    cancelling: "cancelling",
    cancelled: "cancelled",
    past_due: "pastDue",
    unpaid: "unpaid",
  };
  return <Badge variant={STATUS_VARIANTS[status]}>{t(labelKeys[status])}</Badge>;
}
