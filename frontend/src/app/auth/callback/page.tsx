"use client";

import { Suspense, useEffect } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { useAuthStore } from "@/stores/auth-store";
import { exchangeCode, getProfile } from "@/lib/auth";
import { toast } from "sonner";

function CallbackHandler() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { setAuth } = useAuthStore();

  useEffect(() => {
    const codeParam = searchParams.get("code");
    const token = searchParams.get("access");
    const errorParam = searchParams.get("error");

    if (errorParam) {
      toast.error("Google authentication failed. Please try again.");
      router.push("/auth/login");
      return;
    }

    // Email verification flow — exchange one-time code for tokens
    if (codeParam) {
      exchangeCode(codeParam)
        .then(({ access, user }) => {
          setAuth(user, access);
          toast.success(`Welcome, ${user.first_name}!`);
          router.push("/dashboard");
        })
        .catch(() => {
          toast.error("Login code expired. Please sign in.");
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
        toast.error("Failed to load your profile. Please try again.");
        router.push("/auth/login");
      });
  }, [searchParams, setAuth, router]);

  return (
    <div className="flex min-h-screen items-center justify-center">
      <div className="flex flex-col items-center gap-4">
        <div className="h-8 w-8 animate-spin rounded-full border-2 border-slate-200 border-t-slate-900" />
        <p className="text-sm text-muted-foreground">Completing sign in...</p>
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
