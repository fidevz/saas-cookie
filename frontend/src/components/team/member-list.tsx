"use client";

import React from "react";
import { useTranslations } from "next-intl";
import { Mail, Trash2 } from "lucide-react";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { RoleBadge } from "./role-badge";
import { Invitation, TenantMembership } from "@/types";
import { getInitials } from "@/lib/utils";
import { useTenantStore } from "@/stores/tenant-store";
import { api } from "@/lib/api";
import { toast } from "sonner";
import { useAuthStore } from "@/stores/auth-store";

interface MemberListProps {
  members: TenantMembership[];
  invitations: Invitation[];
  currentUserRole: "admin" | "member";
}

export function MemberList({ members, invitations, currentUserRole }: MemberListProps) {
  const t = useTranslations("team");
  const { removeMember, removeInvitation } = useTenantStore();
  const { user: currentUser } = useAuthStore();
  const isAdmin = currentUserRole === "admin";

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

  const handleCancelInvite = async (invitation: Invitation) => {
    if (!confirm(t("cancelInviteConfirm"))) return;
    try {
      await api.delete(`/teams/invitations/${invitation.id}/cancel/`);
      removeInvitation(invitation.id);
      toast.success(t("inviteCancelled"));
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Failed to cancel invitation");
    }
  };

  return (
    <div className="divide-y divide-border rounded-xl border border-border">
      {members.map((membership) => {
        const isCurrentUser = membership.user.id === currentUser?.id;
        const canRemove = isAdmin && !isCurrentUser;

        return (
          <div
            key={membership.id}
            className="flex items-center justify-between gap-4 p-4"
          >
            <div className="flex items-center gap-3">
              <Avatar className="h-9 w-9">
                <AvatarFallback className="bg-muted text-muted-foreground text-xs">
                  {getInitials(membership.user.first_name, membership.user.last_name)}
                </AvatarFallback>
              </Avatar>
              <div>
                <p className="text-sm font-medium text-foreground">
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
      {invitations.map((invitation) => (
        <div
          key={`invite-${invitation.id}`}
          className="flex items-center justify-between gap-4 p-4 opacity-70"
        >
          <div className="flex items-center gap-3">
            <Avatar className="h-9 w-9">
              <AvatarFallback className="bg-amber-500/15 text-amber-500 text-xs">
                <Mail className="h-4 w-4" />
              </AvatarFallback>
            </Avatar>
            <div>
              <p className="text-sm font-medium text-muted-foreground">{t("pendingInvitation")}</p>
              <p className="text-xs text-muted-foreground">{invitation.email}</p>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <Badge variant="outline" className="border-amber-500/40 text-amber-500 bg-amber-500/10">
              {t("invited")}
            </Badge>
            <RoleBadge role={invitation.role} />
            {isAdmin && (
              <Button
                variant="ghost"
                size="icon"
                className="h-8 w-8 text-muted-foreground hover:text-destructive"
                onClick={() => handleCancelInvite(invitation)}
              >
                <Trash2 className="h-4 w-4" />
                <span className="sr-only">{t("cancelInvite")}</span>
              </Button>
            )}
          </div>
        </div>
      ))}
    </div>
  );
}
