"use client";

import React, { useState } from "react";
import Link from "next/link";
import { Check } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { formatCurrency } from "@/lib/utils";
import { createCheckoutSession } from "@/lib/stripe";
import { Plan } from "@/types";
import { toast } from "sonner";

interface PlanCardProps {
  plan: Plan;
  isCurrentPlan?: boolean;
  isPopular?: boolean;
}

export function PlanCard({ plan, isCurrentPlan, isPopular }: PlanCardProps) {
  const [loading, setLoading] = useState(false);

  const handleSelect = async () => {
    setLoading(true);
    try {
      await createCheckoutSession(plan.id);
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Failed to start checkout");
      setLoading(false);
    }
  };

  return (
    <Card className={isPopular ? "border-slate-900 ring-1 ring-slate-900" : ""}>
      {isPopular && (
        <div className="relative">
          <div className="absolute -top-3.5 left-1/2 -translate-x-1/2">
            <span className="rounded-full bg-slate-900 px-3 py-1 text-xs font-semibold text-white">
              Most popular
            </span>
          </div>
        </div>
      )}
      <CardHeader>
        <CardTitle className="text-base">{plan.name}</CardTitle>
        <div className="flex items-baseline gap-1 mt-2">
          <span className="text-3xl font-bold">
            {formatCurrency(plan.amount, plan.currency)}
          </span>
          <span className="text-sm text-muted-foreground">/ {plan.interval}</span>
        </div>
        {plan.trial_days > 0 && (
          <p className="text-xs text-muted-foreground">{plan.trial_days}-day free trial</p>
        )}
      </CardHeader>

      <CardContent>
        <ul className="space-y-2.5">
          {Object.entries(plan.features).map(([feature, enabled]) => (
            <li
              key={feature}
              className={`flex items-center gap-2 text-sm ${
                enabled ? "text-foreground" : "text-muted-foreground line-through"
              }`}
            >
              <Check
                className={`h-4 w-4 shrink-0 ${
                  enabled ? "text-emerald-500" : "opacity-30"
                }`}
              />
              {feature}
            </li>
          ))}
        </ul>
      </CardContent>

      <CardFooter>
        {isCurrentPlan ? (
          <Button variant="outline" className="w-full" disabled>
            Current plan
          </Button>
        ) : (
          <Button
            className="w-full"
            variant={isPopular ? "default" : "outline"}
            onClick={handleSelect}
            disabled={loading}
          >
            {loading ? "Loading..." : "Get started"}
          </Button>
        )}
      </CardFooter>
    </Card>
  );
}
