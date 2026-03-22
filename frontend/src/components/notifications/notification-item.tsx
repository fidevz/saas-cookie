"use client";

import React from "react";
import { Info, AlertTriangle, XCircle, Gift } from "lucide-react";
import { cn, timeAgo } from "@/lib/utils";
import { Notification } from "@/types";
import { useNotificationStore } from "@/stores/notification-store";
import { api } from "@/lib/api";

interface NotificationItemProps {
  notification: Notification;
}

const TYPE_ICONS = {
  welcome: Gift,
  info: Info,
  warning: AlertTriangle,
  error: XCircle,
};

const TYPE_COLORS = {
  welcome: "text-blue-500",
  info: "text-blue-500",
  warning: "text-amber-500",
  error: "text-red-500",
};

export function NotificationItem({ notification }: NotificationItemProps) {
  const { markRead } = useNotificationStore();
  const Icon = TYPE_ICONS[notification.type];

  const handleClick = async () => {
    if (!notification.read) {
      markRead(notification.id);
      try {
        await api.patch(`/notifications/${notification.id}/`, { read: true });
      } catch {
        // Best-effort
      }
    }
  };

  return (
    <button
      className={cn(
        "w-full flex items-start gap-3 px-4 py-3 text-left transition-colors hover:bg-accent",
        !notification.read && "bg-slate-50"
      )}
      onClick={handleClick}
    >
      <div className={cn("mt-0.5 shrink-0", TYPE_COLORS[notification.type])}>
        <Icon className="h-4 w-4" />
      </div>
      <div className="flex flex-1 flex-col gap-0.5 min-w-0">
        <p
          className={cn(
            "truncate text-sm",
            notification.read ? "font-normal" : "font-medium"
          )}
        >
          {notification.title}
        </p>
        <p className="text-xs text-muted-foreground line-clamp-2 leading-relaxed">
          {notification.body}
        </p>
        <p className="text-xs text-muted-foreground mt-0.5">
          {timeAgo(notification.created_at)}
        </p>
      </div>
      {!notification.read && (
        <div className="mt-1.5 shrink-0 h-2 w-2 rounded-full bg-blue-500" />
      )}
    </button>
  );
}
