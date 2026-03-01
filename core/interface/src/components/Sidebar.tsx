"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { 
  IoSearchOutline, 
  IoDocumentTextOutline, 
  IoTimeOutline, 
  IoShieldOutline,
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
    <aside className="w-64 bg-white h-screen flex flex-col border-r border-slate-200 shadow-sm z-10">
      {/* Logo */}
      <div className="px-6 py-6 flex items-center justify-start border-b border-transparent">
        <div className="w-8 h-8 rounded bg-slate-800 text-white flex items-center justify-center mr-3 font-bold text-lg tracking-wider">
          IS
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
                  className={`flex items-center gap-3 px-6 py-3 text-sm font-medium transition-colors border-l-4 ${
                    isActive
                      ? "border-blue-600 bg-blue-50/50 text-blue-700"
                      : "border-transparent text-slate-600 hover:bg-slate-50 hover:text-slate-900"
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
      <div className="px-6 py-4 border-t border-slate-100 pb-6">
        <p className="text-xs text-slate-400 font-medium">Sandbox Version 0.1.0</p>
      </div>
    </aside>
  );
}
