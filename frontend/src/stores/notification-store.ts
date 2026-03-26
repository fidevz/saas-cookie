"use client";

import { create } from "zustand";
import { Notification } from "@/types";
import { wsClient } from "@/lib/ws";

interface NotificationState {
  notifications: Notification[];
  unreadCount: number;
  hasMore: boolean;
  currentPage: number;
  setNotifications: (notifs: Notification[], hasMore?: boolean) => void;
  appendNotifications: (notifs: Notification[], hasMore: boolean) => void;
  addNotification: (notif: Notification) => void;
  markRead: (id: number) => void;
  markAllRead: () => void;
  removeNotification: (id: number) => void;
  clearRead: () => void;
  connectWebSocket: (token: string) => void;
  disconnectWebSocket: () => void;
}

export const useNotificationStore = create<NotificationState>((set, get) => ({
  notifications: [],
  unreadCount: 0,
  hasMore: false,
  currentPage: 1,

  setNotifications: (notifs: Notification[], hasMore = false) =>
    set({
      notifications: notifs,
      unreadCount: notifs.filter((n) => !n.read).length,
      hasMore,
      currentPage: 1,
    }),

  appendNotifications: (notifs: Notification[], hasMore: boolean) =>
    set((state) => {
      const existingIds = new Set(state.notifications.map((n) => n.id));
      const newNotifs = notifs.filter((n) => !existingIds.has(n.id));
      const merged = [...state.notifications, ...newNotifs];
      return {
        notifications: merged,
        unreadCount: merged.filter((n) => !n.read).length,
        hasMore,
        currentPage: state.currentPage + 1,
      };
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

  removeNotification: (id: number) =>
    set((state) => {
      const notifications = state.notifications.filter((n) => n.id !== id);
      return {
        notifications,
        unreadCount: notifications.filter((n) => !n.read).length,
      };
    }),

  clearRead: () =>
    set((state) => ({
      notifications: state.notifications.filter((n) => !n.read),
    })),

  connectWebSocket: (token: string) => {
    wsClient.connect(token, (data: unknown) => {
      if (
        data &&
        typeof data === "object" &&
        "type" in data &&
        (data as { type: string }).type === "notification"
      ) {
        const payload = (data as unknown as { notification: Notification }).notification;
        get().addNotification(payload);
      }
    });
  },

  disconnectWebSocket: () => {
    wsClient.disconnect();
  },
}));
