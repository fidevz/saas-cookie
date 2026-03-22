import React from "react";
import { Badge } from "@/components/ui/badge";

interface RoleBadgeProps {
  role: "admin" | "member";
}

export function RoleBadge({ role }: RoleBadgeProps) {
  return (
    <Badge variant={role === "admin" ? "info" : "secondary"}>
      {role === "admin" ? "Admin" : "Member"}
    </Badge>
  );
}
