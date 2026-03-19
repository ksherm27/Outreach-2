"use client";

import { useTransition, useState } from "react";
import { toggleAutomation, triggerScrapeRun, clearScrapedJobs } from "@/app/actions/scraping";

const ALL_BOARDS = [
  "greenhouse", "lever", "ashby", "workable", "smartrecruiters",
  "jazzhr", "jobvite", "wellfound", "bamboohr", "rippling",
  "icims", "recruiterbox", "workday", "linkedin", "indeed",
];

export function AutomationToggle({ initialEnabled }: { initialEnabled: boolean }) {
  const [isPending, startTransition] = useTransition();
  const [enabled, setEnabled] = useState(initialEnabled);

  return (
    <div className="flex items-center gap-3 p-3 bg-[#111118] border border-[#1e1e2e] rounded-xl">
      <div className="flex-1">
        <p className="text-sm font-medium text-gray-200">Automated Scraping</p>
        <p className="text-xs text-gray-500">
          {enabled
            ? "Scraping runs automatically every 6 hours via Celery Beat"
            : "Automation is off \u2014 use manual triggers below to run scrapes"}
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
          enabled ? "bg-emerald-500" : "bg-[#2a2a3a]"
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
    <div className="p-3 bg-[#111118] border border-[#1e1e2e] rounded-xl">
      <p className="text-sm font-medium text-gray-200 mb-2">Manual Scrape</p>
      <div className="flex items-center gap-2 flex-wrap">
        <button
          type="button"
          disabled={isPending}
          onClick={() => handleTrigger()}
          className="px-4 py-1.5 text-sm bg-cyan-600 text-white rounded-lg hover:bg-cyan-500 disabled:opacity-50 transition-colors"
        >
          {isPending ? "Queuing..." : "Run All Boards"}
        </button>
        <button
          type="button"
          disabled={isPending}
          onClick={() => setShowBoardPicker(!showBoardPicker)}
          className="px-4 py-1.5 text-sm bg-[#1a1a24] text-gray-400 rounded-lg hover:bg-[#252533] border border-[#2a2a3a] transition-colors"
        >
          Run Single Board
        </button>
        {result && (
          <span className="text-xs text-emerald-400 bg-emerald-500/10 px-2 py-1 rounded-lg border border-emerald-500/20">{result}</span>
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
              className="px-2.5 py-1 text-xs bg-[#1a1a24] text-gray-400 rounded-lg border border-[#2a2a3a] hover:bg-cyan-500/10 hover:text-cyan-400 hover:border-cyan-500/20 disabled:opacity-50 transition-colors"
            >
              {board}
            </button>
          ))}
        </div>
      )}

      <div className="mt-3 p-2 bg-[#0d0d14] rounded-lg border border-[#1e1e2e]">
        <p className="text-xs text-gray-500 font-medium mb-1">Standalone CLI</p>
        <code className="text-xs text-cyan-400 font-mono">
          python3 scripts/run_once.py scrape
        </code>
        <p className="text-xs text-gray-500 mt-1">
          Run directly from terminal for testing. Also supports: <code className="font-mono text-cyan-400/70">score</code>, <code className="font-mono text-cyan-400/70">poll</code>, <code className="font-mono text-cyan-400/70">full</code>
        </p>
      </div>
    </div>
  );
}

export function ClearJobsButton() {
  const [isPending, startTransition] = useTransition();
  const [showConfirm, setShowConfirm] = useState(false);
  const [result, setResult] = useState<string | null>(null);

  const handleClear = () => {
    startTransition(async () => {
      const res = await clearScrapedJobs();
      if (res.success) {
        setShowConfirm(false);
        setResult(`Cleared ${res.jobsDeleted} jobs and ${res.runsDeleted} runs`);
        setTimeout(() => setResult(null), 5000);
      }
    });
  };

  return (
    <div className="p-3 bg-[#111118] border border-[#1e1e2e] rounded-xl">
      <p className="text-sm font-medium text-gray-200 mb-2">Clear Data</p>
      {!showConfirm ? (
        <button
          type="button"
          onClick={() => setShowConfirm(true)}
          className="px-4 py-1.5 text-sm bg-rose-600/20 text-rose-400 rounded-lg hover:bg-rose-600/30 border border-rose-500/20 transition-colors"
        >
          Clear All Scraped Jobs
        </button>
      ) : (
        <div className="flex items-center gap-2">
          <span className="text-xs text-rose-400">Delete all jobs and run history?</span>
          <button
            type="button"
            disabled={isPending}
            onClick={handleClear}
            className="px-3 py-1.5 text-sm bg-rose-600 text-white rounded-lg hover:bg-rose-500 disabled:opacity-50 transition-colors"
          >
            {isPending ? "Clearing..." : "Yes, Clear All"}
          </button>
          <button
            type="button"
            disabled={isPending}
            onClick={() => setShowConfirm(false)}
            className="px-3 py-1.5 text-sm bg-[#1a1a24] text-gray-400 rounded-lg hover:bg-[#252533] border border-[#2a2a3a] transition-colors"
          >
            Cancel
          </button>
        </div>
      )}
      {result && (
        <span className="mt-2 inline-block text-xs text-emerald-400 bg-emerald-500/10 px-2 py-1 rounded-lg border border-emerald-500/20">{result}</span>
      )}
    </div>
  );
}
