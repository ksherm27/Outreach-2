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
    return <span className="text-xs text-gray-500">Stopped</span>;
  }

  return (
    <div className="flex items-center gap-1.5">
      {status === "pending" && (
        <button
          type="button"
          disabled={isPending}
          onClick={() => startTransition(async () => { await launchOutreachMessage(id); })}
          className="px-2 py-0.5 text-xs bg-emerald-600 text-white rounded hover:bg-emerald-500 disabled:opacity-50 transition-colors"
        >
          {isPending ? "..." : "Launch"}
        </button>
      )}
      {status === "launched" && (
        <button
          type="button"
          disabled={isPending}
          onClick={() => startTransition(async () => { await pauseOutreachMessage(id); })}
          className="px-2 py-0.5 text-xs bg-amber-600 text-white rounded hover:bg-amber-500 disabled:opacity-50 transition-colors"
        >
          {isPending ? "..." : "Pause"}
        </button>
      )}
      {status === "paused" && (
        <button
          type="button"
          disabled={isPending}
          onClick={() => startTransition(async () => { await resumeOutreachMessage(id); })}
          className="px-2 py-0.5 text-xs bg-cyan-600 text-white rounded hover:bg-cyan-500 disabled:opacity-50 transition-colors"
        >
          {isPending ? "..." : "Resume"}
        </button>
      )}
      <button
        type="button"
        disabled={isPending}
        onClick={() => startTransition(async () => { await stopOutreachMessage(id); })}
        className="px-2 py-0.5 text-xs bg-rose-600 text-white rounded hover:bg-rose-500 disabled:opacity-50 transition-colors"
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
      <div className="flex items-center gap-2 mb-4 p-3 bg-amber-500/10 border border-amber-500/20 rounded-xl">
        <span className="text-sm text-amber-400">{labels[confirming]}</span>
        <button
          type="button"
          disabled={isPending}
          onClick={() => handleAction(confirming)}
          className="px-3 py-1 text-xs bg-rose-600 text-white rounded-lg hover:bg-rose-500 disabled:opacity-50 transition-colors"
        >
          {isPending ? "Processing..." : "Confirm"}
        </button>
        <button
          type="button"
          onClick={() => setConfirming(null)}
          className="px-3 py-1 text-xs bg-[#1a1a24] text-gray-400 rounded-lg hover:bg-[#252533] border border-[#2a2a3a] transition-colors"
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
          className="px-3 py-1 text-xs bg-amber-500/10 text-amber-400 rounded-lg hover:bg-amber-500/20 border border-amber-500/20 transition-colors"
        >
          Pause All ({launchedCount})
        </button>
      )}
      {pausedCount > 0 && (
        <button
          type="button"
          onClick={() => setConfirming("resume")}
          className="px-3 py-1 text-xs bg-cyan-500/10 text-cyan-400 rounded-lg hover:bg-cyan-500/20 border border-cyan-500/20 transition-colors"
        >
          Resume All ({pausedCount})
        </button>
      )}
      <button
        type="button"
        onClick={() => setConfirming("stop")}
        className="px-3 py-1 text-xs bg-rose-500/10 text-rose-400 rounded-lg hover:bg-rose-500/20 border border-rose-500/20 transition-colors"
      >
        Stop All
      </button>
      {result && (
        <span className="text-xs text-emerald-400 bg-emerald-500/10 px-2 py-1 rounded-lg border border-emerald-500/20">{result}</span>
      )}
    </div>
  );
}
