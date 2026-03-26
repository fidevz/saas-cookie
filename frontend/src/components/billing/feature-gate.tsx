"use client";

import React, { useEffect, useState } from "react";
import { Lock } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { useSubscription } from "@/hooks/use-subscription";
import { openCustomerPortal, getPlans } from "@/lib/stripe";
import { Plan } from "@/types";
import { toast } from "sonner";

interface FeatureGateProps {
  /** Capability key to check, e.g. "teams" */
  capability: string;
  /** Human-readable feature name shown in the upgrade wall */
  title: string;
  /** Optional description shown below the title */
  description?: string;
  children: React.ReactNode;
}

/**
 * Renders children when the current plan has the required capability.
 * Otherwise renders a full-page upgrade wall listing plans that include it.
 */
export function FeatureGate({ capability, title, description, children }: FeatureGateProps) {
  const { subscription, isLoading, hasCapability } = useSubscription();
  const [plans, setPlans] = useState<Plan[]>([]);
  const [plansLoading, setPlansLoading] = useState(false);
  const [portalLoading, setPortalLoading] = useState(false);

  const locked = !isLoading && !hasCapability(capability);

  useEffect(() => {
    if (!locked) return;
    setPlansLoading(true);
    getPlans()
      .then((all) => setPlans(all.filter((p) => p.capabilities?.[capability] === true)))
      .catch(() => {})
      .finally(() => setPlansLoading(false));
  }, [locked, capability]);

  if (isLoading) return null;

  if (!locked) return <>{children}</>;

  const handleUpgrade = async () => {
    if (!subscription) {
      window.location.href = "/billing";
      return;
    }
    setPortalLoading(true);
    try {
      await openCustomerPortal();
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Failed to open billing portal");
    } finally {
      setPortalLoading(false);
    }
  };

  return (
    <div className="mx-auto max-w-2xl space-y-8 animate-fade-in">
      {/* Lock header */}
      <div className="flex flex-col items-center rounded-xl border border-border bg-muted/50 px-8 py-12 text-center">
        <div className="mb-4 flex h-12 w-12 items-center justify-center rounded-full bg-muted">
          <Lock className="h-6 w-6 text-muted-foreground" />
        </div>
        <h2 className="text-xl font-semibold text-foreground">{title}</h2>
        {description && (
          <p className="mt-2 text-sm text-muted-foreground max-w-sm">{description}</p>
        )}
        <p className="mt-3 text-sm text-muted-foreground">
          This feature is not included in your current plan.
        </p>

        <Button className="mt-6" onClick={handleUpgrade} disabled={portalLoading}>
          {portalLoading ? "Opening portal..." : "Upgrade plan"}
        </Button>
      </div>

      {/* Plans that include this feature */}
      {plansLoading ? (
        <div className="grid gap-4 sm:grid-cols-2">
          <Skeleton className="h-48 w-full rounded-xl" />
          <Skeleton className="h-48 w-full rounded-xl" />
        </div>
      ) : plans.length > 0 ? (
        <div className="space-y-3">
          <p className="text-sm font-medium text-muted-foreground">
            Available in these plans:
          </p>
          <div className="grid gap-4 sm:grid-cols-2">
            {plans.map((plan) => (
              <div
                key={plan.id}
                className="flex items-center justify-between rounded-xl border border-border bg-background p-4"
              >
                <div>
                  <p className="font-semibold">{plan.name}</p>
                  <p className="text-sm text-muted-foreground">
                    {new Intl.NumberFormat("en-US", {
                      style: "currency",
                      currency: plan.currency,
                    }).format(plan.amount / 100)}
                    {" "}/ {plan.interval}
                  </p>
                </div>
                <Button variant="outline" size="sm" onClick={handleUpgrade} disabled={portalLoading}>
                  Upgrade
                </Button>
              </div>
            ))}
          </div>
        </div>
      ) : null}
    </div>
  );
}
