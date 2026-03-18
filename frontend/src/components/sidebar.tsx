"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard,
  Briefcase,
  Users,
  Rocket,
  MessageSquare,
  Search,
  Mail,
  FileText,
  UserCog,
  Zap,
} from "lucide-react";

const navItems = [
  { label: "Overview", href: "/", icon: LayoutDashboard },
  { label: "Jobs", href: "/jobs", icon: Briefcase },
  { label: "Contacts", href: "/contacts", icon: Users },
  { label: "Outreach", href: "/outreach", icon: Rocket },
  { label: "Replies", href: "/replies", icon: MessageSquare },
  { label: "Scrape Runs", href: "/scrape-runs", icon: Search },
];

const settingsItems = [
  { label: "Email Accounts", href: "/settings/email-accounts", icon: Mail },
  { label: "Templates", href: "/settings/templates", icon: FileText },
  { label: "Users", href: "/settings/users", icon: UserCog },
];

export function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="w-60 bg-[#111118] border-r border-[#1e1e2e] min-h-screen p-4 flex flex-col">
      <div className="mb-8 px-3">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-cyan-500 to-violet-500 flex items-center justify-center">
            <Zap className="w-4 h-4 text-white" />
          </div>
          <div>
            <h1 className="text-base font-semibold text-gray-100">GTM Outreach</h1>
            <p className="text-[10px] text-gray-500 uppercase tracking-widest">Dashboard</p>
          </div>
        </div>
      </div>

      <nav className="space-y-0.5">
        {navItems.map((item) => {
          const isActive = pathname === item.href;
          const Icon = item.icon;
          return (
            <Link
              key={item.href}
              href={item.href}
              className={`flex items-center gap-3 px-3 py-2.5 text-sm rounded-lg transition-all duration-150 ${
                isActive
                  ? "bg-cyan-500/10 text-cyan-400 border border-cyan-500/20"
                  : "text-gray-400 hover:text-gray-200 hover:bg-[#1a1a24] border border-transparent"
              }`}
            >
              <Icon className="w-4 h-4 flex-shrink-0" />
              <span className="font-medium">{item.label}</span>
            </Link>
          );
        })}
      </nav>

      <div className="mt-8 pt-4 border-t border-[#1e1e2e]">
        <p className="px-3 mb-3 text-[10px] font-semibold text-gray-500 uppercase tracking-widest">
          Settings
        </p>
        <nav className="space-y-0.5">
          {settingsItems.map((item) => {
            const isActive = pathname.startsWith(item.href);
            const Icon = item.icon;
            return (
              <Link
                key={item.href}
                href={item.href}
                className={`flex items-center gap-3 px-3 py-2.5 text-sm rounded-lg transition-all duration-150 ${
                  isActive
                    ? "bg-cyan-500/10 text-cyan-400 border border-cyan-500/20"
                    : "text-gray-400 hover:text-gray-200 hover:bg-[#1a1a24] border border-transparent"
                }`}
              >
                <Icon className="w-4 h-4 flex-shrink-0" />
                <span className="font-medium">{item.label}</span>
              </Link>
            );
          })}
        </nav>
      </div>

      <div className="mt-auto pt-4 border-t border-[#1e1e2e]">
        <div className="px-3 py-2">
          <p className="text-[10px] text-gray-600">v1.0 &middot; Series A-D Pipeline</p>
        </div>
      </div>
    </aside>
  );
}
