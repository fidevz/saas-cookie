/**
 * Formatting utilities.
 */

/**
 * Format a number as Mexican Pesos.
 * formatMXN(1234.5) → "$1,234.50"
 */
export function formatMXN(value: number): string {
  return new Intl.NumberFormat("es-MX", {
    style: "currency",
    currency: "MXN",
    minimumFractionDigits: 2,
  }).format(value);
}

/**
 * Format a decimal as a percentage string.
 * formatPct(0.1234) → "12.34%"
 */
export function formatPct(value: number, decimals = 2): string {
  return `${(value * 100).toFixed(decimals)}%`;
}

/**
 * Format an ISO date string as a localized short date.
 * formatDate("2024-01-15") → "15 ene 2024" (es-MX locale)
 */
export function formatDate(isoString: string): string {
  return new Intl.DateTimeFormat("es-MX", {
    year: "numeric",
    month: "short",
    day: "numeric",
    timeZone: "America/Mexico_City",
  }).format(new Date(isoString));
}

/**
 * Format a date as a relative human-readable string.
 * Returns "Hoy", "Ayer", "Hace N días" or the formatted date for older dates.
 */
export function formatRelativeDays(isoString: string): string {
  const now = new Date();
  const date = new Date(isoString);
  const diffMs = now.getTime() - date.getTime();
  const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));

  if (diffDays === 0) return "Hoy";
  if (diffDays === 1) return "Ayer";
  if (diffDays < 30) return `Hace ${diffDays} días`;
  return formatDate(isoString);
}
