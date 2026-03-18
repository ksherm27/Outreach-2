"use client";

import { useTransition } from "react";

export function ToggleSwitch({
  isActive,
  onToggle,
}: {
  isActive: boolean;
  onToggle: () => Promise<any>;
}) {
  const [isPending, startTransition] = useTransition();

  return (
    <button
      type="button"
      disabled={isPending}
      onClick={() => startTransition(() => onToggle())}
      className={`relative inline-flex h-5 w-9 items-center rounded-full transition-colors ${
        isActive ? "bg-emerald-500" : "bg-[#2a2a3a]"
      } ${isPending ? "opacity-50" : ""}`}
    >
      <span
        className={`inline-block h-3.5 w-3.5 transform rounded-full bg-white transition-transform ${
          isActive ? "translate-x-4" : "translate-x-0.5"
        }`}
      />
    </button>
  );
}
