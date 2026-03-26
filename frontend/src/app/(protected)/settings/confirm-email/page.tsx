"use client";

import { useEffect, useRef } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import { toast } from "sonner";
import { api } from "@/lib/api";
import { useAuthStore } from "@/stores/auth-store";
import { User } from "@/types";

export default function ConfirmEmailPage() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const { setAccessToken, setUser } = useAuthStore();
  const fired = useRef(false);

  useEffect(() => {
    if (fired.current) return;
    fired.current = true;

    const token = searchParams.get("token");
    if (!token) {
      toast.error("Invalid confirmation link.");
      router.replace("/settings");
      return;
    }

    api
      .post<{ detail: string; access: string; user: User }>(
        "/users/me/email/confirm/",
        { token },
        { skipAuth: true }
      )
      .then((data) => {
        setAccessToken(data.access);
        setUser(data.user);
        toast.success("Email updated successfully.");
        router.replace("/settings");
      })
      .catch((err) => {
        toast.error(err instanceof Error ? err.message : "Confirmation failed.");
        router.replace("/settings");
      });
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return null;
}
