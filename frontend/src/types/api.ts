/**
 * Ručno sinhronizovani tipovi sa `docs/api-contract-v1.md` (ARCHITECTURE.md
 * Sekcija 5 — kontrakt piše Chief Architect prije koda; Frontend agent gradi
 * protiv ovog fajla, ne čeka gotov backend). Kad FastAPI počne generisati
 * stvaran OpenAPI, ovaj fajl se zamjenjuje generisanim tipovima — do tada je
 * ovo izvor istine na frontendu.
 */

export type Locale = "me" | "en";

export type UserRole = "sponsor" | "caf_lead" | "cae_team_member" | "employee";

export type SarStatus = "draft" | "submitted" | "approved";

export type QualityFlag = "ok" | "too_short" | "too_generic" | null;

export type CipQuadrant = "quick_win" | "strategic" | "fill_in" | "reconsider";

export type CipStatus = "planned" | "in_progress" | "done";

// --- 1.2 Standardni format greške -----------------------------------------

/** Stabilni mašinski ključevi grešaka (api-contract-v1.md 1.2, 1.3). */
export type ApiErrorCode =
  | "invalid_credentials"
  | "invalid_token"
  | "tenant_mismatch"
  | "not_found"
  | "sar_locked"
  | "sar_incomplete"
  | "insufficient_role"
  | "unknown_subcriteria"
  | "validation_error"
  | "ai_provider_unavailable"
  | "consensus_needs_evidence"
  | "evidence_infected"
  | "evidence_too_large"
  | "evidence_type_not_allowed"
  | "av_scanner_unavailable"
  | "storage_unavailable"
  | "network_error"
  | "unknown_error";

export interface ApiErrorBody {
  error: ApiErrorCode | (string & {});
  message: string;
}

// --- 1.4 Paginacija ---------------------------------------------------------

export interface Paginated<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
}

// --- 2. Auth -----------------------------------------------------------------

export interface LoginRequest {
  email: string;
  password: string;
  lang: Locale;
}

export interface UserOut {
  id: string;
  email: string;
  role: UserRole;
  institution_id: string;
  lang: Locale;
}

export interface LoginResponse {
  access_token: string;
  token_type: "bearer";
  expires_in: number;
  user: UserOut;
}

// --- 3. Institutions -----------------------------------------------------------

export interface InstitutionMe {
  id: string;
  name_me: string;
  name_en: string;
  sag_members_count: number;
  maturity_status: "in_progress" | "caf_user" | null;
}

// --- 4. Self-Assessments (SAR) --------------------------------------------------

export interface SarListItem {
  id: string;
  status: SarStatus;
  created_at: string;
  approved_at: string | null;
}

export interface SubcriteriaScore {
  subcriteria_code: string;
  criterion_number: number;
  name_me: string;
  name_en: string;
  score: number;
  evidence_text: string;
  weaknesses_text: string;
  quality_flag: QualityFlag;
}

export interface SarDetail {
  id: string;
  status: SarStatus;
  approved_at: string | null;
  approved_by: string | null;
  subcriteria_scores: SubcriteriaScore[];
}

export interface UpdateSubcriteriaRequest {
  evidence_text: string;
  weaknesses_text: string;
  score: number;
}

export interface AiConsensusResponse {
  suggested_score: number;
  suggested_summary_text: string;
  source: "ai" | "fallback";
  requires_human_confirmation: true;
  /** Ocjena po PDCA fazi (Enableri) ili dimenziji rezultata — samo za `source: "fallback"`. */
  breakdown?: Record<string, number>;
}

export interface ApproveSarResponse {
  id: string;
  status: "approved";
  approved_at: string;
  approved_by: string;
}

// --- 5. CIP Akcioni plan ----------------------------------------------------

export interface CipItem {
  id: string;
  title_me: string;
  title_en: string;
  quadrant: CipQuadrant;
  as_is: string;
  to_be: string;
  status: CipStatus;
}

/** 5.1 odgovor nema paginaciju (za razliku od 1.4) — samo `items`, po kontraktu. */
export interface CipListResponse {
  items: CipItem[];
}

/** 5.2 request body — api-contract-v1.md (dopuna 16.9.2026). */
export interface CreateCipItemRequest {
  title_me: string;
  title_en: string;
  quadrant: CipQuadrant;
  as_is: string;
  to_be: string;
}

// --- 6. Evidence (MinIO) -----------------------------------------------------

export type AvScanStatus = "clean" | "infected" | "pending";

export interface EvidenceUploadResponse {
  id: string;
  filename: string;
  sha256: string;
  av_scan_status: AvScanStatus;
}
