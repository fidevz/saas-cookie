"use client";

import { useEffect } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { useAuthStore } from "@/stores/auth-store";
import { getProfile } from "@/lib/auth";
import { toast } from "sonner";

export default function AuthCallbackPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { setAuth } = useAuthStore();

  useEffect(() => {
    const token = searchParams.get("access");
    const errorParam = searchParams.get("error");

    if (errorParam) {
      toast.error("Google authentication failed. Please try again.");
      router.push("/auth/login");
      return;
    }

    if (!token) {
      router.push("/auth/login");
      return;
    }

    // Set the access token, then fetch user profile
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
