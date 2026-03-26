"use client";

import { Suspense, useEffect } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { useTranslations } from "next-intl";
import { useAuthStore } from "@/stores/auth-store";
import { exchangeCode, getProfile } from "@/lib/auth";
import { toast } from "sonner";

function CallbackHandler() {
  const t = useTranslations("auth.callback");
  const router = useRouter();
  const searchParams = useSearchParams();
  const { setAuth } = useAuthStore();

  useEffect(() => {
    const codeParam = searchParams.get("code");
    const token = searchParams.get("access");
    const errorParam = searchParams.get("error");

    if (errorParam) {
      toast.error(t("googleFailed"));
      router.push("/auth/login");
      return;
    }

    // Email verification flow — exchange one-time code for tokens
    if (codeParam) {
      exchangeCode(codeParam)
        .then(({ access, user }) => {
          setAuth(user, access);
          toast.success(t("welcome", { name: user.first_name }));
          router.push("/dashboard");
        })
        .catch(() => {
          toast.error(t("loginExpired"));
          router.push("/auth/login");
        });
      return;
    }

    // Google OAuth flow — direct access token in URL
    if (!token) {
      router.push("/auth/login");
      return;
    }

    useAuthStore.getState().setAccessToken(token);
    getProfile()
      .then((user) => {
        setAuth(user, token);
        toast.success(`Welcome, ${user.first_name}!`);
        router.push("/dashboard");
      })
      .catch(() => {
        toast.error(t("profileFailed"));
        router.push("/auth/login");
      });
  }, [searchParams, setAuth, router]);

  return (
    <div className="flex min-h-screen items-center justify-center">
      <div className="flex flex-col items-center gap-4">
        <div className="h-8 w-8 animate-spin rounded-full border-2 border-slate-200 border-t-slate-900" />
        <p className="text-sm text-muted-foreground">{t("completingSignIn")}</p>
      </div>
    </div>
  );
}

export default function AuthCallbackPage() {
  return (
    <Suspense
      fallback={
        <div className="flex min-h-screen items-center justify-center">
          <div className="h-8 w-8 animate-spin rounded-full border-2 border-slate-200 border-t-slate-900" />
        </div>
      }
    >
      <CallbackHandler />
    </Suspense>
  );
}
