"use client";

import { create } from "zustand";
import { Tenant, TenantMembership } from "@/types";

interface TenantState {
  currentTenant: Tenant | null;
  members: TenantMembership[];
  currentUserRole: "admin" | "member" | null;
  setTenant: (tenant: Tenant) => void;
  setMembers: (members: TenantMembership[]) => void;
  setCurrentUserRole: (role: "admin" | "member" | null) => void;
  addMember: (member: TenantMembership) => void;
  removeMember: (userId: number) => void;
  updateMemberRole: (userId: number, role: "admin" | "member") => void;
  reset: () => void;
}

export const useTenantStore = create<TenantState>((set) => ({
  currentTenant: null,
  members: [],
  currentUserRole: null,

  setTenant: (tenant: Tenant) => set({ currentTenant: tenant }),

  setMembers: (members: TenantMembership[]) => set({ members }),

  setCurrentUserRole: (role) => set({ currentUserRole: role }),

  addMember: (member: TenantMembership) =>
    set((state) => ({ members: [...state.members, member] })),

  removeMember: (userId: number) =>
    set((state) => ({
      members: state.members.filter((m) => m.user.id !== userId),
    })),

  updateMemberRole: (userId: number, role: "admin" | "member") =>
    set((state) => ({
      members: state.members.map((m) =>
        m.user.id === userId ? { ...m, role } : m
      ),
    })),

  reset: () => set({ currentTenant: null, members: [], currentUserRole: null }),
}));
