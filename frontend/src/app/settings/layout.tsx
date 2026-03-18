import Link from "next/link";

const tabs = [
  { label: "Email Accounts", href: "/settings/email-accounts" },
  { label: "Templates", href: "/settings/templates" },
  { label: "Users", href: "/settings/users" },
];

export default function SettingsLayout({ children }: { children: React.ReactNode }) {
  return (
    <div>
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-gray-100 mb-4">Settings</h1>
        <nav className="flex gap-1 border-b border-[#1e1e2e]">
          {tabs.map((tab) => (
            <Link
              key={tab.href}
              href={tab.href}
              className="px-4 py-2.5 text-sm font-medium text-gray-400 hover:text-gray-200 border-b-2 border-transparent hover:border-cyan-500/50 -mb-px transition-all"
            >
              {tab.label}
            </Link>
          ))}
        </nav>
      </div>
      {children}
    </div>
  );
}
