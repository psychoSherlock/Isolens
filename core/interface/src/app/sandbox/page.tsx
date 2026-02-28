"use client";

import {
  IoStopCircle,
  IoPause,
  IoRefresh,
  IoCheckmarkCircle,
  IoTimeOutline,
  IoChevronDown,
  IoChevronForward,
  IoChevronBack,
  IoDocumentOutline,
  IoCodeSlashOutline,
  IoRemove,
} from "react-icons/io5";

/* ── Mock Data ─────────────────────────────────────────── */

const logEntries = [
  { time: "18:33:26", message: "Filesystem mounted successfully." },
  { time: "18:33:36", message: "Controller: Analysis in progress_phas malware_sample.exe." },
  { time: "18:33:48", message: "Controller: analysis_filesystem_backup completed, pe: True" },
  { time: "18:33:39", message: 'Dropping file "malware_sample.exe" into SandboxShare.' },
  { time: "18:33:48", message: "Controller: waiting for sandbox_guest to initiate analysis." },
  { time: "18:33:42", message: "Controller: analyse_malware requested against malware_sample.exe" },
];

/* ── Page Component ────────────────────────────────────── */

export default function SandboxPage() {
  return (
    <div className="space-y-6">
      {/* Page Title */}
      <h1 className="text-2xl font-bold text-gray-900">Sandbox Environment</h1>

      {/* ── Status Banner ────────────────────────────── */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
        <div className="flex items-center gap-4 mb-5">
          {/* rotating ring indicator */}
          <div className="relative w-14 h-14 flex items-center justify-center">
            <div className="absolute inset-0 rounded-full border-4 border-gray-200" />
            <div className="absolute inset-0 rounded-full border-4 border-t-green-500 animate-spin" />
            <div className="w-8 h-8 bg-green-500 rounded-full" />
          </div>
          <div>
            <h2 className="text-xl font-semibold text-gray-900">
              Sandbox Status: <span className="font-bold">Running</span>
            </h2>
            <p className="text-sm text-gray-500">Uptime: 2 hours 15 minutes</p>
          </div>
        </div>

        {/* control buttons */}
        <div className="flex gap-3">
          <button className="inline-flex items-center gap-2 bg-red-500 hover:bg-red-600 text-white text-sm font-medium px-5 py-2.5 rounded-lg transition-colors">
            <IoStopCircle className="w-4 h-4" />
            Stop
          </button>
          <button className="inline-flex items-center gap-2 bg-white border border-gray-300 hover:bg-gray-50 text-gray-700 text-sm font-medium px-5 py-2.5 rounded-lg transition-colors">
            <IoPause className="w-4 h-4" />
            Pause
          </button>
          <button className="inline-flex items-center gap-2 bg-white border border-gray-300 hover:bg-gray-50 text-gray-700 text-sm font-medium px-5 py-2.5 rounded-lg transition-colors">
            <IoRefresh className="w-4 h-4" />
            Restore Snapshot
          </button>
        </div>
      </div>

      {/* ── Two-column cards ─────────────────────────── */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Current Analysis */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Current Analysis</h3>
          <p className="text-base font-mono text-gray-800 mb-3">malware_sample.exe</p>
          <div className="mb-1 flex items-center gap-2">
            <span className="text-sm text-gray-500">Current Phase</span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-2.5 mb-3">
            <div className="bg-violet-500 h-2.5 rounded-full" style={{ width: "45%" }} />
          </div>
          <p className="text-sm text-gray-500 mb-5">
            Elapsed Time: <span className="font-medium text-gray-700">00:02:17</span>
          </p>
          <button className="w-full bg-red-500 hover:bg-red-600 text-white font-medium py-3 rounded-lg transition-colors">
            Stop Analysis
          </button>
        </div>

        {/* Right column: Agent + Shared Folder */}
        <div className="space-y-6">
          {/* Agent Connection Status */}
          <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-3">Agent Connection Status</h3>
            <div className="flex items-center gap-2">
              <IoCheckmarkCircle className="w-6 h-6 text-green-500" />
              <span className="text-base font-medium text-green-600">Connected</span>
            </div>
            <p className="text-sm text-gray-400 mt-1 ml-8">Last Heartbeat: A few seconds ago</p>
          </div>

          {/* Shared Folder Status */}
          <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-3">Shared Folder Status</h3>
            <div className="flex items-center gap-2">
              <IoCheckmarkCircle className="w-6 h-6 text-green-500" />
              <span className="text-base font-medium text-gray-800">SandboxShare/</span>
            </div>
            <p className="text-sm text-gray-400 mt-1 ml-8">Mounted (Read/Write)</p>
          </div>
        </div>
      </div>

      {/* ── Bottom row ───────────────────────────────── */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Real-time Activity Log */}
        <div className="bg-gray-900 rounded-xl shadow-sm border border-gray-700 p-6 text-gray-200">
          <h3 className="text-lg font-semibold text-white mb-4">Real-time Activity Log</h3>
          <div className="space-y-3 max-h-64 overflow-y-auto pr-2 font-mono text-sm">
            {logEntries.map((entry, idx) => (
              <div key={idx} className="flex gap-3">
                <IoTimeOutline className="w-4 h-4 mt-0.5 text-violet-400 shrink-0" />
                <span className="text-violet-300 shrink-0">{entry.time}</span>
                <span className="text-gray-300">{entry.message}</span>
              </div>
            ))}
          </div>
          {/* Scroll indicator bar */}
          <div className="mt-4 flex items-center gap-2">
            <div className="flex-1 h-1.5 bg-gray-700 rounded-full overflow-hidden">
              <div className="h-full bg-violet-500 rounded-full" style={{ width: "60%" }} />
            </div>
            <IoRefresh className="w-4 h-4 text-gray-500 cursor-pointer hover:text-gray-300" />
          </div>
        </div>

        {/* Right column: VM Info + Snapshot Selector */}
        <div className="space-y-6">
          {/* Sandbox VM Info */}
          <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Sandbox VM Info</h3>
            <dl className="space-y-3 text-sm">
              <div className="flex justify-between">
                <dt className="text-gray-500 font-medium">VM Name:</dt>
                <dd className="text-gray-800">Isolens_VM1</dd>
              </div>
              <div className="flex justify-between">
                <dt className="text-gray-500 font-medium">OS:</dt>
                <dd className="text-gray-800">Windows 7 (64-bit)</dd>
              </div>
              <div className="flex justify-between">
                <dt className="text-gray-500 font-medium">RAM:</dt>
                <dd className="text-gray-800">4 GB</dd>
              </div>
              <div className="flex justify-between">
                <dt className="text-gray-500 font-medium">Network:</dt>
                <dd className="text-gray-800 text-right">
                  Host Only Adapter<br />192.168.55.101
                </dd>
              </div>
            </dl>
          </div>

          {/* Snapshot Selector */}
          <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Snapshot Selector</h3>
            <div className="relative mb-4">
              <select className="w-full appearance-none border border-gray-300 rounded-lg px-4 py-2.5 pr-10 text-sm text-gray-700 bg-white focus:outline-none focus:ring-2 focus:ring-violet-300">
                <option>Clean State (14 Apr 2024)</option>
                <option>Post-install (10 Apr 2024)</option>
              </select>
              <IoChevronDown className="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400 pointer-events-none" />
            </div>
            <button className="w-full border border-gray-300 hover:bg-gray-50 text-gray-700 font-medium py-2.5 rounded-lg transition-colors text-sm">
              Restore Snapshot
            </button>
          </div>
        </div>
      </div>

      {/* ── Pagination + Export ───────────────────────── */}
      <div className="flex items-center justify-between">
        {/* Pagination */}
        <div className="flex items-center gap-2">
          <span className="text-sm text-gray-500">Page:</span>
          <input
            type="number"
            defaultValue={1}
            className="w-12 border border-gray-300 rounded-md text-center text-sm py-1 focus:outline-none focus:ring-2 focus:ring-violet-300"
            readOnly
          />
          <button className="p-1 hover:bg-gray-100 rounded transition-colors">
            <IoChevronDown className="w-4 h-4 text-gray-500" />
          </button>
          <span className="text-sm text-gray-400 mx-1">10</span>
          <button className="p-1 hover:bg-gray-100 rounded transition-colors">
            <IoChevronForward className="w-4 h-4 text-gray-500" />
          </button>
          <button className="p-1 hover:bg-gray-100 rounded transition-colors">
            <IoRemove className="w-4 h-4 text-gray-500" />
          </button>
        </div>

        {/* Export buttons */}
        <div className="flex gap-3">
          <button className="inline-flex items-center gap-2 border border-gray-300 bg-white hover:bg-gray-50 text-gray-700 text-sm font-medium px-4 py-2 rounded-lg transition-colors">
            <IoDocumentOutline className="w-4 h-4" />
            Export CSV
          </button>
          <button className="inline-flex items-center gap-2 border border-gray-300 bg-white hover:bg-gray-50 text-gray-700 text-sm font-medium px-4 py-2 rounded-lg transition-colors">
            <IoCodeSlashOutline className="w-4 h-4" />
            Export JSON
          </button>
        </div>
      </div>
    </div>
  );
}
