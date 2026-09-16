import type { ApiErrorBody, ApiErrorCode } from "@/types/api";

/**
 * Tipizovan fetch wrapper ka FastAPI backendu (ARCHITECTURE.md Sekcija 3 —
 * `lib/api-client.ts`). Jedino mjesto u frontendu koje zna URL backenda i
 * standardni error-envelope format (api-contract-v1.md 1.2/1.3).
 *
 * Namjerno NE čita JWT iz cookie-ja/headers ovdje — token se prosleđuje
 * eksplicitno po pozivu (vidi `lib/auth.ts`), da ovaj fajl ostane bez
 * zavisnosti na `next/headers` i bude upotrebljiv i sa Server Action-a i
 * (kasnije, ako zatreba) sa client komponente.
 */

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL?.replace(/\/+$/, "") ?? "http://localhost:8765";

const API_PREFIX = "/api/v1";

export class ApiError extends Error {
  readonly status: number;
  readonly code: ApiErrorCode | (string & {});

  constructor(status: number, body: ApiErrorBody) {
    super(body.message);
    this.name = "ApiError";
    this.status = status;
    this.code = body.error;
  }
}

/** Mreža je pukla prije nego što je odgovor uopšte stigao (CLAUDE.md 3.3 — i ovo mora biti hendlovano, ne samo HTTP greške). */
export class NetworkError extends Error {
  constructor(cause: unknown) {
    super("network_error");
    this.name = "NetworkError";
    this.cause = cause;
  }
}

interface RequestOptions {
  method?: "GET" | "POST" | "PATCH" | "DELETE";
  body?: unknown;
  /** JWT iz sesije — eksplicitno prosleđen, vidi napomenu iznad. */
  token?: string;
  /** AbortSignal za otkazivanje (npr. iz React 19 useTransition tokova). */
  signal?: AbortSignal;
}

async function request<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const { method = "GET", body, token, signal } = options;

  // Multipart upload (6.1 — evidence): FormData nosi svoj Content-Type sa
  // boundary-jem, fetch to postavlja SAM. Ručno postavljanje "Content-Type"
  // za FormData bi pokvarilo boundary i backend ne bi mogao parsirati telo.
  const isFormData = typeof FormData !== "undefined" && body instanceof FormData;

  const headers: Record<string, string> = {
    Accept: "application/json",
  };
  if (body !== undefined && !isFormData) {
    headers["Content-Type"] = "application/json";
  }
  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }

  let response: Response;
  try {
    response = await fetch(`${API_BASE_URL}${API_PREFIX}${path}`, {
      method,
      headers,
      body: isFormData ? (body as FormData) : body !== undefined ? JSON.stringify(body) : undefined,
      signal,
      // Server Actions/RSC fetch keširanje je opasno za autentifikovane,
      // korisnički-specifične podatke — svaki poziv je svjež.
      cache: "no-store",
    });
  } catch (cause) {
    throw new NetworkError(cause);
  }

  if (response.status === 204) {
    return undefined as T;
  }

  const warning = response.headers.get("X-Consensus-Warning");

  let payload: unknown;
  try {
    payload = await response.json();
  } catch {
    payload = null;
  }

  if (!response.ok) {
    const errorBody: ApiErrorBody =
      payload && typeof payload === "object" && "error" in payload
        ? (payload as ApiErrorBody)
        : { error: "unknown_error", message: response.statusText };
    throw new ApiError(response.status, errorBody);
  }

  // 4.5 — AI provider nedostupan se NE tretira kao HTTP greška (status 200 +
  // warning header, source:"fallback" u telu). Wrapper ne guta upozorenje —
  // pozivalac (AI/Consensus feature) odlučuje da li ga prikazuje.
  if (warning === "ai_provider_unavailable" && typeof console !== "undefined") {
    console.warn("[api-client] ai_provider_unavailable — fallback rezultat vraćen");
  }

  return payload as T;
}

export const apiClient = {
  get: <T>(path: string, options?: Omit<RequestOptions, "method" | "body">) =>
    request<T>(path, { ...options, method: "GET" }),
  /** `body` prima i `FormData` (6.1 — multipart evidence upload) — `request()` ga tada NE JSON.stringify-uje. */
  post: <T>(path: string, body?: unknown, options?: Omit<RequestOptions, "method" | "body">) =>
    request<T>(path, { ...options, method: "POST", body }),
  patch: <T>(path: string, body?: unknown, options?: Omit<RequestOptions, "method" | "body">) =>
    request<T>(path, { ...options, method: "PATCH", body }),
  delete: <T>(path: string, options?: Omit<RequestOptions, "method" | "body">) =>
    request<T>(path, { ...options, method: "DELETE" }),
};
