"use client";

import React, { useState, useEffect, useRef } from "react";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { useTranslations } from "next-intl";
import { toast } from "sonner";
import { CheckCircle2, XCircle, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Separator } from "@/components/ui/separator";
import { GoogleButton } from "./google-button";
import { register, checkSlug } from "@/lib/auth";
import { getTenantUrl } from "@/lib/tenant";
import { useAuthStore } from "@/stores/auth-store";
import { api } from "@/lib/api";
import { Invitation } from "@/types";

function slugify(value: string): string {
  return value
    .toLowerCase()
    .trim()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "")
    .slice(0, 50);
}

export function RegisterForm() {
  const t = useTranslations("auth.register");
  const tCommon = useTranslations("common");
  const router = useRouter();
  const searchParams = useSearchParams();
  const { setAuth } = useAuthStore();

  const [form, setForm] = useState({
    company_name: "",
    slug: "",
    first_name: "",
    last_name: "",
    email: "",
    password: "",
  });
  const [tosAccepted, setTosAccepted] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [slugEdited, setSlugEdited] = useState(false);
  const [slugStatus, setSlugStatus] = useState<"idle" | "checking" | "available" | "taken" | "invalid">("idle");
  const [slugSuggestion, setSlugSuggestion] = useState<string | null>(null);
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const inviteToken = searchParams.get("invite_token") ?? undefined;
  const baseDomain = process.env.NEXT_PUBLIC_BASE_DOMAIN || "localhost";
  const [invitation, setInvitation] = useState<Invitation | null>(null);

  useEffect(() => {
    if (!inviteToken) return;
    api
      .get<Invitation>(`/teams/invitations/${inviteToken}/`)
      .then((inv) => {
        setInvitation(inv);
        if (inv.email) setForm((prev) => ({ ...prev, email: inv.email }));
      })
      .catch(() => {});
  }, [inviteToken]);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setForm((prev) => {
      const next = { ...prev, [name]: value };
      // Auto-populate slug from company_name unless user has manually edited it
      if (name === "company_name" && !slugEdited) {
        next.slug = slugify(value);
      }
      return next;
    });
  };

  const handleSlugChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value.toLowerCase().replace(/[^a-z0-9-]/g, "");
    setSlugEdited(true);
    setForm((prev) => ({ ...prev, slug: value }));
  };

  // Debounced slug availability check
  useEffect(() => {
    const slug = form.slug;
    if (!slug || slug.length < 3) {
      setSlugStatus("idle");
      setSlugSuggestion(null);
      return;
    }

    setSlugStatus("checking");
    if (debounceRef.current) clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(async () => {
      try {
        const result = await checkSlug(slug);
        if (result.error) {
          setSlugStatus("invalid");
        } else if (result.available) {
          setSlugStatus("available");
          setSlugSuggestion(null);
        } else {
          setSlugStatus("taken");
          setSlugSuggestion(result.suggestion ?? null);
        }
      } catch {
        setSlugStatus("idle");
      }
    }, 500);

    return () => {
      if (debounceRef.current) clearTimeout(debounceRef.current);
    };
  }, [form.slug]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!tosAccepted) {
      setError("Please accept the terms of service to continue.");
      return;
    }
    if (slugStatus === "taken" || slugStatus === "invalid") {
      setError("Please choose an available workspace URL.");
      return;
    }
    setError(null);
    setLoading(true);

    try {
      const { access, user, tenant_slug } = await register({
        ...form,
        invite_token: inviteToken,
      });
      setAuth(user, access, tenant_slug);
      toast.success(`Welcome, ${user.first_name}! Your workspace is ready.`);
      // Hard redirect to tenant subdomain
      window.location.href = getTenantUrl(tenant_slug, "/dashboard");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Registration failed");
    } finally {
      setLoading(false);
    }
  };

  const slugIndicator = () => {
    if (form.slug.length < 3) return null;
    if (slugStatus === "checking") return <Loader2 className="h-4 w-4 animate-spin text-muted-foreground" />;
    if (slugStatus === "available") return <CheckCircle2 className="h-4 w-4 text-green-500" />;
    if (slugStatus === "taken" || slugStatus === "invalid") return <XCircle className="h-4 w-4 text-destructive" />;
    return null;
  };

  return (
    <div className="flex flex-col gap-6">
      {/* Invite context banner */}
      {inviteToken && invitation?.tenant && (
        <div className="rounded-lg border border-border bg-muted/50 px-4 py-3 text-sm text-center text-muted-foreground">
          You&apos;re joining <strong className="text-foreground">{invitation.tenant.name}</strong>
        </div>
      )}

      <form onSubmit={handleSubmit} className="flex flex-col gap-4">
        {/* Workspace fields — hidden when accepting an invitation */}
        {!inviteToken && (
          <>
            {/* Workspace name */}
            <div className="flex flex-col gap-2">
              <Label htmlFor="company_name">Workspace name</Label>
              <Input
                id="company_name"
                name="company_name"
                type="text"
                placeholder="Acme Inc."
                value={form.company_name}
                onChange={handleChange}
                required
                minLength={2}
                autoFocus
              />
            </div>

            {/* Workspace URL (slug) */}
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="slug">Workspace URL</Label>
              <div className="flex items-center gap-0 rounded-md border border-input overflow-hidden focus-within:ring-2 focus-within:ring-ring">
                <span className="px-3 py-2 text-sm text-muted-foreground bg-muted border-r border-input select-none whitespace-nowrap">
                  {baseDomain}/
                </span>
                <div className="relative flex-1">
                  <Input
                    id="slug"
                    name="slug"
                    type="text"
                    placeholder="acme"
                    value={form.slug}
                    onChange={handleSlugChange}
                    required
                    minLength={3}
                    maxLength={50}
                    pattern="^[a-z0-9][a-z0-9-]{1,48}[a-z0-9]$"
                    className="border-0 focus-visible:ring-0 rounded-none pr-8"
                  />
                  <div className="absolute right-2 top-1/2 -translate-y-1/2">
                    {slugIndicator()}
                  </div>
                </div>
              </div>
              {slugStatus === "taken" && slugSuggestion && (
                <p className="text-xs text-muted-foreground">
                  Already taken.{" "}
                  <button
                    type="button"
                    className="underline text-foreground hover:text-foreground/80"
                    onClick={() => {
                      setForm((prev) => ({ ...prev, slug: slugSuggestion }));
                      setSlugEdited(true);
                    }}
                  >
                    Use &ldquo;{slugSuggestion}&rdquo; instead
                  </button>
                </p>
              )}
              {slugStatus === "invalid" && (
                <p className="text-xs text-destructive">
                  3–50 characters, lowercase letters, numbers, and hyphens only.
                </p>
              )}
              {slugStatus === "available" && (
                <p className="text-xs text-green-600">
                  {form.slug}.{baseDomain} is available
                </p>
              )}
            </div>
          </>
        )}

        {/* Name */}
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
            readOnly={!!inviteToken}
            className={inviteToken ? "bg-muted text-muted-foreground" : ""}
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

        <Button
          type="submit"
          className="w-full"
          disabled={loading || (!inviteToken && (slugStatus === "taken" || slugStatus === "invalid" || slugStatus === "checking"))}
        >
          {loading ? "Creating account..." : t("submit")}
        </Button>
      </form>

      {!inviteToken && (
        <>
          <div className="flex items-center gap-3">
            <Separator className="flex-1" />
            <span className="text-xs text-muted-foreground uppercase">
              {tCommon("or")}
            </span>
            <Separator className="flex-1" />
          </div>
          <GoogleButton />
        </>
      )}

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
