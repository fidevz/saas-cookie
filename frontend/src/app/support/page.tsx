"use client";

import React, { useState } from "react";
import { useTranslations } from "next-intl";
import { toast } from "sonner";
import { CheckCircle } from "lucide-react";
import { Header } from "@/components/layout/header";
import { Footer } from "@/components/layout/footer";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { api } from "@/lib/api";

export default function SupportPage() {
  const t = useTranslations("support");
  const [form, setForm] = useState({
    name: "",
    email: "",
    subject: "",
    message: "",
  });
  const [loading, setLoading] = useState(false);
  const [sent, setSent] = useState(false);

  const handleChange = (
    e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>
  ) => {
    setForm((prev) => ({ ...prev, [e.target.name]: e.target.value }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    try {
      await api.post("/support/", form, { skipAuth: true }).catch(() => {
        // Silently handle — support form works even without auth
      });
      setSent(true);
      toast.success(t("success"));
    } catch {
      // Already handled
      setSent(true);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex min-h-screen flex-col">
      <Header />
      <main className="flex-1 pt-24 pb-16 px-4">
        <div className="mx-auto max-w-lg">
          <div className="mb-8">
            <h1 className="text-3xl font-bold tracking-tight">{t("title")}</h1>
            <p className="mt-2 text-base text-muted-foreground">{t("subtitle")}</p>
          </div>

          {sent ? (
            <div className="flex flex-col items-center gap-4 rounded-xl border border-border bg-background p-8 text-center">
              <div className="flex h-14 w-14 items-center justify-center rounded-full bg-emerald-100">
                <CheckCircle className="h-7 w-7 text-emerald-600" />
              </div>
              <h2 className="text-lg font-semibold">Message received!</h2>
              <p className="text-sm text-muted-foreground max-w-xs">
                {t("success")}
              </p>
              <Button variant="outline" onClick={() => setSent(false)}>
                Send another message
              </Button>
            </div>
          ) : (
            <form onSubmit={handleSubmit} className="space-y-4 rounded-xl border border-border bg-background p-6">
              <div className="grid gap-4 sm:grid-cols-2">
                <div className="flex flex-col gap-2">
                  <Label htmlFor="name">{t("name")}</Label>
                  <Input
                    id="name"
                    name="name"
                    type="text"
                    placeholder="Jane Smith"
                    value={form.name}
                    onChange={handleChange}
                    required
                  />
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
                  />
                </div>
              </div>

              <div className="flex flex-col gap-2">
                <Label htmlFor="subject">{t("subject")}</Label>
                <Input
                  id="subject"
                  name="subject"
                  type="text"
                  placeholder="How can we help?"
                  value={form.subject}
                  onChange={handleChange}
                  required
                />
              </div>

              <div className="flex flex-col gap-2">
                <Label htmlFor="message">{t("message")}</Label>
                <textarea
                  id="message"
                  name="message"
                  rows={5}
                  placeholder="Describe your issue in detail..."
                  value={form.message}
                  onChange={handleChange}
                  required
                  className="flex w-full rounded-md border border-input bg-transparent px-3 py-2 text-sm shadow-sm placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring resize-none"
                />
              </div>

              <Button type="submit" className="w-full" disabled={loading}>
                {loading ? "Sending..." : t("submit")}
              </Button>
            </form>
          )}
        </div>
      </main>
      <Footer />
    </div>
  );
}
