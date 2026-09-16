import { CAF_CRITERIA } from "@/features/wizard/content/caf-content";
import type { Locale, SubcriteriaScore } from "@/types/api";

export interface CriterionMaturityPoint {
  criterionNumber: number;
  nameMe: string;
  nameEn: string;
  /** Prosjek ocjena popunjenih podkriterijuma unutar kriterijuma, 0-5. */
  average: number;
  /** Koliko je od podkriterijuma unutar ovog kriterijuma ocijenjeno. */
  scoredCount: number;
  totalCount: number;
}

/**
 * Radar spidogram zahtijeva jednu tačku po SVIH 9 kriterijuma (CLAUDE.md
 * Sekcija 2 — "Vizuelizacija: Recharts... radar spidogrami"; caf 2027.pdf —
 * "Sponzor/Ministar vidi jednopagazni dashboard sa Radar Spidogramom").
 * Kriterijum bez ijednog ocijenjenog podkriterijuma i dalje dobija osu sa
 * vrijednošću 0 — spidogram mora imati svih 9 osa da bi bio čitljiv, prazna
 * osa je i sama informacija (taj dio SAR-a još nije počet).
 */
export function computeCriterionMaturity(
  scores: SubcriteriaScore[]
): CriterionMaturityPoint[] {
  const byCriterion = new Map<number, number[]>();
  const totals = new Map<number, number>();

  for (const item of scores) {
    totals.set(item.criterion_number, (totals.get(item.criterion_number) ?? 0) + 1);
    if (item.score >= 1 && item.score <= 5) {
      const list = byCriterion.get(item.criterion_number) ?? [];
      list.push(item.score);
      byCriterion.set(item.criterion_number, list);
    }
  }

  const points: CriterionMaturityPoint[] = [];
  for (let criterionNumber = 1; criterionNumber <= 9; criterionNumber += 1) {
    const criterionContent = CAF_CRITERIA[criterionNumber];
    const scored = byCriterion.get(criterionNumber) ?? [];
    const average =
      scored.length > 0
        ? Math.round((scored.reduce((sum, s) => sum + s, 0) / scored.length) * 10) / 10
        : 0;
    points.push({
      criterionNumber,
      nameMe: criterionContent?.nameMe ?? `Kriterijum ${criterionNumber}`,
      nameEn: criterionContent?.nameEn ?? `Criterion ${criterionNumber}`,
      average,
      scoredCount: scored.length,
      totalCount: totals.get(criterionNumber) ?? 0,
    });
  }
  return points;
}

/** Ukupan indeks zrelosti (0-100) — prosjek svih 9 osa preveden na procenat. */
export function computeOverallMaturityIndex(points: CriterionMaturityPoint[]): number {
  if (points.length === 0) return 0;
  const avgOf5 = points.reduce((sum, p) => sum + p.average, 0) / points.length;
  return Math.round((avgOf5 / 5) * 100);
}

export function radarLabel(point: CriterionMaturityPoint, locale: Locale): string {
  const name = locale === "en" ? point.nameEn : point.nameMe;
  return `${point.criterionNumber}. ${name}`;
}
