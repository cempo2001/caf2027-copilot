import { getRequestConfig } from "next-intl/server";
import { isSupportedLocale, routing } from "./routing";

// next-intl server config — učitava poruke za aktivni [locale] segment rute.
// Ovo NIJE isto što i jezik u JWT-u (vidi lib/auth.ts): ruta određuje jezik
// UI-ja prije logina i za javne stranice; poslije logina, sesija drži svoj
// `lang` claim, a middleware.ts usmjerava korisnika na odgovarajući prefiks.
export default getRequestConfig(async ({ requestLocale }) => {
  const requested = await requestLocale;
  const locale = isSupportedLocale(requested) ? requested : routing.defaultLocale;

  return {
    locale,
    messages: (await import(`./messages/${locale}.json`)).default,
  };
});
