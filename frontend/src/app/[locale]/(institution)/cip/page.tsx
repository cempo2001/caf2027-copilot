import { notFound } from "next/navigation";
import { getTranslations } from "next-intl/server";
import { isSupportedLocale } from "@/i18n/routing";
import { ApiError } from "@/lib/api-client";
import { getSession } from "@/lib/auth";
import { getActiveSar } from "@/features/sar/actions";
import { listCipItems } from "@/features/cip/actions";
import { CipBoard } from "@/features/cip/components/cip-board";
import type { Locale } from "@/types/api";

/**
 * CIP akcioni plan (ARCHITECTURE.md Sekcija 3: `cip/page.tsx`, bez sarId u
 * URL-u — implicitno aktivan SAR, isti obrazac kao `wizard/[subcriteriaId]`).
 * 404 na `listCipItems` je rijedak slučaj (SAR obrisan između dva upita) i
 * prikazuje se kao čitljiva poruka umjesto Next.js error boundary-ja.
 */
export default async function CipPage({
  params,
}: {
  params: Promise<{ locale: string }>;
}) {
  const { locale: rawLocale } = await params;
  if (!isSupportedLocale(rawLocale)) notFound();
  const locale = rawLocale as Locale;

  const [t, tErrors, sar, session] = await Promise.all([
    getTranslations("Cip"),
    getTranslations("Errors"),
    getActiveSar(),
    getSession(),
  ]);

  if (!sar) {
    return (
      <div className="max-w-2xl">
        <h1 className="text-2xl font-semibold tracking-tight">{t("title")}</h1>
        <p className="mt-2 text-sm text-slate-500 dark:text-slate-400">{t("noActiveSar")}</p>
      </div>
    );
  }

  let items;
  try {
    items = await listCipItems(sar.id);
  } catch (err) {
    if (err instanceof ApiError && err.status === 404) {
      return (
        <div className="max-w-2xl space-y-2">
          <h1 className="text-2xl font-semibold tracking-tight">{t("title")}</h1>
          <p className="rounded-md border border-dashed border-slate-300 px-3 py-2 text-sm text-slate-500 dark:border-slate-700 dark:text-slate-400">
            {tErrors("not_found")}
          </p>
        </div>
      );
    }
    throw err;
  }
  const role = session?.user.role;
  const isEditorRole = role === "sponsor" || role === "caf_lead" || role === "cae_team_member";
  const isLocked = sar.status === "approved";
  const canEdit = !isLocked && isEditorRole;

  return (
    <div className="max-w-5xl space-y-4">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">{t("title")}</h1>
        <p className="text-sm text-slate-500 dark:text-slate-400">{t("subtitle")}</p>
        {isLocked && (
          <p className="mt-2 rounded-md border border-emerald-200 bg-emerald-50 px-3 py-2 text-sm text-emerald-800 dark:border-emerald-900 dark:bg-emerald-950 dark:text-emerald-300">
            {t("lockedNote")}
          </p>
        )}
      </div>

      <CipBoard sarId={sar.id} initialItems={items} canEdit={canEdit} locale={locale} />
    </div>
  );
}
