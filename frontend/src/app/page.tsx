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

  // Recent replies
  const recentReplies = await prisma.replies.findMany({
    take: 10,
    orderBy: { received_at: "desc" },
    include: { contact: { include: { company: true } } },
  });

  return (
    <div>
      <h2 className="text-2xl font-bold mb-6">Overview</h2>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
        <StatCard title="Total Jobs Scraped" value={totalJobs} color="blue" />
        <StatCard title="Qualified Leads" value={qualifiedJobs} color="green" />
        <StatCard title="Contacts" value={totalContacts} color="purple" />
        <StatCard title="Active Outreach" value={activeOutreach} color="yellow" />
        <StatCard title="Total Replies" value={totalReplies} color="blue" />
        <StatCard title="Positive Replies" value={positiveReplies} subtitle={`${positiveRate}% of replies`} color="green" />
        <StatCard title="Reply Rate" value={`${replyRate}%`} color="purple" />
        <StatCard title="Suppressed" value={suppressedCount} color="red" />
      </div>

      <h3 className="text-lg font-semibold mb-3">Recent Replies</h3>
      {recentReplies.length === 0 ? (
        <p className="text-sm text-gray-500">No replies yet.</p>
      ) : (
        <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
          <table className="min-w-full text-sm">
            <thead className="bg-gray-50 border-b">
              <tr>
                <th className="px-4 py-2 text-left font-medium text-gray-600">Contact</th>
                <th className="px-4 py-2 text-left font-medium text-gray-600">Company</th>
                <th className="px-4 py-2 text-left font-medium text-gray-600">Type</th>
                <th className="px-4 py-2 text-left font-medium text-gray-600">Received</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {recentReplies.map((r) => (
                <tr key={r.id} className="hover:bg-gray-50">
                  <td className="px-4 py-2">
                    {r.contact.first_name} {r.contact.last_name}
                  </td>
                  <td className="px-4 py-2 text-gray-600">
                    {r.contact.company?.name ?? "—"}
                  </td>
                  <td className="px-4 py-2">
                    <span className={`inline-flex px-2 py-0.5 rounded text-xs font-medium ${
                      r.reply_type === "positive" ? "bg-green-100 text-green-700" :
                      r.reply_type === "objection" ? "bg-yellow-100 text-yellow-700" :
                      r.reply_type === "unsubscribe" ? "bg-red-100 text-red-700" :
                      "bg-gray-100 text-gray-700"
                    }`}>
                      {r.reply_type ?? "pending"}
                    </span>
                  </td>
                  <td className="px-4 py-2 text-gray-500">
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
