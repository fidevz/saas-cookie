"use client";

import React, { useEffect } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useTranslations } from "next-intl";
import { ExternalLink } from "lucide-react";
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { SubscriptionStatus } from "@/components/billing/subscription-status";
import { useSubscription } from "@/hooks/use-subscription";
import { openCustomerPortal } from "@/lib/stripe";
import { useTenantStore } from "@/stores/tenant-store";
import { formatDate } from "@/lib/utils";
import { toast } from "sonner";

export default function BillingPage() {
  const t = useTranslations("billing");
  const router = useRouter();
  const { subscription, isLoading, isActive, isCancelling } = useSubscription();
  const { currentUserRole } = useTenantStore();

  useEffect(() => {
    if (currentUserRole && currentUserRole !== "admin") {
      router.replace("/dashboard");
    }
  }, [currentUserRole, router]);

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
                  <p className="text-lg font-semibold">{subscription.plan.name}</p>
                  <p className="text-sm text-muted-foreground">
                    {new Intl.NumberFormat("en-US", {
                      style: "currency",
                      currency: subscription.plan.currency,
                    }).format(subscription.plan.amount / 100)}{" "}
                    / {subscription.plan.interval}
                  </p>
                </div>
                <SubscriptionStatus status={subscription.status} />
              </div>

              <div className="grid gap-3 sm:grid-cols-2 rounded-lg border border-border p-4 bg-slate-50/50">
                <div>
                  <p className="text-xs font-medium uppercase tracking-wider text-muted-foreground">
                    Current period
                  </p>
                  <p className="mt-1 text-sm">
                    {formatDate(subscription.current_period_start)} –{" "}
                    {formatDate(subscription.current_period_end)}
                  </p>
                </div>
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
            </div>
          ) : (
            <div className="py-6 text-center">
              <p className="text-sm text-muted-foreground">No active subscription.</p>
              <Button asChild className="mt-4" size="sm">
                <Link href="/pricing">View plans</Link>
              </Button>
            </div>
          )}
        </CardContent>
        {subscription && isActive && (
          <CardFooter className="flex flex-col items-start gap-3 border-t border-border pt-6">
            <Button onClick={handleManage} className="gap-2">
              <ExternalLink className="h-4 w-4" />
              {t("manage")}
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
    </div>
  );
}
