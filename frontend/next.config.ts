import type { NextConfig } from "next";
import createNextIntlPlugin from "next-intl/plugin";

const withNextIntl = createNextIntlPlugin("./src/i18n/request.ts");

const isDev = process.env.NODE_ENV === "development";

const nextConfig: NextConfig = {
  output: "standalone",
  // Preserve trailing slashes so Django's APPEND_SLASH doesn't reject POSTs.
  skipTrailingSlashRedirect: true,
  // Proxy /api/v1/* to the Django backend so cookies are same-origin.
  // Only active when INTERNAL_API_URL is set (local dev).
  // In production, NEXT_PUBLIC_API_URL points directly to the API domain.
  async rewrites() {
    const internalApiUrl = process.env.INTERNAL_API_URL;
    if (!internalApiUrl) return [];
    return [
      {
        source: "/api/v1/:path*/",
        destination: `${internalApiUrl}/api/v1/:path*/`,
      },
      {
        source: "/api/v1/:path*",
        destination: `${internalApiUrl}/api/v1/:path*`,
      },
    ];
  },
  async headers() {
    return [
      {
        source: "/(.*)",
        headers: [
          { key: "X-Frame-Options", value: "DENY" },
          { key: "X-Content-Type-Options", value: "nosniff" },
          { key: "Referrer-Policy", value: "strict-origin-when-cross-origin" },
          {
            key: "Content-Security-Policy",
            value: isDev
              ? "default-src 'self'; script-src 'self' 'unsafe-eval' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data: https: http:; connect-src 'self' ws: wss: http: https:;"
              : "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data: https:; connect-src 'self' wss: https:;",
          },
        ],
      },
    ];
  },
};

export default withNextIntl(nextConfig);
