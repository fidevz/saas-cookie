import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { cn, formatCurrency, formatDate, getTimeOfDay, timeAgo, getInitials } from "../utils";

describe("cn", () => {
  it("merges class names", () => {
    expect(cn("foo", "bar")).toBe("foo bar");
  });

  it("deduplicates tailwind conflicting classes", () => {
    expect(cn("p-4", "p-2")).toBe("p-2");
  });

  it("handles conditional classes", () => {
    expect(cn("base", false && "excluded", "included")).toBe("base included");
  });

  it("handles undefined and null", () => {
    expect(cn(undefined, null, "valid")).toBe("valid");
  });
});

describe("formatCurrency", () => {
  it("formats cents to USD string", () => {
    expect(formatCurrency(2900, "usd")).toBe("$29.00");
  });

  it("defaults to USD", () => {
    expect(formatCurrency(900)).toBe("$9.00");
  });

  it("formats zero correctly", () => {
    expect(formatCurrency(0)).toBe("$0.00");
  });

  it("formats large amounts", () => {
    expect(formatCurrency(99900, "usd")).toBe("$999.00");
  });
});

describe("formatDate", () => {
  it("formats a valid ISO date string", () => {
    // Use noon UTC to avoid timezone drift
    const result = formatDate("2024-01-15T12:00:00Z");
    expect(result).toMatch(/Jan(uary)? 15,? 2024/);
  });

  it("returns a non-empty string for any valid date", () => {
    const result = formatDate("2023-12-31T12:00:00Z");
    expect(result.length).toBeGreaterThan(0);
  });

  it("includes the year in the output", () => {
    const result = formatDate("2022-06-20T12:00:00Z");
    expect(result).toContain("2022");
  });
});

describe("getTimeOfDay", () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it("returns morning for 8am", () => {
    vi.setSystemTime(new Date("2024-01-01T08:00:00"));
    expect(getTimeOfDay()).toBe("morning");
  });

  it("returns afternoon for 2pm", () => {
    vi.setSystemTime(new Date("2024-01-01T14:00:00"));
    expect(getTimeOfDay()).toBe("afternoon");
  });

  it("returns evening for 8pm", () => {
    vi.setSystemTime(new Date("2024-01-01T20:00:00"));
    expect(getTimeOfDay()).toBe("evening");
  });

  it("returns morning at midnight boundary (hour 0)", () => {
    vi.setSystemTime(new Date("2024-01-01T00:00:00"));
    expect(getTimeOfDay()).toBe("morning");
  });

  it("returns afternoon at noon (hour 12)", () => {
    vi.setSystemTime(new Date("2024-01-01T12:00:00"));
    expect(getTimeOfDay()).toBe("afternoon");
  });

  it("returns evening at 6pm boundary (hour 18)", () => {
    vi.setSystemTime(new Date("2024-01-01T18:00:00"));
    expect(getTimeOfDay()).toBe("evening");
  });
});

describe("timeAgo", () => {
  beforeEach(() => {
    vi.useFakeTimers();
    vi.setSystemTime(new Date("2024-01-15T12:00:00Z"));
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it("returns just now for < 60s ago", () => {
    const date = new Date("2024-01-15T11:59:30Z").toISOString();
    expect(timeAgo(date)).toBe("just now");
  });

  it("returns minutes ago", () => {
    const date = new Date("2024-01-15T11:45:00Z").toISOString();
    expect(timeAgo(date)).toBe("15m ago");
  });

  it("returns hours ago", () => {
    const date = new Date("2024-01-15T09:00:00Z").toISOString();
    expect(timeAgo(date)).toBe("3h ago");
  });

  it("returns days ago", () => {
    const date = new Date("2024-01-13T12:00:00Z").toISOString();
    expect(timeAgo(date)).toBe("2d ago");
  });

  it("returns formatted date for 7+ days ago", () => {
    const date = new Date("2024-01-01T12:00:00Z").toISOString();
    const result = timeAgo(date);
    expect(result).toMatch(/Jan/);
  });
});

describe("getInitials", () => {
  it("returns uppercase initials of first and last name", () => {
    expect(getInitials("John", "Doe")).toBe("JD");
  });

  it("handles single character names", () => {
    expect(getInitials("A", "B")).toBe("AB");
  });

  it("uses first character only", () => {
    expect(getInitials("Alice", "Wonderland")).toBe("AW");
  });
});
