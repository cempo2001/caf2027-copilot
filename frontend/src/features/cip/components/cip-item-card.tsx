import { useTranslations } from "next-intl";
import { cn } from "@/lib/utils";
import type { CipItem, CipStatus, Locale } from "@/types/api";

const STATUS_CLASSES: Record<CipStatus, string> = {
  planned: "bg-slate-100 text-slate-600 dark:bg-slate-800 dark:text-slate-300",
  in_progress: "bg-amber-100 text-amber-800 dark:bg-amber-950 dark:text-amber-300",
  done: "bg-emerald-100 text-emerald-800 dark:bg-emerald-950 dark:text-emerald-300",
};

export function CipItemCard({ item, locale }: { item: CipItem; locale: Locale }) {
  const t = useTranslations("Cip");
  const statusLabel =
    item.status === "done"
      ? t("statusDone")
      : item.status === "in_progress"
        ? t("statusInProgress")
        : t("statusPlanned");

  return (
    <div className="rounded-md border border-slate-200 bg-white p-3 text-sm dark:border-slate-800 dark:bg-slate-900">
      <div className="flex items-start justify-between gap-2">
        <p className="font-medium">{locale === "en" ? item.title_en : item.title_me}</p>
        <span className={cn("shrink-0 rounded-full px-2 py-0.5 text-xs font-medium", STATUS_CLASSES[item.status])}>
          {statusLabel}
        </span>
      </div>
      <dl className="mt-2 space-y-1 text-xs text-slate-500 dark:text-slate-400">
        <div>
          <dt className="inline font-medium">{t("asIsLabel")}: </dt>
          <dd className="inline">{item.as_is}</dd>
        </div>
        <div>
          <dt className="inline font-medium">{t("toBeLabel")}: </dt>
          <dd className="inline">{item.to_be}</dd>
        </div>
      </dl>
    </div>
  );
}
