"use client";

import * as React from "react";
import { useTranslations } from "next-intl";
import { Button } from "@/components/ui/button";
import { resolveErrorMessage } from "@/lib/error-messages";
import { useRouter } from "@/i18n/navigation";
import { createSarAction } from "@/features/sar/actions";

/** Pokreće novu samoprocjenu (4.2 — samo CAFLead/Sponsor) i vodi na njen pregled. */
export function CreateSarButton() {
  const t = useTranslations("Sar");
  const tErrors = useTranslations("Errors");
  const router = useRouter();
  const [isPending, startTransition] = React.useTransition();
  const [errorKey, setErrorKey] = React.useState<string | null>(null);

  const handleCreate = () => {
    setErrorKey(null);
    startTransition(async () => {
      const result = await createSarAction();
      if (result.ok) {
        router.push(`/sar/${result.data.id}`);
      } else {
        setErrorKey(result.errorKey);
      }
    });
  };

  return (
    <div className="space-y-2">
      <Button type="button" onClick={handleCreate} disabled={isPending}>
        {isPending ? t("creating") : t("createSar")}
      </Button>
      {errorKey && (
        <p role="alert" className="text-sm text-red-600 dark:text-red-400">
          {resolveErrorMessage(tErrors, errorKey)}
        </p>
      )}
    </div>
  );
}
