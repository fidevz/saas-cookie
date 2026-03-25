import { describe, it, expect, beforeEach } from "vitest";
import { getTenantUrl, getCurrentTenantSlug } from "@/lib/tenant";

function setLocation(overrides: Partial<typeof window.location>) {
  Object.defineProperty(window, "location", {
    value: { ...window.location, ...overrides },
    writable: true,
    configurable: true,
  });
}

describe("getTenantUrl", () => {
  beforeEach(() => {
    delete process.env.NEXT_PUBLIC_BASE_DOMAIN;
  });

  it("builds URL with subdomain on localhost with port", () => {
    setLocation({ protocol: "http:", port: "3000", hostname: "localhost" });
    const url = getTenantUrl("acme", "/dashboard");
    expect(url).toBe("http://acme.localhost:3000/dashboard");
  });

  it("builds URL without port for standard HTTP", () => {
    setLocation({ protocol: "http:", port: "", hostname: "myapp.com" });
    process.env.NEXT_PUBLIC_BASE_DOMAIN = "myapp.com";
    const url = getTenantUrl("acme", "/dashboard");
    expect(url).toBe("http://acme.myapp.com/dashboard");
  });

  it("defaults path to /dashboard", () => {
    setLocation({ protocol: "http:", port: "3000", hostname: "localhost" });
    const url = getTenantUrl("acme");
    expect(url).toContain("/dashboard");
  });
});

describe("getCurrentTenantSlug", () => {
  beforeEach(() => {
    delete process.env.NEXT_PUBLIC_BASE_DOMAIN;
  });

  it("returns null on root localhost", () => {
    setLocation({ hostname: "localhost" });
    expect(getCurrentTenantSlug()).toBeNull();
  });

  it("returns null on root domain", () => {
    setLocation({ hostname: "myapp.com" });
    process.env.NEXT_PUBLIC_BASE_DOMAIN = "myapp.com";
    expect(getCurrentTenantSlug()).toBeNull();
  });

  it("extracts slug from subdomain", () => {
    setLocation({ hostname: "acme.localhost" });
    expect(getCurrentTenantSlug()).toBe("acme");
  });

  it("extracts slug from production subdomain", () => {
    setLocation({ hostname: "startup.myapp.com" });
    process.env.NEXT_PUBLIC_BASE_DOMAIN = "myapp.com";
    expect(getCurrentTenantSlug()).toBe("startup");
  });
});
