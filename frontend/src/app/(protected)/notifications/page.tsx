"use client";

import React, { useCallback, useEffect, useRef, useState } from "react";
import { useTranslations } from "next-intl";
import { Bell, Loader2 } from "lucide-react";
import { useRouter } from "next/navigation";
import { toast } from "sonner";
import { NotificationItem } from "@/components/notifications/notification-item";
import { Button } from "@/components/ui/button";
import { useNotificationStore } from "@/stores/notification-store";
import { useFeatureStore } from "@/stores/feature-store";
import { api } from "@/lib/api";
import { PaginatedResponse, Notification } from "@/types";

export default function NotificationsPage() {
  const t = useTranslations("notifications");
  const router = useRouter();
  const { flags } = useFeatureStore();
  const {
    notifications,
    unreadCount,
    hasMore,
    currentPage,
    markAllRead,
    removeNotification,
    clearRead,
    appendNotifications,
    setNotifications,
  } = useNotificationStore();

  const [loadingMore, setLoadingMore] = useState(false);
  const [initialLoaded, setInitialLoaded] = useState(notifications.length > 0);
  const sentinelRef = useRef<HTMLDivElement>(null);

  // Feature flag guard
  useEffect(() => {
    if (flags.NOTIFICATIONS === false) {
      router.replace("/dashboard");
    }
  }, [flags.NOTIFICATIONS, router]);

  // Fetch page 1 if store is empty (e.g. direct navigation)
  useEffect(() => {
    if (notifications.length === 0 && !initialLoaded) {
      setInitialLoaded(true);
      api
        .get<PaginatedResponse<Notification>>("/notifications/")
        .then((data) => setNotifications(data.results, data.next !== null))
        .catch(() => {});
    }
  }, [notifications.length, initialLoaded, setNotifications]);

  const fetchNextPage = useCallback(async () => {
    if (!hasMore || loadingMore) return;
    setLoadingMore(true);
    try {
      const data = await api.get<PaginatedResponse<Notification>>(
        `/notifications/?page=${currentPage + 1}`
      );
      appendNotifications(data.results, data.next !== null);
    } catch {
      // Silent failure — user can scroll again
    } finally {
      setLoadingMore(false);
    }
  }, [hasMore, loadingMore, currentPage, appendNotifications]);

  // Infinite scroll via IntersectionObserver
  useEffect(() => {
    const sentinel = sentinelRef.current;
    if (!sentinel) return;
    const observer = new IntersectionObserver(
      (entries) => {
        if (entries[0].isIntersecting) {
          fetchNextPage();
        }
      },
      { threshold: 0.1 }
    );
    observer.observe(sentinel);
    return () => observer.disconnect();
  }, [fetchNextPage]);

  const handleMarkAllRead = async () => {
    markAllRead();
    try {
      await api.post("/notifications/read-all/", {});
    } catch {
      toast.error(t("clearFailed"));
    }
  };

  const handleClearRead = async () => {
    const hadRead = notifications.some((n) => n.read);
    if (!hadRead) return;
    clearRead();
    try {
      await api.post("/notifications/clear-read/", {});
      toast.success(t("cleared"));
    } catch {
      toast.error(t("clearFailed"));
    }
  };

  const handleDelete = async (id: number) => {
    removeNotification(id);
    try {
      await api.delete(`/notifications/${id}/`);
    } catch {
      toast.error(t("deleteFailed"));
    }
  };

  const hasRead = notifications.some((n) => n.read);

  return (
    <div className="max-w-2xl mx-auto">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-semibold">{t("title")}</h1>
          {unreadCount > 0 && (
            <p className="text-sm text-muted-foreground mt-0.5">
              {t("unread", { count: unreadCount })}
            </p>
          )}
        </div>
        <div className="flex items-center gap-2">
          {unreadCount > 0 && (
            <Button variant="outline" size="sm" onClick={handleMarkAllRead}>
              {t("markAllRead")}
            </Button>
          )}
          {hasRead && (
            <Button variant="outline" size="sm" onClick={handleClearRead}>
              {t("clearAllRead")}
            </Button>
          )}
        </div>
      </div>

      {/* Notification list */}
      <div className="rounded-lg border border-border bg-card overflow-hidden">
        {notifications.length === 0 ? (
          <div className="flex flex-col items-center justify-center gap-3 py-20">
            <Bell className="h-10 w-10 text-muted-foreground/30" />
            <p className="text-sm text-muted-foreground">{t("empty")}</p>
          </div>
        ) : (
          <div className="divide-y divide-border">
            {notifications.map((n) => (
              <NotificationItem
                key={n.id}
                notification={n}
                showDelete
                clampBody={false}
                onDelete={handleDelete}
              />
            ))}
          </div>
        )}

        {/* Infinite scroll sentinel */}
        <div ref={sentinelRef} className="h-px" />

        {/* Loading spinner */}
        {loadingMore && (
          <div className="flex justify-center py-4">
            <Loader2 className="h-5 w-5 animate-spin text-muted-foreground" />
          </div>
        )}
      </div>
    </div>
  );
}
