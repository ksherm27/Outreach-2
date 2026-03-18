"use client";

import { useTransition, useState } from "react";
import {
  pauseOutreachMessage,
  resumeOutreachMessage,
  launchOutreachMessage,
  stopOutreachMessage,
  bulkPauseOutreach,
  bulkResumeOutreach,
  bulkStopOutreach,
} from "@/app/actions/outreach";

export function OutreachRowActions({ id, status }: { id: number; status: string }) {
  const [isPending, startTransition] = useTransition();

  if (status === "completed") {
    return <span className="text-xs text-gray-400">Stopped</span>;
  }

  return (
    <div className="flex items-center gap-1.5">
      {status === "pending" && (
        <button
          type="button"
          disabled={isPending}
          onClick={() => startTransition(async () => { await launchOutreachMessage(id); })}
          className="px-2 py-0.5 text-xs bg-green-600 text-white rounded hover:bg-green-700 disabled:opacity-50"
        >
          {isPending ? "..." : "Launch"}
        </button>
      )}
      {status === "launched" && (
        <button
          type="button"
          disabled={isPending}
          onClick={() => startTransition(async () => { await pauseOutreachMessage(id); })}
          className="px-2 py-0.5 text-xs bg-yellow-500 text-white rounded hover:bg-yellow-600 disabled:opacity-50"
        >
          {isPending ? "..." : "Pause"}
        </button>
      )}
      {status === "paused" && (
        <button
          type="button"
          disabled={isPending}
          onClick={() => startTransition(async () => { await resumeOutreachMessage(id); })}
          className="px-2 py-0.5 text-xs bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50"
        >
          {isPending ? "..." : "Resume"}
        </button>
      )}
      <button
        type="button"
        disabled={isPending}
        onClick={() => startTransition(async () => { await stopOutreachMessage(id); })}
        className="px-2 py-0.5 text-xs bg-red-600 text-white rounded hover:bg-red-700 disabled:opacity-50"
      >
        {isPending ? "..." : "Stop"}
      </button>
    </div>
  );
}

export function BulkActions({
  filters,
  launchedCount,
  pausedCount,
}: {
  filters: { status?: string; platform?: string };
  launchedCount: number;
  pausedCount: number;
}) {
  const [isPending, startTransition] = useTransition();
  const [confirming, setConfirming] = useState<string | null>(null);
  const [result, setResult] = useState<string | null>(null);

  const handleAction = (action: string) => {
    setConfirming(null);
    setResult(null);
    startTransition(async () => {
      let res;
      if (action === "pause") {
        res = await bulkPauseOutreach(filters);
      } else if (action === "resume") {
        res = await bulkResumeOutreach(filters);
      } else {
        res = await bulkStopOutreach(filters);
      }
      if (res.success) {
        setResult(`${res.count} message${res.count === 1 ? "" : "s"} updated.`);
        setTimeout(() => setResult(null), 3000);
      }
    });
  };

  if (confirming) {
    const labels: Record<string, string> = {
      pause: `Pause all ${launchedCount} launched messages?`,
      resume: `Resume all ${pausedCount} paused messages?`,
      stop: "Stop all active messages? This cannot be undone.",
    };
    return (
      <div className="flex items-center gap-2 mb-4 p-3 bg-yellow-50 border border-yellow-200 rounded-lg">
        <span className="text-sm text-yellow-800">{labels[confirming]}</span>
        <button
          type="button"
          disabled={isPending}
          onClick={() => handleAction(confirming)}
          className="px-3 py-1 text-xs bg-red-600 text-white rounded hover:bg-red-700 disabled:opacity-50"
        >
          {isPending ? "Processing..." : "Confirm"}
        </button>
        <button
          type="button"
          onClick={() => setConfirming(null)}
          className="px-3 py-1 text-xs bg-gray-200 text-gray-700 rounded hover:bg-gray-300"
        >
          Cancel
        </button>
      </div>
    );
  }

  return (
    <div className="flex items-center gap-2 mb-4">
      <span className="text-xs text-gray-500 font-medium mr-1">Bulk:</span>
      {launchedCount > 0 && (
        <button
          type="button"
          onClick={() => setConfirming("pause")}
          className="px-3 py-1 text-xs bg-yellow-100 text-yellow-800 rounded hover:bg-yellow-200 border border-yellow-300"
        >
          Pause All ({launchedCount})
        </button>
      )}
      {pausedCount > 0 && (
        <button
          type="button"
          onClick={() => setConfirming("resume")}
          className="px-3 py-1 text-xs bg-blue-100 text-blue-800 rounded hover:bg-blue-200 border border-blue-300"
        >
          Resume All ({pausedCount})
        </button>
      )}
      <button
        type="button"
        onClick={() => setConfirming("stop")}
        className="px-3 py-1 text-xs bg-red-100 text-red-800 rounded hover:bg-red-200 border border-red-300"
      >
        Stop All
      </button>
      {result && (
        <span className="text-xs text-green-700 bg-green-50 px-2 py-1 rounded">{result}</span>
      )}
    </div>
  );
}
