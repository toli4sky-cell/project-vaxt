import type { ButtonHTMLAttributes } from "react";
import { cn } from "@/shared/lib/cn";

type Props = ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: "primary" | "ghost";
};

export function Button({ className, variant = "primary", ...props }: Props) {
  return (
    <button
      type="button"
      className={cn(
        "inline-flex items-center justify-center rounded-lg px-4 py-2 text-sm font-medium transition-colors",
        variant === "primary" &&
          "bg-sky-600 text-white hover:bg-sky-500 disabled:cursor-not-allowed disabled:opacity-50",
        variant === "ghost" && "text-slate-300 hover:bg-slate-800 hover:text-white",
        className,
      )}
      {...props}
    />
  );
}
