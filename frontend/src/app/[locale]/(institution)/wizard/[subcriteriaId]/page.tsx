import { notFound } from "next/navigation";
import { getTranslations } from "next-intl/server";
import { Link } from "@/i18n/navigation";
import { isSupportedLocale } from "@/i18n/routing";
import { getSession } from "@/lib/auth";
import { getActiveSar } from "@/features/sar/actions";
import { findAdjacentCodes } from "@/features/wizard/lib";
import { WizardNav } from "@/features/wizard/components/wizard-nav";
import { WizardStepForm } from "@/features/wizard/components/wizard-step-form";
import { buttonVariants } from "@/components/ui/button";
import type { Locale } from "@/types/api";

/**
 * Vođeni Čarobnjak — jedan korak (jedan podkriterijum). Aktivni SAR je
 * implicitan (vidi `getActiveSar` — institucija ima najviše jedan
 * ne-odobren SAR u Fazi 1), zato URL nosi samo `subcriteriaId`
 * (ARCHITECTURE.md Sekcija 3: `wizard/[subcriteriaId]/page.tsx`).
 */
export default async function WizardStepPage({
  params,
}: {
  params: Promise<{ locale: string; subcriteriaId: string }>;
}) {
  const { locale: rawLocale, subcriteriaId } = await params;
  if (!isSupportedLocale(rawLocale)) notFound();
  const locale = rawLocale as Locale;

  const [session, sar, t] = await Promise.all([
    getSession(),
    getActiveSar(),
    getTranslations("Wizard"),
  ]);

  if (!sar) notFound();

  const subcriteria = sar.subcriteria_scores.find(
    (item) => item.subcriteria_code === subcriteriaId
  );
  if (!subcriteria) notFound();

  // Usklađeno sa backend-om (sar_access.EDITOR_ROLES): SAG tim unosi ocjene,
  // Employee je read-only.
  const role = session?.user.role;
  const canEdit = role === "caf_lead" || role === "sponsor" || role === "cae_team_member";
  const { prev, next, index, total } = findAdjacentCodes(sar.subcriteria_scores, subcriteriaId);

  return (
    <div className="grid grid-cols-1 gap-8 lg:grid-cols-[260px_1fr]">
      <aside className="lg:sticky lg:top-8 lg:self-start">
        <WizardNav
          sarId={sar.id}
          scores={sar.subcriteria_scores}
          currentCode={subcriteriaId}
          sarStatus={sar.status}
          locale={locale}
        />
      </aside>

      <div className="max-w-2xl space-y-6">
        <p className="text-xs text-slate-500 dark:text-slate-400">{t("stepOf", { current: index + 1, total })}</p>

        <WizardStepForm
          sarId={sar.id}
          sarStatus={sar.status}
          subcriteria={subcriteria}
          canEdit={canEdit}
          locale={locale}
        />

        <div className="flex justify-between border-t border-slate-200 pt-4 dark:border-slate-800">
          {prev ? (
            <Link href={`/wizard/${prev}`} locale={locale} className={buttonVariants("secondary")}>
              ← {t("prevStep")}
            </Link>
          ) : (
            <span />
          )}
          {next ? (
            <Link href={`/wizard/${next}`} locale={locale} className={buttonVariants("primary")}>
              {t("nextStep")} →
            </Link>
          ) : (
            <Link href={`/sar/${sar.id}`} locale={locale} className={buttonVariants("primary")}>
              {t("backToOverview")}
            </Link>
          )}
        </div>
      </div>
    </div>
  );
}
