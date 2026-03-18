"use client";

import { useTransition, useState } from "react";
import { createUser, updateUser } from "@/app/actions/users";

type UserRecord = {
  id: number;
  name: string;
  email: string;
  role: string;
  slack_id: string | null;
};

export function UserForm({
  user,
  onClose,
}: {
  user?: UserRecord;
  onClose: () => void;
}) {
  const [isPending, startTransition] = useTransition();
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = (formData: FormData) => {
    setError(null);
    startTransition(async () => {
      const result = user
        ? await updateUser(user.id, formData)
        : await createUser(formData);
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
        {user ? "Edit User" : "Add User"}
      </h3>
      {error && (
        <div className="mb-3 text-sm text-rose-400 bg-rose-500/10 border border-rose-500/20 rounded-lg p-2">{error}</div>
      )}
      <form action={handleSubmit} className="grid grid-cols-2 gap-3">
        <div>
          <label className="block text-xs font-medium text-gray-400 mb-1">Name</label>
          <input
            name="name"
            type="text"
            required
            defaultValue={user?.name}
            className="w-full text-sm bg-[#0a0a0f] border border-[#2a2a3a] rounded-lg px-3 py-1.5 text-gray-200 focus:outline-none focus:ring-1 focus:ring-cyan-500 focus:border-cyan-500 placeholder-gray-600"
            placeholder="Jane Doe"
          />
        </div>
        <div>
          <label className="block text-xs font-medium text-gray-400 mb-1">Email</label>
          <input
            name="email"
            type="email"
            required
            defaultValue={user?.email}
            className="w-full text-sm bg-[#0a0a0f] border border-[#2a2a3a] rounded-lg px-3 py-1.5 text-gray-200 focus:outline-none focus:ring-1 focus:ring-cyan-500 focus:border-cyan-500 placeholder-gray-600"
            placeholder="jane@company.com"
          />
        </div>
        <div>
          <label className="block text-xs font-medium text-gray-400 mb-1">Role</label>
          <select
            name="role"
            defaultValue={user?.role || "recruiter"}
            className="w-full text-sm bg-[#0a0a0f] border border-[#2a2a3a] rounded-lg px-3 py-1.5 text-gray-200 focus:outline-none focus:ring-1 focus:ring-cyan-500 focus:border-cyan-500"
          >
            <option value="admin">Admin</option>
            <option value="recruiter">Recruiter</option>
            <option value="viewer">Viewer</option>
          </select>
        </div>
        <div>
          <label className="block text-xs font-medium text-gray-400 mb-1">Slack ID</label>
          <input
            name="slack_id"
            type="text"
            defaultValue={user?.slack_id || ""}
            className="w-full text-sm bg-[#0a0a0f] border border-[#2a2a3a] rounded-lg px-3 py-1.5 text-gray-200 focus:outline-none focus:ring-1 focus:ring-cyan-500 focus:border-cyan-500 placeholder-gray-600"
            placeholder="U0123456789"
          />
        </div>
        <div className="col-span-2 flex gap-2">
          <button
            type="submit"
            disabled={isPending}
            className="px-4 py-1.5 text-sm bg-cyan-600 text-white rounded-lg hover:bg-cyan-500 disabled:opacity-50 transition-colors"
          >
            {isPending ? "Saving..." : user ? "Update" : "Add User"}
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

export function AddUserButton({ children }: { children: React.ReactNode }) {
  const [isOpen, setIsOpen] = useState(false);

  if (isOpen) {
    return <UserForm onClose={() => setIsOpen(false)} />;
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

export function EditUserButton({ user }: { user: UserRecord }) {
  const [isEditing, setIsEditing] = useState(false);

  if (isEditing) {
    return <UserForm user={user} onClose={() => setIsEditing(false)} />;
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
