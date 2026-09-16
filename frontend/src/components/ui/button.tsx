import * as React from "react";
import { cn } from "@/lib/utils";

export type ButtonVariant = "primary" | "secondary" | "ghost" | "destructive";

export interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant;
}

const VARIANT_CLASSES: Record<ButtonVariant, string> = {
  primary:
    "bg-slate-900 text-white hover:bg-slate-800 dark:bg-slate-100 dark:text-slate-900 dark:hover:bg-white",
  secondary:
    "bg-slate-100 text-slate-900 hover:bg-slate-200 dark:bg-slate-800 dark:text-slate-100 dark:hover:bg-slate-700",
  ghost: "bg-transparent hover:bg-slate-100 dark:hover:bg-slate-800",
  destructive: "bg-red-600 text-white hover:bg-red-700",
};

/**
 * Dijeljena klasa dugmeta — koristi je i `<Button>` (pravi `<button>`) i bilo
 * koji drugi element koji treba da IZGLEDA kao dugme (npr. next-intl `<Link>`
 * za navigaciju). Nema "asChild" API (Radix Slot) u ovom primitivnom skupu —
 * `Button` uvijek renderuje `<button>`, nikad nije wrapper oko `<a>`
 * (ugnježdeni `<a>` unutar `<button>` je nevalidan HTML).
 */
export function buttonVariants(variant: ButtonVariant = "primary", className?: string): string {
  return cn(
    "inline-flex items-center justify-center gap-2 rounded-md px-4 py-2 text-sm font-medium",
    "transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-slate-600 dark:focus-visible:ring-slate-300",
    "disabled:pointer-events-none disabled:opacity-50",
    VARIANT_CLASSES[variant],
    className
  );
}

/**
 * Generička dugme primitiva (ARCHITECTURE.md Sekcija 3 — `components/ui/`
 * ne smije znati ništa o SAR-u/CIP-u/CAF terminologiji).
 */
export const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant = "primary", disabled, ...props }, ref) => (
    <button
      ref={ref}
      disabled={disabled}
      className={buttonVariants(variant, className)}
      {...props}
    />
  )
);
Button.displayName = "Button";
