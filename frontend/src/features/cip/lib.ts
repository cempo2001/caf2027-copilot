import type { CipItem, CipQuadrant } from "@/types/api";

/** Redosljed kvadranata u 2x2 mreži — CLAUDE.md: "Quick Wins vs. Strateški projekti", As-Is/To-Be. */
export const QUADRANTS: readonly CipQuadrant[] = [
  "quick_win",
  "strategic",
  "fill_in",
  "reconsider",
];

export function groupByQuadrant(items: CipItem[]): Record<CipQuadrant, CipItem[]> {
  const grouped: Record<CipQuadrant, CipItem[]> = {
    quick_win: [],
    strategic: [],
    fill_in: [],
    reconsider: [],
  };
  for (const item of items) {
    grouped[item.quadrant].push(item);
  }
  return grouped;
}
