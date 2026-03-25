"use client";

import React, { useState } from "react";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { useTranslations } from "next-intl";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Separator } from "@/components/ui/separator";
import { GoogleButton } from "./google-button";
import { EmailVerificationGate } from "./email-verification-gate";
import { login } from "@/lib/auth";
import { getTenantUrl, getCurrentTenantSlug } from "@/lib/tenant";
import { useAuthStore } from "@/stores/auth-store";

export function LoginForm() {
  const t = useTranslations("auth.login");
  const tCommon = useTranslations("common");
  const router = useRouter();
  const searchParams = useSearchParams();
  const { setAuth } = useAuthStore();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [unverifiedEmail, setUnverifiedEmail] = useState<string | null>(null);

  const callbackUrl = searchParams.get("callbackUrl") || "/dashboard";

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);

    try {
      const { access, user, tenant_slug } = await login(email, password);
      setAuth(user, access, tenant_slug);
      toast.success(`Welcome back, ${user.first_name}!`);

      // Redirect to tenant subdomain if not already there
      if (tenant_slug && getCurrentTenantSlug() !== tenant_slug) {
        window.location.href = getTenantUrl(tenant_slug, callbackUrl);
      } else {
        router.push(callbackUrl);
      }
    } catch (err) {
      if (err instanceof Error) {
        // Backend returns {"code": "email_not_verified"} as the error message
        if (err.message.includes("email_not_verified") || err.message.includes("verify your email")) {
          setUnverifiedEmail(email);
          return;
        }
        setError(err.message);
      } else {
        setError("Login failed");
      }
    } finally {
      setLoading(false);
    }
  };

  // Show verification gate instead of login form
  if (unverifiedEmail) {
    return (
      <EmailVerificationGate
        email={unverifiedEmail}
        onBack={() => setUnverifiedEmail(null)}
      />
    );
  }

  return (
    <div className="flex flex-col gap-6">
      <form onSubmit={handleSubmit} className="flex flex-col gap-4">
        <div className="flex flex-col gap-2">
          <Label htmlFor="email">{t("email")}</Label>
          <Input
            id="email"
            type="email"
            placeholder="you@example.com"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
            autoComplete="email"
            autoFocus
          />
        </div>

        <div className="flex flex-col gap-2">
          <div className="flex items-center justify-between">
            <Label htmlFor="password">{t("password")}</Label>
            <Link
              href="/auth/forgot-password"
              tabIndex={-1}
              className="text-xs text-muted-foreground underline underline-offset-4 hover:text-foreground"
            >
              {t("forgotPassword")}
            </Link>
          </div>
          <Input
            id="password"
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
            autoComplete="current-password"
          />
        </div>

        {error && (
          <p className="rounded-md bg-destructive/10 px-3 py-2 text-sm text-destructive">
            {error}
          </p>
        )}

        <Button type="submit" className="w-full" disabled={loading}>
          {loading ? "Signing in..." : t("submit")}
        </Button>
      </form>

      <div className="flex items-center gap-3">
        <Separator className="flex-1" />
        <span className="text-xs text-muted-foreground uppercase">
          {tCommon("or")}
        </span>
        <Separator className="flex-1" />
      </div>

      <GoogleButton />

      <p className="text-center text-sm text-muted-foreground">
        {t("noAccount")}{" "}
        <Link
          href="/auth/register"
          className="font-medium text-foreground underline underline-offset-4 hover:text-foreground/80"
        >
          {t("signUp")}
        </Link>
      </p>
    </div>
  );
}
