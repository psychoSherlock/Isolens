"use client";

import { useEffect, useState } from "react";
import {
  IoDocumentTextOutline,
  IoImageOutline,
  IoChevronBack,
  IoChevronForward,
  IoCloseOutline,
  IoAlertCircleOutline,
  IoCheckmarkCircleOutline,
  IoTimeOutline,
  IoFolderOpenOutline,
  IoBugOutline,
  IoRefreshOutline,
} from "react-icons/io5";
import {
  getAnalysisStatus,
  listScreenshots,
  listReports,
  screenshotURL,
  type AnalysisResult,
} from "@/lib/api";

export default function ReportsPage() {
  const [reports, setReports] = useState<AnalysisResult[]>([]);
  const [selected, setSelected] = useState<AnalysisResult | null>(null);
  const [screenshots, setScreenshots] = useState<string[]>([]);
  const [lightboxIdx, setLightboxIdx] = useState<number | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchData = async () => {
    setLoading(true);
    setError(null);
    try {
      // Fetch all saved reports
      const reportsResp = await listReports();
      let allReports: AnalysisResult[] = [];
      if (reportsResp.status === "ok" && reportsResp.data) {
        allReports = (reportsResp.data as { reports: AnalysisResult[] }).reports || [];
      }

      // Also check current/last analysis status
      const statusResp = await getAnalysisStatus();
      if (statusResp.status === "ok" && statusResp.data && "analysis_id" in statusResp.data) {
        const current = statusResp.data as AnalysisResult;
        // Add current if not already in the list
        if (!allReports.find((r) => r.analysis_id === current.analysis_id)) {
          allReports.unshift(current);
        }
      }

      setReports(allReports);

      // Auto-select the most recent if available
      if (allReports.length > 0 && !selected) {
        await selectReport(allReports[0]);
      }
    } catch {
      setError("Cannot connect to IsoLens gateway. Is it running on port 6969?");
    } finally {
      setLoading(false);
    }
  };

  const selectReport = async (report: AnalysisResult) => {
    setSelected(report);
    setScreenshots([]);
    if (report.analysis_id) {
      try {
        const resp = await listScreenshots(report.analysis_id);
        if (resp.status === "ok" && resp.data) {
          setScreenshots((resp.data as { screenshots: string[] }).screenshots || []);
        }
      } catch {
        // No screenshots available
      }
    }
  };

  useEffect(() => {
    fetchData();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const statusColor = (status: string) => {
    switch (status) {
      case "complete":
        return "text-green-600 bg-green-50 border-green-200";
      case "failed":
        return "text-red-600 bg-red-50 border-red-200";
      case "running":
        return "text-blue-600 bg-blue-50 border-blue-200";
      default:
        return "text-gray-600 bg-gray-50 border-gray-200";
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900">Reports</h1>
        <button
          onClick={fetchData}
          className="inline-flex items-center gap-2 text-sm text-gray-600 hover:text-violet-600 transition-colors"
        >
          <IoRefreshOutline className="w-4 h-4" />
          Refresh
        </button>
      </div>

      {loading && (
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-12 text-center">
          <div className="animate-spin w-8 h-8 border-4 border-violet-200 border-t-violet-500 rounded-full mx-auto mb-3" />
          <p className="text-sm text-gray-500">Loading reports...</p>
        </div>
      )}

      {error && (
        <div className="bg-red-50 border border-red-200 rounded-xl p-4 flex items-center gap-3">
          <IoAlertCircleOutline className="w-5 h-5 text-red-500 shrink-0" />
          <p className="text-sm text-red-700">{error}</p>
        </div>
      )}

      {!loading && !error && reports.length === 0 && (
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-12 text-center">
          <IoDocumentTextOutline className="w-12 h-12 text-gray-300 mx-auto mb-3" />
          <p className="text-gray-500">No analysis reports yet.</p>
          <p className="text-sm text-gray-400 mt-1">
            Submit a sample from the <a href="/scan" className="text-violet-600 hover:text-violet-700">Scan</a> page to generate a report.
          </p>
        </div>
      )}

      {!loading && reports.length > 0 && (
        <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
          {/* Report list (left sidebar) */}
          <div className="lg:col-span-1 space-y-2">
            <h3 className="text-sm font-semibold text-gray-500 uppercase tracking-wider mb-3">
              Analysis Reports
            </h3>
            {reports.map((report) => (
              <button
                key={report.analysis_id}
                onClick={() => selectReport(report)}
                className={`w-full text-left p-3 rounded-lg border transition-colors ${
                  selected?.analysis_id === report.analysis_id
                    ? "border-violet-300 bg-violet-50"
                    : "border-gray-200 bg-white hover:bg-gray-50"
                }`}
              >
                <p className="text-sm font-medium text-gray-800 truncate">
                  {report.sample_name || "Unknown"}
                </p>
                <div className="flex items-center gap-2 mt-1">
                  <span
                    className={`inline-block px-2 py-0.5 rounded text-xs font-medium border ${statusColor(
                      report.status
                    )}`}
                  >
                    {report.status}
                  </span>
                </div>
                {report.started_at && (
                  <p className="text-xs text-gray-400 mt-1">
                    {new Date(report.started_at).toLocaleString()}
                  </p>
                )}
              </button>
            ))}
          </div>

          {/* Report detail (right) */}
          <div className="lg:col-span-3 space-y-6">
            {selected ? (
              <>
                {/* Summary card */}
                <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
                  <div className="flex items-start justify-between mb-4">
                    <div>
                      <h2 className="text-lg font-semibold text-gray-900">
                        {selected.sample_name}
                      </h2>
                      <p className="text-xs text-gray-400 mt-0.5 font-mono">
                        ID: {selected.analysis_id}
                      </p>
                    </div>
                    <span
                      className={`inline-block px-3 py-1 rounded-full text-xs font-medium border ${statusColor(
                        selected.status
                      )}`}
                    >
                      {selected.status}
                    </span>
                  </div>

                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    <div className="bg-gray-50 rounded-lg p-3">
                      <div className="flex items-center gap-2 mb-1">
                        <IoTimeOutline className="w-4 h-4 text-gray-400" />
                        <span className="text-xs text-gray-500">Timeout</span>
                      </div>
                      <p className="text-sm font-medium text-gray-800">
                        {selected.timeout}s
                      </p>
                    </div>
                    <div className="bg-gray-50 rounded-lg p-3">
                      <div className="flex items-center gap-2 mb-1">
                        <IoBugOutline className="w-4 h-4 text-gray-400" />
                        <span className="text-xs text-gray-500">
                          Sysmon Events
                        </span>
                      </div>
                      <p className="text-sm font-medium text-gray-800">
                        {selected.sysmon_events}
                      </p>
                    </div>
                    <div className="bg-gray-50 rounded-lg p-3">
                      <div className="flex items-center gap-2 mb-1">
                        <IoFolderOpenOutline className="w-4 h-4 text-gray-400" />
                        <span className="text-xs text-gray-500">Files</span>
                      </div>
                      <p className="text-sm font-medium text-gray-800">
                        {selected.files_collected?.length || 0}
                      </p>
                    </div>
                    <div className="bg-gray-50 rounded-lg p-3">
                      <div className="flex items-center gap-2 mb-1">
                        <IoImageOutline className="w-4 h-4 text-gray-400" />
                        <span className="text-xs text-gray-500">
                          Screenshots
                        </span>
                      </div>
                      <p className="text-sm font-medium text-gray-800">
                        {screenshots.length}
                      </p>
                    </div>
                  </div>

                  {/* Timestamps */}
                  <div className="mt-4 flex flex-wrap gap-4 text-xs text-gray-500">
                    {selected.started_at && (
                      <span>
                        Started: {new Date(selected.started_at).toLocaleString()}
                      </span>
                    )}
                    {selected.completed_at && (
                      <span>
                        Completed:{" "}
                        {new Date(selected.completed_at).toLocaleString()}
                      </span>
                    )}
                  </div>

                  {selected.error && (
                    <div className="mt-4 bg-red-50 border border-red-200 rounded-lg p-3">
                      <p className="text-sm text-red-700">{selected.error}</p>
                    </div>
                  )}
                </div>

                {/* Files collected */}
                {selected.files_collected && selected.files_collected.length > 0 && (
                  <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
                    <h3 className="text-lg font-semibold text-gray-900 mb-4">
                      Collected Files
                    </h3>
                    <div className="space-y-1 max-h-48 overflow-y-auto">
                      {selected.files_collected.map((file, idx) => (
                        <div
                          key={idx}
                          className="flex items-center gap-2 px-3 py-2 rounded-md hover:bg-gray-50 text-sm"
                        >
                          <IoDocumentTextOutline className="w-4 h-4 text-gray-400 shrink-0" />
                          <span className="text-gray-700 font-mono text-xs truncate">
                            {file}
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Screenshots gallery */}
                {screenshots.length > 0 && (
                  <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
                    <h3 className="text-lg font-semibold text-gray-900 mb-4">
                      <IoImageOutline className="w-5 h-5 inline mr-2 text-violet-500" />
                      Screenshots ({screenshots.length})
                    </h3>
                    <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3">
                      {screenshots.map((name, idx) => (
                        <button
                          key={name}
                          onClick={() => setLightboxIdx(idx)}
                          className="group relative aspect-video rounded-lg overflow-hidden border border-gray-200 hover:border-violet-300 transition-colors"
                        >
                          <img
                            src={screenshotURL(selected.analysis_id, name)}
                            alt={name}
                            className="w-full h-full object-cover group-hover:scale-105 transition-transform"
                          />
                          <div className="absolute bottom-0 inset-x-0 bg-gradient-to-t from-black/60 to-transparent p-2">
                            <p className="text-[10px] text-white truncate">
                              {name}
                            </p>
                          </div>
                        </button>
                      ))}
                    </div>
                  </div>
                )}

                {/* Threat Intelligence — Coming Soon */}
                <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 opacity-60">
                  <div className="flex items-center gap-3">
                    <div className="p-2 bg-violet-100 rounded-lg">
                      <IoAlertCircleOutline className="w-5 h-5 text-violet-600" />
                    </div>
                    <div>
                      <h3 className="text-lg font-semibold text-gray-900">
                        AI Threat Intelligence{" "}
                        <span className="text-xs font-normal bg-amber-100 text-amber-700 px-2 py-0.5 rounded-full ml-2">
                          Coming Soon
                        </span>
                      </h3>
                      <p className="text-sm text-gray-500">
                        AI-powered threat classification, risk scoring, and
                        natural language summaries will appear here.
                      </p>
                    </div>
                  </div>
                </div>
              </>
            ) : (
              <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-12 text-center">
                <p className="text-gray-500">Select a report to view details</p>
              </div>
            )}
          </div>
        </div>
      )}

      {/* ── Lightbox ──────────────────────────── */}
      {lightboxIdx !== null && selected && (
        <div
          className="fixed inset-0 z-50 bg-black/80 flex items-center justify-center"
          onClick={() => setLightboxIdx(null)}
        >
          <div
            className="relative max-w-5xl max-h-[90vh] mx-4"
            onClick={(e) => e.stopPropagation()}
          >
            <img
              src={screenshotURL(selected.analysis_id, screenshots[lightboxIdx])}
              alt={screenshots[lightboxIdx]}
              className="max-w-full max-h-[85vh] rounded-lg shadow-2xl"
            />
            <p className="text-center text-white text-sm mt-2 opacity-75">
              {screenshots[lightboxIdx]} ({lightboxIdx + 1} / {screenshots.length})
            </p>

            {/* Close */}
            <button
              onClick={() => setLightboxIdx(null)}
              className="absolute -top-3 -right-3 w-8 h-8 rounded-full bg-white shadow flex items-center justify-center hover:bg-gray-100"
            >
              <IoCloseOutline className="w-5 h-5 text-gray-700" />
            </button>

            {/* Prev / Next */}
            {lightboxIdx > 0 && (
              <button
                onClick={() => setLightboxIdx(lightboxIdx - 1)}
                className="absolute left-2 top-1/2 -translate-y-1/2 w-10 h-10 rounded-full bg-white/80 shadow flex items-center justify-center hover:bg-white"
              >
                <IoChevronBack className="w-5 h-5 text-gray-700" />
              </button>
            )}
            {lightboxIdx < screenshots.length - 1 && (
              <button
                onClick={() => setLightboxIdx(lightboxIdx + 1)}
                className="absolute right-2 top-1/2 -translate-y-1/2 w-10 h-10 rounded-full bg-white/80 shadow flex items-center justify-center hover:bg-white"
              >
                <IoChevronForward className="w-5 h-5 text-gray-700" />
              </button>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
