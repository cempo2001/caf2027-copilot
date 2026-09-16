"use server";

import { redirect } from "next/navigation";
import { apiClient, ApiError, NetworkError } from "@/lib/api-client";
import { createSession } from "@/lib/auth";
import type { LoginRequest, LoginResponse, Locale } from "@/types/api";

export interface LoginFormState {
  /** Stabilan error ključ za lokalizovanu poruku (Errors.* iz i18n poruka) — null kad nema greške. */
  errorKey: string | null;
  fieldErrors?: Partial<Record<"email" | "password", string>>;
}

/**
 * Server Action — jedino mjesto u frontendu koje zove `POST /auth/login`
 * (ARCHITECTURE.md Sekcija 3 — actions.ts unutar svakog features/ modula). Uspješan login
 * postavlja httpOnly session cookie (`lib/auth.ts`) i redirektuje na
 * dashboard u JEZIKU koji je korisnik izabrao na login ekranu — ne u jeziku
 * rute sa koje je došao (CLAUDE.md 6.2: izbor jezika pri loginu postaje
 * trajni claim).
 */
export async function loginAction(
  _prevState: LoginFormState,
  formData: FormData
): Promise<LoginFormState> {
  const email = String(formData.get("email") ?? "").trim();
  const password = String(formData.get("password") ?? "");
  const lang = String(formData.get("lang") ?? "me") as Locale;

  if (!email || !password) {
    return {
      errorKey: null,
      fieldErrors: {
        ...(email ? {} : { email: "required" }),
        ...(password ? {} : { password: "required" }),
      },
    };
  }

  const payload: LoginRequest = { email, password, lang };

  let response: LoginResponse;
  try {
    response = await apiClient.post<LoginResponse>("/auth/login", payload);
  } catch (err) {
    if (err instanceof ApiError) {
      return { errorKey: err.code };
    }
    if (err instanceof NetworkError) {
      return { errorKey: "network_error" };
    }
    return { errorKey: "unknown_error" };
  }

  await createSession(response);
  redirect(`/${response.user.lang}/dashboard`);
}
