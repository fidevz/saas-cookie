"use client";

import { create } from "zustand";
import { Invitation, Tenant, TenantMembership } from "@/types";

interface TenantState {
  currentTenant: Tenant | null;
  members: TenantMembership[];
  invitations: Invitation[];
  currentUserRole: "admin" | "member" | null;
  setTenant: (tenant: Tenant) => void;
  setMembers: (members: TenantMembership[]) => void;
  setInvitations: (invitations: Invitation[]) => void;
  setCurrentUserRole: (role: "admin" | "member" | null) => void;
  addMember: (member: TenantMembership) => void;
  removeMember: (userId: number) => void;
  updateMemberRole: (userId: number, role: "admin" | "member") => void;
  addInvitation: (invitation: Invitation) => void;
  removeInvitation: (id: number) => void;
  reset: () => void;
}

export const useTenantStore = create<TenantState>((set) => ({
  currentTenant: null,
  members: [],
  invitations: [],
  currentUserRole: null,

  setTenant: (tenant: Tenant) => set({ currentTenant: tenant }),

  setMembers: (members: TenantMembership[]) => set({ members }),

  setInvitations: (invitations: Invitation[]) => set({ invitations }),

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

  addInvitation: (invitation: Invitation) =>
    set((state) => ({ invitations: [invitation, ...state.invitations] })),

  removeInvitation: (id: number) =>
    set((state) => ({
      invitations: state.invitations.filter((inv) => inv.id !== id),
    })),

  reset: () => set({ currentTenant: null, members: [], invitations: [], currentUserRole: null }),
}));
