import { prisma } from "@/lib/prisma";
import { toggleUser, deleteUser } from "@/app/actions/users";
import { ToggleSwitch } from "@/components/form/toggle-switch";
import { DeleteButton } from "@/components/form/delete-button";
import { AddUserButton, EditUserButton } from "./user-form";

export const dynamic = "force-dynamic";

export default async function UsersPage() {
  const users = await prisma.users.findMany({
    orderBy: { name: "asc" },
  });

  return (
    <div>
      <AddUserButton>+ Add User</AddUserButton>

      <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Name</th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Email</th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Role</th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Slack ID</th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Assignments</th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Active</th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-200">
            {users.length === 0 && (
              <tr>
                <td colSpan={7} className="px-4 py-8 text-center text-sm text-gray-500">
                  No users configured. Add recruiters and admins to get started.
                </td>
              </tr>
            )}
            {users.map((user) => (
              <tr key={user.id} className="hover:bg-gray-50">
                <td className="px-4 py-3 text-sm text-gray-900 font-medium">{user.name}</td>
                <td className="px-4 py-3 text-sm text-gray-600">{user.email}</td>
                <td className="px-4 py-3">
                  <span className={`inline-block px-2 py-0.5 text-xs rounded-full font-medium ${
                    user.role === "admin"
                      ? "bg-red-100 text-red-800"
                      : user.role === "recruiter"
                      ? "bg-blue-100 text-blue-800"
                      : "bg-gray-100 text-gray-800"
                  }`}>
                    {user.role}
                  </span>
                </td>
                <td className="px-4 py-3 text-sm text-gray-600 font-mono">{user.slack_id || "—"}</td>
                <td className="px-4 py-3 text-sm text-gray-600">{user.assignment_count}</td>
                <td className="px-4 py-3">
                  <ToggleSwitch
                    isActive={user.is_active}
                    onToggle={async () => {
                      "use server";
                      return toggleUser(user.id);
                    }}
                  />
                </td>
                <td className="px-4 py-3">
                  <div className="flex items-center gap-3">
                    <EditUserButton user={user} />
                    <DeleteButton
                      onDelete={async () => {
                        "use server";
                        return deleteUser(user.id);
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
  );
}
