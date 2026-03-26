export interface User {
  id: number;
  email: string;
  pending_email?: string;
  first_name: string;
  last_name: string;
  is_first_login: boolean;
  tenant_slug: string | null;
  theme: "system" | "light" | "dark";
}

export interface Tenant {
  id: number;
  name: string;
  slug: string;
}

export interface TenantMembership {
  id: number;
  user: User;
  tenant: Tenant;
  role: "admin" | "member";
}

export interface Plan {
  id: number;
  name: string;
  amount: number;
  currency: string;
  interval: "month" | "year";
  trial_days: number;
  features: string[] | Record<string, boolean>;
  capabilities: Record<string, boolean | number | null>;
  stripe_publishable_key?: string;
}

export interface Subscription {
  id: number;
  plan: Plan;
  status: "trialing" | "active" | "cancelling" | "cancelled" | "past_due" | "unpaid";
  /** Snapshot of plan capabilities at subscription time. Use this for access control. */
  capabilities: Record<string, boolean | number | null>;
  current_period_start: string;
  current_period_end: string;
  trial_end: string | null;
  cancelled_at: string | null;
}

export interface Invitation {
  id: number;
  email: string;
  role: "admin" | "member";
  token: string;
  expires_at: string;
  accepted: boolean;
  created_at?: string;
  tenant?: Tenant;
}

export interface Notification {
  id: number;
  type: "welcome" | "info" | "warning" | "error";
  title: string;
  body: string;
  read: boolean;
  created_at: string;
}

export interface FeatureFlags {
  TEAMS: boolean;
  BILLING: boolean;
  NOTIFICATIONS: boolean;
  REQUIRE_SUBSCRIPTION: boolean;
}

export interface PaginatedResponse<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}

export interface ApiError {
  detail?: string;
  [key: string]: string | string[] | undefined;
}

export interface RegisterData {
  company_name: string;
  slug: string;
  email: string;
  password: string;
  first_name: string;
  last_name: string;
  invite_token?: string;
}
