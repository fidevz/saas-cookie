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
import { register } from "@/lib/auth";
import { useAuthStore } from "@/stores/auth-store";

export function RegisterForm() {
  const t = useTranslations("auth.register");
  const tCommon = useTranslations("common");
  const router = useRouter();
  const searchParams = useSearchParams();
  const { setAuth } = useAuthStore();

  const [form, setForm] = useState({
    first_name: "",
    last_name: "",
    email: "",
    password: "",
  });
  const [tosAccepted, setTosAccepted] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const inviteToken = searchParams.get("invite_token") ?? undefined;

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setForm((prev) => ({ ...prev, [e.target.name]: e.target.value }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!tosAccepted) {
      setError("Please accept the terms of service to continue.");
      return;
    }
    setError(null);
    setLoading(true);

    try {
      const { access, user } = await register({
        ...form,
        invite_token: inviteToken,
      });
      setAuth(user, access);
      toast.success(`Welcome, ${user.first_name}!`);
      router.push("/dashboard");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Registration failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex flex-col gap-6">
      <form onSubmit={handleSubmit} className="flex flex-col gap-4">
        <div className="grid grid-cols-2 gap-3">
          <div className="flex flex-col gap-2">
            <Label htmlFor="first_name">{t("firstName")}</Label>
            <Input
              id="first_name"
              name="first_name"
              type="text"
              placeholder="Jane"
              value={form.first_name}
              onChange={handleChange}
              required
              autoFocus
            />
          </div>
          <div className="flex flex-col gap-2">
            <Label htmlFor="last_name">{t("lastName")}</Label>
            <Input
              id="last_name"
              name="last_name"
              type="text"
              placeholder="Smith"
              value={form.last_name}
              onChange={handleChange}
              required
            />
          </div>
        </div>

        <div className="flex flex-col gap-2">
          <Label htmlFor="email">{t("email")}</Label>
          <Input
            id="email"
            name="email"
            type="email"
            placeholder="you@example.com"
            value={form.email}
            onChange={handleChange}
            required
            autoComplete="email"
          />
        </div>

        <div className="flex flex-col gap-2">
          <Label htmlFor="password">{t("password")}</Label>
          <Input
            id="password"
            name="password"
            type="password"
            value={form.password}
            onChange={handleChange}
            required
            autoComplete="new-password"
            minLength={8}
          />
        </div>

        <div className="flex items-start gap-3">
          <input
            id="tos"
            type="checkbox"
            checked={tosAccepted}
            onChange={(e) => setTosAccepted(e.target.checked)}
            className="mt-0.5 h-4 w-4 rounded border-border"
          />
          <label htmlFor="tos" className="text-xs text-muted-foreground leading-relaxed">
            {t("terms")}{" "}
            <Link
              href="/legal/tos"
              className="font-medium text-foreground underline underline-offset-4"
            >
              {t("termsLink")}
            </Link>{" "}
            {t("and")}{" "}
            <Link
              href="/legal/privacy"
              className="font-medium text-foreground underline underline-offset-4"
            >
              {t("privacyLink")}
            </Link>
          </label>
        </div>

        {error && (
          <p className="rounded-md bg-destructive/10 px-3 py-2 text-sm text-destructive">
            {error}
          </p>
        )}

        <Button type="submit" className="w-full" disabled={loading}>
          {loading ? "Creating account..." : t("submit")}
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
        {t("haveAccount")}{" "}
        <Link
          href="/auth/login"
          className="font-medium text-foreground underline underline-offset-4 hover:text-foreground/80"
        >
          {t("signIn")}
        </Link>
      </p>
    </div>
  );
}
