import { prisma } from "@/lib/prisma";
import { Badge, statusBadgeVariant } from "@/components/badge";
import { StatCard } from "@/components/stat-card";
import { OutreachRowActions, BulkActions } from "./outreach-actions";

export const dynamic = "force-dynamic";

export default async function OutreachPage({
  searchParams,
}: {
  searchParams: Promise<{ status?: string; platform?: string; page?: string }>;
}) {
  const params = await searchParams;
  const page = parseInt(params.page ?? "1", 10);
  const pageSize = 50;

  const where: any = {};
  if (params.status) where.status = params.status;
  if (params.platform) where.platform = params.platform;

  const [messages, total, launched, paused, pending, completed] = await Promise.all([
    prisma.outreach_messages.findMany({
      where,
      orderBy: { created_at: "desc" },
      take: pageSize,
      skip: (page - 1) * pageSize,
      include: {
        contact: { include: { company: true } },
        job: true,
      },
    }),
    prisma.outreach_messages.count({ where }),
    prisma.outreach_messages.count({ where: { status: "launched" } }),
    prisma.outreach_messages.count({ where: { status: "paused" } }),
    prisma.outreach_messages.count({ where: { status: "pending" } }),
    prisma.outreach_messages.count({ where: { status: "completed" } }),
  ]);

  const totalPages = Math.ceil(total / pageSize);

  return (
    <div>
      <h2 className="text-2xl font-bold mb-6">Outreach</h2>

      <div className="grid grid-cols-4 gap-4 mb-6">
        <StatCard title="Launched" value={launched} color="green" />
        <StatCard title="Paused" value={paused} color="yellow" />
        <StatCard title="Pending" value={pending} color="blue" />
        <StatCard title="Stopped" value={completed} color="gray" />
      </div>

      <div className="flex gap-2 mb-4 flex-wrap">
        <a href="/outreach" className={`px-3 py-1 rounded text-sm ${!params.status && !params.platform ? 'bg-gray-900 text-white' : 'bg-gray-100 text-gray-700'}`}>All ({total})</a>
        <a href="/outreach?status=launched" className={`px-3 py-1 rounded text-sm ${params.status === 'launched' ? 'bg-green-600 text-white' : 'bg-gray-100 text-gray-700'}`}>Launched</a>
        <a href="/outreach?status=paused" className={`px-3 py-1 rounded text-sm ${params.status === 'paused' ? 'bg-yellow-600 text-white' : 'bg-gray-100 text-gray-700'}`}>Paused</a>
        <a href="/outreach?status=pending" className={`px-3 py-1 rounded text-sm ${params.status === 'pending' ? 'bg-blue-600 text-white' : 'bg-gray-100 text-gray-700'}`}>Pending</a>
        <a href="/outreach?status=completed" className={`px-3 py-1 rounded text-sm ${params.status === 'completed' ? 'bg-gray-600 text-white' : 'bg-gray-100 text-gray-700'}`}>Stopped</a>
        <span className="border-l border-gray-300 mx-1" />
        <a href="/outreach?platform=instantly" className={`px-3 py-1 rounded text-sm ${params.platform === 'instantly' ? 'bg-purple-600 text-white' : 'bg-gray-100 text-gray-700'}`}>Instantly</a>
        <a href="/outreach?platform=lemlist" className={`px-3 py-1 rounded text-sm ${params.platform === 'lemlist' ? 'bg-orange-600 text-white' : 'bg-gray-100 text-gray-700'}`}>Lemlist</a>
      </div>

      <BulkActions
        filters={{ status: params.status, platform: params.platform }}
        launchedCount={launched}
        pausedCount={paused}
      />

      <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
        <table className="min-w-full text-sm">
          <thead className="bg-gray-50 border-b">
            <tr>
              <th className="px-4 py-2 text-left font-medium text-gray-600">Contact</th>
              <th className="px-4 py-2 text-left font-medium text-gray-600">Company</th>
              <th className="px-4 py-2 text-left font-medium text-gray-600">Platform</th>
              <th className="px-4 py-2 text-left font-medium text-gray-600">Status</th>
              <th className="px-4 py-2 text-left font-medium text-gray-600">Job Title</th>
              <th className="px-4 py-2 text-left font-medium text-gray-600">Launched</th>
              <th className="px-4 py-2 text-left font-medium text-gray-600">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {messages.length === 0 && (
              <tr>
                <td colSpan={7} className="px-4 py-8 text-center text-sm text-gray-500">
                  No outreach messages found.
                </td>
              </tr>
            )}
            {messages.map((msg) => (
              <tr key={msg.id} className="hover:bg-gray-50">
                <td className="px-4 py-2">{msg.contact.first_name} {msg.contact.last_name}</td>
                <td className="px-4 py-2 text-gray-600">{msg.contact.company?.name ?? "—"}</td>
                <td className="px-4 py-2"><Badge label={msg.platform} variant="info" /></td>
                <td className="px-4 py-2"><Badge label={msg.status} variant={statusBadgeVariant(msg.status)} /></td>
                <td className="px-4 py-2 text-gray-600 max-w-[200px] truncate">{msg.job?.title ?? "—"}</td>
                <td className="px-4 py-2 text-gray-500">{msg.launched_at ? new Date(msg.launched_at).toLocaleDateString() : "—"}</td>
                <td className="px-4 py-2">
                  <OutreachRowActions id={msg.id} status={msg.status} />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {totalPages > 1 && (
        <div className="flex gap-2 mt-4 justify-center">
          {page > 1 && <a href={`/outreach?page=${page - 1}`} className="px-3 py-1 bg-gray-100 rounded text-sm">Previous</a>}
          <span className="px-3 py-1 text-sm text-gray-500">Page {page} of {totalPages}</span>
          {page < totalPages && <a href={`/outreach?page=${page + 1}`} className="px-3 py-1 bg-gray-100 rounded text-sm">Next</a>}
        </div>
      )}
    </div>
  );
}
