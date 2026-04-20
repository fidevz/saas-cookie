/**
 * Date range helpers for dashboard/analytics filters.
 * All dates are returned in ISO 8601 format (YYYY-MM-DD) in America/Mexico_City timezone.
 */

const TIMEZONE = "America/Mexico_City";

function toLocalDateString(date: Date): string {
  return new Intl.DateTimeFormat("en-CA", {
    timeZone: TIMEZONE,
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
  }).format(date);
}

export type DateRangeKey =
  | "today"
  | "yesterday"
  | "last7"
  | "last30"
  | "thisMonth"
  | "lastMonth"
  | "last90"
  | "thisYear";

export interface DateRange {
  start: string; // YYYY-MM-DD
  end: string;   // YYYY-MM-DD
}

/**
 * Returns start/end date strings for a named range, anchored to today in
 * America/Mexico_City timezone.
 */
export function getDateRange(key: DateRangeKey): DateRange {
  const now = new Date();
  const todayStr = toLocalDateString(now);

  const daysAgo = (n: number): string => {
    const d = new Date(now);
    d.setDate(d.getDate() - n);
    return toLocalDateString(d);
  };

  switch (key) {
    case "today":
      return { start: todayStr, end: todayStr };

    case "yesterday": {
      const y = daysAgo(1);
      return { start: y, end: y };
    }

    case "last7":
      return { start: daysAgo(6), end: todayStr };

    case "last30":
      return { start: daysAgo(29), end: todayStr };

    case "thisMonth": {
      const d = new Date(now);
      d.setDate(1);
      return { start: toLocalDateString(d), end: todayStr };
    }

    case "lastMonth": {
      const firstOfThisMonth = new Date(now);
      firstOfThisMonth.setDate(1);
      const lastOfLastMonth = new Date(firstOfThisMonth);
      lastOfLastMonth.setDate(0);
      const firstOfLastMonth = new Date(lastOfLastMonth);
      firstOfLastMonth.setDate(1);
      return {
        start: toLocalDateString(firstOfLastMonth),
        end: toLocalDateString(lastOfLastMonth),
      };
    }

    case "last90":
      return { start: daysAgo(89), end: todayStr };

    case "thisYear": {
      const d = new Date(now);
      d.setMonth(0, 1);
      return { start: toLocalDateString(d), end: todayStr };
    }
  }
}
