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
    <div className="bg-gray-50 border border-gray-200 rounded-lg p-4 mb-4">
      <h3 className="text-sm font-semibold text-gray-900 mb-3">
        {account ? "Edit Email Account" : "Add Email Account"}
      </h3>
      {error && (
        <div className="mb-3 text-sm text-red-600 bg-red-50 border border-red-200 rounded p-2">{error}</div>
      )}
      <form action={handleSubmit} className="grid grid-cols-2 gap-3">
        <div>
          <label className="block text-xs font-medium text-gray-700 mb-1">Email Address</label>
          <input
            name="email_address"
            type="email"
            required
            defaultValue={account?.email_address}
            className="w-full text-sm border border-gray-300 rounded px-3 py-1.5 focus:outline-none focus:ring-1 focus:ring-blue-500"
            placeholder="sender@company.com"
          />
        </div>
        <div>
          <label className="block text-xs font-medium text-gray-700 mb-1">Display Name</label>
          <input
            name="display_name"
            type="text"
            required
            defaultValue={account?.display_name}
            className="w-full text-sm border border-gray-300 rounded px-3 py-1.5 focus:outline-none focus:ring-1 focus:ring-blue-500"
            placeholder="John Smith"
          />
        </div>
        <div>
          <label className="block text-xs font-medium text-gray-700 mb-1">Platform</label>
          <select
            name="platform"
            required
            defaultValue={account?.platform || "instantly"}
            className="w-full text-sm border border-gray-300 rounded px-3 py-1.5 focus:outline-none focus:ring-1 focus:ring-blue-500 bg-white"
          >
            <option value="instantly">Instantly</option>
            <option value="lemlist">Lemlist</option>
          </select>
        </div>
        <div>
          <label className="block text-xs font-medium text-gray-700 mb-1">Warmup Status</label>
          <select
            name="warmup_status"
            defaultValue={account?.warmup_status || "pending"}
            className="w-full text-sm border border-gray-300 rounded px-3 py-1.5 focus:outline-none focus:ring-1 focus:ring-blue-500 bg-white"
          >
            <option value="pending">Pending</option>
            <option value="warming">Warming</option>
            <option value="warmed">Warmed</option>
            <option value="paused">Paused</option>
          </select>
        </div>
        <div>
          <label className="block text-xs font-medium text-gray-700 mb-1">Daily Send Limit</label>
          <input
            name="daily_send_limit"
            type="number"
            min={1}
            max={500}
            defaultValue={account?.daily_send_limit || 30}
            className="w-full text-sm border border-gray-300 rounded px-3 py-1.5 focus:outline-none focus:ring-1 focus:ring-blue-500"
          />
        </div>
        <div className="flex items-end gap-2">
          <button
            type="submit"
            disabled={isPending}
            className="px-4 py-1.5 text-sm bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50"
          >
            {isPending ? "Saving..." : account ? "Update" : "Add Account"}
          </button>
          <button
            type="button"
            onClick={onClose}
            className="px-4 py-1.5 text-sm bg-gray-200 text-gray-700 rounded hover:bg-gray-300"
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
      className="mb-4 px-4 py-2 text-sm bg-blue-600 text-white rounded-lg hover:bg-blue-700"
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
      className="text-xs text-blue-600 hover:text-blue-800"
    >
      Edit
    </button>
  );
}
