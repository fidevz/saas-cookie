import createMiddleware from "next-intl/middleware";
import { NextRequest, NextResponse } from "next/server";
import { routing } from "./i18n/routing";

const intlMiddleware = createMiddleware(routing);

const PUBLIC_PATHS = [
  "/",
  "/pricing",
  "/support",
];

const PUBLIC_PATH_PREFIXES = [
  "/auth/",
  "/legal/",
  "/invite/",
];

const PROTECTED_PATH_PREFIXES = [
  "/dashboard",
  "/billing",
  "/settings",
];

function isPublicPath(pathname: string): boolean {
  if (PUBLIC_PATHS.includes(pathname)) return true;
  return PUBLIC_PATH_PREFIXES.some((prefix) => pathname.startsWith(prefix));
}

function isProtectedPath(pathname: string): boolean {
  return PROTECTED_PATH_PREFIXES.some((prefix) => pathname.startsWith(prefix));
}

function isAuthPath(pathname: string): boolean {
  return pathname.startsWith("/auth/");
}

function getAuthTokenFromCookies(request: NextRequest): string | null {
  // We check for a custom indicator cookie set by the client
  // The actual httpOnly refresh token is handled transparently
  const authIndicator = request.cookies.get("auth_session")?.value;
  return authIndicator ?? null;
}

export async function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;

  // Run next-intl middleware first
  const intlResponse = intlMiddleware(request);

  // Check auth state via cookie presence
  const hasSession = getAuthTokenFromCookies(request);

  // Redirect authenticated users away from auth pages
  if (isAuthPath(pathname) && hasSession) {
    const dashboardUrl = new URL("/dashboard", request.url);
    return NextResponse.redirect(dashboardUrl);
  }

  // Redirect unauthenticated users away from protected pages
  if (isProtectedPath(pathname) && !hasSession) {
    const loginUrl = new URL("/auth/login", request.url);
    loginUrl.searchParams.set("callbackUrl", pathname);
    return NextResponse.redirect(loginUrl);
  }

  return intlResponse;
}

export const config = {
  matcher: [
    // Match all pathnames except for static files and API routes
    "/((?!_next/static|_next/image|favicon.ico|.*\\.(?:svg|png|jpg|jpeg|gif|webp|ico|css|js)$).*)",
  ],
};
