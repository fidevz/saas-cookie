"use client";

import React, { useEffect, useState } from "react";
import { Mail, RefreshCw } from "lucide-react";
import { useTranslations } from "next-intl";
import { Button } from "@/components/ui/button";
import { resendVerificationEmail } from "@/lib/auth";
import { toast } from "sonner";

const COOLDOWN_SECONDS = 300; // 5 minutes
const STORAGE_KEY = "email_verification_sent_at";

/** Read remaining cooldown seconds from localStorage (client-side only). */
function getRemainingSeconds(): number {
  if (typeof window === "undefined") return 0;
  const raw = localStorage.getItem(STORAGE_KEY);
  if (!raw) return 0;
  const sentAt = parseInt(raw, 10);
  if (isNaN(sentAt)) return 0;
  const elapsed = Math.floor((Date.now() - sentAt) / 1000);
  return Math.max(0, COOLDOWN_SECONDS - elapsed);
}

interface Props {
  email: string;
  onBack: () => void;
}

export function EmailVerificationGate({ email, onBack }: Props) {
  const t = useTranslations("auth.emailVerificationGate");
  // Start with COOLDOWN_SECONDS as a conservative initial value to avoid a
  // flash of the enabled button before localStorage is read in the effect.
  const [secondsLeft, setSecondsLeft] = useState(COOLDOWN_SECONDS);
  const [sending, setSending] = useState(false);
  const [initialized, setInitialized] = useState(false);

  // Initialize countdown from localStorage (runs only on the client after mount)
  useEffect(() => {
    setSecondsLeft(getRemainingSeconds());
    setInitialized(true);
  }, []);

  // Tick
  useEffect(() => {
    if (secondsLeft <= 0) return;
    const timer = setInterval(() => {
      setSecondsLeft((s) => {
        if (s <= 1) {
          clearInterval(timer);
          return 0;
        }
        return s - 1;
      });
    }, 1000);
    return () => clearInterval(timer);
  }, [secondsLeft]);

  const formatCountdown = (s: number) => {
    const m = Math.floor(s / 60);
    const sec = s % 60;
    return `${m}:${sec.toString().padStart(2, "0")}`;
  };

  const handleResend = async () => {
    setSending(true);
    try {
      await resendVerificationEmail(email);
      if (typeof window !== "undefined") {
        localStorage.setItem(STORAGE_KEY, Date.now().toString());
      }
      setSecondsLeft(COOLDOWN_SECONDS);
      toast.success(t("sent"));
    } catch {
      toast.error(t("failed"));
    } finally {
      setSending(false);
    }
  };

  return (
    <div className="flex flex-col items-center text-center space-y-6 py-4">
      <div className="flex h-16 w-16 items-center justify-center rounded-full bg-primary/10">
        <Mail className="h-8 w-8 text-primary" />
      </div>

      <div className="space-y-2">
        <h2 className="text-xl font-semibold tracking-tight">{t("title")}</h2>
        <p className="text-sm text-muted-foreground max-w-xs">
          {t("description", { email })}
        </p>
      </div>

      <div className="flex flex-col gap-3 w-full">
        <Button
          onClick={handleResend}
          disabled={!initialized || secondsLeft > 0 || sending}
          variant="outline"
          className="w-full"
        >
          <RefreshCw className={`mr-2 h-4 w-4 ${sending ? "animate-spin" : ""}`} />
          {secondsLeft > 0
            ? t("resendIn", { time: formatCountdown(secondsLeft) })
            : sending
            ? t("sending")
            : t("resend")}
        </Button>

        <Button variant="ghost" onClick={onBack} className="w-full text-muted-foreground">
          {t("differentAccount")}
        </Button>
      </div>

      <p className="text-xs text-muted-foreground">
        {t("checkSpam")}
      </p>
    </div>
  );
}
