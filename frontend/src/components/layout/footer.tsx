import React from "react";
import Link from "next/link";
import { useTranslations } from "next-intl";

const APP_NAME = process.env.NEXT_PUBLIC_APP_NAME ?? "MyApp";

export function Footer() {
  const t = useTranslations("nav");
  const tFooter = useTranslations("footer");

  return (
    <footer className="border-t border-border bg-background">
      <div className="container mx-auto max-w-6xl px-4 py-12">
        <div className="grid grid-cols-1 gap-8 md:grid-cols-4">
          {/* Brand */}
          <div className="md:col-span-1">
            <Link href="/" className="flex items-center gap-2">
              <div className="flex h-7 w-7 items-center justify-center rounded-md bg-slate-900">
                <span className="text-xs font-bold text-white">
                  {APP_NAME.charAt(0)}
                </span>
              </div>
              <span className="text-sm font-semibold">{APP_NAME}</span>
            </Link>
            <p className="mt-3 text-sm text-muted-foreground leading-relaxed">
              {tFooter("tagline")}
            </p>
          </div>

          {/* Product */}
          <div>
            <h3 className="mb-3 text-sm font-semibold">{tFooter("product")}</h3>
            <ul className="space-y-2">
              <li>
                <Link
                  href="/#features"
                  className="text-sm text-muted-foreground transition-colors hover:text-foreground"
                >
                  {t("features")}
                </Link>
              </li>
              <li>
                <Link
                  href="/pricing"
                  className="text-sm text-muted-foreground transition-colors hover:text-foreground"
                >
                  {t("pricing")}
                </Link>
              </li>
            </ul>
          </div>

          {/* Legal */}
          <div>
            <h3 className="mb-3 text-sm font-semibold">{tFooter("legal")}</h3>
            <ul className="space-y-2">
              <li>
                <Link
                  href="/legal/tos"
                  className="text-sm text-muted-foreground transition-colors hover:text-foreground"
                >
                  {tFooter("legalTos")}
                </Link>
              </li>
              <li>
                <Link
                  href="/legal/privacy"
                  className="text-sm text-muted-foreground transition-colors hover:text-foreground"
                >
                  {tFooter("legalPrivacy")}
                </Link>
              </li>
              <li>
                <Link
                  href="/legal/cookies"
                  className="text-sm text-muted-foreground transition-colors hover:text-foreground"
                >
                  {tFooter("legalCookies")}
                </Link>
              </li>
            </ul>
          </div>

          {/* Support */}
          <div>
            <h3 className="mb-3 text-sm font-semibold">{tFooter("support")}</h3>
            <ul className="space-y-2">
              <li>
                <Link
                  href="/support"
                  className="text-sm text-muted-foreground transition-colors hover:text-foreground"
                >
                  {tFooter("contactUs")}
                </Link>
              </li>
            </ul>
          </div>
        </div>

        <div className="mt-12 flex flex-col items-center justify-between gap-4 border-t border-border pt-8 md:flex-row">
          <p className="text-sm text-muted-foreground">
            &copy; {new Date().getFullYear()} {APP_NAME}. {tFooter("allRightsReserved")}
          </p>
          <div className="flex items-center gap-4">
            <Link
              href="/legal/tos"
              className="text-xs text-muted-foreground hover:text-foreground"
            >
              {tFooter("terms")}
            </Link>
            <Link
              href="/legal/privacy"
              className="text-xs text-muted-foreground hover:text-foreground"
            >
              {tFooter("privacy")}
            </Link>
            <Link
              href="/legal/cookies"
              className="text-xs text-muted-foreground hover:text-foreground"
            >
              {tFooter("cookies")}
            </Link>
          </div>
        </div>
      </div>
    </footer>
  );
}
