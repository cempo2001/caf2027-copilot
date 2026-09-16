"use server";

import { revalidatePath } from "next/cache";
import { apiClient, ApiError, NetworkError } from "@/lib/api-client";
import { requireAccessToken } from "@/lib/auth";
import type { UpdateSubcriteriaState } from "@/features/wizard/lib";
import type { AiConsensusResponse, SubcriteriaScore, UpdateSubcriteriaRequest } from "@/types/api";

/**
 * Server Actions za Vođeni Čarobnjak (ARCHITECTURE.md Sekcija 3 —
 * `features/wizard/actions.ts`). Dvije operacije, obje protiv jednog
 * podkriterijuma: čuvanje unosa (4.4, mora hendlovati 409 Approved Lock) i
 * AI/Consensus predlog (4.5, human-in-the-loop — CLAUDE.md Sekcija 7.5:
 * predlog se NIKAD ne upisuje automatski, korisnik ga eksplicitno prihvata
 * na klijentu prije nego što se uopšte pozove `updateSubcriteriaAction`).
 *
 * VAŽNO: fajl sa "use server" direktivom smije izvoziti SAMO async funkcije
 * (Next.js runtime ograničenje) — zato `UpdateSubcriteriaState` tip i
 * `INITIAL_UPDATE_STATE` konstanta žive u `features/wizard/lib.ts`, ne ovdje.
 */

export async function updateSubcriteriaAction(
  _prevState: UpdateSubcriteriaState,
  formData: FormData
): Promise<UpdateSubcriteriaState> {
  const sarId = String(formData.get("sarId") ?? "");
  const code = String(formData.get("subcriteriaCode") ?? "");
  const evidenceText = String(formData.get("evidence_text") ?? "");
  const weaknessesText = String(formData.get("weaknesses_text") ?? "");
  const score = Number(formData.get("score"));

  if (!sarId || !code) {
    return { status: "error", errorKey: "unknown_error", subcriteriaCode: code || null };
  }
  if (!Number.isInteger(score) || score < 1 || score > 5) {
    return { status: "error", errorKey: "validation_error", subcriteriaCode: code };
  }

  const payload: UpdateSubcriteriaRequest = {
    evidence_text: evidenceText,
    weaknesses_text: weaknessesText,
    score,
  };

  try {
    const token = await requireAccessToken();
    const updated = await apiClient.patch<SubcriteriaScore>(
      `/self-assessments/${sarId}/subcriteria/${code}`,
      payload,
      { token }
    );
    // Osvježava server-renderovane stranice (wizard step + SAR pregled) da
    // prikažu novi quality_flag i napredak bez punog reload-a. Koristi se
    // dinamički route TEMPLATE (Next.js "page" revalidation mode) — URL
    // OBLIK, ne fajl-sistem putanja, zato BEZ "(institution)" route grupe
    // (route grupe se ne pojavljuju u URL-u). Briše keš za sve
    // [locale]/[subcriteriaId]/[sarId] kombinacije, jer server action ne zna
    // koji je konkretan locale pozvao.
    revalidatePath("/[locale]/wizard/[subcriteriaId]", "page");
    revalidatePath("/[locale]/sar/[sarId]", "page");
    return { status: "success", errorKey: null, subcriteriaCode: code, updated };
  } catch (err) {
    if (err instanceof ApiError) {
      return { status: "error", errorKey: err.code, subcriteriaCode: code };
    }
    if (err instanceof NetworkError) {
      return { status: "error", errorKey: "network_error", subcriteriaCode: code };
    }
    return { status: "error", errorKey: "unknown_error", subcriteriaCode: code };
  }
}

export type AiConsensusResult =
  | { ok: true; data: AiConsensusResponse }
  | { ok: false; errorKey: string };

/**
 * Poziva se direktno iz client komponente (React 19 `useTransition`), ne kao
 * `<form action>` — AI predlog ne mijenja stanje na serveru, samo vraća
 * podatke koje korisnik vidi i eksplicitno prihvata ili odbacuje.
 */
export async function requestAiConsensusAction(
  sarId: string,
  subcriteriaCode: string
): Promise<AiConsensusResult> {
  try {
    const token = await requireAccessToken();
    const data = await apiClient.post<AiConsensusResponse>(
      `/self-assessments/${sarId}/subcriteria/${subcriteriaCode}/ai-consensus`,
      undefined,
      { token }
    );
    return { ok: true, data };
  } catch (err) {
    if (err instanceof ApiError) {
      return { ok: false, errorKey: err.code };
    }
    if (err instanceof NetworkError) {
      return { ok: false, errorKey: "network_error" };
    }
    return { ok: false, errorKey: "unknown_error" };
  }
}
