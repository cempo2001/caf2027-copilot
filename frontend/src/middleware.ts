import createMiddleware from "next-intl/middleware";
import { routing } from "@/i18n/routing";

export default createMiddleware(routing);

export const config = {
  // Sve rute osim Next.js internih, statičkih fajlova i API route handlera
  // (koji su, po ARCHITECTURE.md Sekciji 3, samo za BFF potrebe — ne
  // poslovna logika, ne treba im locale prefiks).
  matcher: ["/((?!api|_next|_vercel|.*\\..*).*)"],
};
