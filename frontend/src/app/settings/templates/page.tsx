import { prisma } from "@/lib/prisma";
import { toggleTemplate, deleteTemplate } from "@/app/actions/templates";
import { ToggleSwitch } from "@/components/form/toggle-switch";
import { DeleteButton } from "@/components/form/delete-button";
import { AddTemplateButton, EditTemplateButton } from "./template-form";

export const dynamic = "force-dynamic";

export default async function TemplatesPage() {
  const templates = await prisma.outreach_templates.findMany({
    orderBy: [{ sequence_group: "asc" }, { stage_number: "asc" }],
  });

  // Get unique sequence groups for the form datalist
  const existingGroups = [
    ...new Set(templates.map((t) => t.sequence_group).filter(Boolean) as string[]),
  ];

  // Group templates by sequence_group
  const grouped = new Map<string, typeof templates>();
  for (const t of templates) {
    const key = t.sequence_group || "Ungrouped";
    if (!grouped.has(key)) grouped.set(key, []);
    grouped.get(key)!.push(t);
  }

  return (
    <div>
      <AddTemplateButton existingGroups={existingGroups}>+ Add Template</AddTemplateButton>

      {templates.length === 0 && (
        <div className="bg-[#111118] rounded-xl border border-[#1e1e2e] px-4 py-8 text-center text-sm text-gray-500">
          No templates configured. Add outreach message templates to get started.
        </div>
      )}

      {Array.from(grouped.entries()).map(([groupName, groupTemplates]) => (
        <div key={groupName} className="mb-6">
          <h3 className="text-sm font-semibold text-gray-300 mb-2 flex items-center gap-2">
            <span className="inline-block w-2 h-2 rounded-full bg-cyan-500" />
            {groupName}
            <span className="text-xs font-normal text-gray-500">
              ({groupTemplates.length} {groupTemplates.length === 1 ? "step" : "steps"})
            </span>
          </h3>
          <div className="bg-[#111118] rounded-xl border border-[#1e1e2e] overflow-hidden">
            <table className="min-w-full text-sm">
              <thead className="bg-[#0d0d14] border-b border-[#1e1e2e]">
                <tr>
                  <th className="px-4 py-3 text-left text-[11px] font-medium uppercase tracking-wider text-gray-500">Stage</th>
                  <th className="px-4 py-3 text-left text-[11px] font-medium uppercase tracking-wider text-gray-500">Name</th>
                  <th className="px-4 py-3 text-left text-[11px] font-medium uppercase tracking-wider text-gray-500">Platform</th>
                  <th className="px-4 py-3 text-left text-[11px] font-medium uppercase tracking-wider text-gray-500">Subject</th>
                  <th className="px-4 py-3 text-left text-[11px] font-medium uppercase tracking-wider text-gray-500">Active</th>
                  <th className="px-4 py-3 text-left text-[11px] font-medium uppercase tracking-wider text-gray-500">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#1e1e2e]">
                {groupTemplates.map((template) => (
                  <tr key={template.id} className="hover:bg-[#1a1a24] transition-colors">
                    <td className="px-4 py-3">
                      <span className="inline-flex items-center gap-1.5">
                        <span className="inline-block w-5 h-5 rounded-full bg-cyan-500/10 text-cyan-400 text-xs font-bold flex items-center justify-center leading-none text-center border border-cyan-500/20">
                          {template.stage_number}
                        </span>
                        <span className="text-xs text-gray-400">{template.stage_label}</span>
                      </span>
                    </td>
                    <td className="px-4 py-3 text-gray-200 font-medium">{template.name}</td>
                    <td className="px-4 py-3">
                      <span className={`inline-block px-2 py-0.5 text-xs rounded-full font-medium border ${
                        template.platform === "instantly"
                          ? "bg-violet-500/10 text-violet-400 border-violet-500/20"
                          : template.platform === "lemlist"
                          ? "bg-orange-500/10 text-orange-400 border-orange-500/20"
                          : "bg-cyan-500/10 text-cyan-400 border-cyan-500/20"
                      }`}>
                        {template.platform}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-gray-400 max-w-xs truncate">
                      {template.subject || "\u2014"}
                    </td>
                    <td className="px-4 py-3">
                      <ToggleSwitch
                        isActive={template.is_active}
                        onToggle={async () => {
                          "use server";
                          return toggleTemplate(template.id);
                        }}
                      />
                    </td>
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-3">
                        <EditTemplateButton template={template} existingGroups={existingGroups} />
                        <DeleteButton
                          onDelete={async () => {
                            "use server";
                            return deleteTemplate(template.id);
                          }}
                        />
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      ))}
    </div>
  );
}
