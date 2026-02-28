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
    <header className="h-16 bg-white border-b border-gray-200 flex items-center justify-end px-6 gap-4">
      {/* Gateway status indicator */}
      <div className="flex items-center gap-2 mr-auto ml-2">
        <span
          className={`w-2 h-2 rounded-full ${
            gatewayOk === null
              ? "bg-gray-300"
              : gatewayOk
                ? "bg-green-500"
                : "bg-red-400"
          }`}
        />
        <span className="text-xs text-gray-500">
          Gateway{" "}
          {gatewayOk === null ? "..." : gatewayOk ? "Connected" : "Offline"}
        </span>
      </div>

      {/* Notification Bell */}
      <button className="p-2 hover:bg-gray-100 rounded-lg transition-colors">
        <IoNotificationsOutline className="w-5 h-5 text-gray-600" />
      </button>

      {/* User Avatar */}
      <div className="w-9 h-9 rounded-full bg-violet-200 flex items-center justify-center overflow-hidden">
        <span className="text-violet-700 font-medium text-sm">U</span>
      </div>
    </header>
  );
}
