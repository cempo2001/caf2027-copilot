import { useTranslations } from "next-intl";
import { getCafSubcriteriaContent } from "@/features/wizard/content/caf-content";
import type { Locale } from "@/types/api";

/**
 * Djelimično usvajanje CAF_Questions_2.docx sadržaja (dogovoreno 16.9.2026,
 * vidi razgovor u sesiji) — samo uvod i usmjeravajuća pitanja kao pomoć pri
 * unosu, BEZ promjene modela ocjenjivanja (i dalje slobodan tekst + ručna
 * ocjena 1-5, ne ponderisana pitanja sa više odgovora). Statički sadržaj
 * (`features/wizard/content/caf-content.ts`) jer kontrakt (api-contract-v1.md)
 * trenutno ne prenosi `introduction`/`guiding_questions` sa backend-a — ovo je
 * čisto frontend prikaz, ne dira API ni bazu.
 *
 * Ako podkriterijum nije u statičkom sadržaju (ne bi trebalo da se desi za
 * standardnih 28), panel se jednostavno ne renderuje — nema slomljenog UI-ja.
 */
export function GuidingQuestionsPanel({
  subcriteriaCode,
  locale,
}: {
  subcriteriaCode: string;
  locale: Locale;
}) {
  const t = useTranslations("Wizard");
  const content = getCafSubcriteriaContent(subcriteriaCode);

  if (!content) {
    return null;
  }

  const introduction = locale === "en" ? content.introductionEn : content.introductionMe;
  const questions = locale === "en" ? content.guidingQuestionsEn : content.guidingQuestionsMe;

  return (
    <details className="group rounded-md border border-slate-200 bg-slate-50 px-3 py-2 text-sm dark:border-slate-700 dark:bg-slate-800/60">
      <summary className="cursor-pointer select-none font-medium text-slate-700 dark:text-slate-200">
        {t("guidingQuestionsHeading")}
      </summary>
      <div className="mt-2 space-y-2 text-slate-600 dark:text-slate-300">
        <p>{introduction}</p>
        <ul className="list-disc space-y-1 pl-5">
          {questions.map((question, index) => (
            <li key={index}>{question}</li>
          ))}
        </ul>
        <p className="text-xs text-slate-500 dark:text-slate-400">{t("guidingQuestionsSourceNote")}</p>
      </div>
    </details>
  );
}
