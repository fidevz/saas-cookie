import { describe, it, expect, beforeEach } from "vitest";
import { useTenantStore } from "../tenant-store";
import type { Tenant, TenantMembership, User } from "@/types";

const mockTenant: Tenant = { id: 1, name: "Acme Corp", slug: "acme" };

const mockUser: User = {
  id: 1,
  email: "alice@acme.com",
  first_name: "Alice",
  last_name: "Smith",
  is_first_login: false, tenant_slug: null,
};

const mockUser2: User = {
  id: 2,
  email: "bob@acme.com",
  first_name: "Bob",
  last_name: "Jones",
  is_first_login: false, tenant_slug: null,
};

const mockMember: TenantMembership = {
  id: 1,
  user: mockUser,
  tenant: mockTenant,
  role: "admin",
};

const mockMember2: TenantMembership = {
  id: 2,
  user: mockUser2,
  tenant: mockTenant,
  role: "member",
};

describe("useTenantStore", () => {
  beforeEach(() => {
    useTenantStore.setState({ currentTenant: null, members: [] });
  });

  it("setTenant stores the tenant", () => {
    useTenantStore.getState().setTenant(mockTenant);
    expect(useTenantStore.getState().currentTenant).toEqual(mockTenant);
  });

  it("setMembers replaces the members list", () => {
    useTenantStore.getState().setMembers([mockMember, mockMember2]);
    expect(useTenantStore.getState().members).toHaveLength(2);
  });

  it("addMember appends a member", () => {
    useTenantStore.getState().setMembers([mockMember]);
    useTenantStore.getState().addMember(mockMember2);
    expect(useTenantStore.getState().members).toHaveLength(2);
    expect(useTenantStore.getState().members[1]).toEqual(mockMember2);
  });

  it("removeMember removes by user id", () => {
    useTenantStore.getState().setMembers([mockMember, mockMember2]);
    useTenantStore.getState().removeMember(1);
    const { members } = useTenantStore.getState();
    expect(members).toHaveLength(1);
    expect(members[0].user.id).toBe(2);
  });

  it("removeMember with unknown id does not change list", () => {
    useTenantStore.getState().setMembers([mockMember]);
    useTenantStore.getState().removeMember(999);
    expect(useTenantStore.getState().members).toHaveLength(1);
  });

  it("updateMemberRole changes the role of the specified user", () => {
    useTenantStore.getState().setMembers([mockMember, mockMember2]);
    useTenantStore.getState().updateMemberRole(1, "member");
    const { members } = useTenantStore.getState();
    expect(members.find((m) => m.user.id === 1)?.role).toBe("member");
    expect(members.find((m) => m.user.id === 2)?.role).toBe("member");
  });

  it("reset clears tenant and members", () => {
    useTenantStore.getState().setTenant(mockTenant);
    useTenantStore.getState().setMembers([mockMember]);
    useTenantStore.getState().reset();
    const state = useTenantStore.getState();
    expect(state.currentTenant).toBeNull();
    expect(state.members).toHaveLength(0);
  });
});
