"use client";

import { Sun, Moon, Monitor } from "lucide-react";
import { useTranslations } from "next-intl";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { useTheme } from "@/hooks/use-theme";
import { cn } from "@/lib/utils";

interface ThemeToggleProps {
  collapsed?: boolean;
}

const icons = {
  light: Sun,
  dark: Moon,
  system: Monitor,
};

export function ThemeToggle({ collapsed = false }: ThemeToggleProps) {
  const t = useTranslations("settings.appearance");
  const { theme, resolvedTheme, setTheme } = useTheme();

  const ActiveIcon = icons[theme] ?? (resolvedTheme === "dark" ? Moon : Sun);

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
          <ActiveIcon className="h-4 w-4 shrink-0" />
          {!collapsed && <span>{t("label")}</span>}
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end" side="top">
        <DropdownMenuItem onClick={() => setTheme("light")}>
          <Sun className="mr-2 h-4 w-4" />
          {t("light")}
        </DropdownMenuItem>
        <DropdownMenuItem onClick={() => setTheme("dark")}>
          <Moon className="mr-2 h-4 w-4" />
          {t("dark")}
        </DropdownMenuItem>
        <DropdownMenuItem onClick={() => setTheme("system")}>
          <Monitor className="mr-2 h-4 w-4" />
          {t("system")}
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  );
}
