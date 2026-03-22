import { api } from "./api";
import { Subscription, Plan } from "@/types";

export async function getPlans(): Promise<Plan[]> {
  return api.get<Plan[]>("/billing/plans/");
}

export async function getSubscription(): Promise<Subscription | null> {
  try {
    return await api.get<Subscription>("/billing/subscription/");
  } catch {
    return null;
  }
}

export async function createCheckoutSession(planId: number): Promise<void> {
  const { url } = await api.post<{ url: string }>("/billing/checkout/", { plan_id: planId });
  if (typeof window !== "undefined") {
    window.location.href = url;
  }
}

export async function openCustomerPortal(): Promise<void> {
  const { url } = await api.post<{ url: string }>("/billing/portal/", {});
  if (typeof window !== "undefined") {
    window.location.href = url;
  }
}

export async function cancelSubscription(reason?: string): Promise<void> {
  await api.post<void>("/billing/subscription/cancel/", { reason });
}
