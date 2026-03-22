import React from "react";
import Link from "next/link";
import { useTranslations } from "next-intl";
import { ArrowRight } from "lucide-react";
import { Button } from "@/components/ui/button";

export function CTA() {
  const t = useTranslations("landing.cta");

  return (
    <section className="px-4 py-24">
      <div className="mx-auto max-w-4xl">
        <div className="relative overflow-hidden rounded-2xl bg-slate-900 px-8 py-16 text-center shadow-2xl">
          {/* Background pattern */}
          <div
            className="absolute inset-0 opacity-10"
            style={{
              backgroundImage:
                "radial-gradient(circle at 1px 1px, white 1px, transparent 0)",
              backgroundSize: "24px 24px",
            }}
          />
          {/* Gradient blob */}
          <div className="absolute top-0 left-1/2 -translate-x-1/2 h-64 w-64 rounded-full bg-white/5 blur-3xl" />

          <div className="relative">
            <h2 className="text-3xl font-bold tracking-tight text-white sm:text-4xl">
              {t("title")}
            </h2>
            <p className="mt-4 text-base text-slate-400">{t("subtitle")}</p>
            <div className="mt-8">
              <Button
                asChild
                size="lg"
                className="bg-white text-slate-900 hover:bg-slate-100 gap-2"
              >
                <Link href="/auth/register">
                  {t("button")}
                  <ArrowRight className="h-4 w-4" />
                </Link>
              </Button>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
