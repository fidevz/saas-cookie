"use client";

import { useState, useEffect } from "react";
import { getSubscription } from "@/lib/stripe";
import { Subscription } from "@/types";

export function useSubscription() {
  const [subscription, setSubscription] = useState<Subscription | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);

  useEffect(() => {
    let mounted = true;
    setIsLoading(true);
    getSubscription()
      .then((sub) => {
        if (mounted) {
          setSubscription(sub);
          setError(null);
        }
      })
      .catch((err: Error) => {
        if (mounted) setError(err);
      })
      .finally(() => {
        if (mounted) setIsLoading(false);
      });
    return () => {
      mounted = false;
    };
  }, []);

  const isActive =
    subscription?.status === "active" || subscription?.status === "trialing";
  const isTrial = subscription?.status === "trialing";
  const isCancelling = subscription?.status === "cancelling";
  const isCancelled = subscription?.status === "cancelled";

  return { subscription, isLoading, error, isActive, isTrial, isCancelling, isCancelled };
}
