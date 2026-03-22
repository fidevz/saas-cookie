"use client";

import React, { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useTranslations } from "next-intl";
import { MemberList } from "@/components/team/member-list";
import { InviteForm } from "@/components/team/invite-form";
import { Skeleton } from "@/components/ui/skeleton";
import { useFeatureStore } from "@/stores/feature-store";
import { useTenantStore } from "@/stores/tenant-store";
import { useAuthStore } from "@/stores/auth-store";
import { api } from "@/lib/api";
import { TenantMembership } from "@/types";

export default function TeamPage() {
  const t = useTranslations("team");
  const router = useRouter();
  const { flags, isLoaded } = useFeatureStore();
  const { members, setMembers } = useTenantStore();
  const { user } = useAuthStore();
  const [loading, setLoading] = useState(true);

  // Feature flag guard
  useEffect(() => {
    if (isLoaded && !flags.TEAMS) {
      router.replace("/dashboard");
    }
  }, [flags.TEAMS, isLoaded, router]);

  useEffect(() => {
    if (!flags.TEAMS) return;
    api
      .get<TenantMembership[]>("/tenants/members/")
      .then(setMembers)
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [flags.TEAMS, setMembers]);

  const currentUserMembership = members.find((m) => m.user.id === user?.id);
  const currentUserRole = currentUserMembership?.role ?? "member";
  const isAdmin = currentUserRole === "admin";

  if (!isLoaded || !flags.TEAMS) return null;

  return (
    <div className="mx-auto max-w-3xl space-y-8 animate-fade-in">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">{t("title")}</h1>
        <p className="mt-1 text-sm text-muted-foreground">
          Manage your team members and their permissions.
        </p>
      </div>

      {/* Invite form — admins only */}
      {isAdmin && (
        <div className="rounded-xl border border-border bg-background p-6">
          <h2 className="mb-4 text-sm font-semibold">{t("invite")}</h2>
          <InviteForm />
        </div>
      )}

      {/* Member list */}
      <div>
        <h2 className="mb-4 text-sm font-semibold">
          Members ({members.length})
        </h2>
        {loading ? (
          <div className="space-y-3">
            {[1, 2, 3].map((i) => (
              <div key={i} className="flex items-center gap-3 p-4 rounded-xl border border-border">
                <Skeleton className="h-9 w-9 rounded-full" />
                <div className="space-y-2 flex-1">
                  <Skeleton className="h-3 w-32" />
                  <Skeleton className="h-3 w-48" />
                </div>
                <Skeleton className="h-5 w-16 rounded-full" />
              </div>
            ))}
          </div>
        ) : (
          <MemberList members={members} currentUserRole={currentUserRole} />
        )}
      </div>
    </div>
  );
}
