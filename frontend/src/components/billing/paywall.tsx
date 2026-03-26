"use client";

import React, { useEffect, useState } from "react";
import { LogOut } from "lucide-react";
import { useTranslations } from "next-intl";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { PlanCard } from "@/components/billing/plan-card";
import { getPlans } from "@/lib/stripe";
import { useAuthStore } from "@/stores/auth-store";
import { logout as logoutApi } from "@/lib/auth";
import { Plan } from "@/types";

export function Paywall() {
  const t = useTranslations("billing.paywall");
  const { logout, user } = useAuthStore();
  const [plans, setPlans] = useState<Plan[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getPlans()
      .then(setPlans)
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  const handleLogout = async () => {
    await logoutApi();
    logout();
    window.location.href = "/";
  };

  const appName = process.env.NEXT_PUBLIC_APP_NAME ?? "MyApp";

  return (
    <div className="flex min-h-screen flex-col bg-muted/30">
      {/* Header */}
      <header className="flex items-center justify-between border-b border-border bg-background px-6 py-4">
        <div className="flex items-center gap-2">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-slate-900">
            <span className="text-sm font-bold text-white">
              {appName.charAt(0)}
            </span>
          </div>
          <span className="text-lg font-semibold">{appName}</span>
        </div>
        <div className="flex items-center gap-3">
          {user && (
            <span className="text-sm text-muted-foreground">{user.email}</span>
          )}
          <Button variant="ghost" size="sm" onClick={handleLogout} className="gap-2">
            <LogOut className="h-4 w-4" />
            {t("logOut")}
          </Button>
        </div>
      </header>

      {/* Main */}
      <main className="flex flex-1 flex-col items-center justify-center px-4 py-16">
        <div className="mx-auto max-w-2xl text-center mb-10">
          <h1 className="text-3xl font-bold tracking-tight">
            {t("choosePlan")}
          </h1>
          <p className="mt-3 text-muted-foreground">
            {t("choosePlanSubtitle")}
          </p>
        </div>

        {loading ? (
          <div className="grid gap-6 sm:grid-cols-3 w-full max-w-4xl">
            <Skeleton className="h-72 w-full rounded-xl" />
            <Skeleton className="h-72 w-full rounded-xl" />
            <Skeleton className="h-72 w-full rounded-xl" />
          </div>
        ) : (
          <div className="grid gap-6 sm:grid-cols-3 w-full max-w-4xl">
            {plans.map((plan, index) => (
              <PlanCard
                key={plan.id}
                plan={plan}
                isPopular={index === plans.length - 1}
              />
            ))}
          </div>
        )}
      </main>
    </div>
  );
}
