import { readFileSync } from "node:fs";
import path from "node:path";

/**
 * Tekstovi iz ISTIH i18n kataloga koje koristi aplikacija — test ne
 * duplira stringove, pa promjena prevoda ne lomi selektore tiho.
 */
export type Lang = "me" | "en";

type Catalog = Record<string, Record<string, string>>;

const MESSAGES_DIR = path.resolve(process.cwd(), "src", "i18n", "messages");
const catalogs: Record<Lang, Catalog> = {
  me: JSON.parse(readFileSync(path.join(MESSAGES_DIR, "me.json"), "utf-8")) as Catalog,
  en: JSON.parse(readFileSync(path.join(MESSAGES_DIR, "en.json"), "utf-8")) as Catalog,
};

export function msg(
  lang: Lang,
  namespace: string,
  key: string,
  vars: Record<string, string | number> = {}
): string {
  const template = catalogs[lang][namespace]?.[key];
  if (template === undefined) {
    throw new Error(`Nedostaje poruka ${lang}:${namespace}.${key}`);
  }
  return Object.entries(vars).reduce(
    (text, [name, value]) => text.replaceAll(`{${name}}`, String(value)),
    template
  );
}

/** Regex koji traži poruku sa promjenljivim dijelom na mjestu `{placeholder}`. */
export function msgPattern(lang: Lang, namespace: string, key: string, placeholder: string): RegExp {
  const [before = "", after = ""] = msg(lang, namespace, key).split(`{${placeholder}}`);
  const escape = (s: string) => s.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
  return new RegExp(`${escape(before)}.+${escape(after)}`);
}
