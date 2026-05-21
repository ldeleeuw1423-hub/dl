import Cookies from "js-cookie";
import { User } from "@/types";

const TOKEN_KEY = "access_token";
const USER_KEY = "user";
const COOKIE_EXPIRES = 1; // days

export function setAuthToken(token: string, user: User): void {
  Cookies.set(TOKEN_KEY, token, {
    expires: COOKIE_EXPIRES,
    secure: process.env.NODE_ENV === "production",
    sameSite: "strict",
  });
  Cookies.set(USER_KEY, JSON.stringify(user), {
    expires: COOKIE_EXPIRES,
    secure: process.env.NODE_ENV === "production",
    sameSite: "strict",
  });
}

export function getAuthToken(): string | undefined {
  return Cookies.get(TOKEN_KEY);
}

export function getStoredUser(): User | null {
  const raw = Cookies.get(USER_KEY);
  if (!raw) return null;
  try {
    return JSON.parse(raw) as User;
  } catch {
    return null;
  }
}

export function clearAuth(): void {
  Cookies.remove(TOKEN_KEY);
  Cookies.remove(USER_KEY);
}

export function isAuthenticated(): boolean {
  return !!getAuthToken();
}

export function hasRole(user: User | null, ...roles: string[]): boolean {
  if (!user) return false;
  return roles.includes(user.role);
}
