"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter, useParams } from "next/navigation";
import { useTranslations } from "next-intl";
import { toast } from "sonner";
import { Header } from "@/components/layout/header";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { api } from "@/lib/api";
import { useAuthStore } from "@/stores/auth-store";
import { Invitation } from "@/types";
import { Users } from "lucide-react";

const APP_NAME = process.env.NEXT_PUBLIC_APP_NAME ?? "MyApp";

export default function InvitePage() {
  const t = useTranslations("invite");
  const params = useParams();
  const router = useRouter();
  const token = params.token as string;
  const { isAuthenticated, isLoading } = useAuthStore();

  const [invitation, setInvitation] = useState<Invitation | null>(null);
  const [fetchLoading, setFetchLoading] = useState(true);
  const [fetchError, setFetchError] = useState<string | null>(null);
  const [accepting, setAccepting] = useState(false);

  useEffect(() => {
    api
      .get<Invitation>(`/teams/invitations/${token}/`)
      .then(setInvitation)
      .catch((err: Error) => setFetchError(err.message))
      .finally(() => setFetchLoading(false));
  }, [token]);

  const handleAccept = async () => {
    if (!isAuthenticated) {
      router.push(`/auth/register?invite_token=${token}`);
      return;
    }
    setAccepting(true);
    try {
      await api.post(`/teams/accept-invite/${token}/`, {});
      toast.success("You've joined the team!");
      router.push("/dashboard");
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Failed to accept invitation");
      setAccepting(false);
    }
  };

  const isExpired =
    invitation &&
    new Date(invitation.expires_at) < new Date();

  return (
    <div className="flex min-h-screen flex-col">
      <Header />
      <main className="flex flex-1 items-center justify-center px-4 py-24">
        <div className="w-full max-w-sm">
          {fetchLoading ? (
            <Card>
              <CardHeader>
                <Skeleton className="h-5 w-40" />
                <Skeleton className="h-4 w-56 mt-1" />
              </CardHeader>
              <CardContent>
                <Skeleton className="h-9 w-full" />
              </CardContent>
            </Card>
          ) : fetchError ? (
            <Card>
              <CardContent className="flex flex-col items-center gap-4 py-8 text-center">
                <p className="text-sm text-muted-foreground">{fetchError}</p>
                <Button asChild variant="outline">
                  <Link href="/">Go home</Link>
                </Button>
              </CardContent>
            </Card>
          ) : invitation?.accepted ? (
            <Card>
              <CardContent className="flex flex-col items-center gap-4 py-8 text-center">
                <p className="text-sm font-medium">{t("alreadyMember")}</p>
                <Button asChild>
                  <Link href="/dashboard">Go to dashboard</Link>
                </Button>
              </CardContent>
            </Card>
          ) : isExpired ? (
            <Card>
              <CardContent className="flex flex-col items-center gap-4 py-8 text-center">
                <p className="text-sm text-muted-foreground">{t("expired")}</p>
                <Button asChild variant="outline">
                  <Link href="/">Go home</Link>
                </Button>
              </CardContent>
            </Card>
          ) : (
            <Card>
              <CardHeader className="text-center">
                <div className="mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-full bg-muted">
                  <Users className="h-7 w-7 text-muted-foreground" />
                </div>
                <CardTitle>{t("title")}</CardTitle>
                <CardDescription>
                  {t("subtitle", {
                    tenantName: invitation?.tenant?.name ?? "a workspace",
                    appName: APP_NAME,
                  })}
                </CardDescription>
              </CardHeader>
              <CardContent className="flex flex-col gap-3">
                {invitation && (
                  <div className="rounded-lg bg-muted/50 px-4 py-3 text-sm text-center text-muted-foreground">
                    Invitation for <strong>{invitation.email}</strong>
                  </div>
                )}
                {!isLoading && (
                  <Button onClick={handleAccept} disabled={accepting} className="w-full">
                    {accepting
                      ? "Accepting..."
                      : isAuthenticated
                      ? t("accept")
                      : "Sign up to accept"}
                  </Button>
                )}
                {!isAuthenticated && !isLoading && (
                  <Button asChild variant="outline" className="w-full">
                    <Link href={`/auth/login?callbackUrl=/invite/${token}`}>
                      Already have an account? Sign in
                    </Link>
                  </Button>
                )}
              </CardContent>
            </Card>
          )}
        </div>
      </main>
    </div>
  );
}
