import Link from "next/link";

const navItems = [
  { label: "Overview", href: "/", icon: "📊" },
  { label: "Jobs", href: "/jobs", icon: "💼" },
  { label: "Contacts", href: "/contacts", icon: "👤" },
  { label: "Outreach", href: "/outreach", icon: "🚀" },
  { label: "Replies", href: "/replies", icon: "💬" },
  { label: "Scrape Runs", href: "/scrape-runs", icon: "🔍" },
];

const settingsItems = [
  { label: "Email Accounts", href: "/settings/email-accounts", icon: "📧" },
  { label: "Templates", href: "/settings/templates", icon: "📝" },
  { label: "Users", href: "/settings/users", icon: "👥" },
];

export function Sidebar() {
  return (
    <aside className="w-56 bg-white border-r border-gray-200 min-h-screen p-4 flex flex-col">
      <div className="mb-8">
        <h1 className="text-lg font-bold text-gray-900">GTM Outreach</h1>
        <p className="text-xs text-gray-500">Dashboard</p>
      </div>
      <nav className="space-y-1">
        {navItems.map((item) => (
          <Link
            key={item.href}
            href={item.href}
            className="flex items-center gap-2 px-3 py-2 text-sm rounded-md hover:bg-gray-100 text-gray-700 hover:text-gray-900 transition-colors"
          >
            <span>{item.icon}</span>
            <span>{item.label}</span>
          </Link>
        ))}
      </nav>
      <div className="mt-6 pt-4 border-t border-gray-200">
        <p className="px-3 mb-2 text-xs font-semibold text-gray-400 uppercase tracking-wider">Settings</p>
        <nav className="space-y-1">
          {settingsItems.map((item) => (
            <Link
              key={item.href}
              href={item.href}
              className="flex items-center gap-2 px-3 py-2 text-sm rounded-md hover:bg-gray-100 text-gray-700 hover:text-gray-900 transition-colors"
            >
              <span>{item.icon}</span>
              <span>{item.label}</span>
            </Link>
          ))}
        </nav>
      </div>
    </aside>
  );
}
