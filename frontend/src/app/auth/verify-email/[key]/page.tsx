"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { useTranslations } from "next-intl";
import { CheckCircle, XCircle, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { verifyEmail } from "@/lib/auth";
import { getTenantUrl } from "@/lib/tenant";

type State = "loading" | "success" | "error";

export default function VerifyEmailPage() {
  const t = useTranslations("auth.verifyEmail");
  const params = useParams<{ key: string }>();
  const router = useRouter();
  const [state, setState] = useState<State>("loading");
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [loginCode, setLoginCode] = useState<string | null>(null);
  const [verifyTenantSlug, setVerifyTenantSlug] = useState<string | null>(null);

  // Effect 1 — verify the key and capture the one-time login code.
  useEffect(() => {
    const key = decodeURIComponent(params.key);
    if (!key) {
      setState("error");
      setErrorMessage(t("invalidLink"));
      return;
    }

    verifyEmail(key)
      .then((res) => {
        setState("success");
        setLoginCode(res.code);
        setVerifyTenantSlug(res.tenant_slug);
      })
      .catch((err) => {
        setState("error");
        setErrorMessage(
          err instanceof Error ? err.message : t("expiredLink")
        );
      });
  }, [params.key]);

  // Effect 2 — once the code is ready, redirect to the callback page which
  // exchanges it for real tokens. The code travels in the URL but is opaque,
  // single-use, and expires in 60 seconds — no bearer token is ever in the URL.
  useEffect(() => {
    if (!loginCode) return;

    const callbackPath = `/auth/callback?code=${loginCode}`;

    if (verifyTenantSlug) {
      window.location.href = getTenantUrl(verifyTenantSlug, callbackPath);
    } else {
      router.push(callbackPath);
    }
  }, [loginCode, verifyTenantSlug, router]);

  return (
    <div className="flex min-h-screen items-center justify-center px-4 py-12">
      <div className="w-full max-w-sm">
        <div className="mb-8 text-center">
          <Link href="/" className="inline-flex items-center gap-2">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-slate-900">
              <span className="text-sm font-bold text-white">
                {(process.env.NEXT_PUBLIC_APP_NAME ?? "M").charAt(0)}
              </span>
            </div>
          </Link>
          <h1 className="mt-4 text-2xl font-bold tracking-tight">{t("title")}</h1>
        </div>

        <div className="flex flex-col items-center gap-4 rounded-xl border border-border bg-background p-8 text-center">
          {state === "loading" && (
            <>
              <Loader2 className="h-10 w-10 animate-spin text-muted-foreground" />
              <p className="text-sm text-muted-foreground">{t("verifying")}</p>
            </>
          )}

          {state === "success" && (
            <>
              <div className="flex h-14 w-14 items-center justify-center rounded-full bg-emerald-100">
                <CheckCircle className="h-7 w-7 text-emerald-600" />
              </div>
              <div>
                <p className="font-semibold">{t("verified")}</p>
                <p className="mt-1 text-sm text-muted-foreground">
                  {t("verifiedDescription")}
                </p>
              </div>
              <Loader2 className="h-5 w-5 animate-spin text-muted-foreground" />
            </>
          )}

          {state === "error" && (
            <>
              <div className="flex h-14 w-14 items-center justify-center rounded-full bg-destructive/10">
                <XCircle className="h-7 w-7 text-destructive" />
              </div>
              <div>
                <p className="font-semibold">{t("failed")}</p>
                <p className="mt-1 text-sm text-muted-foreground">
                  {errorMessage ?? t("failedDescription")}
                </p>
              </div>
              <Button asChild className="w-full">
                <Link href="/auth/login">{t("backToSignIn")}</Link>
              </Button>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
