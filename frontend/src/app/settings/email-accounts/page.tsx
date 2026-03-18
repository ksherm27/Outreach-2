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

      <div className="bg-[#111118] rounded-xl border border-[#1e1e2e] overflow-hidden">
        <table className="min-w-full text-sm">
          <thead className="bg-[#0d0d14] border-b border-[#1e1e2e]">
            <tr>
              <th className="px-4 py-3 text-left text-[11px] font-medium uppercase tracking-wider text-gray-500">Email</th>
              <th className="px-4 py-3 text-left text-[11px] font-medium uppercase tracking-wider text-gray-500">Display Name</th>
              <th className="px-4 py-3 text-left text-[11px] font-medium uppercase tracking-wider text-gray-500">Platform</th>
              <th className="px-4 py-3 text-left text-[11px] font-medium uppercase tracking-wider text-gray-500">Warmup</th>
              <th className="px-4 py-3 text-left text-[11px] font-medium uppercase tracking-wider text-gray-500">Daily Limit</th>
              <th className="px-4 py-3 text-left text-[11px] font-medium uppercase tracking-wider text-gray-500">Active</th>
              <th className="px-4 py-3 text-left text-[11px] font-medium uppercase tracking-wider text-gray-500">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-[#1e1e2e]">
            {accounts.length === 0 && (
              <tr>
                <td colSpan={7} className="px-4 py-8 text-center text-sm text-gray-500">
                  No email accounts configured. Add one to get started.
                </td>
              </tr>
            )}
            {accounts.map((account) => (
              <tr key={account.id} className="hover:bg-[#1a1a24] transition-colors">
                <td className="px-4 py-3 text-gray-200 font-medium">{account.email_address}</td>
                <td className="px-4 py-3 text-gray-400">{account.display_name}</td>
                <td className="px-4 py-3">
                  <span className={`inline-block px-2 py-0.5 text-xs rounded-full font-medium border ${
                    account.platform === "instantly"
                      ? "bg-violet-500/10 text-violet-400 border-violet-500/20"
                      : "bg-orange-500/10 text-orange-400 border-orange-500/20"
                  }`}>
                    {account.platform}
                  </span>
                </td>
                <td className="px-4 py-3">
                  <span className={`inline-block px-2 py-0.5 text-xs rounded-full font-medium border ${
                    account.warmup_status === "warmed"
                      ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/20"
                      : account.warmup_status === "warming"
                      ? "bg-amber-500/10 text-amber-400 border-amber-500/20"
                      : account.warmup_status === "paused"
                      ? "bg-rose-500/10 text-rose-400 border-rose-500/20"
                      : "bg-gray-500/10 text-gray-400 border-gray-500/20"
                  }`}>
                    {account.warmup_status}
                  </span>
                </td>
                <td className="px-4 py-3 text-gray-400">{account.daily_send_limit}</td>
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
