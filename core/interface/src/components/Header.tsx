"use client";

import { IoNotificationsOutline } from "react-icons/io5";

export default function Header() {
  return (
    <header className="h-16 bg-white border-b border-gray-200 flex items-center justify-end px-6 gap-4">
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
