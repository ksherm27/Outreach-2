import Link from "next/link";

const tabs = [
  { label: "Email Accounts", href: "/settings/email-accounts" },
  { label: "Templates", href: "/settings/templates" },
  { label: "Users", href: "/settings/users" },
];

export default function SettingsLayout({ children }: { children: React.ReactNode }) {
  return (
    <div>
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900 mb-4">Settings</h1>
        <nav className="flex gap-1 border-b border-gray-200">
          {tabs.map((tab) => (
            <Link
              key={tab.href}
              href={tab.href}
              className="px-4 py-2 text-sm font-medium text-gray-600 hover:text-gray-900 border-b-2 border-transparent hover:border-gray-300 -mb-px transition-colors"
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
