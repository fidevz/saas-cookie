"use client";

import { Globe } from "lucide-react";
import { useTranslations } from "next-intl";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { cn } from "@/lib/utils";

const LOCALES = [
  { code: "en", label: "English" },
  { code: "es", label: "Español" },
] as const;

interface LanguageToggleProps {
  collapsed?: boolean;
}

export function LanguageToggle({ collapsed = false }: LanguageToggleProps) {
  const t = useTranslations("settings.language");

  function setLocale(locale: string) {
    document.cookie = `NEXT_LOCALE=${locale};path=/;max-age=31536000`;
    window.location.reload();
  }

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button
          variant="ghost"
          size={collapsed ? "icon" : "sm"}
          className={cn(
            "text-muted-foreground hover:text-foreground",
            collapsed ? "h-8 w-8" : "w-full justify-start gap-2 px-2"
          )}
          aria-label={t("toggleLabel")}
          title={collapsed ? t("label") : undefined}
        >
          <Globe className="h-4 w-4 shrink-0" />
          {!collapsed && <span>{t("label")}</span>}
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end" side="top">
        {LOCALES.map(({ code, label }) => (
          <DropdownMenuItem key={code} onClick={() => setLocale(code)}>
            {label}
          </DropdownMenuItem>
        ))}
      </DropdownMenuContent>
    </DropdownMenu>
  );
}
