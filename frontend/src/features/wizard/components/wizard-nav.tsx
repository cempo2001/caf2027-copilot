import { getTranslations } from "next-intl/server";
import { Link } from "@/i18n/navigation";
import { cn } from "@/lib/utils";
import type { Locale, SarStatus, SubcriteriaScore } from "@/types/api";
import { groupByCriterion, isSubcriteriaComplete } from "@/features/wizard/lib";

/**
 * Bočna navigacija kroz 28 podkriterijuma, grupisana po 9 kriterijuma.
 * Čisto prikazna Server Component (samo linkovi) — ARCHITECTURE.md pravilo
 * sloja: `app/` i navigacija ne sadrže poslovnu logiku, samo je konzumiraju
 * iz `features/wizard/lib.ts`. Koristi `getTranslations` (next-intl/server),
 * ne sync `useTranslations`, radi konzistentnosti sa ostalim Server
 * Component stranicama u ovom projektu.
 */
export async function WizardNav({
  sarId,
  scores,
  currentCode,
  sarStatus,
  locale,
}: {
  sarId: string;
  scores: SubcriteriaScore[];
  currentCode: string;
  sarStatus: SarStatus;
  locale: Locale;
}) {
  const [t, tWizard] = await Promise.all([
    getTranslations({ locale, namespace: "Sar" }),
    getTranslations({ locale, namespace: "Wizard" }),
  ]);
  const groups = groupByCriterion(scores);

  return (
    <nav aria-label={tWizard("navLabel")} className="space-y-4 text-sm">
      <Link
        href={`/sar/${sarId}`}
        locale={locale}
        className="inline-flex items-center gap-1 text-slate-500 hover:text-slate-900 dark:text-slate-400 dark:hover:text-slate-100"
      >
        ← {tWizard("backToOverview")}
      </Link>

      {sarStatus === "approved" && (
        <p className="rounded-md bg-emerald-50 px-2 py-1 text-xs font-medium text-emerald-700 dark:bg-emerald-950 dark:text-emerald-300">
          {t("statusApproved")}
        </p>
      )}

      {groups.map((group) => (
        <div key={group.criterionNumber}>
          <h3 className="mb-1.5 text-xs font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-400">
            {t("criterionHeading", { number: group.criterionNumber })}
          </h3>
          <ul className="space-y-0.5">
            {group.subcriteria.map((item) => {
              const active = item.subcriteria_code === currentCode;
              const done = isSubcriteriaComplete(item);
              return (
                <li key={item.subcriteria_code}>
                  <Link
                    href={`/wizard/${item.subcriteria_code}`}
                    locale={locale}
                    className={cn(
                      "flex items-center gap-2 rounded-md px-2 py-1.5",
                      active
                        ? "bg-slate-900 text-white dark:bg-slate-100 dark:text-slate-900"
                        : "hover:bg-slate-100 dark:hover:bg-slate-800"
                    )}
                  >
                    <span
                      className={cn(
                        "size-1.5 shrink-0 rounded-full",
                        done ? "bg-emerald-500" : "bg-slate-300 dark:bg-slate-600"
                      )}
                      aria-hidden
                    />
                    <span className="sr-only">
                      {done ? tWizard("statusComplete") : tWizard("statusIncomplete")}
                    </span>
                    <span className="font-mono text-xs">{item.subcriteria_code}</span>
                    <span className="truncate">{locale === "en" ? item.name_en : item.name_me}</span>
                  </Link>
                </li>
              );
            })}
          </ul>
        </div>
      ))}
    </nav>
  );
}
