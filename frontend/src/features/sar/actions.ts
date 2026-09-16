"use server";

import { apiClient, ApiError, NetworkError } from "@/lib/api-client";
import { requireAccessToken } from "@/lib/auth";
import type {
  ApproveSarResponse,
  Paginated,
  SarDetail,
  SarListItem,
} from "@/types/api";

/**
 * Server Actions za SAR (Self-Assessment Report) — jedino mjesto koje zove
 * self-assessments rute (ARCHITECTURE.md Sekcija 3). Wizard i Sar feature-i
 * dijele ove funkcije umjesto da svaki duplira fetch logiku.
 */

export async function listSelfAssessments(): Promise<Paginated<SarListItem>> {
  const token = await requireAccessToken();
  return apiClient.get<Paginated<SarListItem>>("/self-assessments", { token });
}

export async function getSelfAssessment(sarId: string): Promise<SarDetail> {
  const token = await requireAccessToken();
  return apiClient.get<SarDetail>(`/self-assessments/${sarId}`, { token });
}

export async function createSelfAssessment(): Promise<SarListItem> {
  const token = await requireAccessToken();
  return apiClient.post<SarListItem>("/self-assessments", undefined, { token });
}

/**
 * Nalazi aktivnu (ne-odobrenu) samoprocjenu institucije, ili null ako ne
 * postoji. Ne kreira automatski — kreiranje je eksplicitna akcija korisnika
 * (`createSelfAssessment`), jer je to CAFLead/Sponsor odluka (4.2), ne nešto
 * što se dešava tiho u pozadini kad Employee samo otvori stranicu.
 */
export async function getActiveSar(): Promise<SarDetail | null> {
  const { items } = await listSelfAssessments();
  const active = items.find((item) => item.status !== "approved") ?? items[0] ?? null;
  if (!active) return null;
  return getSelfAssessment(active.id);
}

export async function approveSelfAssessment(sarId: string): Promise<ApproveSarResponse> {
  const token = await requireAccessToken();
  return apiClient.post<ApproveSarResponse>(`/self-assessments/${sarId}/approve`, undefined, {
    token,
  });
}

/**
 * Diskriminovani rezultat umjesto bacanja greške na klijent — pozivaoci
 * (client komponente preko `useTransition`) prikazuju lokalizovanu poruku
 * bez try/catch oko Server Action poziva (Next.js server-action greške
 * inače stižu na klijent kao generički Error, bez `error` koda).
 */
export type SarActionResult<T> = { ok: true; data: T } | { ok: false; errorKey: string };

export async function createSarAction(): Promise<SarActionResult<SarListItem>> {
  try {
    const data = await createSelfAssessment();
    return { ok: true, data };
  } catch (err) {
    if (err instanceof ApiError) return { ok: false, errorKey: err.code };
    if (err instanceof NetworkError) return { ok: false, errorKey: "network_error" };
    return { ok: false, errorKey: "unknown_error" };
  }
}

export async function approveSarAction(
  sarId: string
): Promise<SarActionResult<ApproveSarResponse>> {
  try {
    const data = await approveSelfAssessment(sarId);
    return { ok: true, data };
  } catch (err) {
    if (err instanceof ApiError) return { ok: false, errorKey: err.code };
    if (err instanceof NetworkError) return { ok: false, errorKey: "network_error" };
    return { ok: false, errorKey: "unknown_error" };
  }
}
