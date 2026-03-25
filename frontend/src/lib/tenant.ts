/**
 * Utilities for tenant subdomain resolution and URL construction.
 */

export function getTenantUrl(slug: string, path = "/dashboard"): string {
  if (typeof window === "undefined") return path;

  const { protocol, port } = window.location;
  const baseDomain = process.env.NEXT_PUBLIC_BASE_DOMAIN || "localhost";
  const portSuffix = port && port !== "80" && port !== "443" ? `:${port}` : "";
  return `${protocol}//${slug}.${baseDomain}${portSuffix}${path}`;
}

export function getCurrentTenantSlug(): string | null {
  if (typeof window === "undefined") return null;

  const baseDomain = process.env.NEXT_PUBLIC_BASE_DOMAIN || "localhost";
  const hostname = window.location.hostname;

  // Root domain — no tenant
  if (hostname === baseDomain || hostname === "localhost") return null;

  // Subdomain: extract first part (e.g. "acme" from "acme.localhost")
  const parts = hostname.split(".");
  if (parts.length < 2) return null;

  return parts[0] || null;
}
