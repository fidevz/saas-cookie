"use client";

import React, { useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useTranslations } from "next-intl";
import {
  LayoutDashboard,
  CreditCard,
  Users,
  Settings,
  LogOut,
  ChevronLeft,
  ChevronRight,
  Menu,
  X,
} from "lucide-react";
import { cn, getInitials } from "@/lib/utils";
import { useAuthStore } from "@/stores/auth-store";
import { useFeatureStore } from "@/stores/feature-store";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Button } from "@/components/ui/button";
import { logout } from "@/lib/auth";
import { useRouter } from "next/navigation";

const APP_NAME = process.env.NEXT_PUBLIC_APP_NAME ?? "MyApp";

export function Sidebar() {
  const t = useTranslations("nav");
  const pathname = usePathname();
  const router = useRouter();
  const { user, logout: clearAuth } = useAuthStore();
  const { flags } = useFeatureStore();
  const [collapsed, setCollapsed] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);

  const navItems = [
    {
      href: "/dashboard",
      label: t("dashboard"),
      icon: LayoutDashboard,
      show: true,
    },
    {
      href: "/billing",
      label: t("billing"),
      icon: CreditCard,
      show: flags.BILLING,
    },
    {
      href: "/settings/team",
      label: t("team"),
      icon: Users,
      show: flags.TEAMS,
    },
    {
      href: "/settings",
      label: t("settings"),
      icon: Settings,
      show: true,
    },
  ].filter((item) => item.show);

  const handleSignOut = async () => {
    await logout();
    clearAuth();
    router.push("/auth/login");
  };

  const SidebarContent = () => (
    <div
      className={cn(
        "flex h-full flex-col border-r border-border bg-background transition-all duration-300",
        collapsed ? "w-16" : "w-60"
      )}
    >
      {/* Logo */}
      <div className="flex h-16 items-center justify-between border-b border-border px-4">
        {!collapsed && (
          <Link href="/dashboard" className="flex items-center gap-2">
            <div className="flex h-7 w-7 items-center justify-center rounded-md bg-slate-900">
              <span className="text-xs font-bold text-white">
                {APP_NAME.charAt(0)}
              </span>
            </div>
            <span className="text-sm font-semibold">{APP_NAME}</span>
          </Link>
        )}
        {collapsed && (
          <Link href="/dashboard" className="mx-auto">
            <div className="flex h-7 w-7 items-center justify-center rounded-md bg-slate-900">
              <span className="text-xs font-bold text-white">
                {APP_NAME.charAt(0)}
              </span>
            </div>
          </Link>
        )}
        <button
          onClick={() => setCollapsed(!collapsed)}
          className="hidden rounded-md p-1.5 text-muted-foreground hover:bg-accent hover:text-foreground lg:flex"
          aria-label="Toggle sidebar"
        >
          {collapsed ? (
            <ChevronRight className="h-4 w-4" />
          ) : (
            <ChevronLeft className="h-4 w-4" />
          )}
        </button>
      </div>

      {/* Navigation */}
      <nav className="flex-1 overflow-y-auto p-3">
        <ul className="space-y-1">
          {navItems.map((item) => {
            const isActive = pathname === item.href || pathname.startsWith(item.href + "/");
            const Icon = item.icon;
            return (
              <li key={item.href}>
                <Link
                  href={item.href}
                  onClick={() => setMobileOpen(false)}
                  className={cn(
                    "flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium transition-colors",
                    isActive
                      ? "bg-accent text-foreground"
                      : "text-muted-foreground hover:bg-accent hover:text-foreground",
                    collapsed && "justify-center px-2"
                  )}
                  title={collapsed ? item.label : undefined}
                >
                  <Icon className="h-4 w-4 shrink-0" />
                  {!collapsed && <span>{item.label}</span>}
                </Link>
              </li>
            );
          })}
        </ul>
      </nav>

      {/* User section */}
      <div className="border-t border-border p-3">
        <div
          className={cn(
            "flex items-center gap-3 rounded-md px-2 py-2",
            collapsed && "justify-center"
          )}
        >
          <Avatar className="h-8 w-8 shrink-0">
            <AvatarFallback className="bg-slate-200 text-slate-700 text-xs">
              {user
                ? getInitials(user.first_name, user.last_name)
                : "?"}
            </AvatarFallback>
          </Avatar>
          {!collapsed && (
            <div className="flex flex-1 flex-col min-w-0">
              <p className="truncate text-sm font-medium">
                {user ? `${user.first_name} ${user.last_name}` : ""}
              </p>
              <p className="truncate text-xs text-muted-foreground">
                {user?.email ?? ""}
              </p>
            </div>
          )}
          {!collapsed && (
            <button
              onClick={handleSignOut}
              className="shrink-0 rounded-md p-1.5 text-muted-foreground hover:bg-accent hover:text-foreground"
              aria-label={t("signOut")}
            >
              <LogOut className="h-4 w-4" />
            </button>
          )}
        </div>
        {collapsed && (
          <button
            onClick={handleSignOut}
            className="mt-1 flex w-full items-center justify-center rounded-md p-1.5 text-muted-foreground hover:bg-accent hover:text-foreground"
            aria-label={t("signOut")}
          >
            <LogOut className="h-4 w-4" />
          </button>
        )}
      </div>
    </div>
  );

  return (
    <>
      {/* Desktop sidebar */}
      <aside className="hidden lg:flex lg:flex-col lg:flex-shrink-0">
        <SidebarContent />
      </aside>

      {/* Mobile sidebar toggle */}
      <div className="fixed left-4 top-4 z-50 lg:hidden">
        <Button
          variant="outline"
          size="icon"
          onClick={() => setMobileOpen(!mobileOpen)}
          className="h-9 w-9 shadow-sm"
        >
          {mobileOpen ? <X className="h-4 w-4" /> : <Menu className="h-4 w-4" />}
        </Button>
      </div>

      {/* Mobile sidebar overlay */}
      {mobileOpen && (
        <>
          <div
            className="fixed inset-0 z-40 bg-black/50 lg:hidden"
            onClick={() => setMobileOpen(false)}
          />
          <aside className="fixed inset-y-0 left-0 z-50 lg:hidden">
            <SidebarContent />
          </aside>
        </>
      )}
    </>
  );
}
