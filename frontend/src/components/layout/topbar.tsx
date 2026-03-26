"use client";

import React from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useTranslations } from "next-intl";
import { LogOut, Settings, User } from "lucide-react";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { NotificationBell } from "@/components/notifications/notification-bell";
import { useAuthStore } from "@/stores/auth-store";
import { useFeatureStore } from "@/stores/feature-store";
import { getInitials } from "@/lib/utils";
import { logout } from "@/lib/auth";

interface TopbarProps {
  title?: string;
}

export function Topbar({ title }: TopbarProps) {
  const t = useTranslations("nav");
  const router = useRouter();
  const { user, logout: clearAuth } = useAuthStore();
  const { flags } = useFeatureStore();

  const handleSignOut = async () => {
    await logout();
    clearAuth();
    router.push("/auth/login");
  };

  return (
    <header className="flex h-16 items-center justify-between border-b border-border bg-background px-6">
      {/* Page title / breadcrumb */}
      <div className="flex items-center gap-2">
        {title && (
          <h1 className="text-base font-semibold tracking-tight">{title}</h1>
        )}
      </div>

      {/* Right actions */}
      <div className="flex items-center gap-3">
        {/* Notification bell */}
        {flags.NOTIFICATIONS && <NotificationBell />}

        {/* User dropdown */}
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <button aria-label="User menu" className="flex items-center gap-2 rounded-full outline-none focus-visible:ring-2 focus-visible:ring-ring">
              <Avatar className="h-8 w-8">
                <AvatarFallback className="bg-muted text-muted-foreground text-xs">
                  {user
                    ? getInitials(user.first_name, user.last_name)
                    : "?"}
                </AvatarFallback>
              </Avatar>
            </button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end" className="w-56">
            <DropdownMenuLabel className="font-normal">
              <div className="flex flex-col space-y-1">
                <p className="text-sm font-medium leading-none">
                  {user ? `${user.first_name} ${user.last_name}` : ""}
                </p>
                <p className="text-xs leading-none text-muted-foreground">
                  {user?.email ?? ""}
                </p>
              </div>
            </DropdownMenuLabel>
            <DropdownMenuSeparator />
            <DropdownMenuItem asChild>
              <Link href="/settings" className="flex items-center gap-2 cursor-pointer">
                <Settings className="h-4 w-4" />
                {t("settings")}
              </Link>
            </DropdownMenuItem>
            <DropdownMenuSeparator />
            <DropdownMenuItem
              onClick={handleSignOut}
              className="flex items-center gap-2 cursor-pointer text-destructive focus:text-destructive"
            >
              <LogOut className="h-4 w-4" />
              {t("signOut")}
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>
    </header>
  );
}
