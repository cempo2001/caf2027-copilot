"use server";

import { apiClient, ApiError, NetworkError } from "@/lib/api-client";
import { requireAccessToken } from "@/lib/auth";
import type { CipItem, CipListResponse, CipQuadrant, CreateCipItemRequest } from "@/types/api";

/**
 * Server Actions za CIP akcioni plan (api-contract-v1.md Sekcija 5).
 * Backend: `backend/src/caf/api/v1/cip.py`. Kreiranje je dozvoljeno samo
 * ulogama SAG tima (403 insufficient_role za Employee) i samo dok SAR nije
 * zaključan (409 sar_locked).
 */

export async function listCipItems(sarId: string): Promise<CipItem[]> {
  const token = await requireAccessToken();
  const { items } = await apiClient.get<CipListResponse>(`/self-assessments/${sarId}/cip`, {
    token,
  });
  return items;
}

export type CipActionResult<T> = { ok: true; data: T } | { ok: false; errorKey: string };

export interface CreateCipItemFormInput {
  sarId: string;
  titleMe: string;
  titleEn: string;
  quadrant: CipQuadrant;
  asIs: string;
  toBe: string;
}

export async function createCipItemAction(
  input: CreateCipItemFormInput
): Promise<CipActionResult<CipItem>> {
  const payload: CreateCipItemRequest = {
    title_me: input.titleMe,
    title_en: input.titleEn,
    quadrant: input.quadrant,
    as_is: input.asIs,
    to_be: input.toBe,
  };

  try {
    const token = await requireAccessToken();
    const data = await apiClient.post<CipItem>(`/self-assessments/${input.sarId}/cip`, payload, {
      token,
    });
    return { ok: true, data };
  } catch (err) {
    if (err instanceof ApiError) return { ok: false, errorKey: err.code };
    if (err instanceof NetworkError) return { ok: false, errorKey: "network_error" };
    return { ok: false, errorKey: "unknown_error" };
  }
}
