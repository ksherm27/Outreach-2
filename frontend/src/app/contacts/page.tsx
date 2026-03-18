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
        <h2 className="text-2xl font-bold">Contacts</h2>
        <span className="text-sm text-gray-500">{total} total</span>
      </div>

      <div className="flex gap-2 mb-4">
        <a href="/contacts" className={`px-3 py-1 rounded text-sm ${!params.suppressed ? 'bg-gray-900 text-white' : 'bg-gray-100 text-gray-700'}`}>All</a>
        <a href="/contacts?suppressed=true" className={`px-3 py-1 rounded text-sm ${params.suppressed === 'true' ? 'bg-red-600 text-white' : 'bg-gray-100 text-gray-700'}`}>Suppressed</a>
      </div>

      <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
        <table className="min-w-full text-sm">
          <thead className="bg-gray-50 border-b">
            <tr>
              <th className="px-4 py-2 text-left font-medium text-gray-600">Name</th>
              <th className="px-4 py-2 text-left font-medium text-gray-600">Email</th>
              <th className="px-4 py-2 text-left font-medium text-gray-600">Title</th>
              <th className="px-4 py-2 text-left font-medium text-gray-600">Company</th>
              <th className="px-4 py-2 text-left font-medium text-gray-600">Source</th>
              <th className="px-4 py-2 text-left font-medium text-gray-600">Confidence</th>
              <th className="px-4 py-2 text-left font-medium text-gray-600">Status</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {contacts.map((c) => (
              <tr key={c.id} className="hover:bg-gray-50">
                <td className="px-4 py-2 font-medium">{c.first_name} {c.last_name}</td>
                <td className="px-4 py-2 text-gray-600">{c.email}</td>
                <td className="px-4 py-2 text-gray-600">{c.title ?? "—"}</td>
                <td className="px-4 py-2">{c.company?.name ?? "—"}</td>
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
          {page > 1 && <a href={`/contacts?page=${page - 1}`} className="px-3 py-1 bg-gray-100 rounded text-sm">Previous</a>}
          <span className="px-3 py-1 text-sm text-gray-500">Page {page} of {totalPages}</span>
          {page < totalPages && <a href={`/contacts?page=${page + 1}`} className="px-3 py-1 bg-gray-100 rounded text-sm">Next</a>}
        </div>
      )}
    </div>
  );
}
