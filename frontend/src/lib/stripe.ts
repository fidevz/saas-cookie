import { api } from "./api";
import { Subscription, Plan } from "@/types";

export async function getPlans(): Promise<Plan[]> {
  return api.get<Plan[]>("/subscriptions/plans/");
}

export async function getSubscription(): Promise<Subscription | null> {
  try {
    return await api.get<Subscription>("/subscriptions/current/");
  } catch {
    return null;
  }
}

export async function createCheckoutSession(planId: number): Promise<void> {
  const origin = typeof window !== "undefined" ? window.location.origin : "";
  const { url } = await api.post<{ url: string }>("/subscriptions/checkout/", {
    plan_id: planId,
    success_url: `${origin}/billing/success`,
    cancel_url: `${origin}/billing`,
  });
  if (typeof window !== "undefined") {
    window.location.href = url;
  }
}

export async function openCustomerPortal(): Promise<void> {
  const { url } = await api.post<{ url: string }>("/subscriptions/portal/", {});
  if (typeof window !== "undefined") {
    window.location.href = url;
  }
}

export async function cancelSubscription(reason?: string): Promise<void> {
  await api.post<void>("/subscriptions/cancel/", { reason });
}

export async function selectFreePlan(): Promise<void> {
  await api.post<void>("/subscriptions/select-free/");
}
