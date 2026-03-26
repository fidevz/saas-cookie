"use client";

import React from "react";
import { useTranslations } from "next-intl";
import { Bell } from "lucide-react";
import Link from "next/link";
import { NotificationItem } from "./notification-item";
import { useNotificationStore } from "@/stores/notification-store";
import { api } from "@/lib/api";
import { toast } from "sonner";

export function NotificationDropdown() {
  const t = useTranslations("notifications");
  const { notifications, markAllRead } = useNotificationStore();

  const handleMarkAllRead = async () => {
    markAllRead();
    try {
      await api.post("/notifications/read-all/", {});
    } catch {
      toast.error("Failed to mark notifications as read");
    }
  };

  return (
    <div className="w-80 max-h-96 flex flex-col">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-border px-4 py-3">
        <h3 className="text-sm font-semibold">{t("title")}</h3>
        {notifications.some((n) => !n.read) && (
          <button
            onClick={handleMarkAllRead}
            className="text-xs text-muted-foreground hover:text-foreground underline underline-offset-4"
          >
            {t("markAllRead")}
          </button>
        )}
      </div>

      {/* Notification list */}
      <div className="flex-1 overflow-y-auto">
        {notifications.length === 0 ? (
          <div className="flex flex-col items-center justify-center gap-2 py-12">
            <Bell className="h-8 w-8 text-muted-foreground/40" />
            <p className="text-sm text-muted-foreground">{t("empty")}</p>
          </div>
        ) : (
          <div className="divide-y divide-border">
            {notifications.map((n) => (
              <NotificationItem key={n.id} notification={n} />
            ))}
          </div>
        )}
      </div>

      {/* Footer */}
      <div className="border-t border-border px-4 py-2.5">
        <Link
          href="/notifications"
          className="text-xs text-muted-foreground hover:text-foreground transition-colors"
        >
          {t("viewAll")}
        </Link>
      </div>
    </div>
  );
}
