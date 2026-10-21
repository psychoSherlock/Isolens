"use client";

import { useEffect, useState } from "react";
import { usePathname } from "next/navigation";
import { ping } from "@/lib/api";

export default function Header() {
  const pathname = usePathname();
  const [gatewayOk, setGatewayOk] = useState<boolean | null>(null);
  const pageName = pathname === "/" || pathname === "/scan" ? "New scan" :
    pathname === "/reports" ? "Reports" :
    pathname === "/scan-history" ? "Scan history" :
    pathname === "/settings" ? "Settings" : "Help & support";

  useEffect(() => {
    const check = async () => {
      try {
        const resp = await ping();
        setGatewayOk(resp.status === "ok");
      } catch {
        setGatewayOk(false);
      }
    };
    check();
    const interval = setInterval(check, 15000);
    return () => clearInterval(interval);
  }, []);

  return (
    <header className="app-header flex items-center justify-between px-8 z-10">
      <h1 className="text-lg font-semibold text-slate-800">{pageName}</h1>
      {/* Gateway status indicator */}
      <div className="gateway-status flex items-center gap-2">
        <span
          className={`w-2 h-2 rounded-full shadow-sm ${
            gatewayOk === null
              ? "bg-slate-300"
              : gatewayOk
                ? "bg-emerald-500"
                : "bg-red-500"
          }`}
        />
        <span className="text-xs font-medium text-slate-600">
          Gateway{" "}
          {gatewayOk === null ? "..." : gatewayOk ? "Online" : "Offline"}
        </span>
      </div>

    </header>
  );
}
