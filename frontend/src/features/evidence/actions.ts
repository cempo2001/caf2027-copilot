"use server";

import { apiClient, ApiError, NetworkError } from "@/lib/api-client";
import { requireAccessToken } from "@/lib/auth";
import type { UploadEvidenceState } from "@/features/evidence/lib";
import type { EvidenceUploadResponse } from "@/types/api";

/**
 * Vault & Documents agent — upload dokaza (api-contract-v1.md 6.1).
 * Multipart polje je `file` (kontrakt, dopuna 16.9.2026). Limit veličine
 * Server Action tijela je podignut u next.config.ts (`bodySizeLimit`).
 *
 * VAŽNO: "use server" fajl smije izvoziti SAMO async funkcije — zato
 * `UploadEvidenceState`/`INITIAL_UPLOAD_STATE` žive u `features/evidence/lib.ts`
 * (isti razlog kao u features/wizard/actions.ts).
 */
export async function uploadEvidenceAction(
  _prevState: UploadEvidenceState,
  formData: FormData
): Promise<UploadEvidenceState> {
  const sarId = String(formData.get("sarId") ?? "");
  const code = String(formData.get("subcriteriaCode") ?? "");
  const file = formData.get("file");

  if (!sarId || !code) {
    return { status: "error", errorKey: "unknown_error" };
  }
  if (!(file instanceof File) || file.size === 0) {
    return { status: "error", errorKey: "validation_error" };
  }

  const outbound = new FormData();
  outbound.append("file", file, file.name);

  try {
    const token = await requireAccessToken();
    const data = await apiClient.post<EvidenceUploadResponse>(
      `/self-assessments/${sarId}/subcriteria/${code}/evidence`,
      outbound,
      { token }
    );
    return { status: "success", errorKey: null, result: data };
  } catch (err) {
    if (err instanceof ApiError) {
      return { status: "error", errorKey: err.code, httpStatus: err.status };
    }
    if (err instanceof NetworkError) {
      return { status: "error", errorKey: "network_error" };
    }
    return { status: "error", errorKey: "unknown_error" };
  }
}
