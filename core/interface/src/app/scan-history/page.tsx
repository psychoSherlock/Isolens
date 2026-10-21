"use client";

import Link from "next/link";
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
        map[status] || "bg-slate-50 text-slate-700 border border-slate-200"
      }`}
    >
      {status}
    </span>
  );
}

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
    <div className="history-page space-y-7 max-w-6xl mx-auto">
      <div className="page-intro flex flex-wrap items-end justify-between gap-4">
        <div>
          <h1 className="text-3xl font-semibold text-slate-900">Scan history</h1>
          <p className="text-sm text-slate-600 mt-2">
            Past analyses saved in local report storage.
          </p>
        </div>
        {!loading && <span className="page-count">{filtered.length} {filtered.length === 1 ? "sample" : "samples"}</span>}
      </div>

      {/* Search bar */}
      <div className="flex flex-wrap items-center gap-3">
        <div className="relative flex-1 min-w-[220px]">
          <IoSearchOutline className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search by sample name..."
            className="w-full pl-10 pr-4 py-2.5 border border-slate-300 rounded-lg text-sm text-slate-700 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-300"
          />
        </div>
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 rounded p-4 flex items-center gap-3">
          <IoAlertCircleOutline className="w-5 h-5 text-red-500 shrink-0" />
          <p className="text-sm text-red-700">{error}</p>
        </div>
      )}

      {loading ? (
        <div className="bg-white rounded shadow-sm border border-slate-200 p-12 text-center">
          <div className="animate-spin w-8 h-8 border-4 border-blue-200 border-t-blue-500 rounded-full mx-auto mb-3" />
          <p className="text-sm text-slate-500">Loading history...</p>
        </div>
      ) : filtered.length === 0 ? (
        <div className="bg-white rounded shadow-sm border border-slate-200 p-12 text-center">
          <IoTimeOutline className="w-12 h-12 text-slate-300 mx-auto mb-3" />
          <p className="text-slate-500">No scan history found.</p>
          <p className="text-sm text-slate-400 mt-1">
            Submit a sample from the{" "}
            <Link href="/scan" className="text-blue-600 hover:text-blue-700">
              Scan
            </Link>{" "}
            page.
          </p>
        </div>
      ) : (
        <div className="bg-white rounded shadow-sm border border-slate-200 overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-slate-200 text-left text-slate-500 font-medium">
                <th className="px-4 py-3">Sample</th>
                <th className="px-3 py-3">Started</th>
                <th className="px-3 py-3">Status</th>
                <th className="px-3 py-3">Events</th>
                <th className="px-3 py-3">Files</th>
                <th className="px-3 py-3">Actions</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((report) => (
                <tr
                  key={report.analysis_id}
                  className="border-b border-slate-100 hover:bg-slate-50 transition-colors"
                >
                  <td className="px-4 py-3">
                    <div className="flex items-center gap-3">
                      <div
                        className="w-8 h-8 rounded-lg bg-[#eee9f7] flex items-center justify-center"
                      >
                        <IoDocumentOutline className="w-4 h-4 text-[#6042b2]" />
                      </div>
                      <div>
                        <p className="font-medium text-slate-800">
                          {report.sample_name}
                        </p>
                        <p className="text-xs text-slate-400 font-mono">
                          {report.analysis_id?.slice(0, 12)}...
                        </p>
                      </div>
                    </div>
                  </td>
                  <td className="px-3 py-3 text-slate-600 whitespace-nowrap">
                    {report.started_at
                      ? new Date(report.started_at).toLocaleString()
                      : "—"}
                  </td>
                  <td className="px-3 py-3">{statusBadge(report.status)}</td>
                  <td className="px-3 py-3 text-slate-600">
                    {report.sysmon_events}
                  </td>
                  <td className="px-3 py-3 text-slate-600">
                    {report.files_collected?.length || 0}
                  </td>
                  <td className="px-3 py-3">
                    <Link
                      href="/reports"
                      className="text-sm text-blue-600 hover:text-blue-700 font-medium"
                    >
                      View →
                    </Link>
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
