"use client";

import { useEffect, useState } from "react";
import { IoNotificationsOutline } from "react-icons/io5";
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
    <header className="h-16 bg-white border-b border-slate-200 flex items-center justify-end px-6 gap-4 z-10">
      {/* Gateway status indicator */}
      <div className="flex items-center gap-2 mr-auto">
        <span
          className={`w-2 h-2 rounded-full shadow-sm ${
            gatewayOk === null
              ? "bg-slate-300"
              : gatewayOk
                ? "bg-emerald-500"
                : "bg-red-500"
          }`}
        />
        <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">
          Gateway{" "}
          {gatewayOk === null ? "..." : gatewayOk ? "Online" : "Offline"}
        </span>
      </div>

      {/* Notification Bell */}
      <button className="p-2 border border-slate-200 hover:bg-slate-50 rounded-md transition-colors text-slate-500 hover:text-slate-800">
        <IoNotificationsOutline className="w-4 h-4" />
      </button>

      {/* User Avatar */}
      <div className="w-8 h-8 rounded border border-slate-200 bg-slate-50 flex items-center justify-center overflow-hidden cursor-pointer hover:bg-slate-100 transition-colors">
        <span className="text-slate-700 font-bold text-xs uppercase">Admin</span>
      </div>
    </header>
  );
}
