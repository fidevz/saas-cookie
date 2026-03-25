import { describe, it, expect, beforeEach } from "vitest";
import { useNotificationStore } from "../notification-store";
import type { Notification } from "@/types";

function makeNotification(overrides: Partial<Notification> = {}): Notification {
  return {
    id: 1,
    type: "welcome",
    title: "Welcome!",
    body: "Thanks for joining.",
    read: false,
    created_at: "2024-01-01T00:00:00Z",
    ...overrides,
  };
}

describe("useNotificationStore", () => {
  beforeEach(() => {
    useNotificationStore.setState({ notifications: [], unreadCount: 0 });
  });

  it("setNotifications replaces notifications and recalculates unread count", () => {
    const notifs = [
      makeNotification({ id: 1, read: false }),
      makeNotification({ id: 2, read: true }),
      makeNotification({ id: 3, read: false }),
    ];
    useNotificationStore.getState().setNotifications(notifs);
    const { notifications, unreadCount } = useNotificationStore.getState();
    expect(notifications).toHaveLength(3);
    expect(unreadCount).toBe(2);
  });

  it("addNotification prepends and increments unread for unread notification", () => {
    useNotificationStore.getState().addNotification(makeNotification({ id: 1, read: false }));
    const { notifications, unreadCount } = useNotificationStore.getState();
    expect(notifications).toHaveLength(1);
    expect(unreadCount).toBe(1);
  });

  it("addNotification does not increment unread for already-read notification", () => {
    useNotificationStore.getState().addNotification(makeNotification({ id: 1, read: true }));
    const { unreadCount } = useNotificationStore.getState();
    expect(unreadCount).toBe(0);
  });

  it("addNotification prepends (newest first)", () => {
    useNotificationStore.getState().addNotification(makeNotification({ id: 1, title: "First" }));
    useNotificationStore.getState().addNotification(makeNotification({ id: 2, title: "Second" }));
    const { notifications } = useNotificationStore.getState();
    expect(notifications[0].title).toBe("Second");
    expect(notifications[1].title).toBe("First");
  });

  it("markRead marks a single notification as read", () => {
    useNotificationStore.getState().setNotifications([
      makeNotification({ id: 1, read: false }),
      makeNotification({ id: 2, read: false }),
    ]);
    useNotificationStore.getState().markRead(1);
    const { notifications, unreadCount } = useNotificationStore.getState();
    expect(notifications.find((n) => n.id === 1)?.read).toBe(true);
    expect(notifications.find((n) => n.id === 2)?.read).toBe(false);
    expect(unreadCount).toBe(1);
  });

  it("markRead on already-read notification does not change count", () => {
    useNotificationStore.getState().setNotifications([
      makeNotification({ id: 1, read: true }),
    ]);
    useNotificationStore.getState().markRead(1);
    expect(useNotificationStore.getState().unreadCount).toBe(0);
  });

  it("markAllRead sets all to read and unreadCount to 0", () => {
    useNotificationStore.getState().setNotifications([
      makeNotification({ id: 1, read: false }),
      makeNotification({ id: 2, read: false }),
      makeNotification({ id: 3, read: false }),
    ]);
    useNotificationStore.getState().markAllRead();
    const { notifications, unreadCount } = useNotificationStore.getState();
    expect(notifications.every((n) => n.read)).toBe(true);
    expect(unreadCount).toBe(0);
  });
});
