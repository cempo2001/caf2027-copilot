"use client";

import * as React from "react";
import { useActionState } from "react";
import { useTranslations } from "next-intl";
import { Button } from "@/components/ui/button";
import { resolveErrorMessage } from "@/lib/error-messages";
import { cn } from "@/lib/utils";
import { uploadEvidenceAction } from "@/features/evidence/actions";
import { INITIAL_UPLOAD_STATE, MAX_EVIDENCE_FILE_BYTES } from "@/features/evidence/lib";

const SCAN_BADGE_CLASSES: Record<string, string> = {
  clean: "bg-emerald-100 text-emerald-800 dark:bg-emerald-950 dark:text-emerald-300",
  infected: "bg-red-100 text-red-800 dark:bg-red-950 dark:text-red-300",
  pending: "bg-amber-100 text-amber-800 dark:bg-amber-950 dark:text-amber-300",
};

/**
 * Upload dokaza za jedan podkriterijum (api-contract-v1.md 6.1). Zaražen
 * fajl backend odbija (422 evidence_infected) i ne čuva; `pending` znači da
 * je AV skeniranje isključeno u tom okruženju (samo lokalni razvoj).
 */
export function EvidenceUploadForm({
  sarId,
  subcriteriaCode,
  disabled,
}: {
  sarId: string;
  subcriteriaCode: string;
  disabled: boolean;
}) {
  const t = useTranslations("Evidence");
  const tErrors = useTranslations("Errors");
  const [state, formAction, isPending] = useActionState(
    uploadEvidenceAction,
    INITIAL_UPLOAD_STATE
  );
  const [fileName, setFileName] = React.useState<string | null>(null);
  const [clientError, setClientError] = React.useState<string | null>(null);
  const formRef = React.useRef<HTMLFormElement>(null);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0] ?? null;
    setClientError(null);
    if (file && file.size > MAX_EVIDENCE_FILE_BYTES) {
      setFileName(null);
      e.target.value = "";
      setClientError(t("fileTooLarge"));
      return;
    }
    setFileName(file?.name ?? null);
  };

  return (
    <div className="space-y-2">
      <p className="text-sm font-medium">{t("heading")}</p>
      <form ref={formRef} action={formAction} className="flex flex-wrap items-center gap-2">
        <input type="hidden" name="sarId" value={sarId} />
        <input type="hidden" name="subcriteriaCode" value={subcriteriaCode} />
        <input
          type="file"
          name="file"
          aria-label={t("chooseFile")}
          onChange={handleFileChange}
          disabled={disabled || isPending}
          className="text-sm file:mr-2 file:rounded-md file:border-0 file:bg-slate-100 file:px-3 file:py-1.5 file:text-sm file:font-medium hover:file:bg-slate-200 dark:file:bg-slate-800 dark:hover:file:bg-slate-700"
        />
        <Button type="submit" variant="secondary" disabled={disabled || isPending || !fileName}>
          {isPending ? t("uploading") : t("uploadButton")}
        </Button>
      </form>

      {clientError && (
        <p role="alert" className="text-xs text-red-600 dark:text-red-400">
          {clientError}
        </p>
      )}

      {state.status === "error" && (
        <p role="alert" className="text-xs text-red-600 dark:text-red-400">
          {resolveErrorMessage(tErrors, state.errorKey)}
        </p>
      )}

      {state.status === "success" && state.result && (
        <div className="flex flex-wrap items-center gap-2 text-xs">
          <span className="text-emerald-700 dark:text-emerald-400">
            {t("uploadSuccess", { filename: state.result.filename })}
          </span>
          <span
            className={cn(
              "rounded-full px-2 py-0.5 font-medium",
              SCAN_BADGE_CLASSES[state.result.av_scan_status]
            )}
          >
            {state.result.av_scan_status === "clean"
              ? t("scanClean")
              : state.result.av_scan_status === "infected"
                ? t("scanInfected")
                : t("scanPending")}
          </span>
          <span className="font-mono text-slate-500 dark:text-slate-400">
            {t("sha256Label")}: {state.result.sha256.slice(0, 12)}…
          </span>
          {state.result.av_scan_status === "pending" && (
            <span className="basis-full text-amber-700 dark:text-amber-400">{t("pendingNote")}</span>
          )}
        </div>
      )}
    </div>
  );
}
