"use client";

import * as React from "react";
import { useActionState } from "react";
import { useTranslations } from "next-intl";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Select } from "@/components/ui/select";
import { Textarea } from "@/components/ui/textarea";
import { resolveErrorMessage } from "@/lib/error-messages";
import { cn } from "@/lib/utils";
import { updateSubcriteriaAction } from "@/features/wizard/actions";
import { AiConsensusPanel } from "@/features/wizard/components/ai-consensus-panel";
import { GuidingQuestionsPanel } from "@/features/wizard/components/guiding-questions-panel";
import { EvidenceUploadForm } from "@/features/evidence/components/evidence-upload-form";
import { getCafSubcriteriaContent } from "@/features/wizard/content/caf-content";
import {
  countWords,
  INITIAL_UPDATE_STATE,
  isBelowRecommendedLength,
  MIN_RECOMMENDED_WORDS,
} from "@/features/wizard/lib";
import type { AiConsensusResponse, Locale, SarStatus, SubcriteriaScore } from "@/types/api";

const SCORE_OPTIONS = [1, 2, 3, 4, 5] as const;

export function WizardStepForm({
  sarId,
  sarStatus,
  subcriteria,
  canEdit,
  locale,
}: {
  sarId: string;
  sarStatus: SarStatus;
  subcriteria: SubcriteriaScore;
  canEdit: boolean;
  locale: Locale;
}) {
  const t = useTranslations("Wizard");
  const tErrors = useTranslations("Errors");

  const [state, formAction, isPending] = useActionState(
    updateSubcriteriaAction,
    INITIAL_UPDATE_STATE
  );

  // Kontrolisan unos radi live brojača riječi — ali i dalje prirodni <form>
  // submit (name atributi), useActionState čita iz FormData na submit-u.
  // Backend u praksi vraća `null` za još-neupisan tekst (kontrakt kaže
  // string) — `?? ""` odmah na ulazu, kontrolisan <textarea> ne smije dobiti
  // `null` kao `value`.
  const [evidenceText, setEvidenceText] = React.useState(subcriteria.evidence_text ?? "");
  const [weaknessesText, setWeaknessesText] = React.useState(subcriteria.weaknesses_text ?? "");
  const [score, setScore] = React.useState<number>(subcriteria.score);
  const [qualityFlag, setQualityFlag] = React.useState(subcriteria.quality_flag);

  // Kad korisnik pređe na drugi podkriterijum (nova `subcriteria` prop od
  // servera), resetuje lokalni state na te vrijednosti — inače bi ostao
  // prethodni unos vidljiv dok se ne osvježi stranica.
  const lastLoadedCode = React.useRef(subcriteria.subcriteria_code);
  if (lastLoadedCode.current !== subcriteria.subcriteria_code) {
    lastLoadedCode.current = subcriteria.subcriteria_code;
    setEvidenceText(subcriteria.evidence_text ?? "");
    setWeaknessesText(subcriteria.weaknesses_text ?? "");
    setScore(subcriteria.score);
    setQualityFlag(subcriteria.quality_flag);
  }

  React.useEffect(() => {
    if (state.status === "success" && state.updated) {
      setQualityFlag(state.updated.quality_flag);
    }
  }, [state]);

  const isLocked = sarStatus === "approved";
  const readOnly = !canEdit || isLocked;
  const wordCount = countWords(evidenceText);
  const belowRecommended = isBelowRecommendedLength(evidenceText);
  const scoreIsValid = score >= 1 && score <= 5;

  // Prihvatanje predloga mijenja SAMO ocjenu. Objašnjenje predloga se ne
  // lijepi u dokaze: to bi izmijenilo korisnikov dokaz tekstom sistema i
  // pri sledećem predlogu naduvalo ocjenu (fallback broji pojmove u dokazu).
  const handleAiAccept = (suggestion: AiConsensusResponse) => {
    setScore(suggestion.suggested_score);
  };

  // Backend `subcriteria.name_me`/`name_en` je i dalje izvor istine kad je
  // popunjen (vidi alembic/versions/0001_initial_schema.py — ostavljeno
  // namjerno NULL dok se ne unesu iz zvaničnog CAF teksta). Dok backend seed
  // ne stigne, padamo na statički frontend sadržaj da naslov ne bude prazan.
  const staticContent = getCafSubcriteriaContent(subcriteria.subcriteria_code);
  const displayName =
    (locale === "en" ? subcriteria.name_en : subcriteria.name_me) ??
    (staticContent ? (locale === "en" ? staticContent.nameEn : staticContent.nameMe) : null);

  return (
    <div className="space-y-4">
      <div>
        <p className="font-mono text-xs text-slate-500 dark:text-slate-400">{subcriteria.subcriteria_code}</p>
        <h1 className="text-xl font-semibold tracking-tight">{displayName}</h1>
      </div>

      <GuidingQuestionsPanel subcriteriaCode={subcriteria.subcriteria_code} locale={locale} />

      {isLocked && (
        <p className="rounded-md border border-emerald-200 bg-emerald-50 px-3 py-2 text-sm text-emerald-800 dark:border-emerald-900 dark:bg-emerald-950 dark:text-emerald-300">
          {t("lockedBanner")}
        </p>
      )}
      {!isLocked && !canEdit && (
        <p className="rounded-md border border-slate-200 bg-slate-50 px-3 py-2 text-sm text-slate-600 dark:border-slate-700 dark:bg-slate-800/60 dark:text-slate-300">
          {t("readOnlyBanner")}
        </p>
      )}

      {!readOnly && (
        <AiConsensusPanel
          sarId={sarId}
          subcriteriaCode={subcriteria.subcriteria_code}
          disabled={isPending}
          onAccept={handleAiAccept}
        />
      )}

      <form action={formAction} className="space-y-4">
        <input type="hidden" name="sarId" value={sarId} />
        <input type="hidden" name="subcriteriaCode" value={subcriteria.subcriteria_code} />

        <div className="space-y-1.5">
          <div className="flex items-center justify-between">
            <Label htmlFor="evidence_text">{t("evidenceLabel")}</Label>
            <span
              className={cn(
                "text-xs",
                belowRecommended ? "text-amber-600 dark:text-amber-400" : "text-slate-500 dark:text-slate-400"
              )}
            >
              {t("wordCount", { count: wordCount })}
            </span>
          </div>
          <Textarea
            id="evidence_text"
            name="evidence_text"
            rows={6}
            value={evidenceText}
            onChange={(e) => setEvidenceText(e.target.value)}
            disabled={readOnly || isPending}
          />
          {belowRecommended && (
            <p className="text-xs text-amber-600 dark:text-amber-400">
              {t("wordCountHint", { min: MIN_RECOMMENDED_WORDS })}
            </p>
          )}
          {qualityFlag === "too_short" && (
            <p role="status" className="text-xs text-red-600 dark:text-red-400">{t("qualityTooShort")}</p>
          )}
          {qualityFlag === "too_generic" && (
            <p role="status" className="text-xs text-red-600 dark:text-red-400">{t("qualityTooGeneric")}</p>
          )}
        </div>

        <div className="space-y-1.5">
          <Label htmlFor="weaknesses_text">{t("weaknessesLabel")}</Label>
          <Textarea
            id="weaknesses_text"
            name="weaknesses_text"
            rows={4}
            value={weaknessesText}
            onChange={(e) => setWeaknessesText(e.target.value)}
            disabled={readOnly || isPending}
          />
        </div>

        <div className="space-y-1.5">
          <Label htmlFor="score">{t("scoreLabel")}</Label>
          <Select
            id="score"
            name="score"
            value={scoreIsValid ? String(score) : ""}
            onChange={(e) => setScore(Number(e.target.value))}
            disabled={readOnly || isPending}
            className="w-32"
          >
            {!scoreIsValid && <option value="">—</option>}
            {SCORE_OPTIONS.map((value) => (
              <option key={value} value={value}>
                {value}
              </option>
            ))}
          </Select>
        </div>

        {state.status === "error" && (
          <p role="alert" className="text-sm text-red-600 dark:text-red-400">
            {resolveErrorMessage(tErrors, state.errorKey)}
          </p>
        )}
        {state.status === "success" && (
          <p role="status" className="text-sm text-emerald-700 dark:text-emerald-400">{t("saved")}</p>
        )}

        {!readOnly && (
          <Button type="submit" disabled={isPending || !scoreIsValid}>
            {isPending ? t("saving") : t("save")}
          </Button>
        )}
      </form>

      {/* Evidence upload (6.1) je NEZAVISAN <form> od gornjeg — vlastita
          multipart FormData, ne treba mu score/evidence_text vrijednosti. */}
      <EvidenceUploadForm
        sarId={sarId}
        subcriteriaCode={subcriteria.subcriteria_code}
        disabled={readOnly}
      />
    </div>
  );
}
