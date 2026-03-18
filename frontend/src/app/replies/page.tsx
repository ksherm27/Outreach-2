import { prisma } from "@/lib/prisma";
import { Badge, replyTypeBadgeVariant } from "@/components/badge";
import { StatCard } from "@/components/stat-card";

export const dynamic = "force-dynamic";

export default async function RepliesPage({
  searchParams,
}: {
  searchParams: Promise<{ type?: string; page?: string }>;
}) {
  const params = await searchParams;
  const page = parseInt(params.page ?? "1", 10);
  const pageSize = 50;

  const where: any = {};
  if (params.type) where.reply_type = params.type;

  const [replies, total, positive, objection, ooo, unsub] = await Promise.all([
    prisma.replies.findMany({
      where,
      orderBy: { received_at: "desc" },
      take: pageSize,
      skip: (page - 1) * pageSize,
      include: { contact: { include: { company: true } } },
    }),
    prisma.replies.count({ where }),
    prisma.replies.count({ where: { reply_type: "positive" } }),
    prisma.replies.count({ where: { reply_type: "objection" } }),
    prisma.replies.count({ where: { reply_type: { in: ["ooo_with_date", "ooo_no_date"] } } }),
    prisma.replies.count({ where: { reply_type: "unsubscribe" } }),
  ]);

  const totalPages = Math.ceil(total / pageSize);

  return (
    <div>
      <h2 className="text-2xl font-bold mb-6">Replies</h2>

      <div className="grid grid-cols-4 gap-4 mb-6">
        <StatCard title="Positive" value={positive} color="green" />
        <StatCard title="Objections" value={objection} color="yellow" />
        <StatCard title="Out of Office" value={ooo} color="blue" />
        <StatCard title="Unsubscribes" value={unsub} color="red" />
      </div>

      <div className="flex gap-2 mb-4 flex-wrap">
        <a href="/replies" className={`px-3 py-1 rounded text-sm ${!params.type ? 'bg-gray-900 text-white' : 'bg-gray-100 text-gray-700'}`}>All ({total})</a>
        {["positive", "objection", "ooo_with_date", "ooo_no_date", "unsubscribe", "other"].map(t => (
          <a key={t} href={`/replies?type=${t}`} className={`px-3 py-1 rounded text-sm ${params.type === t ? 'bg-blue-600 text-white' : 'bg-gray-100 text-gray-700'}`}>{t.replace(/_/g, " ")}</a>
        ))}
      </div>

      <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
        <table className="min-w-full text-sm">
          <thead className="bg-gray-50 border-b">
            <tr>
              <th className="px-4 py-2 text-left font-medium text-gray-600">Contact</th>
              <th className="px-4 py-2 text-left font-medium text-gray-600">Company</th>
              <th className="px-4 py-2 text-left font-medium text-gray-600">Type</th>
              <th className="px-4 py-2 text-left font-medium text-gray-600">Confidence</th>
              <th className="px-4 py-2 text-left font-medium text-gray-600">Subject</th>
              <th className="px-4 py-2 text-left font-medium text-gray-600">Action</th>
              <th className="px-4 py-2 text-left font-medium text-gray-600">Received</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {replies.map((r) => (
              <tr key={r.id} className="hover:bg-gray-50">
                <td className="px-4 py-2">{r.contact.first_name} {r.contact.last_name}</td>
                <td className="px-4 py-2 text-gray-600">{r.contact.company?.name ?? "—"}</td>
                <td className="px-4 py-2">
                  <Badge label={r.reply_type ?? "pending"} variant={replyTypeBadgeVariant(r.reply_type)} />
                </td>
                <td className="px-4 py-2 text-gray-500">
                  {r.classification_confidence ? `${(r.classification_confidence * 100).toFixed(0)}%` : "—"}
                </td>
                <td className="px-4 py-2 text-gray-600 max-w-[200px] truncate">{r.subject ?? "—"}</td>
                <td className="px-4 py-2 text-gray-500">{r.action_taken ?? "—"}</td>
                <td className="px-4 py-2 text-gray-500">{new Date(r.received_at).toLocaleDateString()}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {totalPages > 1 && (
        <div className="flex gap-2 mt-4 justify-center">
          {page > 1 && <a href={`/replies?page=${page - 1}${params.type ? `&type=${params.type}` : ''}`} className="px-3 py-1 bg-gray-100 rounded text-sm">Previous</a>}
          <span className="px-3 py-1 text-sm text-gray-500">Page {page} of {totalPages}</span>
          {page < totalPages && <a href={`/replies?page=${page + 1}${params.type ? `&type=${params.type}` : ''}`} className="px-3 py-1 bg-gray-100 rounded text-sm">Next</a>}
        </div>
      )}
    </div>
  );
}
