import { prisma } from "@/lib/prisma";
import { Badge, statusBadgeVariant } from "@/components/badge";

export const dynamic = "force-dynamic";

export default async function JobsPage({
  searchParams,
}: {
  searchParams: Promise<{ board?: string; qualified?: string; category?: string; page?: string }>;
}) {
  const params = await searchParams;
  const page = parseInt(params.page ?? "1", 10);
  const pageSize = 50;

  const where: any = {};
  if (params.board) where.board_name = params.board;
  if (params.qualified === "true") where.is_qualified = true;
  if (params.category) where.gtm_category = params.category;

  const [jobs, total] = await Promise.all([
    prisma.scraped_jobs.findMany({
      where,
      orderBy: { created_at: "desc" },
      take: pageSize,
      skip: (page - 1) * pageSize,
    }),
    prisma.scraped_jobs.count({ where }),
  ]);

  const totalPages = Math.ceil(total / pageSize);

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-2xl font-bold">Scraped Jobs</h2>
        <span className="text-sm text-gray-500">{total} total</span>
      </div>

      <div className="flex gap-2 mb-4 flex-wrap">
        <a href="/jobs" className={`px-3 py-1 rounded text-sm ${!params.board && !params.qualified ? 'bg-gray-900 text-white' : 'bg-gray-100 text-gray-700 hover:bg-gray-200'}`}>All</a>
        <a href="/jobs?qualified=true" className={`px-3 py-1 rounded text-sm ${params.qualified === 'true' ? 'bg-green-600 text-white' : 'bg-gray-100 text-gray-700 hover:bg-gray-200'}`}>Qualified Only</a>
        {["greenhouse", "lever", "linkedin", "indeed", "ashby", "workday"].map(b => (
          <a key={b} href={`/jobs?board=${b}`} className={`px-3 py-1 rounded text-sm capitalize ${params.board === b ? 'bg-blue-600 text-white' : 'bg-gray-100 text-gray-700 hover:bg-gray-200'}`}>{b}</a>
        ))}
      </div>

      <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
        <table className="min-w-full text-sm">
          <thead className="bg-gray-50 border-b">
            <tr>
              <th className="px-4 py-2 text-left font-medium text-gray-600">Title</th>
              <th className="px-4 py-2 text-left font-medium text-gray-600">Company</th>
              <th className="px-4 py-2 text-left font-medium text-gray-600">Board</th>
              <th className="px-4 py-2 text-left font-medium text-gray-600">ICP Score</th>
              <th className="px-4 py-2 text-left font-medium text-gray-600">Category</th>
              <th className="px-4 py-2 text-left font-medium text-gray-600">Location</th>
              <th className="px-4 py-2 text-left font-medium text-gray-600">Scraped</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {jobs.map((job) => (
              <tr key={job.id} className="hover:bg-gray-50">
                <td className="px-4 py-2">
                  <a href={job.source_url} target="_blank" rel="noopener noreferrer" className="text-blue-600 hover:underline">
                    {job.title}
                  </a>
                </td>
                <td className="px-4 py-2">{job.company_name}</td>
                <td className="px-4 py-2">
                  <Badge label={job.board_name} variant="info" />
                </td>
                <td className="px-4 py-2">
                  {job.icp_score !== null ? (
                    <span className={`font-medium ${job.icp_score >= 65 ? 'text-green-600' : job.icp_score >= 40 ? 'text-yellow-600' : 'text-gray-400'}`}>
                      {job.icp_score}
                    </span>
                  ) : "—"}
                </td>
                <td className="px-4 py-2 text-gray-600">{job.gtm_category ?? "—"}</td>
                <td className="px-4 py-2 text-gray-500 max-w-[150px] truncate">{job.location ?? "—"}</td>
                <td className="px-4 py-2 text-gray-500">{new Date(job.created_at).toLocaleDateString()}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {totalPages > 1 && (
        <div className="flex gap-2 mt-4 justify-center">
          {page > 1 && <a href={`/jobs?page=${page - 1}${params.board ? `&board=${params.board}` : ''}${params.qualified ? `&qualified=${params.qualified}` : ''}`} className="px-3 py-1 bg-gray-100 rounded text-sm hover:bg-gray-200">Previous</a>}
          <span className="px-3 py-1 text-sm text-gray-500">Page {page} of {totalPages}</span>
          {page < totalPages && <a href={`/jobs?page=${page + 1}${params.board ? `&board=${params.board}` : ''}${params.qualified ? `&qualified=${params.qualified}` : ''}`} className="px-3 py-1 bg-gray-100 rounded text-sm hover:bg-gray-200">Next</a>}
        </div>
      )}
    </div>
  );
}
