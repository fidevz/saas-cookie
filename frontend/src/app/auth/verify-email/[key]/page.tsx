"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { CheckCircle, XCircle, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { verifyEmail } from "@/lib/auth";

type State = "loading" | "success" | "error";

export default function VerifyEmailPage() {
  const params = useParams<{ key: string }>();
  const router = useRouter();
  const [state, setState] = useState<State>("loading");
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  useEffect(() => {
    const key = params.key;
    if (!key) {
      setState("error");
      setErrorMessage("Invalid verification link.");
      return;
    }

    verifyEmail(key)
      .then(() => {
        setState("success");
        setTimeout(() => router.push("/auth/login"), 3000);
      })
      .catch((err) => {
        setState("error");
        setErrorMessage(
          err instanceof Error ? err.message : "Invalid or expired verification link."
        );
      });
  }, [params.key, router]);

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
          <h1 className="mt-4 text-2xl font-bold tracking-tight">Email Verification</h1>
        </div>

        <div className="flex flex-col items-center gap-4 rounded-xl border border-border bg-background p-8 text-center">
          {state === "loading" && (
            <>
              <Loader2 className="h-10 w-10 animate-spin text-muted-foreground" />
              <p className="text-sm text-muted-foreground">Verifying your email address…</p>
            </>
          )}

          {state === "success" && (
            <>
              <div className="flex h-14 w-14 items-center justify-center rounded-full bg-emerald-100">
                <CheckCircle className="h-7 w-7 text-emerald-600" />
              </div>
              <div>
                <p className="font-semibold">Email verified!</p>
                <p className="mt-1 text-sm text-muted-foreground">
                  Your account is now active. Redirecting to sign in…
                </p>
              </div>
              <Button asChild className="w-full" variant="outline">
                <Link href="/auth/login">Sign in now</Link>
              </Button>
            </>
          )}

          {state === "error" && (
            <>
              <div className="flex h-14 w-14 items-center justify-center rounded-full bg-destructive/10">
                <XCircle className="h-7 w-7 text-destructive" />
              </div>
              <div>
                <p className="font-semibold">Verification failed</p>
                <p className="mt-1 text-sm text-muted-foreground">
                  {errorMessage ?? "This link may have expired or already been used."}
                </p>
              </div>
              <Button asChild className="w-full">
                <Link href="/auth/login">Back to sign in</Link>
              </Button>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
