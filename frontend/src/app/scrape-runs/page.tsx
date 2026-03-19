import { prisma } from "@/lib/prisma";
import { Badge, statusBadgeVariant } from "@/components/badge";
import { AutomationToggle, ManualScrapeControls, ClearJobsButton } from "./scrape-controls";

export const dynamic = "force-dynamic";

export default async function ScrapeRunsPage() {
  const [runs, automationSetting] = await Promise.all([
    prisma.scrape_runs.findMany({
      orderBy: { started_at: "desc" },
      take: 100,
    }),
    prisma.system_settings.findUnique({
      where: { key: "scraping_automation_enabled" },
    }),
  ]);

  const automationEnabled = automationSetting?.value === "true";
  const completedRuns = runs.filter(r => r.status === "completed");
  const failedRuns = runs.filter(r => r.status === "failed");
  const queuedRuns = runs.filter(r => r.status === "queued");
  const totalJobsFound = runs.reduce((sum, r) => sum + r.jobs_found, 0);
  const totalNew = runs.reduce((sum, r) => sum + r.jobs_new, 0);

  return (
    <div>
      <h2 className="text-2xl font-bold mb-8 text-gray-100">Scrape Runs</h2>

      <div className="grid grid-cols-3 gap-4 mb-6">
        <AutomationToggle initialEnabled={automationEnabled} />
        <ManualScrapeControls />
        <ClearJobsButton />
      </div>

      <div className="grid grid-cols-5 gap-4 mb-8">
        <div className="rounded-xl border p-5 bg-[#111118] border-cyan-500/20 hover:border-cyan-500/40 transition-all">
          <p className="text-[11px] font-medium uppercase tracking-wider text-gray-500">Total Runs</p>
          <p className="mt-2 text-3xl font-bold text-cyan-400">{runs.length}</p>
        </div>
        <div className="rounded-xl border p-5 bg-[#111118] border-emerald-500/20 hover:border-emerald-500/40 transition-all">
          <p className="text-[11px] font-medium uppercase tracking-wider text-gray-500">Completed</p>
          <p className="mt-2 text-3xl font-bold text-emerald-400">{completedRuns.length}</p>
        </div>
        <div className="rounded-xl border p-5 bg-[#111118] border-rose-500/20 hover:border-rose-500/40 transition-all">
          <p className="text-[11px] font-medium uppercase tracking-wider text-gray-500">Failed</p>
          <p className="mt-2 text-3xl font-bold text-rose-400">{failedRuns.length}</p>
        </div>
        <div className="rounded-xl border p-5 bg-[#111118] border-amber-500/20 hover:border-amber-500/40 transition-all">
          <p className="text-[11px] font-medium uppercase tracking-wider text-gray-500">Queued</p>
          <p className="mt-2 text-3xl font-bold text-amber-400">{queuedRuns.length}</p>
        </div>
        <div className="rounded-xl border p-5 bg-[#111118] border-violet-500/20 hover:border-violet-500/40 transition-all">
          <p className="text-[11px] font-medium uppercase tracking-wider text-gray-500">New Jobs</p>
          <p className="mt-2 text-3xl font-bold text-violet-400">{totalNew}</p>
          <p className="mt-1 text-xs text-gray-500">of {totalJobsFound} found</p>
        </div>
      </div>

      <div className="bg-[#111118] rounded-xl border border-[#1e1e2e] overflow-hidden">
        <table className="min-w-full text-sm">
          <thead className="bg-[#0d0d14] border-b border-[#1e1e2e]">
            <tr>
              <th className="px-4 py-3 text-left text-[11px] font-medium uppercase tracking-wider text-gray-500">ID</th>
              <th className="px-4 py-3 text-left text-[11px] font-medium uppercase tracking-wider text-gray-500">Board</th>
              <th className="px-4 py-3 text-left text-[11px] font-medium uppercase tracking-wider text-gray-500">Status</th>
              <th className="px-4 py-3 text-left text-[11px] font-medium uppercase tracking-wider text-gray-500">Found</th>
              <th className="px-4 py-3 text-left text-[11px] font-medium uppercase tracking-wider text-gray-500">New</th>
              <th className="px-4 py-3 text-left text-[11px] font-medium uppercase tracking-wider text-gray-500">Dupes</th>
              <th className="px-4 py-3 text-left text-[11px] font-medium uppercase tracking-wider text-gray-500">Started</th>
              <th className="px-4 py-3 text-left text-[11px] font-medium uppercase tracking-wider text-gray-500">Duration</th>
              <th className="px-4 py-3 text-left text-[11px] font-medium uppercase tracking-wider text-gray-500">Error</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-[#1e1e2e]">
            {runs.length === 0 && (
              <tr>
                <td colSpan={9} className="px-4 py-8 text-center text-sm text-gray-500">
                  No scrape runs yet. Use the controls above to trigger one.
                </td>
              </tr>
            )}
            {runs.map((run) => {
              const duration = run.completed_at && run.started_at
                ? Math.round((new Date(run.completed_at).getTime() - new Date(run.started_at).getTime()) / 1000)
                : null;

              return (
                <tr key={run.id} className="hover:bg-[#1a1a24] transition-colors">
                  <td className="px-4 py-3 text-gray-500">#{run.id}</td>
                  <td className="px-4 py-3"><Badge label={run.board_name} variant="info" /></td>
                  <td className="px-4 py-3"><Badge label={run.status} variant={statusBadgeVariant(run.status)} /></td>
                  <td className="px-4 py-3 text-gray-300">{run.jobs_found}</td>
                  <td className="px-4 py-3 font-medium text-emerald-400">{run.jobs_new}</td>
                  <td className="px-4 py-3 text-gray-500">{run.jobs_duplicate}</td>
                  <td className="px-4 py-3 text-gray-500">{new Date(run.started_at).toLocaleString()}</td>
                  <td className="px-4 py-3 text-gray-500">{duration !== null ? `${duration}s` : "\u2014"}</td>
                  <td className="px-4 py-3 text-rose-400 max-w-[200px] truncate">{run.error_message ?? "\u2014"}</td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}
