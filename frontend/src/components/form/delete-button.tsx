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
          className="text-xs px-2 py-1 bg-red-600 text-white rounded hover:bg-red-700 disabled:opacity-50"
        >
          {isPending ? "..." : "Confirm"}
        </button>
        <button
          type="button"
          onClick={() => setConfirming(false)}
          className="text-xs px-2 py-1 bg-gray-200 text-gray-700 rounded hover:bg-gray-300"
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
      className="text-xs text-red-600 hover:text-red-800"
    >
      {label}
    </button>
  );
}
