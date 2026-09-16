import { notFound } from "next/navigation";
import { getTranslations } from "next-intl/server";
import { Link } from "@/i18n/navigation";
import { isSupportedLocale } from "@/i18n/routing";
import { getSession } from "@/lib/auth";
import { getActiveSar } from "@/features/sar/actions";
import { CreateSarButton } from "@/features/sar/components/create-sar-button";
import { completionStats } from "@/features/wizard/lib";
import { computeCriterionMaturity, computeOverallMaturityIndex } from "@/features/dashboard/lib";
import { MaturityRadarChart } from "@/features/dashboard/components/maturity-radar-chart";
import { buttonVariants } from "@/components/ui/button";

/**
 * Dashboard je ulazna tačka u SAR tok (CLAUDE.md Faza 1 izlaz — "jedna
 * institucija može kompletno sprovesti SAR proces od unosa do Approved
 * Lock-a") I jednopagazni pregled zrelosti za Sponsora/Ministra (radar
 * spidogram — caf 2027.pdf, Role-Based UI princip). Employee/CAETeamMember
 * vide samo progres traku — radar je namijenjen ulogama koje odlučuju, ne
 * onima koji unose pojedinačne podkriterijume.
 */
export default async function DashboardPage({
  params,
}: {
  params: Promise<{ locale: string }>;
}) {
  const { locale: rawLocale } = await params;
  if (!isSupportedLocale(rawLocale)) notFound();
  const locale = rawLocale;

  const [session, sar, t, tSar] = await Promise.all([
    getSession(),
    getActiveSar(),
    getTranslations("Nav"),
    getTranslations("Sar"),
  ]);

  const canCreate = session?.user.role === "caf_lead" || session?.user.role === "sponsor";
  const showMaturityOverview =
    session?.user.role === "sponsor" || session?.user.role === "caf_lead";
  const stats = sar ? completionStats(sar.subcriteria_scores) : null;
  const maturityPoints = sar ? computeCriterionMaturity(sar.subcriteria_scores) : null;
  const maturityIndex = maturityPoints ? computeOverallMaturityIndex(maturityPoints) : null;

  return (
    <div className="max-w-3xl space-y-4">
      <h1 className="text-2xl font-semibold tracking-tight">{t("dashboard")}</h1>
      <p className="text-sm text-slate-500 dark:text-slate-400">
        {session?.user.email} — {session?.user.role}
      </p>

      {sar && stats ? (
        <div className="rounded-lg border border-slate-200 p-4 dark:border-slate-800">
          <p className="mb-3 text-sm text-slate-600 dark:text-slate-300">
            {tSar("progressLabel", { done: stats.done, total: stats.total })}
          </p>
          <Link href={`/sar/${sar.id}`} locale={locale} className={buttonVariants("primary")}>
            {tSar("title")}
          </Link>
        </div>
      ) : (
        <div className="rounded-lg border border-dashed border-slate-300 p-4 dark:border-slate-700">
          <p className="mb-3 text-sm text-slate-500 dark:text-slate-400">{tSar("noActiveSar")}</p>
          {canCreate && <CreateSarButton />}
        </div>
      )}

      {showMaturityOverview && sar && maturityPoints && maturityIndex !== null && (
        <div className="rounded-lg border border-slate-200 p-4 dark:border-slate-800">
          <div className="mb-3 flex items-baseline justify-between">
            <p className="text-sm font-medium text-slate-700 dark:text-slate-200">
              {tSar("maturityOverviewHeading")}
            </p>
            <p className="text-sm text-slate-500 dark:text-slate-400">
              {tSar("maturityIndexLabel", { index: maturityIndex })}
            </p>
          </div>
          <MaturityRadarChart points={maturityPoints} locale={locale} />
          {/* WCAG 1.1.1 — tekstualna alternativa za radar (screen reader). */}
          <table className="sr-only">
            <caption>{tSar("maturityTableCaption")}</caption>
            <thead>
              <tr>
                <th scope="col">{tSar("maturityCriterionColumn")}</th>
                <th scope="col">{tSar("maturityScoreColumn")}</th>
              </tr>
            </thead>
            <tbody>
              {maturityPoints.map((point) => (
                <tr key={point.criterionNumber}>
                  <th scope="row">
                    {point.criterionNumber}. {locale === "en" ? point.nameEn : point.nameMe}
                  </th>
                  <td>{point.average.toFixed(1)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
