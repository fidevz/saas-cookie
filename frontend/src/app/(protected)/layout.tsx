"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { Sidebar } from "@/components/layout/sidebar";
import { Topbar } from "@/components/layout/topbar";
import { useAuthStore } from "@/stores/auth-store";
import { useFeatureStore } from "@/stores/feature-store";
import { useNotificationStore } from "@/stores/notification-store";
import { useTenantStore } from "@/stores/tenant-store";
import { fetchFeatureFlags } from "@/lib/features";
import { useSubscription } from "@/hooks/use-subscription";
import { api } from "@/lib/api";
import { TenantMembership, PaginatedResponse, Notification } from "@/types";
import { Skeleton } from "@/components/ui/skeleton";
import { Paywall } from "@/components/billing/paywall";
import { useThemeStore } from "@/stores/theme-store";
import { cn } from "@/lib/utils";

export default function ProtectedLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const router = useRouter();
  const { isAuthenticated, isLoading, accessToken, user } = useAuthStore();
  const { flags, setFlags, isLoaded } = useFeatureStore();
  const { connectWebSocket, setNotifications } = useNotificationStore();
  const { setCurrentUserRole } = useTenantStore();
  const { isActive: hasActiveSub, isLoading: subLoading } = useSubscription();
  const { resolvedTheme, resolveTheme } = useThemeStore();

  // Auth guard
  useEffect(() => {
    if (!isLoading && !isAuthenticated) {
      router.replace("/auth/login");
    }
  }, [isLoading, isAuthenticated, router]);

  // Load feature flags
  useEffect(() => {
    if (isAuthenticated && !isLoaded) {
      fetchFeatureFlags().then(setFlags);
    }
  }, [isAuthenticated, isLoaded, setFlags]);

  // Load current user's tenant role
  useEffect(() => {
    if (!isAuthenticated || !user) return;
    api
      .get<{ results: TenantMembership[] } | TenantMembership[]>("/tenants/members/")
      .then((data) => {
        const members = Array.isArray(data) ? data : data.results;
        const mine = members.find((m) => m.user.id === user.id);
        setCurrentUserRole((mine?.role as "admin" | "member") ?? "member");
      })
      .catch(() => setCurrentUserRole("member"));
  }, [isAuthenticated, user, setCurrentUserRole]);

  // Listen for OS-level theme changes when user preference is "system"
  useEffect(() => {
    resolveTheme();
    const mq = window.matchMedia("(prefers-color-scheme: dark)");
    const handler = () => resolveTheme();
    mq.addEventListener("change", handler);
    return () => mq.removeEventListener("change", handler);
  }, [resolveTheme]);

  // Initialize WebSocket for notifications
  useEffect(() => {
    if (isAuthenticated && accessToken) {
      // Fetch initial notifications
      import("@/lib/api").then(({ api }) => {
        api
          .get<PaginatedResponse<Notification>>("/notifications/")
          .then((data) => setNotifications(data.results, data.next !== null))
          .catch(() => {});
      });

      // Connect WebSocket
      const { flags } = useFeatureStore.getState();
      if (flags.NOTIFICATIONS) {
        connectWebSocket(accessToken);
      }

      return () => {
        // Cleanup on unmount handled by notification store
      };
    }
  }, [isAuthenticated, accessToken, connectWebSocket, setNotifications]);

  if (isLoading || (isAuthenticated && isLoaded && flags.REQUIRE_SUBSCRIPTION && subLoading)) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <div className="flex flex-col items-center gap-4">
          <div className="h-8 w-8 animate-spin rounded-full border-2 border-slate-200 border-t-slate-900" />
          <Skeleton className="h-4 w-24" />
        </div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return null;
  }

  // Paywall: show full-page plan selection instead of app shell
  if (isLoaded && flags.REQUIRE_SUBSCRIPTION && !subLoading && !hasActiveSub) {
    return <Paywall />;
  }

  return (
    <div className={cn("flex h-screen overflow-hidden bg-background text-foreground", resolvedTheme === "dark" && "dark")} suppressHydrationWarning>
      <Sidebar />
      <div className="flex flex-1 flex-col overflow-hidden">
        <Topbar />
        <main className="flex-1 overflow-y-auto bg-slate-50/30 dark:bg-background p-6">
          {children}
        </main>
      </div>
    </div>
  );
}
