"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { 
  IoSearchOutline, 
  IoDocumentTextOutline, 
  IoTimeOutline, 
  IoSettingsOutline,
  IoHeadsetOutline
} from "react-icons/io5";

interface NavItem {
  name: string;
  href: string;
  icon: React.ComponentType<{ className?: string }>;
  group: string;
}

const navItems: NavItem[] = [
  { name: "Scan", href: "/scan", icon: IoSearchOutline, group: "Analysis" },
  { name: "Reports", href: "/reports", icon: IoDocumentTextOutline, group: "Analysis" },
  { name: "Scan History", href: "/scan-history", icon: IoTimeOutline, group: "Analysis" },
  { name: "Settings", href: "/settings", icon: IoSettingsOutline, group: "System" },
  { name: "Help & Support", href: "/help-support", icon: IoHeadsetOutline, group: "System" },
];

export default function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="app-sidebar flex flex-col border-r border-slate-200 z-10">
      {/* Logo */}
      <div className="sidebar-brand px-6 py-6 flex items-center justify-start">
        <div className="brand-mark mr-3" aria-hidden="true">
          <span />
        </div>
        <p className="text-xl font-semibold tracking-tight text-slate-900">
          IsoLens
        </p>
      </div>

      {/* Navigation */}
      <nav className="flex-1 py-4">
        <ul className="space-y-0.5">
          {navItems.map((item, index) => {
            const isActive = pathname === item.href || 
              (item.href === "/scan" && pathname === "/");
            const Icon = item.icon;

            return (
              <li className="nav-entry" key={item.name}>
                {(index === 0 || navItems[index - 1].group !== item.group) && (
                  <p className="nav-group-label">{item.group}</p>
                )}
                <Link
                  href={item.href}
                  aria-current={isActive ? "page" : undefined}
                  className={`nav-link flex items-center gap-3 px-6 py-3 text-sm font-medium transition-colors ${
                    isActive
                      ? "is-active text-blue-700"
                      : "text-slate-600 hover:bg-slate-50 hover:text-slate-900"
                  }`}
                >
                  <Icon className={`w-5 h-5 ${isActive ? 'text-blue-600' : 'text-slate-400'}`} />
                  {item.name}
                </Link>
              </li>
            );
          })}
        </ul>
      </nav>
      
      {/* Footer */}
      <div className="sidebar-footer px-6 py-4 border-t border-slate-100 pb-6">
        <span className="sidebar-status-dot" aria-hidden="true" />
        <p className="text-xs text-slate-500 font-medium">Local analysis environment</p>
      </div>
    </aside>
  );
}
