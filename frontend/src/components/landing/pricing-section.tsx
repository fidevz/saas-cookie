"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { useTranslations } from "next-intl";
import { Check } from "lucide-react";
import { Button } from "@/components/ui/button";
import { cn, formatCurrency } from "@/lib/utils";
import { Plan } from "@/types";
import { getPlans } from "@/lib/stripe";

interface PricingSectionProps {
  plans?: Plan[];
}

const FALLBACK_PLANS = [
  {
    id: 1,
    name: "Starter",
    amount: 900,
    currency: "usd",
    interval: "month" as const,
    trial_days: 14,
    features: {
      "Up to 3 team members": true,
      "5GB storage": true,
      "Email support": true,
      "API access": false,
      "Custom domain": false,
      "Priority support": false,
    },
  },
  {
    id: 2,
    name: "Pro",
    amount: 2900,
    currency: "usd",
    interval: "month" as const,
    trial_days: 14,
    features: {
      "Up to 20 team members": true,
      "50GB storage": true,
      "Email support": true,
      "API access": true,
      "Custom domain": true,
      "Priority support": false,
    },
  },
  {
    id: 3,
    name: "Enterprise",
    amount: 9900,
    currency: "usd",
    interval: "month" as const,
    trial_days: 14,
    features: {
      "Unlimited team members": true,
      "500GB storage": true,
      "Email support": true,
      "API access": true,
      "Custom domain": true,
      "Priority support": true,
    },
  },
];

export function PricingSection({ plans: initialPlans }: PricingSectionProps) {
  const t = useTranslations("landing.pricing");
  const [annual, setAnnual] = useState(false);
  const [plans, setPlans] = useState<Plan[] | undefined>(initialPlans);

  useEffect(() => {
    if (!plans || plans.length === 0) {
      getPlans().then(setPlans).catch(() => {});
    }
  }, []);  // eslint-disable-line react-hooks/exhaustive-deps

  const displayPlans = plans && plans.length > 0 ? plans : FALLBACK_PLANS;
  const popularIndex = 1;

  function getPrice(plan: Pick<Plan, "amount" | "currency">) {
    const amount = annual ? Math.floor(plan.amount * 0.8) : plan.amount;
    return formatCurrency(amount, plan.currency);
  }

  return (
    <section id="pricing" className="py-24 px-4 bg-slate-50/50">
      <div className="mx-auto max-w-6xl">
        {/* Header */}
        <div className="mx-auto max-w-2xl text-center">
          <h2 className="text-3xl font-bold tracking-tight text-slate-900 sm:text-4xl">
            {t("title")}
          </h2>
          <p className="mt-4 text-base text-muted-foreground">{t("subtitle")}</p>

          {/* Billing toggle */}
          <div className="mt-8 flex items-center justify-center gap-4">
            <span
              className={cn(
                "text-sm font-medium",
                !annual ? "text-foreground" : "text-muted-foreground"
              )}
            >
              {t("monthly")}
            </span>
            <button
              onClick={() => setAnnual(!annual)}
              className={cn(
                "relative inline-flex h-6 w-11 items-center rounded-full transition-colors focus:outline-none focus-visible:ring-2 focus-visible:ring-ring",
                annual ? "bg-slate-900" : "bg-slate-200"
              )}
              role="switch"
              aria-checked={annual}
            >
              <span
                className={cn(
                  "inline-block h-4 w-4 transform rounded-full bg-white shadow transition-transform",
                  annual ? "translate-x-6" : "translate-x-1"
                )}
              />
            </button>
            <span
              className={cn(
                "flex items-center gap-2 text-sm font-medium",
                annual ? "text-foreground" : "text-muted-foreground"
              )}
            >
              {t("annually")}
              <span className="rounded-full bg-emerald-100 px-2 py-0.5 text-xs font-semibold text-emerald-700">
                {t("save")}
              </span>
            </span>
          </div>
        </div>

        {/* Plan cards */}
        <div className="mt-12 grid grid-cols-1 gap-6 md:grid-cols-3">
          {displayPlans.map((plan, index) => {
            const isPopular = index === popularIndex;
            return (
              <div
                key={plan.id}
                className={cn(
                  "relative flex flex-col rounded-xl border bg-background p-6 shadow-sm",
                  isPopular
                    ? "border-slate-900 ring-1 ring-slate-900"
                    : "border-border"
                )}
              >
                {isPopular && (
                  <div className="absolute -top-3.5 left-1/2 -translate-x-1/2">
                    <span className="rounded-full bg-slate-900 px-3 py-1 text-xs font-semibold text-white">
                      {t("popular")}
                    </span>
                  </div>
                )}

                <div className="mb-6">
                  <h3 className="text-base font-semibold">{plan.name}</h3>
                  <div className="mt-3 flex items-baseline gap-1">
                    <span className="text-3xl font-bold tracking-tight">
                      {getPrice(plan)}
                    </span>
                    <span className="text-sm text-muted-foreground">
                      / {plan.interval}
                    </span>
                  </div>
                  {plan.trial_days > 0 && (
                    <p className="mt-1 text-xs text-muted-foreground">
                      {plan.trial_days}-day free trial
                    </p>
                  )}
                </div>

                <ul className="mb-8 flex-1 space-y-3">
                  {(Array.isArray(plan.features)
                    ? plan.features.map((f) => [f, true] as [string, boolean])
                    : Object.entries(plan.features)
                  ).map(([feature, enabled]) => (
                    <li
                      key={feature}
                      className={cn(
                        "flex items-center gap-2.5 text-sm",
                        enabled ? "text-foreground" : "text-muted-foreground line-through"
                      )}
                    >
                      <Check
                        className={cn(
                          "h-4 w-4 shrink-0",
                          enabled ? "text-emerald-500" : "text-muted-foreground/40"
                        )}
                      />
                      {feature}
                    </li>
                  ))}
                </ul>

                <Button
                  asChild
                  variant={isPopular ? "default" : "outline"}
                  className="w-full"
                >
                  <Link href="/auth/register">{t("cta")}</Link>
                </Button>
              </div>
            );
          })}
        </div>
      </div>
    </section>
  );
}
