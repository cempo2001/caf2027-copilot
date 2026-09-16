import { redirect } from "next/navigation";
import { getSession } from "@/lib/auth";

/**
 * Root rute (/me, /en) nemaju sopstveni sadržaj — samo usmjeravaju na login
 * ili dashboard u zavisnosti od sesije. Provjera sesije je server-side
 * (Server Component), token se nikad ne dotiče na klijentu.
 */
export default async function RootPage({
  params,
}: {
  params: Promise<{ locale: string }>;
}) {
  const { locale } = await params;
  const session = await getSession();

  redirect(session ? `/${locale}/dashboard` : `/${locale}/login`);
}
