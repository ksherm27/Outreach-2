"use client";

import { useTransition, useState } from "react";

export function DeleteButton({
  onDelete,
  label = "Delete",
}: {
  onDelete: () => Promise<any>;
  label?: string;
}) {
  const [isPending, startTransition] = useTransition();
  const [confirming, setConfirming] = useState(false);

  if (confirming) {
    return (
      <span className="inline-flex gap-1">
        <button
          type="button"
          disabled={isPending}
          onClick={() => startTransition(() => onDelete())}
          className="text-xs px-2 py-1 bg-rose-600 text-white rounded hover:bg-rose-500 disabled:opacity-50"
        >
          {isPending ? "..." : "Confirm"}
        </button>
        <button
          type="button"
          onClick={() => setConfirming(false)}
          className="text-xs px-2 py-1 bg-[#1a1a24] text-gray-400 rounded hover:bg-[#252533] border border-[#2a2a3a]"
        >
          Cancel
        </button>
      </span>
    );
  }

  return (
    <button
      type="button"
      onClick={() => setConfirming(true)}
      className="text-xs text-rose-400 hover:text-rose-300"
    >
      {label}
    </button>
  );
}
