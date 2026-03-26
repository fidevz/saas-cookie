import React from "react";
import { useTranslations } from "next-intl";

const TESTIMONIALS = [
  {
    id: 1,
    name: "Sarah Chen",
    role: "CTO",
    company: "Velocity Labs",
    avatar: "SC",
    quote:
      "We went from idea to production in two weeks. The auth system, billing, and team management were all ready to go. Saved us months of work.",
  },
  {
    id: 2,
    name: "Marcus Williams",
    role: "Founder",
    company: "Shipfast",
    avatar: "MW",
    quote:
      "The multi-tenancy setup is exactly what we needed. Each customer gets their own isolated workspace. The real-time notifications are a great touch.",
  },
  {
    id: 3,
    name: "Elena Petrova",
    role: "Head of Engineering",
    company: "Cloudbase",
    avatar: "EP",
    quote:
      "Clean code, excellent TypeScript types, and a design system that actually looks professional out of the box. Highly recommend to any SaaS team.",
  },
];

export function Testimonials() {
  const t = useTranslations("landing.testimonials");
  return (
    <section className="py-24 px-4">
      <div className="mx-auto max-w-6xl">
        <div className="mx-auto max-w-2xl text-center">
          <h2 className="text-3xl font-bold tracking-tight text-slate-900 sm:text-4xl">
            {t("title")}
          </h2>
          <p className="mt-4 text-base text-muted-foreground">
            {t("subtitle")}
          </p>
        </div>

        <div className="mt-16 grid grid-cols-1 gap-6 md:grid-cols-3">
          {TESTIMONIALS.map((item) => (
            <div
              key={item.id}
              className="flex flex-col rounded-xl border border-border bg-background p-6 shadow-sm"
            >
              {/* Quote marks */}
              <div className="mb-4 text-3xl font-serif text-slate-200">&ldquo;</div>

              <p className="flex-1 text-sm leading-relaxed text-muted-foreground">
                {item.quote}
              </p>

              <div className="mt-6 flex items-center gap-3">
                <div className="flex h-9 w-9 items-center justify-center rounded-full bg-slate-900 text-xs font-semibold text-white">
                  {item.avatar}
                </div>
                <div>
                  <p className="text-sm font-medium">{item.name}</p>
                  <p className="text-xs text-muted-foreground">
                    {t("roleAt", { role: item.role, company: item.company })}
                  </p>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
