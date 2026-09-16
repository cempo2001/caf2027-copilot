import { redirect } from "next/navigation";
import { getTranslations } from "next-intl/server";
import { getSession } from "@/lib/auth";
import { ThemeToggle } from "@/components/theme-toggle";
import { logoutAction } from "@/features/auth/logout-action";
import { Button } from "@/components/ui/button";
import { Link } from "@/i18n/navigation";

/**
 * Role-gated route group za Nivo 1 (Institucija) — vidi ARCHITECTURE.md
 * Sekcija 3. Svaka ruta ispod (wizard, sar, cip, dashboard) prolazi kroz ovu
 * provjeru sesije prije renderovanja; per-rutinska provjera ROLE (npr.
 * Employee ne vidi Approve dugme) radi se u samoj feature komponenti, ne
 * ovdje — ovaj layout garantuje samo "postoji validna sesija".
 */
export default async function InstitutionLayout({
  children,
  params,
}: {
  children: React.ReactNode;
  params: Promise<{ locale: string }>;
}) {
  const { locale } = await params;
  const session = await getSession();
  if (!session) {
    redirect(`/${locale}/login`);
  }

  const t = await getTranslations({ locale, namespace: "Nav" });

  return (
    <div className="min-h-svh">
      <header className="flex items-center justify-between border-b border-slate-200 px-6 py-3 dark:border-slate-800">
        <div className="flex items-center gap-6">
          <span className="text-sm font-semibold tracking-tight">CAF 2027 Copilot</span>
          <nav className="flex items-center gap-4 text-sm text-slate-500 dark:text-slate-400">
            <Link
              href="/dashboard"
              locale={locale}
              className="hover:text-slate-900 dark:hover:text-slate-100"
            >
              {t("dashboard")}
            </Link>
            <Link
              href="/cip"
              locale={locale}
              className="hover:text-slate-900 dark:hover:text-slate-100"
            >
              {t("cip")}
            </Link>
          </nav>
        </div>
        <div className="flex items-center gap-3">
          <span className="text-sm text-slate-500 dark:text-slate-400">
            {session.user.email}
          </span>
          <ThemeToggle />
          <form action={logoutAction}>
            <Button type="submit" variant="secondary">
              {t("logout")}
            </Button>
          </form>
        </div>
      </header>
      <main className="px-6 py-8">{children}</main>
    </div>
  );
}
