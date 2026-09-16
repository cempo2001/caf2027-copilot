"use client";

import * as React from "react";
import { useTranslations } from "next-intl";
import { Button } from "@/components/ui/button";
import { resolveErrorMessage } from "@/lib/error-messages";
import { requestAiConsensusAction } from "@/features/wizard/actions";
import type { AiConsensusResponse } from "@/types/api";

/**
 * AI/Consensus predlog ocjene — human-in-the-loop (CLAUDE.md Sekcija 7.5 i
 * api-contract-v1.md 4.5). Predlog se NIKAD ne upisuje automatski: korisnik
 * mora eksplicitno kliknuti "Prihvati" da bi se prenio u formu iznad (koju
 * kontroliše roditelj preko `onAccept`), a odgovor sa `source: "fallback"`
 * se posebno naglašava (503 se ne tretira kao blokirajuća greška — 1.3, 4.5).
 */
export function AiConsensusPanel({
  sarId,
  subcriteriaCode,
  disabled,
  onAccept,
}: {
  sarId: string;
  subcriteriaCode: string;
  disabled: boolean;
  onAccept: (suggestion: AiConsensusResponse) => void;
}) {
  const t = useTranslations("Wizard");
  const tErrors = useTranslations("Errors");
  const [isPending, startTransition] = React.useTransition();
  const [suggestion, setSuggestion] = React.useState<AiConsensusResponse | null>(null);
  const [errorKey, setErrorKey] = React.useState<string | null>(null);

  const handleRequest = () => {
    setErrorKey(null);
    startTransition(async () => {
      const result = await requestAiConsensusAction(sarId, subcriteriaCode);
      if (result.ok) {
        setSuggestion(result.data);
      } else {
        setErrorKey(result.errorKey);
      }
    });
  };

  const handleAccept = () => {
    if (!suggestion) return;
    onAccept(suggestion);
    setSuggestion(null);
  };

  return (
    <div className="rounded-md border border-dashed border-slate-300 p-3 dark:border-slate-700">
      <div className="flex items-center justify-between gap-3">
        <p className="text-xs text-slate-500 dark:text-slate-400">{t("aiHumanInLoopNote")}</p>
        <Button
          type="button"
          variant="secondary"
          onClick={handleRequest}
          disabled={disabled || isPending}
        >
          {isPending ? t("aiConsensusLoading") : t("aiConsensusButton")}
        </Button>
      </div>

      {errorKey && (
        <p role="alert" className="mt-2 text-sm text-red-600 dark:text-red-400">
          {resolveErrorMessage(tErrors, errorKey)}
        </p>
      )}

      {suggestion && (
        <div role="status" className="mt-3 space-y-2 rounded-md bg-slate-50 p-3 text-sm dark:bg-slate-800/60">
          <div className="flex items-center justify-between">
            <span className="font-medium">
              {t("suggestedScoreLabel", { score: suggestion.suggested_score })}
            </span>
            <span
              className={
                suggestion.source === "fallback"
                  ? "rounded bg-amber-100 px-2 py-0.5 text-xs font-medium text-amber-800 dark:bg-amber-950 dark:text-amber-300"
                  : "rounded bg-slate-200 px-2 py-0.5 text-xs font-medium text-slate-700 dark:bg-slate-700 dark:text-slate-200"
              }
            >
              {suggestion.source === "fallback" ? t("aiSourceFallback") : t("aiSourceAi")}
            </span>
          </div>
          <p className="whitespace-pre-line text-slate-600 dark:text-slate-300">{suggestion.suggested_summary_text}</p>
          <div className="flex gap-2">
            <Button type="button" onClick={handleAccept}>
              {t("aiConsensusAccept")}
            </Button>
            <Button type="button" variant="ghost" onClick={() => setSuggestion(null)}>
              {t("aiConsensusDismiss")}
            </Button>
          </div>
        </div>
      )}
    </div>
  );
}
