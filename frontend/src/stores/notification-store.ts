"use client";

import { create } from "zustand";
import { Notification } from "@/types";
import { wsClient } from "@/lib/ws";

interface NotificationState {
  notifications: Notification[];
  unreadCount: number;
  setNotifications: (notifs: Notification[]) => void;
  addNotification: (notif: Notification) => void;
  markRead: (id: number) => void;
  markAllRead: () => void;
  connectWebSocket: (token: string) => void;
  disconnectWebSocket: () => void;
}

export const useNotificationStore = create<NotificationState>((set, get) => ({
  notifications: [],
  unreadCount: 0,

  setNotifications: (notifs: Notification[]) =>
    set({
      notifications: notifs,
      unreadCount: notifs.filter((n) => !n.read).length,
    }),

  addNotification: (notif: Notification) =>
    set((state) => ({
      notifications: [notif, ...state.notifications],
      unreadCount: notif.read ? state.unreadCount : state.unreadCount + 1,
    })),

  markRead: (id: number) =>
    set((state) => {
      const notifications = state.notifications.map((n) =>
        n.id === id ? { ...n, read: true } : n
      );
      return {
        notifications,
        unreadCount: notifications.filter((n) => !n.read).length,
      };
    }),

  markAllRead: () =>
    set((state) => ({
      notifications: state.notifications.map((n) => ({ ...n, read: true })),
      unreadCount: 0,
    })),

  connectWebSocket: (token: string) => {
    wsClient.connect(token, (data: unknown) => {
      if (
        data &&
        typeof data === "object" &&
        "type" in data &&
        (data as { type: string }).type === "notification"
      ) {
        const payload = (data as { payload: Notification }).payload;
        get().addNotification(payload);
      }
    });
  },

  disconnectWebSocket: () => {
    wsClient.disconnect();
  },
}));
