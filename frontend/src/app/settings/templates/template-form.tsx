"use client";

import { useTransition, useState } from "react";
import { createTemplate, updateTemplate } from "@/app/actions/templates";

const STAGES = [
  { value: 1, label: "Initial Email" },
  { value: 2, label: "Follow-up 1" },
  { value: 3, label: "Follow-up 2" },
  { value: 4, label: "Follow-up 3" },
  { value: 5, label: "LinkedIn Connection" },
  { value: 6, label: "LinkedIn Message" },
];

const MERGE_VARS = [
  "{{first_name}}",
  "{{company}}",
  "{{funding_stage}}",
  "{{role_title}}",
  "{{gtm_role_category}}",
  "{{source_job_url}}",
  "{{icp_score}}",
];

type TemplateRecord = {
  id: number;
  name: string;
  subject: string | null;
  body: string;
  stage_number: number;
  stage_label: string | null;
  platform: string;
  sequence_group: string | null;
};

export function TemplateForm({
  template,
  existingGroups,
  onClose,
}: {
  template?: TemplateRecord;
  existingGroups: string[];
  onClose: () => void;
}) {
  const [isPending, startTransition] = useTransition();
  const [error, setError] = useState<string | null>(null);
  const [platform, setPlatform] = useState(template?.platform || "instantly");
  const [stageNumber, setStageNumber] = useState(template?.stage_number || 1);

  const stageLabel = STAGES.find((s) => s.value === stageNumber)?.label || "";
  const showSubject = platform !== "linkedin";

  const handleSubmit = (formData: FormData) => {
    setError(null);
    const stage = STAGES.find((s) => s.value === parseInt(formData.get("stage_number") as string));
    if (stage) formData.set("stage_label", stage.label);

    startTransition(async () => {
      const result = template
        ? await updateTemplate(template.id, formData)
        : await createTemplate(formData);
      if (result.error) {
        setError(result.error);
      } else {
        onClose();
      }
    });
  };

  return (
    <div className="bg-[#111118] border border-[#1e1e2e] rounded-xl p-4 mb-4">
      <h3 className="text-sm font-semibold text-gray-200 mb-3">
        {template ? "Edit Template" : "Add Template"}
      </h3>
      {error && (
        <div className="mb-3 text-sm text-rose-400 bg-rose-500/10 border border-rose-500/20 rounded-lg p-2">{error}</div>
      )}
      <form action={handleSubmit} className="space-y-3">
        <div className="grid grid-cols-2 gap-3">
          <div>
            <label className="block text-xs font-medium text-gray-400 mb-1">Template Name</label>
            <input
              name="name"
              type="text"
              required
              defaultValue={template?.name}
              className="w-full text-sm bg-[#0a0a0f] border border-[#2a2a3a] rounded-lg px-3 py-1.5 text-gray-200 focus:outline-none focus:ring-1 focus:ring-cyan-500 focus:border-cyan-500 placeholder-gray-600"
              placeholder="VP Sales - Initial Outreach"
            />
          </div>
          <div>
            <label className="block text-xs font-medium text-gray-400 mb-1">Sequence Group</label>
            <input
              name="sequence_group"
              type="text"
              defaultValue={template?.sequence_group || ""}
              list="sequence-groups"
              className="w-full text-sm bg-[#0a0a0f] border border-[#2a2a3a] rounded-lg px-3 py-1.5 text-gray-200 focus:outline-none focus:ring-1 focus:ring-cyan-500 focus:border-cyan-500 placeholder-gray-600"
              placeholder="Sales Leadership Sequence"
            />
            <datalist id="sequence-groups">
              {existingGroups.map((g) => (
                <option key={g} value={g} />
              ))}
            </datalist>
          </div>
          <div>
            <label className="block text-xs font-medium text-gray-400 mb-1">Platform</label>
            <select
              name="platform"
              required
              value={platform}
              onChange={(e) => setPlatform(e.target.value)}
              className="w-full text-sm bg-[#0a0a0f] border border-[#2a2a3a] rounded-lg px-3 py-1.5 text-gray-200 focus:outline-none focus:ring-1 focus:ring-cyan-500 focus:border-cyan-500"
            >
              <option value="instantly">Instantly</option>
              <option value="lemlist">Lemlist</option>
              <option value="linkedin">LinkedIn</option>
            </select>
          </div>
          <div>
            <label className="block text-xs font-medium text-gray-400 mb-1">Stage</label>
            <select
              name="stage_number"
              required
              value={stageNumber}
              onChange={(e) => setStageNumber(parseInt(e.target.value))}
              className="w-full text-sm bg-[#0a0a0f] border border-[#2a2a3a] rounded-lg px-3 py-1.5 text-gray-200 focus:outline-none focus:ring-1 focus:ring-cyan-500 focus:border-cyan-500"
            >
              {STAGES.map((s) => (
                <option key={s.value} value={s.value}>
                  {s.label}
                </option>
              ))}
            </select>
            <input type="hidden" name="stage_label" value={stageLabel} />
          </div>
        </div>

        {showSubject && (
          <div>
            <label className="block text-xs font-medium text-gray-400 mb-1">Subject Line</label>
            <input
              name="subject"
              type="text"
              defaultValue={template?.subject || ""}
              className="w-full text-sm bg-[#0a0a0f] border border-[#2a2a3a] rounded-lg px-3 py-1.5 text-gray-200 focus:outline-none focus:ring-1 focus:ring-cyan-500 focus:border-cyan-500 placeholder-gray-600"
              placeholder="Quick question about {{company}}'s growth plans"
            />
          </div>
        )}

        <div>
          <label className="block text-xs font-medium text-gray-400 mb-1">Message Body</label>
          <textarea
            name="body"
            required
            rows={8}
            defaultValue={template?.body}
            className="w-full text-sm bg-[#0a0a0f] border border-[#2a2a3a] rounded-lg px-3 py-1.5 text-gray-200 focus:outline-none focus:ring-1 focus:ring-cyan-500 focus:border-cyan-500 font-mono placeholder-gray-600"
            placeholder={"Hi {{first_name}},\n\nI noticed {{company}} recently..."}
          />
          <div className="mt-1.5 flex flex-wrap gap-1.5">
            <span className="text-xs text-gray-500">Merge variables:</span>
            {MERGE_VARS.map((v) => (
              <span
                key={v}
                className="inline-block px-1.5 py-0.5 text-xs bg-cyan-500/10 text-cyan-400 rounded border border-cyan-500/20 font-mono"
              >
                {v}
              </span>
            ))}
          </div>
        </div>

        <div className="flex gap-2">
          <button
            type="submit"
            disabled={isPending}
            className="px-4 py-1.5 text-sm bg-cyan-600 text-white rounded-lg hover:bg-cyan-500 disabled:opacity-50 transition-colors"
          >
            {isPending ? "Saving..." : template ? "Update" : "Add Template"}
          </button>
          <button
            type="button"
            onClick={onClose}
            className="px-4 py-1.5 text-sm bg-[#1a1a24] text-gray-400 rounded-lg hover:bg-[#252533] border border-[#2a2a3a] transition-colors"
          >
            Cancel
          </button>
        </div>
      </form>
    </div>
  );
}

export function AddTemplateButton({
  existingGroups,
  children,
}: {
  existingGroups: string[];
  children: React.ReactNode;
}) {
  const [isOpen, setIsOpen] = useState(false);

  if (isOpen) {
    return <TemplateForm existingGroups={existingGroups} onClose={() => setIsOpen(false)} />;
  }

  return (
    <button
      type="button"
      onClick={() => setIsOpen(true)}
      className="mb-4 px-4 py-2 text-sm bg-cyan-600 text-white rounded-lg hover:bg-cyan-500 transition-colors"
    >
      {children}
    </button>
  );
}

export function EditTemplateButton({
  template,
  existingGroups,
}: {
  template: TemplateRecord;
  existingGroups: string[];
}) {
  const [isEditing, setIsEditing] = useState(false);

  if (isEditing) {
    return (
      <TemplateForm
        template={template}
        existingGroups={existingGroups}
        onClose={() => setIsEditing(false)}
      />
    );
  }

  return (
    <button
      type="button"
      onClick={() => setIsEditing(true)}
      className="text-xs text-cyan-400 hover:text-cyan-300"
    >
      Edit
    </button>
  );
}
