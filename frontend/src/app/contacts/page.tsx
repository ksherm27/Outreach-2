import { prisma } from "@/lib/prisma";
import { Badge } from "@/components/badge";

export const dynamic = "force-dynamic";

export default async function ContactsPage({
  searchParams,
}: {
  searchParams: Promise<{ page?: string; suppressed?: string }>;
}) {
  const params = await searchParams;
  const page = parseInt(params.page ?? "1", 10);
  const pageSize = 50;

  const where: any = {};
  if (params.suppressed === "true") where.is_suppressed = true;

  const [contacts, total] = await Promise.all([
    prisma.contacts.findMany({
      where,
      orderBy: { created_at: "desc" },
      take: pageSize,
      skip: (page - 1) * pageSize,
      include: { company: true },
    }),
    prisma.contacts.count({ where }),
  ]);

  const totalPages = Math.ceil(total / pageSize);

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-2xl font-bold text-gray-100">Contacts</h2>
        <span className="text-sm text-gray-500">{total} total</span>
      </div>

      <div className="flex gap-2 mb-4">
        <a href="/contacts" className={`px-3 py-1 rounded-lg text-sm ${!params.suppressed ? 'bg-cyan-600/10 text-cyan-400 border border-cyan-500/30' : 'bg-[#1a1a24] text-gray-400 border border-[#2a2a3a] hover:text-gray-200 hover:bg-[#252533]'}`}>All</a>
        <a href="/contacts?suppressed=true" className={`px-3 py-1 rounded-lg text-sm ${params.suppressed === 'true' ? 'bg-rose-600/10 text-rose-400 border border-rose-500/30' : 'bg-[#1a1a24] text-gray-400 border border-[#2a2a3a] hover:text-gray-200 hover:bg-[#252533]'}`}>Suppressed</a>
      </div>

      <div className="bg-[#111118] rounded-xl border border-[#1e1e2e] overflow-hidden">
        <table className="min-w-full text-sm">
          <thead className="bg-[#0d0d14] border-b border-[#1e1e2e]">
            <tr>
              <th className="px-4 py-3 text-left text-[11px] font-medium uppercase tracking-wider text-gray-500">Name</th>
              <th className="px-4 py-3 text-left text-[11px] font-medium uppercase tracking-wider text-gray-500">Email</th>
              <th className="px-4 py-3 text-left text-[11px] font-medium uppercase tracking-wider text-gray-500">Title</th>
              <th className="px-4 py-3 text-left text-[11px] font-medium uppercase tracking-wider text-gray-500">Company</th>
              <th className="px-4 py-3 text-left text-[11px] font-medium uppercase tracking-wider text-gray-500">Source</th>
              <th className="px-4 py-3 text-left text-[11px] font-medium uppercase tracking-wider text-gray-500">Confidence</th>
              <th className="px-4 py-3 text-left text-[11px] font-medium uppercase tracking-wider text-gray-500">Status</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-[#1e1e2e]">
            {contacts.map((c) => (
              <tr key={c.id} className="hover:bg-[#1a1a24] transition-colors">
                <td className="px-4 py-2 font-medium text-gray-200">{c.first_name} {c.last_name}</td>
                <td className="px-4 py-2 text-gray-400">{c.email}</td>
                <td className="px-4 py-2 text-gray-400">{c.title ?? "—"}</td>
                <td className="px-4 py-2 text-gray-200">{c.company?.name ?? "—"}</td>
                <td className="px-4 py-2"><Badge label={c.source} /></td>
                <td className="px-4 py-2 text-gray-500">{c.email_confidence ? `${(c.email_confidence * 100).toFixed(0)}%` : "—"}</td>
                <td className="px-4 py-2">
                  {c.is_suppressed ? (
                    <Badge label="Suppressed" variant="danger" />
                  ) : (
                    <Badge label="Active" variant="success" />
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {totalPages > 1 && (
        <div className="flex gap-2 mt-4 justify-center">
          {page > 1 && <a href={`/contacts?page=${page - 1}`} className="px-3 py-1 bg-[#1a1a24] text-gray-400 border border-[#2a2a3a] rounded-lg text-sm hover:text-gray-200 hover:bg-[#252533]">Previous</a>}
          <span className="px-3 py-1 text-sm text-gray-500">Page {page} of {totalPages}</span>
          {page < totalPages && <a href={`/contacts?page=${page + 1}`} className="px-3 py-1 bg-[#1a1a24] text-gray-400 border border-[#2a2a3a] rounded-lg text-sm hover:text-gray-200 hover:bg-[#252533]">Next</a>}
        </div>
      )}
    </div>
  );
}
