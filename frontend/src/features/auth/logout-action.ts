"use server";

import { redirect } from "next/navigation";
import { destroySession, getSession } from "@/lib/auth";

export async function logoutAction(): Promise<void> {
  const session = await getSession();
  const locale = session?.user.lang ?? "me";
  await destroySession();
  redirect(`/${locale}/login`);
}
