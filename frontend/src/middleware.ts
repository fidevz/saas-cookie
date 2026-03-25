import { NextRequest, NextResponse } from "next/server";

const PUBLIC_PATHS = ["/", "/pricing", "/support"];

const PUBLIC_PATH_PREFIXES = ["/auth/", "/legal/", "/invite/"];

const PROTECTED_PATH_PREFIXES = ["/dashboard", "/billing", "/settings"];

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

export async function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;
  const hostname = request.headers.get("host") || "";
  const baseDomain = process.env.NEXT_PUBLIC_BASE_DOMAIN || "localhost";

  // Detect root domain (with or without port)
  const rootHostnames = [
    baseDomain,
    `${baseDomain}:3000`,
    "localhost",
    "localhost:3000",
  ];
  const isRootDomain = rootHostnames.some((h) => hostname === h);

  const hasSession = request.cookies.has("auth_session");
  const tenantSlug = request.cookies.get("tenant_slug")?.value;

  // Authenticated user on root domain trying to access a protected route:
  // redirect to their tenant subdomain.
  if (isRootDomain && hasSession && tenantSlug && isProtectedPath(pathname)) {
    const port = hostname.includes(":") ? `:${hostname.split(":")[1]}` : "";
    const proto = request.nextUrl.protocol || "http:";
    const redirectUrl = `${proto}//${tenantSlug}.${baseDomain}${port}${pathname}`;
    return NextResponse.redirect(redirectUrl);
  }

  // Redirect authenticated users away from auth pages
  if (isAuthPath(pathname) && hasSession) {
    // If we know the tenant slug, go straight to their subdomain
    if (tenantSlug && isRootDomain) {
      const port = hostname.includes(":") ? `:${hostname.split(":")[1]}` : "";
      const proto = request.nextUrl.protocol || "http:";
      return NextResponse.redirect(`${proto}//${tenantSlug}.${baseDomain}${port}/dashboard`);
    }
    return NextResponse.redirect(new URL("/dashboard", request.url));
  }

  // Redirect unauthenticated users away from protected pages
  if (isProtectedPath(pathname) && !hasSession) {
    const loginUrl = new URL("/auth/login", request.url);
    loginUrl.searchParams.set("callbackUrl", pathname);
    return NextResponse.redirect(loginUrl);
  }

  return NextResponse.next();
}

export const config = {
  matcher: [
    // Match all pathnames except for static files and API routes
    "/((?!_next/static|_next/image|favicon.ico|.*\\.(?:svg|png|jpg|jpeg|gif|webp|ico|css|js)$).*)",
  ],
};
