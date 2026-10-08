import { API_V1 } from "./config";

const TOKEN_KEY = "clearview_session_token";
export interface AuthUser {
  user_id: string;
  email: string;
  full_name: string | null;
  role: string;
  workspace_id: string;
  business_name: string;
  token?: string | null;
}

export interface TeamMember {
  id: string; email: string; full_name: string | null; role: string;
  joined_at: string; is_current_user: boolean;
}
export interface PendingInvitation {
  id: string; email: string; role: "manager" | "viewer"; expires_at: string; expired: boolean;
}
export interface TeamSnapshot { members: TeamMember[]; invitations: PendingInvitation[] }

export const getAuthToken = () => localStorage.getItem(TOKEN_KEY);
export const saveAuthToken = (token: string) => localStorage.setItem(TOKEN_KEY, token);
export const clearAuthToken = () => localStorage.removeItem(TOKEN_KEY);

export async function authenticatedFetch(input: RequestInfo | URL, init: RequestInit = {}) {
  const headers = new Headers(init.headers);
  const token = getAuthToken();
  if (token) headers.set("Authorization", `Bearer ${token}`);
  return fetch(input, { ...init, headers });
}

export async function login(email: string, password: string): Promise<AuthUser> {
  const response = await fetch(`${API_V1}/auth/login`, {
    method: "POST", headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
  });
  const data = await response.json();
  if (!response.ok) throw new Error(data.detail || "Could not log in.");
  saveAuthToken(data.token);
  return data;
}

export async function signup(input: { business_name: string; full_name: string; email: string; password: string }): Promise<AuthUser> {
  const response = await fetch(`${API_V1}/auth/signup`, {
    method: "POST", headers: { "Content-Type": "application/json" },
    body: JSON.stringify(input),
  });
  const data = await response.json();
  if (!response.ok) throw new Error(data.detail || "Could not create your company account.");
  saveAuthToken(data.token);
  return data;
}

export async function getCurrentUser(): Promise<AuthUser> {
  const response = await authenticatedFetch(`${API_V1}/auth/me`);
  if (!response.ok) throw new Error("Your session has expired.");
  return response.json();
}

export async function logout() {
  await authenticatedFetch(`${API_V1}/auth/logout`, { method: "POST" }).catch(() => undefined);
  clearAuthToken();
}

async function authJson<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await authenticatedFetch(`${API_V1}/auth${path}`, init);
  const body = response.status === 204 ? null : await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(body?.detail || "Could not update company access.");
  return body as T;
}

export const fetchTeam = () => authJson<TeamSnapshot>("/team");
export const createInvitation = (email: string, role: "manager" | "viewer") => authJson<{
  id: string; email: string; role: string; expires_at: string; invitation_url: string; email_sent: boolean;
}>("/invitations", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ email, role }) });
export const revokeInvitation = (id: string) => authJson<void>(`/invitations/${id}`, { method: "DELETE" });
export const updateTeamRole = (id: string, role: "manager" | "viewer") => authJson<{ id: string; role: string }>(`/team/${id}/role`, {
  method: "PATCH", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ role }),
});
export const removeTeamMember = (id: string) => authJson<void>(`/team/${id}`, { method: "DELETE" });

export async function getInvitationPreview(token: string) {
  const response = await fetch(`${API_V1}/auth/invitations/preview?token=${encodeURIComponent(token)}`);
  const body = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(body.detail || "This invitation is invalid or has expired.");
  return body as { email: string; role: string; business_name: string; expires_at: string };
}

export async function acceptInvitation(token: string, password: string, full_name: string) {
  const response = await fetch(`${API_V1}/auth/invitations/accept`, {
    method: "POST", headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ token, password, full_name }),
  });
  const body = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(body.detail || "Could not accept this invitation.");
  saveAuthToken(body.token);
  return body as AuthUser;
}
