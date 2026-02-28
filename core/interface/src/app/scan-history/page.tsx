"use client";

import {
  IoSearchOutline,
  IoCalendarOutline,
  IoChevronDown,
  IoChevronForward,
  IoChevronBack,
  IoDocumentOutline,
  IoCodeSlashOutline,
  IoEllipsisHorizontal,
  IoListOutline,
} from "react-icons/io5";

/* ── Types ─────────────────────────────────────────────── */

type ScanStatus = "Pending" | "Running" | "Completed" | "Failed";
type RiskLevel = "No Threat Detected" | "Suspicious" | "Malicious";

interface ScanEntry {
  id: number;
  fileName: string;
  hash: string;
  submissionDate: string;
  status: ScanStatus;
  riskLevel: RiskLevel;
  iconColor: string;
}

/* ── Mock Data ─────────────────────────────────────────── */

const mockScans: ScanEntry[] = [
  { id: 1,  fileName: "FIl.exe",           hash: "",          submissionDate: "Apr 20, 2024 14:35", status: "Pending",   riskLevel: "No Threat Detected", iconColor: "bg-blue-500"   },
  { id: 2,  fileName: "virus.doc",         hash: "95272494",  submissionDate: "Apr 20, 2024 14:35", status: "Running",   riskLevel: "Suspicious",         iconColor: "bg-yellow-500" },
  { id: 3,  fileName: "trojan.zip",        hash: "68673108",  submissionDate: "Apr 20, 2024 14:35", status: "Failed",    riskLevel: "Malicious",          iconColor: "bg-purple-500" },
  { id: 4,  fileName: "Sample.exe",        hash: "3591584",   submissionDate: "Apr 20, 2024 14:35", status: "Running",   riskLevel: "No Threat Detected", iconColor: "bg-green-500"  },
  { id: 5,  fileName: "loader.bat",        hash: "20435864",  submissionDate: "Apr 20, 2024 14:35", status: "Pending",   riskLevel: "Malicious",          iconColor: "bg-orange-500" },
  { id: 6,  fileName: "ransomware.zip",    hash: "",          submissionDate: "Apr 20, 2024 14:35", status: "Completed", riskLevel: "Suspicious",         iconColor: "bg-red-500"    },
  { id: 7,  fileName: "script.ps1",        hash: "533988910", submissionDate: "Apr 20, 2024 14:35", status: "Completed", riskLevel: "Malicious",          iconColor: "bg-pink-500"   },
  { id: 8,  fileName: "keylogger.dll",     hash: "533096",    submissionDate: "Apr 20, 2024 14:35", status: "Completed", riskLevel: "No Threat Detected", iconColor: "bg-teal-500"   },
  { id: 9,  fileName: "UlDUMP.zip",        hash: "53599965",  submissionDate: "Apr 20, 2024 14:35", status: "Pending",   riskLevel: "Suspicious",         iconColor: "bg-indigo-500" },
  { id: 10, fileName: "exploit.exe",       hash: "26405911",  submissionDate: "Apr 20, 2024 14:35", status: "Completed", riskLevel: "No Threat Detected", iconColor: "bg-gray-500"   },
  { id: 11, fileName: "Fil.exe",           hash: "98598580",  submissionDate: "Apr 20, 2024 14:35", status: "Pending",   riskLevel: "No Threat Detected", iconColor: "bg-blue-400"   },
  { id: 12, fileName: "exploit.exe",       hash: "98398892",  submissionDate: "Apr 20, 2024 14:35", status: "Completed", riskLevel: "No Threat Detected", iconColor: "bg-gray-400"   },
  { id: 13, fileName: "Exploit.exe",       hash: "952255",    submissionDate: "Apr 20, 2024 14:35", status: "Completed", riskLevel: "No Threat Detected", iconColor: "bg-gray-500"   },
];

/* ── Badge helpers ─────────────────────────────────────── */

function statusBadge(status: ScanStatus) {
  const map: Record<ScanStatus, string> = {
    Pending:   "bg-yellow-50 text-yellow-700 border border-yellow-200",
    Running:   "bg-blue-50 text-blue-700 border border-blue-200",
    Completed: "bg-green-50 text-green-700 border border-green-200",
    Failed:    "bg-red-50 text-red-700 border border-red-200",
  };
  return (
    <span className={`inline-flex items-center gap-1 px-3 py-1 rounded-full text-xs font-medium ${map[status]}`}>
      {status === "Failed" && <span className="text-red-500">↓</span>}
      {status}
    </span>
  );
}

function riskBadge(level: RiskLevel) {
  const map: Record<RiskLevel, string> = {
    "No Threat Detected": "bg-green-50 text-green-700 border border-green-200",
    Suspicious:           "bg-yellow-50 text-yellow-700 border border-yellow-200",
    Malicious:            "bg-red-50 text-red-700 border border-red-200",
  };
  return (
    <span className={`inline-block px-3 py-1 rounded-full text-xs font-medium ${map[level]}`}>
      {level}
    </span>
  );
}

/* ── Page Component ────────────────────────────────────── */

export default function ScanHistoryPage() {
  return (
    <div className="space-y-6">
      {/* Page Title */}
      <h1 className="text-2xl font-bold text-gray-900">Scan History</h1>

      {/* ── Search & Filters row ─────────────────────── */}
      <div className="space-y-3">
        {/* Top row: search + date */}
        <div className="flex flex-wrap items-center gap-3">
          {/* Search bar */}
          <div className="relative flex-1 min-w-[220px]">
            <IoSearchOutline className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
            <input
              type="text"
              placeholder="Search scans..."
              className="w-full pl-10 pr-10 py-2.5 border border-gray-300 rounded-lg text-sm text-gray-700 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-violet-300"
              readOnly
            />
            <button className="absolute right-3 top-1/2 -translate-y-1/2">
              <IoChevronDown className="w-4 h-4 text-gray-400" />
            </button>
          </div>

          {/* Date range filter */}
          <button className="inline-flex items-center gap-2 border border-gray-300 bg-white hover:bg-gray-50 text-sm text-gray-700 px-4 py-2.5 rounded-lg transition-colors">
            <IoCalendarOutline className="w-4 h-4 text-gray-400" />
            Apr 01, 2024 - May 01, 2024
          </button>

          {/* List toggle */}
          <button className="p-2.5 border border-gray-300 bg-white hover:bg-gray-50 rounded-lg transition-colors">
            <IoListOutline className="w-4 h-4 text-gray-500" />
          </button>
        </div>

        {/* Second row: quick filters + export */}
        <div className="flex flex-wrap items-center gap-3">
          <button className="inline-flex items-center gap-1.5 border border-gray-300 bg-white hover:bg-gray-50 text-sm text-gray-600 px-3 py-2 rounded-lg transition-colors">
            <IoSearchOutline className="w-3.5 h-3.5" />
            Search slows
            <IoChevronDown className="w-3.5 h-3.5 ml-0.5" />
          </button>
          <button className="inline-flex items-center gap-1.5 border border-gray-300 bg-white hover:bg-gray-50 text-sm text-gray-600 px-3 py-2 rounded-lg transition-colors">
            Any Status
            <IoChevronDown className="w-3.5 h-3.5 ml-0.5" />
          </button>
          <button className="inline-flex items-center gap-1.5 border border-gray-300 bg-white hover:bg-gray-50 text-sm text-gray-600 px-3 py-2 rounded-lg transition-colors">
            Any Risk Level
            <IoChevronDown className="w-3.5 h-3.5 ml-0.5" />
          </button>
          <button className="inline-flex items-center gap-2 border border-gray-300 bg-white hover:bg-gray-50 text-sm text-gray-600 px-3 py-2 rounded-lg transition-colors">
            <IoDocumentOutline className="w-3.5 h-3.5" />
            Export CSV
          </button>
          <button className="p-2 border border-gray-300 bg-white hover:bg-gray-50 rounded-lg transition-colors">
            <IoEllipsisHorizontal className="w-4 h-4 text-gray-500" />
          </button>
        </div>
      </div>

      {/* ── File Name / SHA256 header bar ────────────── */}
      <div className="flex items-center justify-between bg-gray-50 border border-gray-200 rounded-t-xl px-4 py-3">
        <div className="flex items-center gap-3">
          <input type="checkbox" className="w-4 h-4 rounded border-gray-300 text-violet-600 focus:ring-violet-500" readOnly />
          <span className="text-sm font-medium text-gray-700">File Name / SHA256</span>
        </div>
        <span className="text-sm font-medium text-gray-700">Actions</span>
      </div>

      {/* ── Table ────────────────────────────────────── */}
      <div className="bg-white rounded-b-xl shadow-sm border border-t-0 border-gray-200 overflow-x-auto -mt-6">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-gray-200 text-left text-gray-500 font-medium">
              <th className="pl-4 pr-2 py-3 w-10">
                <input type="checkbox" className="w-4 h-4 rounded border-gray-300 text-violet-600 focus:ring-violet-500" readOnly />
              </th>
              <th className="px-3 py-3">File Name</th>
              <th className="px-3 py-3">Submission Date</th>
              <th className="px-3 py-3">Status</th>
              <th className="px-3 py-3">Risk Level</th>
              <th className="px-3 py-3 w-10 text-center">
                <IoEllipsisHorizontal className="w-4 h-4 mx-auto text-gray-400" />
              </th>
            </tr>
          </thead>
          <tbody>
            {mockScans.map((scan) => (
              <tr key={scan.id} className="border-b border-gray-100 hover:bg-gray-50 transition-colors">
                <td className="pl-4 pr-2 py-3">
                  <input type="checkbox" className="w-4 h-4 rounded border-gray-300 text-violet-600 focus:ring-violet-500" readOnly />
                </td>
                <td className="px-3 py-3">
                  <div className="flex items-center gap-3">
                    <div className={`w-8 h-8 rounded-lg ${scan.iconColor} flex items-center justify-center`}>
                      <IoDocumentOutline className="w-4 h-4 text-white" />
                    </div>
                    <div>
                      <p className="font-medium text-gray-800">{scan.fileName}</p>
                      {scan.hash && (
                        <p className="text-xs text-gray-400">{scan.hash}</p>
                      )}
                    </div>
                  </div>
                </td>
                <td className="px-3 py-3 text-gray-600 whitespace-nowrap">{scan.submissionDate}</td>
                <td className="px-3 py-3">{statusBadge(scan.status)}</td>
                <td className="px-3 py-3">{riskBadge(scan.riskLevel)}</td>
                <td className="px-3 py-3 text-center">
                  <button className="p-1 hover:bg-gray-100 rounded transition-colors">
                    <IoEllipsisHorizontal className="w-4 h-4 text-gray-400" />
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
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
          <button className="p-1 hover:bg-gray-100 rounded transition-colors">
            <IoChevronForward className="w-4 h-4 text-gray-500" />
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
