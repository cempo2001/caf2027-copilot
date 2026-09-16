"use client";

import { Moon, Sun } from "lucide-react";
import { useTranslations } from "next-intl";
import { Button } from "@/components/ui/button";
import { useTheme } from "@/components/theme-provider";

export function ThemeToggle() {
  const { theme, toggleTheme } = useTheme();
  const t = useTranslations("Common");

  return (
    <Button
      type="button"
      variant="ghost"
      onClick={toggleTheme}
      aria-label={theme === "light" ? t("themeDark") : t("themeLight")}
      title={theme === "light" ? t("themeDark") : t("themeLight")}
    >
      {theme === "light" ? <Moon className="size-4" /> : <Sun className="size-4" />}
    </Button>
  );
}
