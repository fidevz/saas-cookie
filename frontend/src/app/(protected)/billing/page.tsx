"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useTranslations, useLocale } from "next-intl";
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
  const locale = useLocale();
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
      toast.error(err instanceof Error ? err.message : t("details.failedPortal"));
    }
  };

  return (
    <div className="mx-auto max-w-2xl space-y-6 animate-fade-in">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">{t("title")}</h1>
        <p className="mt-1 text-sm text-muted-foreground">
          {t("subtitle")}
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">{t("currentPlan")}</CardTitle>
          <CardDescription>{t("details.description")}</CardDescription>
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
                  <p className="text-lg font-semibold">{subscription.plan?.name ?? t("details.activePlan")}</p>
                  {subscription.plan && (
                    <p className="text-sm text-muted-foreground">
                      {new Intl.NumberFormat(locale, {
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
                        {t("details.accessUntil")}
                      </p>
                      <p className="mt-1 text-sm font-medium">{formatDate(subscription.current_period_end, locale)}</p>
                    </div>
                  )}
                  {!isCancelling && subscription.current_period_start && subscription.current_period_end && (
                    <div>
                      <p className="text-xs font-medium uppercase tracking-wider text-muted-foreground">
                        {t("details.currentPeriod")}
                      </p>
                      <p className="mt-1 text-sm">
                        {formatDate(subscription.current_period_start, locale)} –{" "}
                        {formatDate(subscription.current_period_end, locale)}
                      </p>
                    </div>
                  )}
                  {subscription.trial_end && (
                    <div>
                      <p className="text-xs font-medium uppercase tracking-wider text-muted-foreground">
                        {t("details.trialEnds")}
                      </p>
                      <p className="mt-1 text-sm">{formatDate(subscription.trial_end, locale)}</p>
                    </div>
                  )}
                  {subscription.cancelled_at && (
                    <div>
                      <p className="text-xs font-medium uppercase tracking-wider text-muted-foreground">
                        {t("details.cancelledOn")}
                      </p>
                      <p className="mt-1 text-sm">{formatDate(subscription.cancelled_at, locale)}</p>
                    </div>
                  )}
                </div>
              )}
            </div>
          ) : (
            <div className="py-4">
              <p className="text-sm text-muted-foreground mb-6">
                {t("details.choosePlan")}
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
                {t("details.reactivateNote")}
              </p>
            )}
            <Button onClick={handleManage} className="gap-2">
              <ExternalLink className="h-4 w-4" />
              {isCancelling ? t("details.reactivate") : t("manage")}
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
