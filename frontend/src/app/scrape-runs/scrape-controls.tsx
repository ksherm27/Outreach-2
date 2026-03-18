"use client";

import { useTransition, useState } from "react";
import { toggleAutomation, triggerScrapeRun } from "@/app/actions/scraping";

const ALL_BOARDS = [
  "greenhouse", "lever", "ashby", "workable", "smartrecruiters",
  "jazzhr", "jobvite", "wellfound", "bamboohr", "rippling",
  "icims", "recruiterbox", "workday", "linkedin", "indeed",
];

export function AutomationToggle({ initialEnabled }: { initialEnabled: boolean }) {
  const [isPending, startTransition] = useTransition();
  const [enabled, setEnabled] = useState(initialEnabled);

  return (
    <div className="flex items-center gap-3 p-3 bg-white border border-gray-200 rounded-lg">
      <div className="flex-1">
        <p className="text-sm font-medium text-gray-900">Automated Scraping</p>
        <p className="text-xs text-gray-500">
          {enabled
            ? "Scraping runs automatically every 6 hours via Celery Beat"
            : "Automation is off — use manual triggers below to run scrapes"}
        </p>
      </div>
      <button
        type="button"
        disabled={isPending}
        onClick={() =>
          startTransition(async () => {
            const res = await toggleAutomation();
            if (res.success) setEnabled(res.enabled);
          })
        }
        className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
          enabled ? "bg-green-500" : "bg-gray-300"
        } ${isPending ? "opacity-50" : ""}`}
      >
        <span
          className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
            enabled ? "translate-x-6" : "translate-x-1"
          }`}
        />
      </button>
    </div>
  );
}

export function ManualScrapeControls() {
  const [isPending, startTransition] = useTransition();
  const [result, setResult] = useState<string | null>(null);
  const [showBoardPicker, setShowBoardPicker] = useState(false);

  const handleTrigger = (board?: string) => {
    setResult(null);
    setShowBoardPicker(false);
    startTransition(async () => {
      const res = await triggerScrapeRun(board);
      if (res.success) {
        setResult(
          board
            ? `Queued scrape for ${board}`
            : `Queued scrapes for ${res.count} boards`
        );
        setTimeout(() => setResult(null), 5000);
      }
    });
  };

  return (
    <div className="p-3 bg-white border border-gray-200 rounded-lg">
      <p className="text-sm font-medium text-gray-900 mb-2">Manual Scrape</p>
      <div className="flex items-center gap-2 flex-wrap">
        <button
          type="button"
          disabled={isPending}
          onClick={() => handleTrigger()}
          className="px-4 py-1.5 text-sm bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50"
        >
          {isPending ? "Queuing..." : "Run All Boards"}
        </button>
        <button
          type="button"
          disabled={isPending}
          onClick={() => setShowBoardPicker(!showBoardPicker)}
          className="px-4 py-1.5 text-sm bg-gray-100 text-gray-700 rounded hover:bg-gray-200 border border-gray-300"
        >
          Run Single Board
        </button>
        {result && (
          <span className="text-xs text-green-700 bg-green-50 px-2 py-1 rounded">{result}</span>
        )}
      </div>
      {showBoardPicker && (
        <div className="mt-3 flex flex-wrap gap-1.5">
          {ALL_BOARDS.map((board) => (
            <button
              key={board}
              type="button"
              disabled={isPending}
              onClick={() => handleTrigger(board)}
              className="px-2.5 py-1 text-xs bg-gray-50 text-gray-700 rounded border border-gray-200 hover:bg-blue-50 hover:text-blue-700 hover:border-blue-200 disabled:opacity-50"
            >
              {board}
            </button>
          ))}
        </div>
      )}

      <div className="mt-3 p-2 bg-gray-50 rounded border border-gray-100">
        <p className="text-xs text-gray-500 font-medium mb-1">Standalone CLI</p>
        <code className="text-xs text-gray-700 font-mono">
          python3 scripts/run_once.py scrape
        </code>
        <p className="text-xs text-gray-400 mt-1">
          Run directly from terminal for testing. Also supports: <code className="font-mono">score</code>, <code className="font-mono">poll</code>, <code className="font-mono">full</code>
        </p>
      </div>
    </div>
  );
}
