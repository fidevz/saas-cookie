import React from "react";
import { useTranslations } from "next-intl";
import {
  ShieldCheck,
  CreditCard,
  Users,
  Building2,
  Bell,
  Globe,
} from "lucide-react";

const featureIcons = {
  auth: ShieldCheck,
  billing: CreditCard,
  teams: Users,
  multitenancy: Building2,
  notifications: Bell,
  i18n: Globe,
};

export function Features() {
  const t = useTranslations("landing.features");

  const features = Object.keys(featureIcons) as Array<keyof typeof featureIcons>;

  return (
    <section id="features" className="py-24 px-4">
      <div className="mx-auto max-w-6xl">
        {/* Section header */}
        <div className="mx-auto max-w-2xl text-center">
          <h2 className="text-3xl font-bold tracking-tight text-slate-900 sm:text-4xl">
            {t("title")}
          </h2>
          <p className="mt-4 text-base leading-relaxed text-muted-foreground">
            {t("subtitle")}
          </p>
        </div>

        {/* Feature grid */}
        <div className="mt-16 grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3">
          {features.map((key) => {
            const Icon = featureIcons[key];
            return (
              <div
                key={key}
                className="group relative rounded-xl border border-border bg-background p-6 shadow-sm transition-all duration-200 hover:shadow-md hover:-translate-y-0.5"
              >
                <div className="mb-4 inline-flex h-10 w-10 items-center justify-center rounded-lg bg-slate-900 text-white">
                  <Icon className="h-5 w-5" />
                </div>
                <h3 className="mb-2 text-base font-semibold">
                  {t(`items.${key}.title`)}
                </h3>
                <p className="text-sm leading-relaxed text-muted-foreground">
                  {t(`items.${key}.description`)}
                </p>
              </div>
            );
          })}
        </div>
      </div>
    </section>
  );
}
