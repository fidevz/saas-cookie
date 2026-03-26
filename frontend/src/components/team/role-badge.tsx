"use client";
import React from "react";
import { useTranslations } from "next-intl";
import { Badge } from "@/components/ui/badge";

interface RoleBadgeProps {
  role: "admin" | "member";
}

export function RoleBadge({ role }: RoleBadgeProps) {
  const t = useTranslations("team");
  return (
    <Badge variant={role === "admin" ? "info" : "secondary"}>
      {role === "admin" ? t("roles.admin") : t("roles.member")}
    </Badge>
  );
}
