"use client";

import { useState, useEffect } from "react";
import { getSubscription } from "@/lib/stripe";
import { useAuthStore } from "@/stores/auth-store";
import { Subscription } from "@/types";

export function useSubscription() {
  const { isAuthenticated } = useAuthStore();
  const [subscription, setSubscription] = useState<Subscription | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);

  useEffect(() => {
    // Don't call the API until the user is authenticated — otherwise we get
    // a 401 which triggers the token-refresh / logout redirect loop.
    if (!isAuthenticated) {
      setIsLoading(false);
      return;
    }

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
  }, [isAuthenticated]);

  const isActive =
    subscription?.status === "active" ||
    subscription?.status === "trialing" ||
    subscription?.status === "cancelling";
  const isTrial = subscription?.status === "trialing";
  const isCancelling = subscription?.status === "cancelling";
  const isCancelled = subscription?.status === "cancelled";

  /**
   * Check if the current subscription has a boolean capability enabled.
   * Uses the subscription capabilities snapshot; falls back to plan capabilities.
   */
  const hasCapability = (key: string): boolean => {
    const caps =
      subscription?.capabilities && Object.keys(subscription.capabilities).length > 0
        ? subscription.capabilities
        : subscription?.plan?.capabilities ?? {};
    return caps[key] === true;
  };

  /**
   * Return the numeric limit for a capability.
   * Returns null if the limit is unlimited (null in DB) or the capability is not found.
   * Returns 0 if the plan has no access (and the capability is 0).
   */
  const getLimit = (key: string): number | null => {
    const caps =
      subscription?.capabilities && Object.keys(subscription.capabilities).length > 0
        ? subscription.capabilities
        : subscription?.plan?.capabilities ?? {};
    const val = caps[key];
    if (typeof val === "number") return val;
    return null; // null = unlimited or not found
  };

  return {
    subscription,
    isLoading,
    error,
    isActive,
    isTrial,
    isCancelling,
    isCancelled,
    hasCapability,
    getLimit,
  };
}
