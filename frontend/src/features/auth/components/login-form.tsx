"use client";

import { useActionState } from "react";
import { useTranslations } from "next-intl";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select } from "@/components/ui/select";
import { loginAction, type LoginFormState } from "@/features/auth/actions";
import { resolveErrorMessage } from "@/lib/error-messages";

const INITIAL_STATE: LoginFormState = { errorKey: null };

/**
 * Login forma (features/auth/components — vidi ARCHITECTURE.md Sekcija 3).
 * Jezik na login ekranu je EKSPLICITAN izbor korisnika (select, ne
 * pretpostavljen iz rute) — CLAUDE.md 6.2.
 */
export function LoginForm({ defaultLang }: { defaultLang: "me" | "en" }) {
  const t = useTranslations("Login");
  const tErrors = useTranslations("Errors");
  const [state, formAction, isPending] = useActionState(loginAction, INITIAL_STATE);

  return (
    <form action={formAction} className="space-y-5" noValidate>
      {state.errorKey && (
        <p
          role="alert"
          className="rounded-md border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700 dark:border-red-900 dark:bg-red-950 dark:text-red-300"
        >
          {resolveErrorMessage(tErrors, state.errorKey)}
        </p>
      )}

      <div className="space-y-1.5">
        <Label htmlFor="email">{t("emailLabel")}</Label>
        <Input
          id="email"
          name="email"
          type="email"
          autoComplete="email"
          placeholder={t("emailPlaceholder")}
          required
          aria-invalid={Boolean(state.fieldErrors?.email)}
        />
      </div>

      <div className="space-y-1.5">
        <Label htmlFor="password">{t("passwordLabel")}</Label>
        <Input
          id="password"
          name="password"
          type="password"
          autoComplete="current-password"
          placeholder={t("passwordPlaceholder")}
          required
          aria-invalid={Boolean(state.fieldErrors?.password)}
        />
      </div>

      <div className="space-y-1.5">
        <Label htmlFor="lang">{t("languageLabel")}</Label>
        <Select id="lang" name="lang" defaultValue={defaultLang}>
          <option value="me">{t("languageMe")}</option>
          <option value="en">{t("languageEn")}</option>
        </Select>
      </div>

      <Button type="submit" className="w-full" disabled={isPending}>
        {isPending ? t("submitting") : t("submit")}
      </Button>

      <p className="text-center text-xs text-slate-500 dark:text-slate-400">
        {t("footerNote")}
      </p>
    </form>
  );
}
