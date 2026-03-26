"use client";

import React, { useState, Suspense } from "react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { useTranslations } from "next-intl";
import { toast } from "sonner";
import { Mail, ArrowLeft } from "lucide-react";
import { Button } from "@/components/ui/button";
import { resendVerificationEmail } from "@/lib/auth";

function CheckEmailContent() {
  const t = useTranslations("auth.checkEmail");
  const searchParams = useSearchParams();
  const email = searchParams.get("email") ?? "";
  const [resending, setResending] = useState(false);

  const handleResend = async () => {
    if (!email) return;
    setResending(true);
    try {
      await resendVerificationEmail(email);
      toast.success(t("resent"));
    } catch {
      toast.error("Failed to resend. Please try again.");
    } finally {
      setResending(false);
    }
  };

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
          <p className="mt-1 text-sm text-muted-foreground">{t("subtitle")}</p>
        </div>

        <div className="flex flex-col items-center gap-5 rounded-xl border border-border bg-background p-8 text-center">
          <div className="flex h-14 w-14 items-center justify-center rounded-full bg-blue-100">
            <Mail className="h-7 w-7 text-blue-600" />
          </div>

          <div className="space-y-1">
            {email && (
              <p className="text-sm font-medium">
                We sent a link to <strong>{email}</strong>
              </p>
            )}
            <p className="text-sm text-muted-foreground">{t("body")}</p>
          </div>

          <Button
            className="w-full"
            onClick={handleResend}
            disabled={resending || !email}
          >
            {resending ? "Sending..." : t("resend")}
          </Button>
        </div>

        <div className="mt-6 text-center">
          <Link
            href="/auth/login"
            className="inline-flex items-center gap-1.5 text-sm text-muted-foreground hover:text-foreground"
          >
            <ArrowLeft className="h-3.5 w-3.5" />
            {t("backToLogin")}
          </Link>
        </div>
      </div>
    </div>
  );
}

export default function CheckEmailPage() {
  return (
    <Suspense>
      <CheckEmailContent />
    </Suspense>
  );
}
