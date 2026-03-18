"use client";

import { useTransition, useState } from "react";
import { createEmailAccount, updateEmailAccount } from "@/app/actions/email-accounts";

type EmailAccount = {
  id: number;
  email_address: string;
  display_name: string;
  platform: string;
  warmup_status: string;
  daily_send_limit: number;
};

export function EmailAccountForm({
  account,
  onClose,
}: {
  account?: EmailAccount;
  onClose: () => void;
}) {
  const [isPending, startTransition] = useTransition();
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = (formData: FormData) => {
    setError(null);
    startTransition(async () => {
      const result = account
        ? await updateEmailAccount(account.id, formData)
        : await createEmailAccount(formData);
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
        {account ? "Edit Email Account" : "Add Email Account"}
      </h3>
      {error && (
        <div className="mb-3 text-sm text-rose-400 bg-rose-500/10 border border-rose-500/20 rounded-lg p-2">{error}</div>
      )}
      <form action={handleSubmit} className="grid grid-cols-2 gap-3">
        <div>
          <label className="block text-xs font-medium text-gray-400 mb-1">Email Address</label>
          <input
            name="email_address"
            type="email"
            required
            defaultValue={account?.email_address}
            className="w-full text-sm bg-[#0a0a0f] border border-[#2a2a3a] rounded-lg px-3 py-1.5 text-gray-200 focus:outline-none focus:ring-1 focus:ring-cyan-500 focus:border-cyan-500 placeholder-gray-600"
            placeholder="sender@company.com"
          />
        </div>
        <div>
          <label className="block text-xs font-medium text-gray-400 mb-1">Display Name</label>
          <input
            name="display_name"
            type="text"
            required
            defaultValue={account?.display_name}
            className="w-full text-sm bg-[#0a0a0f] border border-[#2a2a3a] rounded-lg px-3 py-1.5 text-gray-200 focus:outline-none focus:ring-1 focus:ring-cyan-500 focus:border-cyan-500 placeholder-gray-600"
            placeholder="John Smith"
          />
        </div>
        <div>
          <label className="block text-xs font-medium text-gray-400 mb-1">Platform</label>
          <select
            name="platform"
            required
            defaultValue={account?.platform || "instantly"}
            className="w-full text-sm bg-[#0a0a0f] border border-[#2a2a3a] rounded-lg px-3 py-1.5 text-gray-200 focus:outline-none focus:ring-1 focus:ring-cyan-500 focus:border-cyan-500"
          >
            <option value="instantly">Instantly</option>
            <option value="lemlist">Lemlist</option>
          </select>
        </div>
        <div>
          <label className="block text-xs font-medium text-gray-400 mb-1">Warmup Status</label>
          <select
            name="warmup_status"
            defaultValue={account?.warmup_status || "pending"}
            className="w-full text-sm bg-[#0a0a0f] border border-[#2a2a3a] rounded-lg px-3 py-1.5 text-gray-200 focus:outline-none focus:ring-1 focus:ring-cyan-500 focus:border-cyan-500"
          >
            <option value="pending">Pending</option>
            <option value="warming">Warming</option>
            <option value="warmed">Warmed</option>
            <option value="paused">Paused</option>
          </select>
        </div>
        <div>
          <label className="block text-xs font-medium text-gray-400 mb-1">Daily Send Limit</label>
          <input
            name="daily_send_limit"
            type="number"
            min={1}
            max={500}
            defaultValue={account?.daily_send_limit || 30}
            className="w-full text-sm bg-[#0a0a0f] border border-[#2a2a3a] rounded-lg px-3 py-1.5 text-gray-200 focus:outline-none focus:ring-1 focus:ring-cyan-500 focus:border-cyan-500"
          />
        </div>
        <div className="flex items-end gap-2">
          <button
            type="submit"
            disabled={isPending}
            className="px-4 py-1.5 text-sm bg-cyan-600 text-white rounded-lg hover:bg-cyan-500 disabled:opacity-50 transition-colors"
          >
            {isPending ? "Saving..." : account ? "Update" : "Add Account"}
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

export function AddEmailAccountButton({ children }: { children: React.ReactNode }) {
  const [isOpen, setIsOpen] = useState(false);

  if (isOpen) {
    return <EmailAccountForm onClose={() => setIsOpen(false)} />;
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

export function EditEmailAccountButton({ account }: { account: EmailAccount }) {
  const [isEditing, setIsEditing] = useState(false);

  if (isEditing) {
    return <EmailAccountForm account={account} onClose={() => setIsEditing(false)} />;
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
