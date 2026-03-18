import { prisma } from "@/lib/prisma";
import { toggleEmailAccount, deleteEmailAccount } from "@/app/actions/email-accounts";
import { ToggleSwitch } from "@/components/form/toggle-switch";
import { DeleteButton } from "@/components/form/delete-button";
import { AddEmailAccountButton, EditEmailAccountButton } from "./email-account-form";

export const dynamic = "force-dynamic";

export default async function EmailAccountsPage() {
  const accounts = await prisma.email_accounts.findMany({
    orderBy: { created_at: "desc" },
  });

  return (
    <div>
      <AddEmailAccountButton>+ Add Email Account</AddEmailAccountButton>

      <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Email</th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Display Name</th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Platform</th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Warmup</th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Daily Limit</th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Active</th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-200">
            {accounts.length === 0 && (
              <tr>
                <td colSpan={7} className="px-4 py-8 text-center text-sm text-gray-500">
                  No email accounts configured. Add one to get started.
                </td>
              </tr>
            )}
            {accounts.map((account) => (
              <tr key={account.id} className="hover:bg-gray-50">
                <td className="px-4 py-3 text-sm text-gray-900 font-medium">{account.email_address}</td>
                <td className="px-4 py-3 text-sm text-gray-600">{account.display_name}</td>
                <td className="px-4 py-3">
                  <span className={`inline-block px-2 py-0.5 text-xs rounded-full font-medium ${
                    account.platform === "instantly"
                      ? "bg-purple-100 text-purple-800"
                      : "bg-orange-100 text-orange-800"
                  }`}>
                    {account.platform}
                  </span>
                </td>
                <td className="px-4 py-3">
                  <span className={`inline-block px-2 py-0.5 text-xs rounded-full font-medium ${
                    account.warmup_status === "warmed"
                      ? "bg-green-100 text-green-800"
                      : account.warmup_status === "warming"
                      ? "bg-yellow-100 text-yellow-800"
                      : account.warmup_status === "paused"
                      ? "bg-red-100 text-red-800"
                      : "bg-gray-100 text-gray-800"
                  }`}>
                    {account.warmup_status}
                  </span>
                </td>
                <td className="px-4 py-3 text-sm text-gray-600">{account.daily_send_limit}</td>
                <td className="px-4 py-3">
                  <ToggleSwitch
                    isActive={account.is_active}
                    onToggle={async () => {
                      "use server";
                      return toggleEmailAccount(account.id);
                    }}
                  />
                </td>
                <td className="px-4 py-3">
                  <div className="flex items-center gap-3">
                    <EditEmailAccountButton account={account} />
                    <DeleteButton
                      onDelete={async () => {
                        "use server";
                        return deleteEmailAccount(account.id);
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
