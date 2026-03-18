import { prisma } from "@/lib/prisma";
import { StatCard } from "@/components/stat-card";

export const dynamic = "force-dynamic";

export default async function OverviewPage() {
  const [
    totalJobs,
    qualifiedJobs,
    totalContacts,
    activeOutreach,
    totalReplies,
    positiveReplies,
    scrapeRuns,
    suppressedCount,
  ] = await Promise.all([
    prisma.scraped_jobs.count(),
    prisma.scraped_jobs.count({ where: { is_qualified: true } }),
    prisma.contacts.count(),
    prisma.outreach_messages.count({ where: { status: "launched" } }),
    prisma.replies.count(),
    prisma.replies.count({ where: { reply_type: "positive" } }),
    prisma.scrape_runs.count(),
    prisma.suppression_list.count(),
  ]);

  const replyRate = totalReplies > 0 && activeOutreach > 0
    ? ((totalReplies / (activeOutreach + totalReplies)) * 100).toFixed(1)
    : "0";

  const positiveRate = totalReplies > 0
    ? ((positiveReplies / totalReplies) * 100).toFixed(1)
    : "0";

  const recentReplies = await prisma.replies.findMany({
    take: 10,
    orderBy: { received_at: "desc" },
    include: { contact: { include: { company: true } } },
  });

  return (
    <div>
      <h2 className="text-2xl font-bold mb-8 text-gray-100">Overview</h2>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-10">
        <StatCard title="Total Jobs Scraped" value={totalJobs} color="blue" />
        <StatCard title="Qualified Leads" value={qualifiedJobs} color="green" />
        <StatCard title="Contacts" value={totalContacts} color="purple" />
        <StatCard title="Active Outreach" value={activeOutreach} color="yellow" />
        <StatCard title="Total Replies" value={totalReplies} color="blue" />
        <StatCard title="Positive Replies" value={positiveReplies} subtitle={`${positiveRate}% of replies`} color="green" />
        <StatCard title="Reply Rate" value={`${replyRate}%`} color="purple" />
        <StatCard title="Suppressed" value={suppressedCount} color="red" />
      </div>

      <h3 className="text-lg font-semibold mb-4 text-gray-200">Recent Replies</h3>
      {recentReplies.length === 0 ? (
        <p className="text-sm text-gray-500">No replies yet.</p>
      ) : (
        <div className="bg-[#111118] rounded-xl border border-[#1e1e2e] overflow-hidden">
          <table className="min-w-full text-sm">
            <thead className="bg-[#0d0d14] border-b border-[#1e1e2e]">
              <tr>
                <th className="px-4 py-3 text-left text-[11px] font-medium uppercase tracking-wider text-gray-500">Contact</th>
                <th className="px-4 py-3 text-left text-[11px] font-medium uppercase tracking-wider text-gray-500">Company</th>
                <th className="px-4 py-3 text-left text-[11px] font-medium uppercase tracking-wider text-gray-500">Type</th>
                <th className="px-4 py-3 text-left text-[11px] font-medium uppercase tracking-wider text-gray-500">Received</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#1e1e2e]">
              {recentReplies.map((r) => (
                <tr key={r.id} className="hover:bg-[#1a1a24] transition-colors">
                  <td className="px-4 py-3 text-gray-200">
                    {r.contact.first_name} {r.contact.last_name}
                  </td>
                  <td className="px-4 py-3 text-gray-400">
                    {r.contact.company?.name ?? "\u2014"}
                  </td>
                  <td className="px-4 py-3">
                    <span className={`inline-flex px-2.5 py-0.5 rounded-md text-xs font-medium border ${
                      r.reply_type === "positive" ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/20" :
                      r.reply_type === "objection" ? "bg-amber-500/10 text-amber-400 border-amber-500/20" :
                      r.reply_type === "unsubscribe" ? "bg-rose-500/10 text-rose-400 border-rose-500/20" :
                      "bg-gray-500/10 text-gray-400 border-gray-500/20"
                    }`}>
                      {r.reply_type ?? "pending"}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-gray-500">
                    {new Date(r.received_at).toLocaleDateString()}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
