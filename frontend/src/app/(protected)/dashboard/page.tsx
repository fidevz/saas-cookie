"use client";

import React from "react";
import Link from "next/link";
import { useTranslations } from "next-intl";
import { CreditCard, Users, HelpCircle, ArrowRight } from "lucide-react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { useAuthStore } from "@/stores/auth-store";
import { useFeatureStore } from "@/stores/feature-store";
import { getTimeOfDay } from "@/lib/utils";

const APP_NAME = process.env.NEXT_PUBLIC_APP_NAME ?? "MyApp";

export default function DashboardPage() {
  const t = useTranslations("dashboard");
  const { user } = useAuthStore();
  const { flags } = useFeatureStore();
  const timeOfDay = getTimeOfDay();

  const quickLinks = [
    {
      title: "Billing",
      description: "Manage your subscription and billing details.",
      href: "/billing",
      icon: CreditCard,
      show: flags.BILLING,
    },
    {
      title: "Team",
      description: "Invite members and manage roles.",
      href: "/settings/team",
      icon: Users,
      show: flags.TEAMS,
    },
    {
      title: "Support",
      description: "Get help from our support team.",
      href: "/support",
      icon: HelpCircle,
      show: true,
    },
  ].filter((l) => l.show);

  return (
    <div className="mx-auto max-w-4xl space-y-8 animate-fade-in">
      {/* Greeting */}
      <div>
        <h1 className="text-2xl font-bold tracking-tight">
          {t("greeting", {
            timeOfDay,
            name: user?.first_name ?? "there",
          })}
        </h1>
        <p className="mt-1 text-sm text-muted-foreground">
          {t("subtitle")}
        </p>
      </div>

      {/* Account summary */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Account summary</CardTitle>
          <CardDescription>Your current account details</CardDescription>
        </CardHeader>
        <CardContent className="grid gap-4 sm:grid-cols-2">
          <div className="space-y-1">
            <p className="text-xs font-medium uppercase tracking-wider text-muted-foreground">
              Email
            </p>
            <p className="text-sm font-medium">{user?.email}</p>
          </div>
          <div className="space-y-1">
            <p className="text-xs font-medium uppercase tracking-wider text-muted-foreground">
              Name
            </p>
            <p className="text-sm font-medium">
              {user?.first_name} {user?.last_name}
            </p>
          </div>
          <div className="space-y-1">
            <p className="text-xs font-medium uppercase tracking-wider text-muted-foreground">
              Workspace
            </p>
            <p className="text-sm font-medium">{APP_NAME}</p>
          </div>
        </CardContent>
      </Card>

      {/* Quick links */}
      <div>
        <h2 className="mb-4 text-base font-semibold">Quick actions</h2>
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {quickLinks.map((link) => {
            const Icon = link.icon;
            return (
              <Link key={link.href} href={link.href} className="group">
                <Card className="h-full transition-all duration-200 hover:shadow-md hover:-translate-y-0.5 cursor-pointer">
                  <CardContent className="flex flex-col gap-3 p-6">
                    <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-muted group-hover:bg-muted/70 transition-colors">
                      <Icon className="h-5 w-5 text-muted-foreground" />
                    </div>
                    <div className="flex-1">
                      <p className="text-sm font-semibold">{link.title}</p>
                      <p className="mt-0.5 text-xs text-muted-foreground leading-relaxed">
                        {link.description}
                      </p>
                    </div>
                    <div className="flex items-center gap-1 text-xs font-medium text-slate-500 group-hover:text-slate-900 transition-colors">
                      Go to {link.title.toLowerCase()}
                      <ArrowRight className="h-3 w-3" />
                    </div>
                  </CardContent>
                </Card>
              </Link>
            );
          })}
        </div>
      </div>
    </div>
  );
}
