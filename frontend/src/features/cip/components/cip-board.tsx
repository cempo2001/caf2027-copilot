"use client";

import * as React from "react";
import { useTranslations } from "next-intl";
import { CipItemCard } from "@/features/cip/components/cip-item-card";
import { CreateCipItemForm } from "@/features/cip/components/create-cip-item-form";
import { groupByQuadrant } from "@/features/cip/lib";
import type { CipItem, CipQuadrant, Locale } from "@/types/api";

const QUADRANT_LABEL_KEY: Record<CipQuadrant, "quadrantQuickWin" | "quadrantStrategic" | "quadrantFillIn" | "quadrantReconsider"> = {
  quick_win: "quadrantQuickWin",
  strategic: "quadrantStrategic",
  fill_in: "quadrantFillIn",
  reconsider: "quadrantReconsider",
};
const QUADRANT_HINT_KEY: Record<CipQuadrant, "quadrantQuickWinHint" | "quadrantStrategicHint" | "quadrantFillInHint" | "quadrantReconsiderHint"> = {
  quick_win: "quadrantQuickWinHint",
  strategic: "quadrantStrategicHint",
  fill_in: "quadrantFillInHint",
  reconsider: "quadrantReconsiderHint",
};

/**
 * 2x2 matrica prioritizacije (CLAUDE.md — Quick Wins vs. Strateški projekti,
 * As-Is/To-Be). Raspored: gornji red = visok uticaj (Quick Win lijevo, nizak
 * napor; Strateški desno, visok napor), donji red = nizak uticaj (Popuniti
 * lijevo, nizak napor; Preispitati desno, visok napor) — standardna
 * uticaj/napor matrica.
 */
export function CipBoard({
  sarId,
  initialItems,
  canEdit,
  locale,
}: {
  sarId: string;
  initialItems: CipItem[];
  canEdit: boolean;
  locale: Locale;
}) {
  const t = useTranslations("Cip");
  const [items, setItems] = React.useState(initialItems);
  const [openQuadrant, setOpenQuadrant] = React.useState<CipQuadrant | null>(null);
  const grouped = React.useMemo(() => groupByQuadrant(items), [items]);

  const handleCreated = (item: CipItem) => {
    setItems((current) => [...current, item]);
    setOpenQuadrant(null);
  };

  const quadrants: CipQuadrant[] = ["quick_win", "strategic", "fill_in", "reconsider"];

  return (
    <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
      {quadrants.map((quadrant) => (
        <div
          key={quadrant}
          className="space-y-3 rounded-lg border border-slate-200 p-4 dark:border-slate-800"
        >
          <div className="flex items-start justify-between gap-2">
            <div>
              <h2 className="font-semibold">{t(QUADRANT_LABEL_KEY[quadrant])}</h2>
              <p className="text-xs text-slate-500 dark:text-slate-400">{t(QUADRANT_HINT_KEY[quadrant])}</p>
            </div>
            {canEdit && openQuadrant !== quadrant && (
              <button
                type="button"
                onClick={() => setOpenQuadrant(quadrant)}
                className="rounded-md border border-slate-300 px-2 py-1 text-xs font-medium hover:bg-slate-100 dark:border-slate-700 dark:hover:bg-slate-800"
              >
                + {t("addItem")}
              </button>
            )}
          </div>

          <div className="space-y-2">
            {grouped[quadrant].length === 0 && openQuadrant !== quadrant && (
              <p className="text-xs text-slate-500 dark:text-slate-400">{t("empty")}</p>
            )}
            {grouped[quadrant].map((item) => (
              <CipItemCard key={item.id} item={item} locale={locale} />
            ))}
          </div>

          {openQuadrant === quadrant && (
            <CreateCipItemForm
              sarId={sarId}
              quadrant={quadrant}
              onCreated={handleCreated}
              onCancel={() => setOpenQuadrant(null)}
            />
          )}
        </div>
      ))}
    </div>
  );
}
