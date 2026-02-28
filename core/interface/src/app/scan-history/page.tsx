"use client";

import { useEffect, useState } from "react";
import {
  IoSearchOutline,
  IoDocumentOutline,
  IoTimeOutline,
  IoAlertCircleOutline,
} from "react-icons/io5";
import { listReports, type AnalysisResult } from "@/lib/api";

/* ── Badge helpers ─────────────────────────────────────── */

function statusBadge(status: string) {
  const map: Record<string, string> = {
    pending: "bg-yellow-50 text-yellow-700 border border-yellow-200",
    running: "bg-blue-50 text-blue-700 border border-blue-200",
    complete: "bg-green-50 text-green-700 border border-green-200",
    failed: "bg-red-50 text-red-700 border border-red-200",
  };
  return (
    <span
      className={`inline-flex items-center gap-1 px-3 py-1 rounded-full text-xs font-medium ${
        map[status] || "bg-gray-50 text-gray-700 border border-gray-200"
      }`}
    >
      {status}
    </span>
  );
}

const iconColors = [
  "bg-blue-500",
  "bg-violet-500",
  "bg-green-500",
  "bg-orange-500",
  "bg-pink-500",
  "bg-teal-500",
  "bg-indigo-500",
  "bg-red-500",
];

/* ── Page Component ────────────────────────────────────── */

export default function ScanHistoryPage() {
  const [reports, setReports] = useState<AnalysisResult[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [search, setSearch] = useState("");

  useEffect(() => {
    (async () => {
      setLoading(true);
      try {
        const resp = await listReports();
        if (resp.status === "ok" && resp.data) {
          setReports(
            (resp.data as { reports: AnalysisResult[] }).reports || [],
          );
        }
      } catch {
        setError("Cannot connect to IsoLens gateway.");
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  const filtered = reports.filter((r) =>
    r.sample_name?.toLowerCase().includes(search.toLowerCase()),
  );

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-3">
        <h1 className="text-2xl font-bold text-gray-900">Scan History</h1>
        <span className="text-xs font-medium bg-amber-100 text-amber-700 px-2.5 py-1 rounded-full">
          Database storage — Coming Soon
        </span>
      </div>

      <p className="text-sm text-gray-500">
        Showing completed analysis reports from the local report storage.
        Persistent database-backed history with search, filtering, and export
        will be available in a future update.
      </p>

      {/* Search bar */}
      <div className="flex flex-wrap items-center gap-3">
        <div className="relative flex-1 min-w-[220px]">
          <IoSearchOutline className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search by sample name..."
            className="w-full pl-10 pr-4 py-2.5 border border-gray-300 rounded-lg text-sm text-gray-700 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-violet-300"
          />
        </div>
      </div>

      {/* Coming soon features disabled */}
      <div className="flex flex-wrap items-center gap-3 opacity-50 pointer-events-none">
        <button className="inline-flex items-center gap-1.5 border border-gray-300 bg-white text-sm text-gray-600 px-3 py-2 rounded-lg">
          Any Status ▾
        </button>
        <button className="inline-flex items-center gap-1.5 border border-gray-300 bg-white text-sm text-gray-600 px-3 py-2 rounded-lg">
          Any Risk Level ▾
          <span className="text-[10px] bg-amber-100 text-amber-700 px-1.5 py-0.5 rounded ml-1">
            Soon
          </span>
        </button>
        <button className="inline-flex items-center gap-1.5 border border-gray-300 bg-white text-sm text-gray-600 px-3 py-2 rounded-lg">
          <IoDocumentOutline className="w-3.5 h-3.5" />
          Export CSV
          <span className="text-[10px] bg-amber-100 text-amber-700 px-1.5 py-0.5 rounded ml-1">
            Soon
          </span>
        </button>
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 rounded-xl p-4 flex items-center gap-3">
          <IoAlertCircleOutline className="w-5 h-5 text-red-500 shrink-0" />
          <p className="text-sm text-red-700">{error}</p>
        </div>
      )}

      {loading ? (
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-12 text-center">
          <div className="animate-spin w-8 h-8 border-4 border-violet-200 border-t-violet-500 rounded-full mx-auto mb-3" />
          <p className="text-sm text-gray-500">Loading history...</p>
        </div>
      ) : filtered.length === 0 ? (
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-12 text-center">
          <IoTimeOutline className="w-12 h-12 text-gray-300 mx-auto mb-3" />
          <p className="text-gray-500">No scan history found.</p>
          <p className="text-sm text-gray-400 mt-1">
            Submit a sample from the{" "}
            <a href="/scan" className="text-violet-600 hover:text-violet-700">
              Scan
            </a>{" "}
            page.
          </p>
        </div>
      ) : (
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-gray-200 text-left text-gray-500 font-medium">
                <th className="px-4 py-3">Sample</th>
                <th className="px-3 py-3">Started</th>
                <th className="px-3 py-3">Status</th>
                <th className="px-3 py-3">Events</th>
                <th className="px-3 py-3">Files</th>
                <th className="px-3 py-3">Actions</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((report, idx) => (
                <tr
                  key={report.analysis_id}
                  className="border-b border-gray-100 hover:bg-gray-50 transition-colors"
                >
                  <td className="px-4 py-3">
                    <div className="flex items-center gap-3">
                      <div
                        className={`w-8 h-8 rounded-lg ${
                          iconColors[idx % iconColors.length]
                        } flex items-center justify-center`}
                      >
                        <IoDocumentOutline className="w-4 h-4 text-white" />
                      </div>
                      <div>
                        <p className="font-medium text-gray-800">
                          {report.sample_name}
                        </p>
                        <p className="text-xs text-gray-400 font-mono">
                          {report.analysis_id?.slice(0, 12)}...
                        </p>
                      </div>
                    </div>
                  </td>
                  <td className="px-3 py-3 text-gray-600 whitespace-nowrap">
                    {report.started_at
                      ? new Date(report.started_at).toLocaleString()
                      : "—"}
                  </td>
                  <td className="px-3 py-3">{statusBadge(report.status)}</td>
                  <td className="px-3 py-3 text-gray-600">
                    {report.sysmon_events}
                  </td>
                  <td className="px-3 py-3 text-gray-600">
                    {report.files_collected?.length || 0}
                  </td>
                  <td className="px-3 py-3">
                    <a
                      href="/reports"
                      className="text-sm text-violet-600 hover:text-violet-700 font-medium"
                    >
                      View →
                    </a>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
