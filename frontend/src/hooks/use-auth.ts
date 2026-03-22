"use client";

import { useRouter } from "next/navigation";
import { useAuthStore } from "@/stores/auth-store";
import { login as loginFn, logout as logoutFn } from "@/lib/auth";
import { toast } from "sonner";

export function useAuth() {
  const store = useAuthStore();
  const router = useRouter();

  const login = async (email: string, password: string) => {
    const { access, user } = await loginFn(email, password);
    store.setAuth(user, access);
    toast.success(`Welcome back, ${user.first_name}!`);
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
