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
        <h2 className="text-2xl font-bold text-gray-100">Scraped Jobs</h2>
        <span className="text-sm text-gray-500">{total} total</span>
      </div>

      <div className="flex gap-2 mb-4 flex-wrap">
        <a href="/jobs" className={`px-3 py-1 rounded-lg text-sm ${!params.board && !params.qualified ? 'bg-cyan-600/10 text-cyan-400 border border-cyan-500/30' : 'bg-[#1a1a24] text-gray-400 border border-[#2a2a3a] hover:text-gray-200 hover:bg-[#252533]'}`}>All</a>
        <a href="/jobs?qualified=true" className={`px-3 py-1 rounded-lg text-sm ${params.qualified === 'true' ? 'bg-emerald-600/10 text-emerald-400 border border-emerald-500/30' : 'bg-[#1a1a24] text-gray-400 border border-[#2a2a3a] hover:text-gray-200 hover:bg-[#252533]'}`}>Qualified Only</a>
        {["greenhouse", "lever", "linkedin", "indeed", "ashby", "workday"].map(b => (
          <a key={b} href={`/jobs?board=${b}`} className={`px-3 py-1 rounded-lg text-sm capitalize ${params.board === b ? 'bg-cyan-600/10 text-cyan-400 border border-cyan-500/30' : 'bg-[#1a1a24] text-gray-400 border border-[#2a2a3a] hover:text-gray-200 hover:bg-[#252533]'}`}>{b}</a>
        ))}
      </div>

      <div className="bg-[#111118] rounded-xl border border-[#1e1e2e] overflow-hidden">
        <table className="min-w-full text-sm">
          <thead className="bg-[#0d0d14] border-b border-[#1e1e2e]">
            <tr>
              <th className="px-4 py-3 text-left text-[11px] font-medium uppercase tracking-wider text-gray-500">Title</th>
              <th className="px-4 py-3 text-left text-[11px] font-medium uppercase tracking-wider text-gray-500">Company</th>
              <th className="px-4 py-3 text-left text-[11px] font-medium uppercase tracking-wider text-gray-500">Board</th>
              <th className="px-4 py-3 text-left text-[11px] font-medium uppercase tracking-wider text-gray-500">ICP Score</th>
              <th className="px-4 py-3 text-left text-[11px] font-medium uppercase tracking-wider text-gray-500">Category</th>
              <th className="px-4 py-3 text-left text-[11px] font-medium uppercase tracking-wider text-gray-500">Location</th>
              <th className="px-4 py-3 text-left text-[11px] font-medium uppercase tracking-wider text-gray-500">Scraped</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-[#1e1e2e]">
            {jobs.map((job) => (
              <tr key={job.id} className="hover:bg-[#1a1a24] transition-colors">
                <td className="px-4 py-2">
                  <a href={job.source_url} target="_blank" rel="noopener noreferrer" className="text-cyan-400 hover:text-cyan-300 hover:underline">
                    {job.title}
                  </a>
                </td>
                <td className="px-4 py-2 text-gray-200">{job.company_name}</td>
                <td className="px-4 py-2">
                  <Badge label={job.board_name} variant="info" />
                </td>
                <td className="px-4 py-2">
                  {job.icp_score !== null ? (
                    <span className={`font-medium ${job.icp_score >= 65 ? 'text-emerald-400' : job.icp_score >= 40 ? 'text-amber-400' : 'text-gray-500'}`}>
                      {job.icp_score}
                    </span>
                  ) : "—"}
                </td>
                <td className="px-4 py-2 text-gray-400">{job.gtm_category ?? "—"}</td>
                <td className="px-4 py-2 text-gray-500 max-w-[150px] truncate">{job.location ?? "—"}</td>
                <td className="px-4 py-2 text-gray-500">{new Date(job.created_at).toLocaleDateString()}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {totalPages > 1 && (
        <div className="flex gap-2 mt-4 justify-center">
          {page > 1 && <a href={`/jobs?page=${page - 1}${params.board ? `&board=${params.board}` : ''}${params.qualified ? `&qualified=${params.qualified}` : ''}`} className="px-3 py-1 bg-[#1a1a24] text-gray-400 border border-[#2a2a3a] rounded-lg text-sm hover:text-gray-200 hover:bg-[#252533]">Previous</a>}
          <span className="px-3 py-1 text-sm text-gray-500">Page {page} of {totalPages}</span>
          {page < totalPages && <a href={`/jobs?page=${page + 1}${params.board ? `&board=${params.board}` : ''}${params.qualified ? `&qualified=${params.qualified}` : ''}`} className="px-3 py-1 bg-[#1a1a24] text-gray-400 border border-[#2a2a3a] rounded-lg text-sm hover:text-gray-200 hover:bg-[#252533]">Next</a>}
        </div>
      )}
    </div>
  );
}
