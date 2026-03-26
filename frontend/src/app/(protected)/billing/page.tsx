"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useTranslations } from "next-intl";
import { ExternalLink } from "lucide-react";
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { SubscriptionStatus } from "@/components/billing/subscription-status";
import { PlanCard } from "@/components/billing/plan-card";
import { useSubscription } from "@/hooks/use-subscription";
import { openCustomerPortal, getPlans } from "@/lib/stripe";
import { useTenantStore } from "@/stores/tenant-store";
import { formatDate } from "@/lib/utils";
import { toast } from "sonner";
import { Plan } from "@/types";

export default function BillingPage() {
  const t = useTranslations("billing");
  const router = useRouter();
  const { subscription, isLoading, isActive, isCancelling } = useSubscription();
  const { currentUserRole } = useTenantStore();
  const [plans, setPlans] = useState<Plan[]>([]);
  const [plansLoading, setPlansLoading] = useState(false);

  useEffect(() => {
    // Only enforce admin-only redirect when the user already has a subscription
    // (so tenant owners can always reach billing to choose their initial plan)
    if (subscription && currentUserRole && currentUserRole !== "admin") {
      router.replace("/dashboard");
    }
  }, [subscription, currentUserRole, router]);

  // Load plans whenever subscription state is known
  useEffect(() => {
    if (!isLoading) {
      setPlansLoading(true);
      getPlans()
        .then(setPlans)
        .catch(() => {})
        .finally(() => setPlansLoading(false));
    }
  }, [isLoading]);

  const upgradePlans = subscription?.plan
    ? plans.filter((p) => p.id !== subscription.plan.id && p.amount > subscription.plan.amount)
    : [];
  const showUpgradeSection = isActive && !isCancelling && upgradePlans.length > 0;

  const handleManage = async () => {
    try {
      await openCustomerPortal();
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Failed to open billing portal");
    }
  };

  return (
    <div className="mx-auto max-w-2xl space-y-6 animate-fade-in">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">{t("title")}</h1>
        <p className="mt-1 text-sm text-muted-foreground">
          Manage your subscription and billing information.
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">{t("currentPlan")}</CardTitle>
          <CardDescription>Your current subscription details</CardDescription>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="space-y-3">
              <Skeleton className="h-5 w-32" />
              <Skeleton className="h-4 w-48" />
              <Skeleton className="h-4 w-40" />
            </div>
          ) : subscription ? (
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-lg font-semibold">{subscription.plan?.name ?? "Active subscription"}</p>
                  {subscription.plan && (
                    <p className="text-sm text-muted-foreground">
                      {new Intl.NumberFormat("en-US", {
                        style: "currency",
                        currency: subscription.plan.currency,
                      }).format(subscription.plan.amount / 100)}{" "}
                      / {subscription.plan.interval}
                    </p>
                  )}
                </div>
                <SubscriptionStatus status={subscription.status} />
              </div>

              {(subscription.current_period_end || subscription.trial_end || subscription.cancelled_at) && (
                <div className="grid gap-3 sm:grid-cols-2 rounded-lg border border-border p-4 bg-muted/50">
                  {isCancelling && subscription.current_period_end && (
                    <div>
                      <p className="text-xs font-medium uppercase tracking-wider text-muted-foreground">
                        Access until
                      </p>
                      <p className="mt-1 text-sm font-medium">{formatDate(subscription.current_period_end)}</p>
                    </div>
                  )}
                  {!isCancelling && subscription.current_period_start && subscription.current_period_end && (
                    <div>
                      <p className="text-xs font-medium uppercase tracking-wider text-muted-foreground">
                        Current period
                      </p>
                      <p className="mt-1 text-sm">
                        {formatDate(subscription.current_period_start)} –{" "}
                        {formatDate(subscription.current_period_end)}
                      </p>
                    </div>
                  )}
                  {subscription.trial_end && (
                    <div>
                      <p className="text-xs font-medium uppercase tracking-wider text-muted-foreground">
                        Trial ends
                      </p>
                      <p className="mt-1 text-sm">{formatDate(subscription.trial_end)}</p>
                    </div>
                  )}
                  {subscription.cancelled_at && (
                    <div>
                      <p className="text-xs font-medium uppercase tracking-wider text-muted-foreground">
                        Cancelled on
                      </p>
                      <p className="mt-1 text-sm">{formatDate(subscription.cancelled_at)}</p>
                    </div>
                  )}
                </div>
              )}
            </div>
          ) : (
            <div className="py-4">
              <p className="text-sm text-muted-foreground mb-6">
                Choose a plan to get started. Pick the Free plan to continue at no cost, or upgrade for more features.
              </p>
              {plansLoading ? (
                <div className="grid gap-4 sm:grid-cols-2">
                  <Skeleton className="h-64 w-full rounded-xl" />
                  <Skeleton className="h-64 w-full rounded-xl" />
                </div>
              ) : (
                <div className="grid gap-4 sm:grid-cols-2">
                  {plans.map((plan, index) => (
                    <PlanCard
                      key={plan.id}
                      plan={plan}
                      isPopular={index === plans.length - 1}
                    />
                  ))}
                </div>
              )}
            </div>
          )}
        </CardContent>
        {subscription && (isActive || isCancelling) && (
          <CardFooter className="flex flex-col items-start gap-3 border-t border-border pt-6">
            {isCancelling && (
              <p className="text-sm text-muted-foreground">
                You can reactivate your subscription before the access period ends.
              </p>
            )}
            <Button onClick={handleManage} className="gap-2">
              <ExternalLink className="h-4 w-4" />
              {isCancelling ? "Reactivate subscription" : t("manage")}
            </Button>
            {!isCancelling && (
              <Link
                href="/billing/cancel"
                className="text-sm text-muted-foreground underline underline-offset-4 hover:text-destructive transition-colors"
              >
                {t("cancel")}
              </Link>
            )}
          </CardFooter>
        )}
      </Card>

      {showUpgradeSection && (
        <Card>
          <CardHeader>
            <CardTitle className="text-base">{t("upgrade.title")}</CardTitle>
            <CardDescription>{t("upgrade.subtitle")}</CardDescription>
          </CardHeader>
          <CardContent>
            {plansLoading ? (
              <div className="grid gap-4 sm:grid-cols-2">
                <Skeleton className="h-64 w-full rounded-xl" />
                <Skeleton className="h-64 w-full rounded-xl" />
              </div>
            ) : (
              <div className="grid gap-4 sm:grid-cols-2">
                {upgradePlans.map((plan, index) => (
                  <PlanCard
                    key={plan.id}
                    plan={plan}
                    isPopular={index === upgradePlans.length - 1}
                    onUpgrade={handleManage}
                  />
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      )}
    </div>
  );
}
