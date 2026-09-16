"use client";

import {
  PolarAngleAxis,
  PolarGrid,
  PolarRadiusAxis,
  Radar,
  RadarChart,
  ResponsiveContainer,
  Tooltip,
} from "recharts";
import { radarLabel, type CriterionMaturityPoint } from "@/features/dashboard/lib";
import type { Locale } from "@/types/api";

/**
 * Radar spidogram zrelosti po 9 kriterijuma (caf 2027.pdf — "Sponzor/Ministar
 * vidi jednopagazni dashboard sa Radar Spidogramom"). Client Component jer
 * Recharts renderuje preko browser SVG-a i koristi ResizeObserver
 * (ResponsiveContainer) — ne može biti Server Component.
 *
 * Boje: `currentColor` za natpise osa (prati Tailwind `text-*` klasu roditelja,
 * pa se automatski prilagođava svijetloj/tamnoj temi — CLAUDE.md Sekcija 6
 * traži da teme rade podjednako u oba jezika/moda), fiksna akcentna boja
 * (indigo) za samu popunjenu površinu jer mora biti čitljiva na oba pozadinska
 * tona.
 */
export function MaturityRadarChart({
  points,
  locale,
}: {
  points: CriterionMaturityPoint[];
  locale: Locale;
}) {
  const data = points.map((point) => ({
    criterion: radarLabel(point, locale),
    average: point.average,
    fullMark: 5,
  }));

  return (
    // aria-hidden: grafik je čisto vizuelan; tekstualnu alternativu (WCAG 1.1.1)
    // renderuje roditelj kao sr-only tabelu sa istim podacima.
    <div aria-hidden="true" className="h-80 w-full text-slate-600 dark:text-slate-300">
      <ResponsiveContainer width="100%" height="100%">
        <RadarChart data={data} outerRadius="75%">
          <PolarGrid stroke="#94a3b8" strokeOpacity={0.6} />
          <PolarAngleAxis
            dataKey="criterion"
            tick={{ fontSize: 11, fill: "currentColor" }}
          />
          <PolarRadiusAxis angle={90} domain={[0, 5]} tick={{ fontSize: 10 }} />
          <Radar
            name="average"
            dataKey="average"
            stroke="#6366f1"
            fill="#6366f1"
            fillOpacity={0.35}
          />
          <Tooltip
            formatter={(value) => [
              typeof value === "number" ? value.toFixed(1) : String(value ?? ""),
              locale === "en" ? "Score" : "Ocjena",
            ]}
          />
        </RadarChart>
      </ResponsiveContainer>
    </div>
  );
}
