import React from "react";
import { Badge } from "@/components/ui/badge";
import { Subscription } from "@/types";

interface SubscriptionStatusProps {
  status: Subscription["status"];
}

const STATUS_CONFIG: Record<
  Subscription["status"],
  { label: string; variant: "success" | "warning" | "destructive" | "info" | "secondary" }
> = {
  active: { label: "Active", variant: "success" },
  trialing: { label: "Trial", variant: "info" },
  cancelling: { label: "Cancelling", variant: "warning" },
  cancelled: { label: "Cancelled", variant: "destructive" },
  past_due: { label: "Past due", variant: "warning" },
  unpaid: { label: "Unpaid", variant: "destructive" },
};

export function SubscriptionStatus({ status }: SubscriptionStatusProps) {
  const config = STATUS_CONFIG[status];
  return <Badge variant={config.variant}>{config.label}</Badge>;
}
