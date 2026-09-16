"use client";

import * as React from "react";
import { useTranslations } from "next-intl";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { resolveErrorMessage } from "@/lib/error-messages";
import { approveSarAction } from "@/features/sar/actions";

/**
 * Approved Lock — samo Sponsor (4.6). Nepovratna akcija, zato traži
 * potvrdu prije poziva. Disabled dok nisu sva 28 podkriterijuma ocijenjena
 * (server i dalje vraća `403 sar_incomplete` kao zadnja linija odbrane —
 * ovo je samo UX prečica da se ne klikne uzalud).
 */
export function ApproveSarButton({ sarId, disabled }: { sarId: string; disabled: boolean }) {
  const t = useTranslations("Sar");
  const tErrors = useTranslations("Errors");
  const router = useRouter();
  const [isPending, startTransition] = React.useTransition();
  const [errorKey, setErrorKey] = React.useState<string | null>(null);

  const handleApprove = () => {
    if (!window.confirm(t("approveConfirm"))) return;
    setErrorKey(null);
    startTransition(async () => {
      const result = await approveSarAction(sarId);
      if (result.ok) {
        router.refresh();
      } else {
        setErrorKey(result.errorKey);
      }
    });
  };

  return (
    <div className="space-y-2">
      <Button
        type="button"
        variant="destructive"
        onClick={handleApprove}
        disabled={disabled || isPending}
      >
        {isPending ? t("approving") : t("approveButton")}
      </Button>
      {errorKey && (
        <p role="alert" className="text-sm text-red-600 dark:text-red-400">
          {resolveErrorMessage(tErrors, errorKey)}
        </p>
      )}
    </div>
  );
}
