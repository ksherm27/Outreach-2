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
    <div className="bg-gray-50 border border-gray-200 rounded-lg p-4 mb-4">
      <h3 className="text-sm font-semibold text-gray-900 mb-3">
        {user ? "Edit User" : "Add User"}
      </h3>
      {error && (
        <div className="mb-3 text-sm text-red-600 bg-red-50 border border-red-200 rounded p-2">{error}</div>
      )}
      <form action={handleSubmit} className="grid grid-cols-2 gap-3">
        <div>
          <label className="block text-xs font-medium text-gray-700 mb-1">Name</label>
          <input
            name="name"
            type="text"
            required
            defaultValue={user?.name}
            className="w-full text-sm border border-gray-300 rounded px-3 py-1.5 focus:outline-none focus:ring-1 focus:ring-blue-500"
            placeholder="Jane Doe"
          />
        </div>
        <div>
          <label className="block text-xs font-medium text-gray-700 mb-1">Email</label>
          <input
            name="email"
            type="email"
            required
            defaultValue={user?.email}
            className="w-full text-sm border border-gray-300 rounded px-3 py-1.5 focus:outline-none focus:ring-1 focus:ring-blue-500"
            placeholder="jane@company.com"
          />
        </div>
        <div>
          <label className="block text-xs font-medium text-gray-700 mb-1">Role</label>
          <select
            name="role"
            defaultValue={user?.role || "recruiter"}
            className="w-full text-sm border border-gray-300 rounded px-3 py-1.5 focus:outline-none focus:ring-1 focus:ring-blue-500 bg-white"
          >
            <option value="admin">Admin</option>
            <option value="recruiter">Recruiter</option>
            <option value="viewer">Viewer</option>
          </select>
        </div>
        <div>
          <label className="block text-xs font-medium text-gray-700 mb-1">Slack ID</label>
          <input
            name="slack_id"
            type="text"
            defaultValue={user?.slack_id || ""}
            className="w-full text-sm border border-gray-300 rounded px-3 py-1.5 focus:outline-none focus:ring-1 focus:ring-blue-500"
            placeholder="U0123456789"
          />
        </div>
        <div className="col-span-2 flex gap-2">
          <button
            type="submit"
            disabled={isPending}
            className="px-4 py-1.5 text-sm bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50"
          >
            {isPending ? "Saving..." : user ? "Update" : "Add User"}
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

export function AddUserButton({ children }: { children: React.ReactNode }) {
  const [isOpen, setIsOpen] = useState(false);

  if (isOpen) {
    return <UserForm onClose={() => setIsOpen(false)} />;
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

export function EditUserButton({ user }: { user: UserRecord }) {
  const [isEditing, setIsEditing] = useState(false);

  if (isEditing) {
    return <UserForm user={user} onClose={() => setIsEditing(false)} />;
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
