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

      <div className="bg-[#111118] rounded-xl border border-[#1e1e2e] overflow-hidden">
        <table className="min-w-full text-sm">
          <thead className="bg-[#0d0d14] border-b border-[#1e1e2e]">
            <tr>
              <th className="px-4 py-3 text-left text-[11px] font-medium uppercase tracking-wider text-gray-500">Name</th>
              <th className="px-4 py-3 text-left text-[11px] font-medium uppercase tracking-wider text-gray-500">Email</th>
              <th className="px-4 py-3 text-left text-[11px] font-medium uppercase tracking-wider text-gray-500">Role</th>
              <th className="px-4 py-3 text-left text-[11px] font-medium uppercase tracking-wider text-gray-500">Slack ID</th>
              <th className="px-4 py-3 text-left text-[11px] font-medium uppercase tracking-wider text-gray-500">Assignments</th>
              <th className="px-4 py-3 text-left text-[11px] font-medium uppercase tracking-wider text-gray-500">Active</th>
              <th className="px-4 py-3 text-left text-[11px] font-medium uppercase tracking-wider text-gray-500">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-[#1e1e2e]">
            {users.length === 0 && (
              <tr>
                <td colSpan={7} className="px-4 py-8 text-center text-sm text-gray-500">
                  No users configured. Add recruiters and admins to get started.
                </td>
              </tr>
            )}
            {users.map((user) => (
              <tr key={user.id} className="hover:bg-[#1a1a24] transition-colors">
                <td className="px-4 py-3 text-gray-200 font-medium">{user.name}</td>
                <td className="px-4 py-3 text-gray-400">{user.email}</td>
                <td className="px-4 py-3">
                  <span className={`inline-block px-2 py-0.5 text-xs rounded-full font-medium border ${
                    user.role === "admin"
                      ? "bg-rose-500/10 text-rose-400 border-rose-500/20"
                      : user.role === "recruiter"
                      ? "bg-cyan-500/10 text-cyan-400 border-cyan-500/20"
                      : "bg-gray-500/10 text-gray-400 border-gray-500/20"
                  }`}>
                    {user.role}
                  </span>
                </td>
                <td className="px-4 py-3 text-gray-400 font-mono">{user.slack_id || "\u2014"}</td>
                <td className="px-4 py-3 text-gray-400">{user.assignment_count}</td>
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
