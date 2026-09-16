import { notFound, redirect } from "next/navigation";
import { getTranslations, setRequestLocale } from "next-intl/server";
import { isSupportedLocale } from "@/i18n/routing";
import { getSession } from "@/lib/auth";
import { ThemeToggle } from "@/components/theme-toggle";
import { LoginForm } from "@/features/auth/components/login-form";

export default async function LoginPage({
  params,
}: {
  params: Promise<{ locale: string }>;
}) {
  const { locale } = await params;
  if (!isSupportedLocale(locale)) {
    notFound();
  }
  setRequestLocale(locale);

  // Već ulogovan korisnik ne treba da vidi login formu ponovo.
  const session = await getSession();
  if (session) {
    redirect(`/${locale}/dashboard`);
  }

  const t = await getTranslations({ locale, namespace: "Login" });

  return (
    <main className="flex min-h-svh items-center justify-center px-4 py-12">
      <div className="w-full max-w-sm space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-xl font-semibold tracking-tight">{t("title")}</h1>
            <p className="text-sm text-slate-500 dark:text-slate-400">{t("subtitle")}</p>
          </div>
          <ThemeToggle />
        </div>

        <div className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm dark:border-slate-800 dark:bg-slate-900">
          <LoginForm defaultLang={locale === "en" ? "en" : "me"} />
        </div>
      </div>
    </main>
  );
}
