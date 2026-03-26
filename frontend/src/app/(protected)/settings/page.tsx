"use client";

import React, { useState } from "react";
import { toast } from "sonner";
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useAuthStore } from "@/stores/auth-store";
import { api } from "@/lib/api";
import { User } from "@/types";

export default function SettingsPage() {
  const { user, setUser } = useAuthStore();

  const [form, setForm] = useState({
    first_name: user?.first_name ?? "",
    last_name: user?.last_name ?? "",
  });
  const [saving, setSaving] = useState(false);

  const [showEmailForm, setShowEmailForm] = useState(false);
  const [emailForm, setEmailForm] = useState({ new_email: "", password: "" });
  const [changingEmail, setChangingEmail] = useState(false);

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    try {
      const updated = await api.patch<User>("/users/me/", form);
      setUser(updated);
      toast.success("Settings saved.");
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Failed to save settings");
    } finally {
      setSaving(false);
    }
  };

  const handleEmailChange = async (e: React.FormEvent) => {
    e.preventDefault();
    setChangingEmail(true);
    try {
      await api.post("/users/me/email/", emailForm);
      toast.success(`Verification email sent to ${emailForm.new_email}. Check your inbox.`);
      setShowEmailForm(false);
      setEmailForm({ new_email: "", password: "" });
      const updated = await api.get<User>("/users/me/");
      setUser(updated);
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Failed to initiate email change");
    } finally {
      setChangingEmail(false);
    }
  };

  return (
    <div className="mx-auto max-w-2xl space-y-6 animate-fade-in">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Settings</h1>
        <p className="mt-1 text-sm text-muted-foreground">
          Manage your account settings and preferences.
        </p>
      </div>

      {/* Profile settings */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Profile</CardTitle>
          <CardDescription>Update your personal information.</CardDescription>
        </CardHeader>
        <form onSubmit={handleSave}>
          <CardContent className="space-y-4">
            <div className="grid gap-4 sm:grid-cols-2">
              <div className="flex flex-col gap-2">
                <Label htmlFor="first_name">First name</Label>
                <Input
                  id="first_name"
                  name="first_name"
                  value={form.first_name}
                  onChange={(e) => setForm((p) => ({ ...p, first_name: e.target.value }))}
                />
              </div>
              <div className="flex flex-col gap-2">
                <Label htmlFor="last_name">Last name</Label>
                <Input
                  id="last_name"
                  name="last_name"
                  value={form.last_name}
                  onChange={(e) => setForm((p) => ({ ...p, last_name: e.target.value }))}
                />
              </div>
            </div>
            <div className="flex flex-col gap-2">
              <Label>Email</Label>
              <div className="flex items-center gap-3">
                <Input value={user?.email ?? ""} readOnly className="bg-muted text-muted-foreground" />
                <Button type="button" variant="outline" size="sm" onClick={() => setShowEmailForm((v) => !v)}>
                  Change
                </Button>
              </div>
              {user?.pending_email && (
                <p className="text-xs text-amber-600">
                  Pending change to <strong>{user.pending_email}</strong> — check that inbox to confirm.
                </p>
              )}
            </div>
          </CardContent>
          <CardFooter className="border-t border-border pt-6">
            <Button type="submit" disabled={saving}>
              {saving ? "Saving..." : "Save changes"}
            </Button>
          </CardFooter>
        </form>
      </Card>

      {/* Email change form — separate card, never nested inside the profile form */}
      {showEmailForm && (
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Change email address</CardTitle>
            <CardDescription>We&apos;ll send a verification link to your new address.</CardDescription>
          </CardHeader>
          <form onSubmit={handleEmailChange}>
            <CardContent className="space-y-4">
              <div className="flex flex-col gap-2">
                <Label htmlFor="new_email">New email</Label>
                <Input
                  id="new_email"
                  type="email"
                  required
                  value={emailForm.new_email}
                  onChange={(e) => setEmailForm((p) => ({ ...p, new_email: e.target.value }))}
                />
              </div>
              <div className="flex flex-col gap-2">
                <Label htmlFor="current_password">Current password</Label>
                <Input
                  id="current_password"
                  type="password"
                  required
                  value={emailForm.password}
                  onChange={(e) => setEmailForm((p) => ({ ...p, password: e.target.value }))}
                />
              </div>
            </CardContent>
            <CardFooter className="border-t border-border pt-6 gap-2">
              <Button type="submit" disabled={changingEmail}>
                {changingEmail ? "Sending..." : "Send verification"}
              </Button>
              <Button
                type="button"
                variant="ghost"
                onClick={() => { setShowEmailForm(false); setEmailForm({ new_email: "", password: "" }); }}
              >
                Cancel
              </Button>
            </CardFooter>
          </form>
        </Card>
      )}

      {/* Danger zone */}
      <Card className="border-destructive/30">
        <CardHeader>
          <CardTitle className="text-base text-destructive">Danger zone</CardTitle>
          <CardDescription>Irreversible actions for your account.</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-between rounded-lg border border-destructive/30 bg-destructive/5 p-4">
            <div>
              <p className="text-sm font-medium">Delete account</p>
              <p className="text-xs text-muted-foreground mt-0.5">
                Permanently delete your account and all associated data.
              </p>
            </div>
            <Button
              variant="destructive"
              size="sm"
              onClick={() => toast.error("Please contact support to delete your account.")}
            >
              Delete account
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
