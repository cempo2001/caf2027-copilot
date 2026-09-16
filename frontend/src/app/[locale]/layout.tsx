import type { Metadata } from "next";
import { NextIntlClientProvider } from "next-intl";
import { getMessages, getTranslations, setRequestLocale } from "next-intl/server";
import { notFound } from "next/navigation";
import { isSupportedLocale, routing } from "@/i18n/routing";
import { ThemeProvider } from "@/components/theme-provider";
import "../globals.css";

export function generateStaticParams() {
  return routing.locales.map((locale) => ({ locale }));
}

export async function generateMetadata({
  params,
}: {
  params: Promise<{ locale: string }>;
}): Promise<Metadata> {
  const { locale } = await params;
  const t = await getTranslations({ locale, namespace: "Metadata" });
  return {
    title: t("title"),
    description: t("description"),
  };
}

/**
 * Root layout po jeziku (ARCHITECTURE.md Sekcija 3). `[locale]` je jedini
 * segment koji nosi <html>/<body> — nema odvojenog app/layout.tsx iznad njega
 * (next-intl App Router pattern: locale je dio strukture rute, ne wrapper).
 */
export default async function LocaleLayout({
  children,
  params,
}: {
  children: React.ReactNode;
  params: Promise<{ locale: string }>;
}) {
  const { locale } = await params;
  if (!isSupportedLocale(locale)) {
    notFound();
  }

  // Omogućava static rendering za ostatak stabla (next-intl zahtjev).
  setRequestLocale(locale);

  // Eksplicitno prosleđene poruke — NE oslanjati se na automatsko
  // nasleđivanje iz request config-a (ponašanje se razlikuje između
  // next-intl verzija, isti razlog kao `isSupportedLocale` umjesto
  // `hasLocale` u i18n/routing.ts). Bez ovoga client komponente koje pozovu
  // `useTranslations` van "Login"/"Metadata" namespace-a pucaju sa
  // MISSING_MESSAGE.
  const messages = await getMessages();

  return (
    <html lang={locale} suppressHydrationWarning>
      {/* suppressHydrationWarning i ovdje — browser ekstenzije (npr. Liner,
          Grammarly) ubacuju svoje atribute u <body> prije hidratacije, što
          inače prijavljuje lažno pozitivnu hydration grešku bez veze sa
          našim kodom. */}
      <body suppressHydrationWarning>
        <NextIntlClientProvider locale={locale} messages={messages}>
          <ThemeProvider>{children}</ThemeProvider>
        </NextIntlClientProvider>
      </body>
    </html>
  );
}
