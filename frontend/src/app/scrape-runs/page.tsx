import { prisma } from "@/lib/prisma";
import { Badge, statusBadgeVariant } from "@/components/badge";
import { AutomationToggle, ManualScrapeControls } from "./scrape-controls";

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
      <h2 className="text-2xl font-bold mb-6">Scrape Runs</h2>

      <div className="grid grid-cols-2 gap-4 mb-6">
        <AutomationToggle initialEnabled={automationEnabled} />
        <ManualScrapeControls />
      </div>

      <div className="grid grid-cols-5 gap-4 mb-6">
        <div className="rounded-lg border p-4 bg-blue-50 text-blue-700 border-blue-200">
          <p className="text-xs font-medium uppercase tracking-wide opacity-70">Total Runs</p>
          <p className="mt-1 text-2xl font-bold">{runs.length}</p>
        </div>
        <div className="rounded-lg border p-4 bg-green-50 text-green-700 border-green-200">
          <p className="text-xs font-medium uppercase tracking-wide opacity-70">Completed</p>
          <p className="mt-1 text-2xl font-bold">{completedRuns.length}</p>
        </div>
        <div className="rounded-lg border p-4 bg-red-50 text-red-700 border-red-200">
          <p className="text-xs font-medium uppercase tracking-wide opacity-70">Failed</p>
          <p className="mt-1 text-2xl font-bold">{failedRuns.length}</p>
        </div>
        <div className="rounded-lg border p-4 bg-yellow-50 text-yellow-700 border-yellow-200">
          <p className="text-xs font-medium uppercase tracking-wide opacity-70">Queued</p>
          <p className="mt-1 text-2xl font-bold">{queuedRuns.length}</p>
        </div>
        <div className="rounded-lg border p-4 bg-purple-50 text-purple-700 border-purple-200">
          <p className="text-xs font-medium uppercase tracking-wide opacity-70">New Jobs</p>
          <p className="mt-1 text-2xl font-bold">{totalNew}</p>
          <p className="mt-1 text-xs opacity-60">of {totalJobsFound} found</p>
        </div>
      </div>

      <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
        <table className="min-w-full text-sm">
          <thead className="bg-gray-50 border-b">
            <tr>
              <th className="px-4 py-2 text-left font-medium text-gray-600">ID</th>
              <th className="px-4 py-2 text-left font-medium text-gray-600">Board</th>
              <th className="px-4 py-2 text-left font-medium text-gray-600">Status</th>
              <th className="px-4 py-2 text-left font-medium text-gray-600">Found</th>
              <th className="px-4 py-2 text-left font-medium text-gray-600">New</th>
              <th className="px-4 py-2 text-left font-medium text-gray-600">Dupes</th>
              <th className="px-4 py-2 text-left font-medium text-gray-600">Started</th>
              <th className="px-4 py-2 text-left font-medium text-gray-600">Duration</th>
              <th className="px-4 py-2 text-left font-medium text-gray-600">Error</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
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
                <tr key={run.id} className="hover:bg-gray-50">
                  <td className="px-4 py-2 text-gray-400">#{run.id}</td>
                  <td className="px-4 py-2"><Badge label={run.board_name} variant="info" /></td>
                  <td className="px-4 py-2"><Badge label={run.status} variant={statusBadgeVariant(run.status)} /></td>
                  <td className="px-4 py-2">{run.jobs_found}</td>
                  <td className="px-4 py-2 font-medium text-green-600">{run.jobs_new}</td>
                  <td className="px-4 py-2 text-gray-400">{run.jobs_duplicate}</td>
                  <td className="px-4 py-2 text-gray-500">{new Date(run.started_at).toLocaleString()}</td>
                  <td className="px-4 py-2 text-gray-500">{duration !== null ? `${duration}s` : "—"}</td>
                  <td className="px-4 py-2 text-red-500 max-w-[200px] truncate">{run.error_message ?? "—"}</td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}
