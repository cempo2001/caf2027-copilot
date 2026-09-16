import { createNavigation } from "next-intl/navigation";
import { routing } from "./routing";

// Locale-svjesni Link/useRouter/redirect — svaka navigacija u aplikaciji
// automatski čuva /me/... ili /en/... prefiks (CLAUDE.md 6.2).
export const { Link, redirect, usePathname, useRouter, getPathname } =
  createNavigation(routing);
