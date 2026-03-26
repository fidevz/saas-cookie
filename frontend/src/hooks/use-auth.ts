"use client";

import { useRouter } from "next/navigation";
import { useTranslations } from "next-intl";
import { useAuthStore } from "@/stores/auth-store";
import { login as loginFn, logout as logoutFn } from "@/lib/auth";
import { toast } from "sonner";

export function useAuth() {
  const t = useTranslations("auth.login");
  const store = useAuthStore();
  const router = useRouter();

  const login = async (email: string, password: string) => {
    const { access, user } = await loginFn(email, password);
    store.setAuth(user, access);
    toast.success(t("welcomeBack", { name: user.first_name }));
    router.push("/dashboard");
  };

  const logout = async () => {
    await logoutFn();
    store.logout();
    router.push("/auth/login");
  };

  return {
    user: store.user,
    isAuthenticated: store.isAuthenticated,
    isLoading: store.isLoading,
    login,
    logout,
  };
}
