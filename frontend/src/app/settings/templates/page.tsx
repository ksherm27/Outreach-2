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
        <div className="bg-white rounded-lg border border-gray-200 px-4 py-8 text-center text-sm text-gray-500">
          No templates configured. Add outreach message templates to get started.
        </div>
      )}

      {Array.from(grouped.entries()).map(([groupName, groupTemplates]) => (
        <div key={groupName} className="mb-6">
          <h3 className="text-sm font-semibold text-gray-700 mb-2 flex items-center gap-2">
            <span className="inline-block w-2 h-2 rounded-full bg-blue-500" />
            {groupName}
            <span className="text-xs font-normal text-gray-400">
              ({groupTemplates.length} {groupTemplates.length === 1 ? "step" : "steps"})
            </span>
          </h3>
          <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Stage</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Name</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Platform</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Subject</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Active</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200">
                {groupTemplates.map((template) => (
                  <tr key={template.id} className="hover:bg-gray-50">
                    <td className="px-4 py-3">
                      <span className="inline-flex items-center gap-1.5">
                        <span className="inline-block w-5 h-5 rounded-full bg-blue-100 text-blue-800 text-xs font-bold flex items-center justify-center leading-none text-center">
                          {template.stage_number}
                        </span>
                        <span className="text-xs text-gray-600">{template.stage_label}</span>
                      </span>
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-900 font-medium">{template.name}</td>
                    <td className="px-4 py-3">
                      <span className={`inline-block px-2 py-0.5 text-xs rounded-full font-medium ${
                        template.platform === "instantly"
                          ? "bg-purple-100 text-purple-800"
                          : template.platform === "lemlist"
                          ? "bg-orange-100 text-orange-800"
                          : "bg-sky-100 text-sky-800"
                      }`}>
                        {template.platform}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-600 max-w-xs truncate">
                      {template.subject || "—"}
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
