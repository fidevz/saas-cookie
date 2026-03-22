"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { useTranslations } from "next-intl";
import { Menu, X } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useAuthStore } from "@/stores/auth-store";
import { cn } from "@/lib/utils";

const APP_NAME = process.env.NEXT_PUBLIC_APP_NAME ?? "MyApp";

export function Header() {
  const t = useTranslations("nav");
  const { isAuthenticated } = useAuthStore();
  const [scrolled, setScrolled] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);

  useEffect(() => {
    const handleScroll = () => setScrolled(window.scrollY > 8);
    window.addEventListener("scroll", handleScroll, { passive: true });
    return () => window.removeEventListener("scroll", handleScroll);
  }, []);

  return (
    <header
      className={cn(
        "fixed inset-x-0 top-0 z-50 transition-all duration-300",
        scrolled
          ? "border-b border-border bg-background/80 backdrop-blur-md"
          : "bg-transparent"
      )}
    >
      <div className="container mx-auto flex h-16 max-w-6xl items-center justify-between px-4">
        {/* Logo */}
        <Link href="/" className="flex items-center gap-2">
          <div className="flex h-7 w-7 items-center justify-center rounded-md bg-slate-900">
            <span className="text-xs font-bold text-white">
              {APP_NAME.charAt(0)}
            </span>
          </div>
          <span className="text-sm font-semibold tracking-tight">{APP_NAME}</span>
        </Link>

        {/* Desktop Nav */}
        <nav className="hidden items-center gap-6 md:flex">
          <Link
            href="/#features"
            className="text-sm text-muted-foreground transition-colors hover:text-foreground"
          >
            {t("features")}
          </Link>
          <Link
            href="/pricing"
            className="text-sm text-muted-foreground transition-colors hover:text-foreground"
          >
            {t("pricing")}
          </Link>
        </nav>

        {/* Right actions */}
        <div className="hidden items-center gap-3 md:flex">
          {isAuthenticated ? (
            <Button asChild size="sm">
              <Link href="/dashboard">{t("dashboard")}</Link>
            </Button>
          ) : (
            <>
              <Button asChild variant="ghost" size="sm">
                <Link href="/auth/login">{t("signIn")}</Link>
              </Button>
              <Button asChild size="sm">
                <Link href="/auth/register">{t("getStarted")}</Link>
              </Button>
            </>
          )}
        </div>

        {/* Mobile hamburger */}
        <button
          className="flex items-center justify-center rounded-md p-2 md:hidden"
          onClick={() => setMobileOpen(!mobileOpen)}
          aria-label="Toggle menu"
        >
          {mobileOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
        </button>
      </div>

      {/* Mobile menu */}
      {mobileOpen && (
        <div className="border-t border-border bg-background/95 backdrop-blur-md md:hidden">
          <nav className="container flex flex-col gap-1 px-4 py-4">
            <Link
              href="/#features"
              className="rounded-md px-3 py-2 text-sm font-medium hover:bg-accent"
              onClick={() => setMobileOpen(false)}
            >
              {t("features")}
            </Link>
            <Link
              href="/pricing"
              className="rounded-md px-3 py-2 text-sm font-medium hover:bg-accent"
              onClick={() => setMobileOpen(false)}
            >
              {t("pricing")}
            </Link>
            <div className="mt-2 flex flex-col gap-2 pt-2 border-t border-border">
              {isAuthenticated ? (
                <Button asChild>
                  <Link href="/dashboard" onClick={() => setMobileOpen(false)}>
                    {t("dashboard")}
                  </Link>
                </Button>
              ) : (
                <>
                  <Button asChild variant="outline">
                    <Link href="/auth/login" onClick={() => setMobileOpen(false)}>
                      {t("signIn")}
                    </Link>
                  </Button>
                  <Button asChild>
                    <Link href="/auth/register" onClick={() => setMobileOpen(false)}>
                      {t("getStarted")}
                    </Link>
                  </Button>
                </>
              )}
            </div>
          </nav>
        </div>
      )}
    </header>
  );
}
