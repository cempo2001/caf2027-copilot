import { defineRouting } from "next-intl/routing";

/**
 * Definicija podržanih lokala — sr-ME (crnogorski) i en-US (CLAUDE.md
 * Sekcija 6). Kod lokala u ruti je kratak ("me" / "en") jer next-intl
 * App Router segment mora biti stabilan URL segment; puni BCP-47 tag
 * (me-ME / en-US) se koristi samo u JWT `lang` claim-u i Intl formatiranju,
 * ne u samoj ruti.
 *
 * Nema "default bez prefiksa" (localePrefix: "always") — CLAUDE.md 6.2
 * eksplicitno traži da jezik bude dio URL-a, ne pretpostavljen.
 */
export const routing = defineRouting({
  locales: ["me", "en"],
  defaultLocale: "me",
  localePrefix: "always",
});

export type AppLocale = (typeof routing.locales)[number];

/**
 * Lokalna zamjena za next-intl-ov `hasLocale` helper. Pisana ručno umjesto
 * uvezena iz `next-intl`/`use-intl` jer se ime i lokacija tog exporta
 * mijenjaju između manjih verzija biblioteke (vidi incident: `hasLocale is
 * not a function` nakon rutinskog `npm install` koji je povukao noviju
 * verziju) — ova provjera ne zavisi ni od čega osim `routing.locales`.
 */
export function isSupportedLocale(value: string | undefined | null): value is AppLocale {
  return !!value && (routing.locales as readonly string[]).includes(value);
}
