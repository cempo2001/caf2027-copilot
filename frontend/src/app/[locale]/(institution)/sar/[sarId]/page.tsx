import { notFound } from "next/navigation";
import { getTranslations } from "next-intl/server";
import { Link } from "@/i18n/navigation";
import { isSupportedLocale } from "@/i18n/routing";
import { getSession } from "@/lib/auth";
import { ApiError } from "@/lib/api-client";
import { getSelfAssessment } from "@/features/sar/actions";
import { completionStats, groupByCriterion } from "@/features/wizard/lib";
import { ApproveSarButton } from "@/features/sar/components/approve-sar-button";
import { buttonVariants } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import type { Locale } from "@/types/api";

export default async function SarOverviewPage({
  params,
}: {
  params: Promise<{ locale: string; sarId: string }>;
}) {
  const { locale: rawLocale, sarId } = await params;
  if (!isSupportedLocale(rawLocale)) notFound();
  const locale = rawLocale as Locale;

  const [session, t] = await Promise.all([getSession(), getTranslations("Sar")]);

  let sar;
  try {
    sar = await getSelfAssessment(sarId);
  } catch (err) {
    // 404 pokriva i "ne postoji" i "tuđi SAR" (RLS namjerno ne razlikuje —
    // api-contract-v1.md 1.3). Svaka druga greška ovdje je neočekivana i
    // prosleđuje se dalje ka Next.js error boundary-ju.
    if (err instanceof ApiError && err.status === 404) notFound();
    throw err;
  }

  const { done, total } = completionStats(sar.subcriteria_scores);
  const groups = groupByCriterion(sar.subcriteria_scores);
  const isSponsor = session?.user.role === "sponsor";
  const isApproved = sar.status === "approved";

  return (
    <div className="max-w-3xl space-y-6">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">{t("title")}</h1>
        <p className="text-sm text-slate-500 dark:text-slate-400">
          {t("progressLabel", { done, total })}
        </p>
        <div className="mt-2 h-2 w-full max-w-sm overflow-hidden rounded-full bg-slate-100 dark:bg-slate-800">
          <div
            className="h-full rounded-full bg-slate-900 dark:bg-slate-100"
            style={{ width: `${total === 0 ? 0 : Math.round((done / total) * 100)}%` }}
          />
        </div>
      </div>

      {isApproved && sar.approved_at && (
        <p className="rounded-md border border-emerald-200 bg-emerald-50 px-3 py-2 text-sm text-emerald-800 dark:border-emerald-900 dark:bg-emerald-950 dark:text-emerald-300">
          {t("approvedBadge", {
            date: new Intl.DateTimeFormat(locale === "en" ? "en-US" : "sr-ME").format(
              new Date(sar.approved_at)
            ),
          })}
        </p>
      )}

      {isSponsor && !isApproved && (
        <ApproveSarButton sarId={sar.id} disabled={done < total} />
      )}

      <div className="space-y-6">
        {groups.map((group) => (
          <div key={group.criterionNumber}>
            <h2 className="mb-2 text-sm font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-400">
              {t("criterionHeading", { number: group.criterionNumber })}
            </h2>
            <ul className="divide-y divide-slate-200 rounded-lg border border-slate-200 dark:divide-slate-800 dark:border-slate-800">
              {group.subcriteria.map((item) => {
                const hasScore = item.score >= 1 && item.score <= 5;
                return (
                  <li key={item.subcriteria_code}>
                    <Link
                      href={`/wizard/${item.subcriteria_code}`}
                      locale={locale}
                      className="flex items-center justify-between gap-3 px-4 py-3 hover:bg-slate-50 dark:hover:bg-slate-900"
                    >
                      <span className="flex items-center gap-3">
                        <span className="font-mono text-xs text-slate-500 dark:text-slate-400">
                          {item.subcriteria_code}
                        </span>
                        <span className="text-sm">
                          {locale === "en" ? item.name_en : item.name_me}
                        </span>
                      </span>
                      <span
                        className={cn(
                          "shrink-0 rounded-full px-2 py-0.5 text-xs font-medium",
                          hasScore
                            ? "bg-slate-900 text-white dark:bg-slate-100 dark:text-slate-900"
                            : "bg-slate-100 text-slate-500 dark:bg-slate-800 dark:text-slate-400"
                        )}
                      >
                        {hasScore ? `${t("scoreLabel")}: ${item.score}` : t("notScored")}
                      </span>
                    </Link>
                  </li>
                );
              })}
            </ul>
          </div>
        ))}
      </div>

      {!isApproved && (
        <Link
          href={`/wizard/${sar.subcriteria_scores[0]?.subcriteria_code ?? ""}`}
          locale={locale}
          className={buttonVariants("secondary")}
        >
          {done > 0 ? t("continueWizard") : t("startWizard")}
        </Link>
      )}
    </div>
  );
}
