import React from "react";
import Link from "next/link";
import { useTranslations } from "next-intl";
import { ArrowRight, Sparkles } from "lucide-react";
import { Button } from "@/components/ui/button";

export function Hero() {
  const t = useTranslations("landing.hero");

  return (
    <section className="relative flex min-h-[90vh] flex-col items-center justify-center overflow-hidden px-4 pt-16">
      {/* Background grid */}
      <div
        className="absolute inset-0 -z-10 opacity-40"
        style={{
          backgroundImage:
            "radial-gradient(circle at 1px 1px, rgb(148 163 184 / 0.4) 1px, transparent 0)",
          backgroundSize: "32px 32px",
        }}
      />
      {/* Gradient blob */}
      <div className="absolute -top-40 left-1/2 -z-10 h-80 w-80 -translate-x-1/2 rounded-full bg-slate-200 opacity-40 blur-3xl" />

      <div className="mx-auto flex max-w-3xl flex-col items-center text-center">
        {/* Badge */}
        <div className="mb-6 inline-flex items-center gap-2 rounded-full border border-border bg-background/80 px-3 py-1 text-xs font-medium text-muted-foreground shadow-sm backdrop-blur-sm">
          <Sparkles className="h-3 w-3" />
          {t("badge")}
        </div>

        {/* Headline */}
        <h1 className="text-balance text-4xl font-bold tracking-tight text-slate-900 sm:text-5xl md:text-6xl">
          {t("title")
            .split("\n")
            .map((line, i) => (
              <React.Fragment key={i}>
                {line}
                {i === 0 && <br />}
              </React.Fragment>
            ))}
        </h1>

        {/* Subtitle */}
        <p className="mt-6 max-w-xl text-balance text-base leading-relaxed text-muted-foreground sm:text-lg">
          {t("subtitle")}
        </p>

        {/* CTA buttons */}
        <div className="mt-8 flex flex-col items-center gap-3 sm:flex-row">
          <Button asChild size="lg" className="gap-2 shadow-sm">
            <Link href="/auth/register">
              {t("cta")}
              <ArrowRight className="h-4 w-4" />
            </Link>
          </Button>
          <Button asChild size="lg" variant="outline">
            <Link href="/pricing">{t("ctaSecondary")}</Link>
          </Button>
        </div>

        {/* Social proof */}
        <div className="mt-12 flex flex-col items-center gap-3">
          <p className="text-xs font-medium uppercase tracking-wider text-muted-foreground">
            {t("trustedBy")}
          </p>
          <div className="flex flex-wrap items-center justify-center gap-8">
            {["Acme", "Globex", "Initech", "Umbrella", "Hooli"].map((company) => (
              <span
                key={company}
                className="text-sm font-semibold text-slate-300"
              >
                {company}
              </span>
            ))}
          </div>
        </div>
      </div>

      {/* App screenshot mockup */}
      <div className="relative mt-16 w-full max-w-4xl">
        <div className="overflow-hidden rounded-xl border border-border bg-slate-50 shadow-2xl">
          <div className="flex h-8 items-center gap-2 border-b border-border bg-slate-100 px-4">
            <div className="h-3 w-3 rounded-full bg-red-400" />
            <div className="h-3 w-3 rounded-full bg-yellow-400" />
            <div className="h-3 w-3 rounded-full bg-green-400" />
            <div className="mx-auto w-64 rounded-md bg-white/60 px-3 py-0.5 text-center text-xs text-slate-400">
              app.yourproduct.com
            </div>
          </div>
          <div className="flex h-64 items-center justify-center">
            <div className="grid grid-cols-3 gap-4 p-6 w-full max-w-lg">
              {[1, 2, 3].map((i) => (
                <div key={i} className="rounded-lg bg-white border border-border p-4 shadow-sm">
                  <div className="h-2 w-16 rounded-full bg-slate-200 mb-2" />
                  <div className="h-6 w-12 rounded-md bg-slate-900/10 mb-1" />
                  <div className="h-1.5 w-20 rounded-full bg-slate-100" />
                </div>
              ))}
            </div>
          </div>
        </div>
        {/* Shadow glow */}
        <div className="absolute -bottom-6 left-1/2 -z-10 h-24 w-3/4 -translate-x-1/2 rounded-full bg-slate-900/10 blur-2xl" />
      </div>
    </section>
  );
}
