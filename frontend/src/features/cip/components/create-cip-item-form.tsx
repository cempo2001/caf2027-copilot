"use client";

import * as React from "react";
import { useTranslations } from "next-intl";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { resolveErrorMessage } from "@/lib/error-messages";
import { createCipItemAction } from "@/features/cip/actions";
import type { CipItem, CipQuadrant } from "@/types/api";

/**
 * Forma je vezana za JEDAN kvadrant (prop `quadrant`) — kolona u 2x2 mreži
 * određuje kvadrant, korisnik ga ne bira posebno (manje polja, manje grešaka
 * nego globalni "quadrant" select).
 */
export function CreateCipItemForm({
  sarId,
  quadrant,
  onCreated,
  onCancel,
}: {
  sarId: string;
  quadrant: CipQuadrant;
  onCreated: (item: CipItem) => void;
  onCancel: () => void;
}) {
  const t = useTranslations("Cip");
  const tErrors = useTranslations("Errors");
  const [isPending, startTransition] = React.useTransition();
  const [errorKey, setErrorKey] = React.useState<string | null>(null);

  const handleSubmit = (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    const form = e.currentTarget;
    const data = new FormData(form);
    setErrorKey(null);
    startTransition(async () => {
      const result = await createCipItemAction({
        sarId,
        quadrant,
        titleMe: String(data.get("title_me") ?? ""),
        titleEn: String(data.get("title_en") ?? ""),
        asIs: String(data.get("as_is") ?? ""),
        toBe: String(data.get("to_be") ?? ""),
      });
      if (result.ok) {
        onCreated(result.data);
      } else {
        setErrorKey(result.errorKey);
      }
    });
  };

  return (
    <form
      onSubmit={handleSubmit}
      className="space-y-2 rounded-md border border-dashed border-slate-300 p-3 dark:border-slate-700"
    >
      <div className="space-y-1">
        <Label htmlFor={`title_me-${quadrant}`}>{t("titleLabel")}</Label>
        <Input id={`title_me-${quadrant}`} name="title_me" required disabled={isPending} />
      </div>
      <div className="space-y-1">
        <Label htmlFor={`title_en-${quadrant}`}>{t("titleEnLabel")}</Label>
        <Input id={`title_en-${quadrant}`} name="title_en" required disabled={isPending} />
      </div>
      <div className="space-y-1">
        <Label htmlFor={`as_is-${quadrant}`}>{t("asIsLabel")}</Label>
        <Textarea id={`as_is-${quadrant}`} name="as_is" rows={2} required disabled={isPending} />
      </div>
      <div className="space-y-1">
        <Label htmlFor={`to_be-${quadrant}`}>{t("toBeLabel")}</Label>
        <Textarea id={`to_be-${quadrant}`} name="to_be" rows={2} required disabled={isPending} />
      </div>

      {errorKey && (
        <p role="alert" className="text-xs text-red-600 dark:text-red-400">
          {resolveErrorMessage(tErrors, errorKey)}
        </p>
      )}

      <div className="flex gap-2">
        <Button type="submit" disabled={isPending}>
          {isPending ? t("creating") : t("create")}
        </Button>
        <Button type="button" variant="ghost" onClick={onCancel} disabled={isPending}>
          {t("cancel")}
        </Button>
      </div>
    </form>
  );
}
