"use client";

import React from "react";
import { useTranslations } from "next-intl";
import { Trash2 } from "lucide-react";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Button } from "@/components/ui/button";
import { RoleBadge } from "./role-badge";
import { TenantMembership } from "@/types";
import { getInitials } from "@/lib/utils";
import { useTenantStore } from "@/stores/tenant-store";
import { api } from "@/lib/api";
import { toast } from "sonner";
import { useAuthStore } from "@/stores/auth-store";

interface MemberListProps {
  members: TenantMembership[];
  currentUserRole: "admin" | "member";
}

export function MemberList({ members, currentUserRole }: MemberListProps) {
  const t = useTranslations("team");
  const { removeMember } = useTenantStore();
  const { user: currentUser } = useAuthStore();

  const handleRemove = async (membership: TenantMembership) => {
    if (!confirm(t("removeConfirm"))) return;
    try {
      await api.delete(`/tenants/members/${membership.id}/`);
      removeMember(membership.user.id);
      toast.success(`${membership.user.first_name} removed from team.`);
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Failed to remove member");
    }
  };

  return (
    <div className="divide-y divide-border rounded-xl border border-border">
      {members.map((membership) => {
        const isCurrentUser = membership.user.id === currentUser?.id;
        const canRemove = currentUserRole === "admin" && !isCurrentUser;

        return (
          <div
            key={membership.id}
            className="flex items-center justify-between gap-4 p-4"
          >
            <div className="flex items-center gap-3">
              <Avatar className="h-9 w-9">
                <AvatarFallback className="bg-slate-100 text-slate-700 text-xs">
                  {getInitials(membership.user.first_name, membership.user.last_name)}
                </AvatarFallback>
              </Avatar>
              <div>
                <p className="text-sm font-medium">
                  {membership.user.first_name} {membership.user.last_name}
                  {isCurrentUser && (
                    <span className="ml-2 text-xs text-muted-foreground">(you)</span>
                  )}
                </p>
                <p className="text-xs text-muted-foreground">{membership.user.email}</p>
              </div>
            </div>
            <div className="flex items-center gap-3">
              <RoleBadge role={membership.role} />
              {canRemove && (
                <Button
                  variant="ghost"
                  size="icon"
                  className="h-8 w-8 text-muted-foreground hover:text-destructive"
                  onClick={() => handleRemove(membership)}
                >
                  <Trash2 className="h-4 w-4" />
                  <span className="sr-only">Remove member</span>
                </Button>
              )}
            </div>
          </div>
        );
      })}
    </div>
  );
}
