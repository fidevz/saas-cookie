"use client";

import React from "react";
import { Info, AlertTriangle, XCircle, Gift, Trash2 } from "lucide-react";
import { cn, timeAgo } from "@/lib/utils";
import { Notification } from "@/types";
import { useNotificationStore } from "@/stores/notification-store";
import { api } from "@/lib/api";

interface NotificationItemProps {
  notification: Notification;
  showDelete?: boolean;
  clampBody?: boolean;
  onDelete?: (id: number) => void;
}

export const TYPE_ICONS = {
  welcome: Gift,
  info: Info,
  warning: AlertTriangle,
  error: XCircle,
};

export const TYPE_COLORS = {
  welcome: "text-blue-500",
  info: "text-blue-500",
  warning: "text-amber-500",
  error: "text-red-500",
};

export function NotificationItem({
  notification,
  showDelete = false,
  clampBody = true,
  onDelete,
}: NotificationItemProps) {
  const { markRead } = useNotificationStore();
  const Icon = TYPE_ICONS[notification.type];

  const handleClick = async () => {
    if (!notification.read) {
      markRead(notification.id);
      try {
        await api.patch(`/notifications/${notification.id}/read/`, { read: true });
      } catch {
        // Best-effort
      }
    }
  };

  const handleDelete = async (e: React.MouseEvent) => {
    e.stopPropagation();
    onDelete?.(notification.id);
  };

  return (
    <div
      className={cn(
        "w-full flex items-start gap-3 px-4 py-3 transition-colors hover:bg-accent",
        !notification.read && "bg-muted/50"
      )}
    >
      <button className="flex flex-1 items-start gap-3 text-left min-w-0" onClick={handleClick}>
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
          <p
            className={cn(
              "text-xs text-muted-foreground leading-relaxed",
              clampBody && "line-clamp-2"
            )}
          >
            {notification.body}
          </p>
          <p className="text-xs text-muted-foreground mt-0.5">
            {timeAgo(notification.created_at)}
          </p>
        </div>
        {!notification.read && !showDelete && (
          <div className="mt-1.5 shrink-0 h-2 w-2 rounded-full bg-blue-500" />
        )}
      </button>

      {showDelete ? (
        <div className="flex items-center gap-1.5 shrink-0 mt-0.5">
          {!notification.read && (
            <div className="h-2 w-2 rounded-full bg-blue-500" />
          )}
          <button
            onClick={handleDelete}
            className="p-1 rounded text-muted-foreground hover:text-destructive hover:bg-destructive/10 transition-colors"
            aria-label="Delete notification"
          >
            <Trash2 className="h-3.5 w-3.5" />
          </button>
        </div>
      ) : null}
    </div>
  );
}
