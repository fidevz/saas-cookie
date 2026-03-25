"use client";

import React, { useState } from "react";
import { useTranslations } from "next-intl";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { api } from "@/lib/api";
import { Invitation } from "@/types";

export function InviteForm() {
  const t = useTranslations("team");
  const [email, setEmail] = useState("");
  const [role, setRole] = useState<"admin" | "member">("member");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    try {
      await api.post<Invitation>("/teams/invitations/", { email, role });
      toast.success(t("inviteSent"));
      setEmail("");
      setRole("member");
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Failed to send invitation");
    } finally {
      setLoading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="flex flex-col gap-4 sm:flex-row sm:items-end">
      <div className="flex flex-col gap-2 flex-1">
        <Label htmlFor="invite-email">{t("inviteEmail")}</Label>
        <Input
          id="invite-email"
          type="email"
          placeholder="colleague@company.com"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          required
        />
      </div>

      <div className="flex flex-col gap-2 w-36">
        <Label htmlFor="invite-role">{t("inviteRole")}</Label>
        <Select value={role} onValueChange={(v) => setRole(v as "admin" | "member")}>
          <SelectTrigger id="invite-role">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="member">{t("roles.member")}</SelectItem>
            <SelectItem value="admin">{t("roles.admin")}</SelectItem>
          </SelectContent>
        </Select>
      </div>

      <Button type="submit" disabled={loading} className="sm:shrink-0">
        {loading ? "Sending..." : t("sendInvite")}
      </Button>
    </form>
  );
}
