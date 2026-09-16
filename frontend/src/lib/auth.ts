import "server-only";

import { cookies } from "next/headers";
import { ApiError } from "@/lib/api-client";
import type { LoginResponse, UserOut } from "@/types/api";

/**
 * Session/JWT handling na frontendu (ARCHITECTURE.md Sekcija 3 — `lib/auth.ts`).
 * Token se čuva u httpOnly, Secure cookie-ju — NIKAD u localStorage (XSS
 * površina) i NIKAD čitljiv iz client komponenti direktno; do njega dolaze
 * samo Server Actions/Server Components preko ove datoteke (CLAUDE.md
 * Sekcija 3, pravilo 4 — Security by Design).
 */

const SESSION_COOKIE = "caf_session";

interface SessionCookiePayload {
  access_token: string;
  expires_at: number; // epoch seconds
  user: UserOut;
}

export async function createSession(login: LoginResponse): Promise<void> {
  const store = await cookies();
  const payload: SessionCookiePayload = {
    access_token: login.access_token,
    expires_at: Math.floor(Date.now() / 1000) + login.expires_in,
    user: login.user,
  };

  store.set(SESSION_COOKIE, JSON.stringify(payload), {
    httpOnly: true,
    secure: process.env.NODE_ENV === "production",
    sameSite: "lax",
    path: "/",
    maxAge: login.expires_in,
  });
}

export async function getSession(): Promise<SessionCookiePayload | null> {
  const store = await cookies();
  const raw = store.get(SESSION_COOKIE)?.value;
  if (!raw) return null;

  try {
    const payload = JSON.parse(raw) as SessionCookiePayload;
    if (payload.expires_at * 1000 <= Date.now()) {
      return null; // istekao — tretiramo kao odjavljen, ne bacamo grešku ovdje
    }
    return payload;
  } catch {
    return null;
  }
}

export async function getAccessToken(): Promise<string | null> {
  const session = await getSession();
  return session?.access_token ?? null;
}

export async function getCurrentUser(): Promise<UserOut | null> {
  const session = await getSession();
  return session?.user ?? null;
}

export async function destroySession(): Promise<void> {
  const store = await cookies();
  store.delete(SESSION_COOKIE);
}

/**
 * Zajednički helper za `features/*\/actions.ts` — vraća token ili baca
 * `ApiError(401)` koju pozivaoci već znaju da mapiraju na `invalid_token`
 * poruku (isti pattern kao svaka druga greška sa backend-a).
 */
export async function requireAccessToken(): Promise<string> {
  const token = await getAccessToken();
  if (!token) {
    throw new ApiError(401, { error: "invalid_token", message: "invalid_token" });
  }
  return token;
}
