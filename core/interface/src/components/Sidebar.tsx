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
}

const navItems: NavItem[] = [
  { name: "Scan", href: "/scan", icon: IoSearchOutline },
  { name: "Reports", href: "/reports", icon: IoDocumentTextOutline },
  { name: "Scan History", href: "/scan-history", icon: IoTimeOutline },
  { name: "Settings", href: "/settings", icon: IoSettingsOutline },
  { name: "Help & Support", href: "/help-support", icon: IoHeadsetOutline },
];

export default function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="app-sidebar flex flex-col border-r border-slate-200 z-10">
      {/* Logo */}
      <div className="px-6 py-6 flex items-center justify-start">
        <div className="brand-mark mr-3" aria-hidden="true">
          <span />
        </div>
        <h1 className="text-xl font-bold tracking-tight text-slate-900">
          IsoLens
        </h1>
      </div>

      {/* Navigation */}
      <nav className="flex-1 py-4">
        <ul className="space-y-0.5">
          {navItems.map((item) => {
            const isActive = pathname === item.href || 
              (item.href === "/scan" && pathname === "/");
            const Icon = item.icon;

            return (
              <li key={item.name}>
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
        <p className="text-xs text-slate-400 font-medium">Sandbox Version 0.1.0</p>
      </div>
    </aside>
  );
}
