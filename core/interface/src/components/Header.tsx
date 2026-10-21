"use client";

import { useEffect, useState } from "react";
import { ping } from "@/lib/api";

export default function Header() {
  const [gatewayOk, setGatewayOk] = useState<boolean | null>(null);

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
    <header className="app-header flex items-center justify-end px-8 z-10">
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
