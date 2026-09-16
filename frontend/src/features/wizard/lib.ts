import type { SubcriteriaScore } from "@/types/api";

/**
 * Čisto klijent/server-agnostičke pomoćne funkcije za navigaciju kroz 28
 * podkriterijuma (CAF okvir — 9 kriterijuma). Ne zna ništa o HTTP-u/sesiji,
 * samo o obliku podataka koje `GET /self-assessments/{id}` vrati.
 */

export interface CriterionGroup {
  criterionNumber: number;
  subcriteria: SubcriteriaScore[];
}

/** Grupiše ravnu listu od 28 stavki po `criterion_number` (1–9), sortirano. */
export function groupByCriterion(scores: SubcriteriaScore[]): CriterionGroup[] {
  const byNumber = new Map<number, SubcriteriaScore[]>();
  for (const item of scores) {
    const list = byNumber.get(item.criterion_number) ?? [];
    list.push(item);
    byNumber.set(item.criterion_number, list);
  }
  return Array.from(byNumber.entries())
    .sort(([a], [b]) => a - b)
    .map(([criterionNumber, subcriteria]) => ({
      criterionNumber,
      subcriteria: [...subcriteria].sort((a, b) =>
        a.subcriteria_code.localeCompare(b.subcriteria_code, undefined, { numeric: true })
      ),
    }));
}

/** Ravna, sortirana lista svih kodova — određuje redosljed Prethodni/Sledeći navigacije kroz čarobnjak. */
export function flattenOrderedCodes(scores: SubcriteriaScore[]): string[] {
  return groupByCriterion(scores).flatMap((group) =>
    group.subcriteria.map((s) => s.subcriteria_code)
  );
}

export function findAdjacentCodes(
  scores: SubcriteriaScore[],
  currentCode: string
): { prev: string | null; next: string | null; index: number; total: number } {
  const ordered = flattenOrderedCodes(scores);
  const index = ordered.indexOf(currentCode);
  return {
    // `?? null` — noUncheckedIndexedAccess: indeksiranje niza je `string | undefined`.
    prev: index > 0 ? (ordered[index - 1] ?? null) : null,
    next: index >= 0 && index < ordered.length - 1 ? (ordered[index + 1] ?? null) : null,
    index,
    total: ordered.length,
  };
}

/** Podkriterijum je "završen" ako ima ocjenu > 0 — koristi se za progress indikator u navigaciji. */
export function isSubcriteriaComplete(item: SubcriteriaScore): boolean {
  return item.score >= 1 && item.score <= 5;
}

export function completionStats(scores: SubcriteriaScore[]): { done: number; total: number } {
  return {
    done: scores.filter(isSubcriteriaComplete).length,
    total: scores.length,
  };
}

const MIN_RECOMMENDED_WORDS = 30;

/**
 * `text` prima i `null`/`undefined` iako kontrakt (api-contract-v1.md 4.3)
 * kaže da su `evidence_text`/`weaknesses_text` uvijek string — backend u
 * praksi vraća `null` za još-neupisan podkriterijum, pa se ovdje brani
 * defanzivno umjesto da se oslanja isključivo na tip.
 */
export function countWords(text: string | null | undefined): number {
  const trimmed = (text ?? "").trim();
  if (!trimmed) return 0;
  return trimmed.split(/\s+/).length;
}

export function isBelowRecommendedLength(text: string | null | undefined): boolean {
  return countWords(text) < MIN_RECOMMENDED_WORDS;
}

export { MIN_RECOMMENDED_WORDS };

/**
 * `useActionState` state oblik za `updateSubcriteriaAction`. Živi ovdje, ne u
 * `features/wizard/actions.ts`, jer taj fajl ima "use server" direktivu i
 * Next.js dozvoljava SAMO async funkcije kao export iz takvog fajla — obična
 * vrijednost (`INITIAL_UPDATE_STATE`) bi izazvala build grešku
 * ("A 'use server' file can only export async functions").
 */
export interface UpdateSubcriteriaState {
  status: "idle" | "success" | "error";
  errorKey: string | null;
  subcriteriaCode: string | null;
  updated?: SubcriteriaScore;
}

export const INITIAL_UPDATE_STATE: UpdateSubcriteriaState = {
  status: "idle",
  errorKey: null,
  subcriteriaCode: null,
};
