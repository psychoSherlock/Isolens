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
  { name: "Sand Box", href: "/sandbox", icon: IoShieldOutline },
  { name: "Settings", href: "/settings", icon: IoSettingsOutline },
  { name: "Help & Support", href: "/help-support", icon: IoHeadsetOutline },
];

export default function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="w-64 bg-white h-screen flex flex-col border-r border-gray-200">
      {/* Logo */}
      <div className="px-6 py-6">
        <h1 className="text-2xl font-semibold italic text-violet-600">
          SecureScan
        </h1>
      </div>

      {/* Navigation */}
      <nav className="flex-1 px-4">
        <ul className="space-y-1">
          {navItems.map((item) => {
            const isActive = pathname === item.href || 
              (item.href === "/scan" && pathname === "/");
            const Icon = item.icon;

            return (
              <li key={item.name}>
                <Link
                  href={item.href}
                  className={`flex items-center gap-3 px-4 py-3 rounded-lg text-sm font-medium transition-colors ${
                    isActive
                      ? "bg-violet-100 text-violet-700"
                      : "text-gray-700 hover:bg-gray-100"
                  }`}
                >
                  <Icon className="w-5 h-5" />
                  {item.name}
                </Link>
              </li>
            );
          })}
        </ul>
      </nav>
    </aside>
  );
}
