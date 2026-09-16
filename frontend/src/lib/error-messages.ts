import type { ApiErrorCode } from "@/types/api";

/**
 * Poznati ključevi u i18n poruci "Errors" (vidi i18n/messages/{me,en}.json).
 * Zajednička lista za sve feature komponente koje prikazuju grešku sa
 * backenda — izbjegava next-intl `t.has()` (nesigurno preko verzija
 * biblioteke, vidi incident u features/auth/components/login-form.tsx).
 */
const KNOWN_ERROR_KEYS: ReadonlySet<string> = new Set<ApiErrorCode>([
  "invalid_credentials",
  "invalid_token",
  "tenant_mismatch",
  "sar_locked",
  "sar_incomplete",
  "insufficient_role",
  "unknown_subcriteria",
  "not_found",
  "validation_error",
  "ai_provider_unavailable",
  "consensus_needs_evidence",
  "evidence_infected",
  "evidence_too_large",
  "evidence_type_not_allowed",
  "av_scanner_unavailable",
  "storage_unavailable",
  "network_error",
  "unknown_error",
]);

/** Vraća lokalizovanu poruku za dati error ključ preko next-intl `t` funkcije iz "Errors" namespace-a, sa fallback-om na "unknown_error". */
export function resolveErrorMessage(t: (key: never) => string, key: string | null | undefined): string {
  const safeKey = key && KNOWN_ERROR_KEYS.has(key) ? key : "unknown_error";
  return t(safeKey as never);
}
