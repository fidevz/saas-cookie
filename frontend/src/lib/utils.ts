import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatDate(date: string, locale: string = "en-US") {
  return new Intl.DateTimeFormat(locale, { dateStyle: "medium" }).format(new Date(date));
}

export function formatCurrency(amount: number, currency: string = "usd", locale: string = "en-US") {
  return new Intl.NumberFormat(locale, { style: "currency", currency }).format(amount / 100);
}

export function getTimeOfDay(): "morning" | "afternoon" | "evening" {
  const hour = new Date().getHours();
  if (hour < 12) return "morning";
  if (hour < 18) return "afternoon";
  return "evening";
}

export function timeAgo(date: string, locale: string = "en"): string {
  const rtf = new Intl.RelativeTimeFormat(locale, { numeric: "auto" });
  const now = new Date();
  const past = new Date(date);
  const diffMs = past.getTime() - now.getTime();
  const diffSecs = Math.round(diffMs / 1000);
  const diffMins = Math.round(diffSecs / 60);
  const diffHours = Math.round(diffMins / 60);
  const diffDays = Math.round(diffHours / 24);

  if (Math.abs(diffSecs) < 60) return rtf.format(diffSecs, "second");
  if (Math.abs(diffMins) < 60) return rtf.format(diffMins, "minute");
  if (Math.abs(diffHours) < 24) return rtf.format(diffHours, "hour");
  if (Math.abs(diffDays) < 7) return rtf.format(diffDays, "day");
  return formatDate(date, locale);
}

export function getInitials(firstName: string, lastName: string): string {
  return `${firstName.charAt(0)}${lastName.charAt(0)}`.toUpperCase();
}
