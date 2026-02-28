"use client";

import { useEffect, useState, useRef, useCallback } from "react";
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
  IoGitNetworkOutline,
  IoKeyOutline,
  IoTerminalOutline,
  IoGlobeOutline,
  IoShieldCheckmarkOutline,
  IoChevronDownOutline,
  IoChevronUpOutline,
  IoEyeOutline,
  IoLayersOutline,
  IoHardwareChipOutline,
  IoServerOutline,
  IoSparklesOutline,
} from "react-icons/io5";
import {
  getAnalysisStatus,
  listReports,
  screenshotURL,
  getReportData,
  type AnalysisResult,
  type ReportData,
  type SysmonData,
  type ProcmonData,
  type NetworkData,
  type TcpvconRow,
} from "@/lib/api";

/* ═══════════════════════════════════════════════════════════════════════════
   COLLAPSIBLE SECTION COMPONENT
   ═══════════════════════════════════════════════════════════════════════════ */

function Section({
  title,
  icon,
  badge,
  defaultOpen = true,
  children,
  accentColor = "violet",
}: {
  title: string;
  icon: React.ReactNode;
  badge?: string | number;
  defaultOpen?: boolean;
  children: React.ReactNode;
  accentColor?: string;
}) {
  const [open, setOpen] = useState(defaultOpen);
  const colors: Record<string, string> = {
    violet: "bg-violet-50 border-violet-200 text-violet-700",
    blue: "bg-blue-50 border-blue-200 text-blue-700",
    amber: "bg-amber-50 border-amber-200 text-amber-700",
    emerald: "bg-emerald-50 border-emerald-200 text-emerald-700",
    rose: "bg-rose-50 border-rose-200 text-rose-700",
    sky: "bg-sky-50 border-sky-200 text-sky-700",
    orange: "bg-orange-50 border-orange-200 text-orange-700",
    slate: "bg-slate-50 border-slate-200 text-slate-700",
  };
  const colorClass = colors[accentColor] || colors.violet;

  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
      <button
        onClick={() => setOpen(!open)}
        className="w-full flex items-center gap-3 p-5 text-left hover:bg-gray-50/50 transition-colors"
      >
        <div className={`p-2 rounded-lg border ${colorClass}`}>{icon}</div>
        <h3 className="text-base font-semibold text-gray-900 flex-1">
          {title}
        </h3>
        {badge !== undefined && (
          <span className="text-xs font-medium bg-gray-100 text-gray-600 px-2.5 py-1 rounded-full">
            {badge}
          </span>
        )}
        {open ? (
          <IoChevronUpOutline className="w-4 h-4 text-gray-400" />
        ) : (
          <IoChevronDownOutline className="w-4 h-4 text-gray-400" />
        )}
      </button>
      {open && (
        <div className="px-5 pb-5 border-t border-gray-100">{children}</div>
      )}
    </div>
  );
}

/* ═══════════════════════════════════════════════════════════════════════════
   DATA TABLE COMPONENT
   ═══════════════════════════════════════════════════════════════════════════ */

function DataTable({
  headers,
  rows,
  maxRows = 100,
  mono = false,
}: {
  headers: string[];
  rows: (string | React.ReactNode)[][];
  maxRows?: number;
  mono?: boolean;
}) {
  const [showAll, setShowAll] = useState(false);
  const visible = showAll ? rows : rows.slice(0, maxRows);

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead>
          <tr className="bg-gray-50">
            {headers.map((h, i) => (
              <th
                key={i}
                className="text-left px-3 py-2.5 text-xs font-semibold text-gray-500 uppercase tracking-wider border-b border-gray-200"
              >
                {h}
              </th>
            ))}
          </tr>
        </thead>
        <tbody className="divide-y divide-gray-100">
          {visible.map((row, ri) => (
            <tr key={ri} className="hover:bg-gray-50/70 transition-colors">
              {row.map((cell, ci) => (
                <td
                  key={ci}
                  className={`px-3 py-2 text-gray-700 ${mono ? "font-mono text-xs" : ""} max-w-md truncate`}
                >
                  {cell}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
      {rows.length > maxRows && !showAll && (
        <button
          onClick={() => setShowAll(true)}
          className="mt-2 text-xs text-violet-600 hover:text-violet-700 font-medium"
        >
          Show all {rows.length} rows...
        </button>
      )}
    </div>
  );
}

/* ═══════════════════════════════════════════════════════════════════════════
   STAT PILL
   ═══════════════════════════════════════════════════════════════════════════ */

function Stat({
  label,
  value,
  icon,
}: {
  label: string;
  value: string | number;
  icon: React.ReactNode;
}) {
  return (
    <div className="bg-gray-50 rounded-lg p-3 flex items-start gap-3">
      <div className="text-gray-400 mt-0.5">{icon}</div>
      <div>
        <p className="text-xs text-gray-500">{label}</p>
        <p className="text-sm font-semibold text-gray-800">{value}</p>
      </div>
    </div>
  );
}

/* ═══════════════════════════════════════════════════════════════════════════
   FILE PATH RENDERING HELPER
   ═══════════════════════════════════════════════════════════════════════════ */

function FilePath({ path }: { path: string }) {
  // Highlight suspicious paths
  const isSuspicious =
    /\.(exe|bat|cmd|ps1|vbs|enc|bin|dat|dll)$/i.test(path) ||
    /hidden|payload|exfil|staging|svchost_update/i.test(path);
  return (
    <span
      className={`font-mono text-xs ${isSuspicious ? "text-red-600 font-medium" : "text-gray-600"}`}
      title={path}
    >
      {isSuspicious && "⚠ "}
      {path}
    </span>
  );
}

/* ═══════════════════════════════════════════════════════════════════════════
   SCREENSHOT GALLERY
   ═══════════════════════════════════════════════════════════════════════════ */

function ScreenshotGallery({
  analysisId,
  screenshots,
}: {
  analysisId: string;
  screenshots: string[];
}) {
  const [lightboxIdx, setLightboxIdx] = useState<number | null>(null);
  const scrollRef = useRef<HTMLDivElement>(null);
  const hoverTimerRef = useRef<ReturnType<typeof setInterval> | null>(null);

  // Keyboard navigation in lightbox
  useEffect(() => {
    if (lightboxIdx === null) return;
    const handler = (e: KeyboardEvent) => {
      if (e.key === "Escape") setLightboxIdx(null);
      if (e.key === "ArrowLeft" && lightboxIdx > 0)
        setLightboxIdx(lightboxIdx - 1);
      if (e.key === "ArrowRight" && lightboxIdx < screenshots.length - 1)
        setLightboxIdx(lightboxIdx + 1);
    };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [lightboxIdx, screenshots.length]);

  // Hover-to-advance: while hovering over the image, advance every 700ms
  const startHoverAdvance = useCallback(() => {
    if (hoverTimerRef.current) return;
    hoverTimerRef.current = setInterval(() => {
      setLightboxIdx((prev) => {
        if (prev === null) return null;
        return prev < screenshots.length - 1 ? prev + 1 : 0;
      });
    }, 700);
  }, [screenshots.length]);

  const stopHoverAdvance = useCallback(() => {
    if (hoverTimerRef.current) {
      clearInterval(hoverTimerRef.current);
      hoverTimerRef.current = null;
    }
  }, []);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (hoverTimerRef.current) clearInterval(hoverTimerRef.current);
    };
  }, []);

  const scrollLeft = () =>
    scrollRef.current?.scrollBy({ left: -300, behavior: "smooth" });
  const scrollRight = () =>
    scrollRef.current?.scrollBy({ left: 300, behavior: "smooth" });

  if (screenshots.length === 0) return null;

  return (
    <>
      {/* Scrollable thumbnail strip */}
      <div className="relative group">
        {/* Scroll arrows */}
        <button
          onClick={scrollLeft}
          className="absolute left-0 top-1/2 -translate-y-1/2 z-10 w-8 h-8 bg-white/90 border border-gray-200 shadow rounded-full flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity"
        >
          <IoChevronBack className="w-4 h-4 text-gray-600" />
        </button>
        <button
          onClick={scrollRight}
          className="absolute right-0 top-1/2 -translate-y-1/2 z-10 w-8 h-8 bg-white/90 border border-gray-200 shadow rounded-full flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity"
        >
          <IoChevronForward className="w-4 h-4 text-gray-600" />
        </button>

        <div
          ref={scrollRef}
          className="flex gap-3 overflow-x-auto py-3 px-1 scrollbar-thin scrollbar-thumb-gray-300 scrollbar-track-transparent"
          style={{ scrollbarWidth: "thin" }}
        >
          {screenshots.map((name, idx) => (
            <button
              key={name}
              onClick={() => setLightboxIdx(idx)}
              className="group/thumb relative flex-shrink-0 w-48 aspect-video rounded-lg overflow-hidden border-2 border-gray-200 hover:border-violet-400 transition-all hover:shadow-lg"
            >
              <img
                src={screenshotURL(analysisId, name)}
                alt={`Screenshot ${idx + 1}`}
                className="w-full h-full object-cover group-hover/thumb:scale-105 transition-transform"
                loading="lazy"
              />
              <div className="absolute inset-0 bg-gradient-to-t from-black/60 via-transparent to-transparent opacity-0 group-hover/thumb:opacity-100 transition-opacity" />
              <div className="absolute bottom-0 inset-x-0 p-2 opacity-0 group-hover/thumb:opacity-100 transition-opacity">
                <p className="text-[10px] text-white font-mono truncate">
                  {name}
                </p>
              </div>
              <div className="absolute top-1.5 right-1.5 w-6 h-6 bg-black/50 rounded-full flex items-center justify-center text-white text-[10px] font-bold">
                {idx + 1}
              </div>
            </button>
          ))}
        </div>
      </div>

      {/* Lightbox modal */}
      {lightboxIdx !== null && (
        <div
          className="fixed inset-0 z-50 bg-black/90 flex flex-col items-center justify-center"
          onClick={() => {
            setLightboxIdx(null);
            stopHoverAdvance();
          }}
        >
          {/* Top bar */}
          <div className="absolute top-0 inset-x-0 p-4 flex items-center justify-between z-10">
            <div className="text-white/70 text-sm font-mono">
              {screenshots[lightboxIdx]}
            </div>
            <div className="flex items-center gap-3">
              <span className="text-white/60 text-sm">
                {lightboxIdx + 1} / {screenshots.length}
              </span>
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  setLightboxIdx(null);
                  stopHoverAdvance();
                }}
                className="w-9 h-9 rounded-full bg-white/10 hover:bg-white/20 flex items-center justify-center transition-colors"
              >
                <IoCloseOutline className="w-5 h-5 text-white" />
              </button>
            </div>
          </div>

          {/* Main image — hover to advance */}
          <div
            className="relative max-w-6xl max-h-[80vh] mx-4 cursor-pointer"
            onClick={(e) => e.stopPropagation()}
            onMouseEnter={startHoverAdvance}
            onMouseLeave={stopHoverAdvance}
          >
            <img
              src={screenshotURL(analysisId, screenshots[lightboxIdx])}
              alt={screenshots[lightboxIdx]}
              className="max-w-full max-h-[80vh] rounded-lg shadow-2xl"
            />
            {/* Hover hint */}
            <div className="absolute bottom-3 inset-x-0 text-center pointer-events-none">
              <span className="bg-black/50 text-white/70 text-xs px-3 py-1 rounded-full">
                Hover to auto-advance • Click arrows or use ← → keys
              </span>
            </div>
          </div>

          {/* Navigation arrows */}
          {lightboxIdx > 0 && (
            <button
              onClick={(e) => {
                e.stopPropagation();
                stopHoverAdvance();
                setLightboxIdx(lightboxIdx - 1);
              }}
              className="absolute left-4 top-1/2 -translate-y-1/2 w-12 h-12 rounded-full bg-white/10 hover:bg-white/20 flex items-center justify-center transition-colors"
            >
              <IoChevronBack className="w-6 h-6 text-white" />
            </button>
          )}
          {lightboxIdx < screenshots.length - 1 && (
            <button
              onClick={(e) => {
                e.stopPropagation();
                stopHoverAdvance();
                setLightboxIdx(lightboxIdx + 1);
              }}
              className="absolute right-4 top-1/2 -translate-y-1/2 w-12 h-12 rounded-full bg-white/10 hover:bg-white/20 flex items-center justify-center transition-colors"
            >
              <IoChevronForward className="w-6 h-6 text-white" />
            </button>
          )}

          {/* Bottom thumbnail strip */}
          <div className="absolute bottom-0 inset-x-0 bg-gradient-to-t from-black/80 to-transparent pt-8 pb-4 px-4">
            <div className="flex gap-2 overflow-x-auto justify-center max-w-4xl mx-auto">
              {screenshots.map((name, idx) => (
                <button
                  key={name}
                  onClick={(e) => {
                    e.stopPropagation();
                    stopHoverAdvance();
                    setLightboxIdx(idx);
                  }}
                  className={`flex-shrink-0 w-16 h-10 rounded overflow-hidden border-2 transition-all ${
                    idx === lightboxIdx
                      ? "border-violet-400 scale-110 shadow-lg"
                      : "border-white/20 opacity-60 hover:opacity-100"
                  }`}
                >
                  <img
                    src={screenshotURL(analysisId, name)}
                    alt=""
                    className="w-full h-full object-cover"
                    loading="lazy"
                  />
                </button>
              ))}
            </div>
          </div>
        </div>
      )}
    </>
  );
}

/* ═══════════════════════════════════════════════════════════════════════════
   SYSMON SECTION
   ═══════════════════════════════════════════════════════════════════════════ */

function SysmonSection({ data }: { data: SysmonData }) {
  return (
    <div className="space-y-5 pt-4">
      {/* Stats row */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        <Stat
          label="Total Events"
          value={data.total_events}
          icon={<IoLayersOutline className="w-4 h-4" />}
        />
        <Stat
          label="Sample Events"
          value={data.sample_events}
          icon={<IoBugOutline className="w-4 h-4" />}
        />
        <Stat
          label="Sample PIDs"
          value={data.sample_pids?.join(", ") || "—"}
          icon={<IoTerminalOutline className="w-4 h-4" />}
        />
        <Stat
          label="DLLs Loaded"
          value={data.dlls_loaded?.length || 0}
          icon={<IoHardwareChipOutline className="w-4 h-4" />}
        />
      </div>

      {/* Process creation */}
      {data.processes_created?.length > 0 && (
        <div>
          <h4 className="text-sm font-semibold text-gray-700 mb-2 flex items-center gap-2">
            <IoTerminalOutline className="w-4 h-4 text-violet-500" />
            Process Creation Events
          </h4>
          <DataTable
            headers={["Time", "Image", "PID", "Parent", "User", "Command Line"]}
            rows={data.processes_created.map((p) => [
              <span key="t" className="text-xs text-gray-500 whitespace-nowrap">
                {p.time ? new Date(p.time).toLocaleTimeString() : "—"}
              </span>,
              <FilePath key="i" path={p.image} />,
              <span
                key="p"
                className="font-mono text-xs font-semibold text-violet-700"
              >
                {p.pid}
              </span>,
              <FilePath key="pp" path={p.parent} />,
              <span key="u" className="text-xs">
                {p.user}
              </span>,
              <span
                key="c"
                className="font-mono text-xs text-gray-500 truncate max-w-xs block"
              >
                {p.cmd}
              </span>,
            ])}
            mono
          />
        </div>
      )}

      {/* Network connections from Sysmon */}
      {data.network_connections?.length > 0 && (
        <div>
          <h4 className="text-sm font-semibold text-gray-700 mb-2 flex items-center gap-2">
            <IoGlobeOutline className="w-4 h-4 text-blue-500" />
            Network Connections (Sysmon)
          </h4>
          <DataTable
            headers={["Image", "Protocol", "Source", "Destination", "Hostname"]}
            rows={data.network_connections.map((c) => [
              <FilePath key="i" path={c.image} />,
              c.proto,
              <span key="s" className="font-mono text-xs">
                {c.src}
              </span>,
              <span
                key="d"
                className="font-mono text-xs font-semibold text-red-600"
              >
                {c.dst}
              </span>,
              c.dst_host || "—",
            ])}
            mono
          />
        </div>
      )}

      {/* DNS queries */}
      {data.dns_queries?.length > 0 && (
        <div>
          <h4 className="text-sm font-semibold text-gray-700 mb-2 flex items-center gap-2">
            <IoGlobeOutline className="w-4 h-4 text-sky-500" />
            DNS Queries
          </h4>
          <div className="flex flex-wrap gap-2">
            {data.dns_queries.map((q) => (
              <span
                key={q}
                className="px-2.5 py-1 bg-sky-50 text-sky-700 border border-sky-200 rounded-md text-xs font-mono"
              >
                {q}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Files created */}
      {data.files_created?.length > 0 && (
        <div>
          <h4 className="text-sm font-semibold text-gray-700 mb-2 flex items-center gap-2">
            <IoFolderOpenOutline className="w-4 h-4 text-amber-500" />
            Files Created ({data.files_created.length})
          </h4>
          <div className="space-y-1 max-h-60 overflow-y-auto bg-gray-50 rounded-lg p-3">
            {data.files_created.map((f, i) => (
              <div key={i} className="flex items-center gap-2 py-0.5">
                <IoDocumentTextOutline className="w-3.5 h-3.5 text-gray-400 shrink-0" />
                <FilePath path={f} />
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Registry events */}
      {data.registry_events?.length > 0 && (
        <div>
          <h4 className="text-sm font-semibold text-gray-700 mb-2 flex items-center gap-2">
            <IoKeyOutline className="w-4 h-4 text-rose-500" />
            Registry Events ({data.registry_events.length})
          </h4>
          <DataTable
            headers={["Type", "Key", "Details"]}
            rows={data.registry_events.map((r) => [
              <span
                key="t"
                className={`text-xs font-medium px-2 py-0.5 rounded ${
                  r.type.includes("Set")
                    ? "bg-amber-50 text-amber-700"
                    : r.type.includes("Delete")
                      ? "bg-red-50 text-red-700"
                      : "bg-gray-100 text-gray-600"
                }`}
              >
                {r.type}
              </span>,
              <span
                key="k"
                className="font-mono text-xs text-gray-600 truncate max-w-lg block"
                title={r.key}
              >
                {r.key}
              </span>,
              <span key="d" className="text-xs text-gray-500">
                {r.details || "—"}
              </span>,
            ])}
            mono
          />
        </div>
      )}

      {/* DLLs loaded */}
      {data.dlls_loaded?.length > 0 && (
        <div>
          <h4 className="text-sm font-semibold text-gray-700 mb-2 flex items-center gap-2">
            <IoHardwareChipOutline className="w-4 h-4 text-slate-500" />
            DLLs Loaded ({data.dlls_loaded.length})
          </h4>
          <div className="flex flex-wrap gap-1.5 max-h-40 overflow-y-auto">
            {data.dlls_loaded.map((d, i) => {
              const name = d.split("\\").pop() || d;
              const isCrypto = /crypt|rsa|aes|bcrypt/i.test(name);
              const isNet = /ws2|winsock|winhttp|dnsapi|iphlp/i.test(name);
              const color = isCrypto
                ? "bg-red-50 text-red-600 border-red-200"
                : isNet
                  ? "bg-blue-50 text-blue-600 border-blue-200"
                  : "bg-gray-50 text-gray-600 border-gray-200";
              return (
                <span
                  key={i}
                  className={`px-2 py-0.5 rounded border text-[11px] font-mono ${color}`}
                  title={d}
                >
                  {name}
                </span>
              );
            })}
          </div>
        </div>
      )}

      {/* Empty state */}
      {data.sample_events === 0 && (
        <div className="text-center py-6 text-gray-400 text-sm">
          No sample-related events detected by Sysmon.
        </div>
      )}
    </div>
  );
}

/* ═══════════════════════════════════════════════════════════════════════════
   PROCMON SECTION
   ═══════════════════════════════════════════════════════════════════════════ */

function ProcmonSection({ data }: { data: ProcmonData }) {
  const fileNotable = data.file_activity?.notable || {};
  const regNotable = data.registry_activity?.notable || {};
  const fileOps = data.file_activity?.all_ops || {};
  const regOps = data.registry_activity?.all_ops || {};

  return (
    <div className="space-y-5 pt-4">
      {/* Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        <Stat
          label="Total Rows"
          value={data.total_rows?.toLocaleString() || "0"}
          icon={<IoLayersOutline className="w-4 h-4" />}
        />
        <Stat
          label="Sample Events"
          value={data.sample_events?.toLocaleString() || "0"}
          icon={<IoBugOutline className="w-4 h-4" />}
        />
        <Stat
          label="File Operations"
          value={Object.values(fileOps).reduce((a, b) => a + b, 0)}
          icon={<IoFolderOpenOutline className="w-4 h-4" />}
        />
        <Stat
          label="Registry Operations"
          value={Object.values(regOps).reduce((a, b) => a + b, 0)}
          icon={<IoKeyOutline className="w-4 h-4" />}
        />
      </div>

      {/* File operation breakdown */}
      {Object.keys(fileOps).length > 0 && (
        <div>
          <h4 className="text-sm font-semibold text-gray-700 mb-2">
            File Operation Breakdown
          </h4>
          <div className="flex flex-wrap gap-2">
            {Object.entries(fileOps)
              .sort(([, a], [, b]) => b - a)
              .map(([op, count]) => (
                <span
                  key={op}
                  className="px-2.5 py-1 bg-amber-50 text-amber-700 border border-amber-200 rounded-md text-xs"
                >
                  {op}: <strong>{count}</strong>
                </span>
              ))}
          </div>
        </div>
      )}

      {/* Notable file activity */}
      {Object.keys(fileNotable).length > 0 && (
        <div>
          <h4 className="text-sm font-semibold text-gray-700 mb-2 flex items-center gap-2">
            <IoAlertCircleOutline className="w-4 h-4 text-red-500" />
            Notable File Activity (Write / Create / Delete)
          </h4>
          {Object.entries(fileNotable).map(([op, paths]) => (
            <div key={op} className="mb-3">
              <p className="text-xs font-semibold text-gray-500 uppercase mb-1">
                {op}
              </p>
              <div className="space-y-0.5 bg-gray-50 rounded-lg p-3 max-h-48 overflow-y-auto">
                {paths.map((p, i) => (
                  <div key={i} className="flex items-center gap-2">
                    <IoDocumentTextOutline className="w-3 h-3 text-gray-400 shrink-0" />
                    <FilePath path={p} />
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Registry operation breakdown */}
      {Object.keys(regOps).length > 0 && (
        <div>
          <h4 className="text-sm font-semibold text-gray-700 mb-2">
            Registry Operation Breakdown
          </h4>
          <div className="flex flex-wrap gap-2">
            {Object.entries(regOps)
              .sort(([, a], [, b]) => b - a)
              .map(([op, count]) => (
                <span
                  key={op}
                  className="px-2.5 py-1 bg-rose-50 text-rose-700 border border-rose-200 rounded-md text-xs"
                >
                  {op}: <strong>{count}</strong>
                </span>
              ))}
          </div>
        </div>
      )}

      {/* Notable registry activity */}
      {Object.keys(regNotable).length > 0 && (
        <div>
          <h4 className="text-sm font-semibold text-gray-700 mb-2 flex items-center gap-2">
            <IoAlertCircleOutline className="w-4 h-4 text-red-500" />
            Notable Registry Activity (Set / Create / Delete)
          </h4>
          {Object.entries(regNotable).map(([op, paths]) => (
            <div key={op} className="mb-3">
              <p className="text-xs font-semibold text-gray-500 uppercase mb-1">
                {op}
              </p>
              <div className="space-y-0.5 bg-gray-50 rounded-lg p-3 max-h-48 overflow-y-auto">
                {paths.map((p, i) => (
                  <div key={i} className="flex items-center gap-2">
                    <IoKeyOutline className="w-3 h-3 text-gray-400 shrink-0" />
                    <span
                      className="font-mono text-xs text-gray-600 truncate"
                      title={p}
                    >
                      {p}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Network activity */}
      {data.network_activity?.length > 0 && (
        <div>
          <h4 className="text-sm font-semibold text-gray-700 mb-2 flex items-center gap-2">
            <IoGlobeOutline className="w-4 h-4 text-blue-500" />
            Network Activity ({data.network_activity.length})
          </h4>
          <DataTable
            headers={["Operation", "Endpoint", "Result"]}
            rows={data.network_activity.map((n) => [
              <span key="o" className="font-medium">
                {n.op}
              </span>,
              <span key="p" className="font-mono text-xs">
                {n.path}
              </span>,
              <span
                key="r"
                className={`text-xs font-medium ${n.result === "SUCCESS" ? "text-green-600" : "text-red-600"}`}
              >
                {n.result}
              </span>,
            ])}
            mono
          />
        </div>
      )}

      {/* Process activity */}
      {data.process_activity?.length > 0 && (
        <div>
          <h4 className="text-sm font-semibold text-gray-700 mb-2 flex items-center gap-2">
            <IoTerminalOutline className="w-4 h-4 text-slate-500" />
            Process / Thread Activity ({data.process_activity.length})
          </h4>
          <DataTable
            headers={["Operation", "Path", "Detail"]}
            rows={data.process_activity.map((p) => [
              <span key="o" className="font-medium">
                {p.op}
              </span>,
              <FilePath key="p" path={p.path} />,
              <span
                key="d"
                className="text-xs text-gray-500 truncate max-w-xs block"
              >
                {p.detail}
              </span>,
            ])}
            mono
          />
        </div>
      )}
    </div>
  );
}

/* ═══════════════════════════════════════════════════════════════════════════
   NETWORK SECTION
   ═══════════════════════════════════════════════════════════════════════════ */

function NetworkSection({ data }: { data: NetworkData }) {
  return (
    <div className="space-y-5 pt-4">
      {/* TCP conversations */}
      {data.tcp_conversations && (
        <div>
          <h4 className="text-sm font-semibold text-gray-700 mb-2">
            TCP Conversations
          </h4>
          <pre className="bg-gray-900 text-green-400 rounded-lg p-4 text-xs overflow-x-auto max-h-60 overflow-y-auto font-mono">
            {data.tcp_conversations}
          </pre>
        </div>
      )}

      {/* DNS queries */}
      {data.dns_queries && data.dns_queries.length > 0 && (
        <div>
          <h4 className="text-sm font-semibold text-gray-700 mb-2">
            DNS Queries ({data.dns_queries.length})
          </h4>
          <div className="flex flex-wrap gap-2">
            {data.dns_queries.map((q) => (
              <span
                key={q}
                className="px-2.5 py-1 bg-sky-50 text-sky-700 border border-sky-200 rounded-md text-xs font-mono"
              >
                {q}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* HTTP requests */}
      {data.http_requests && data.http_requests.length > 0 && (
        <div>
          <h4 className="text-sm font-semibold text-gray-700 mb-2">
            HTTP Requests ({data.http_requests.length})
          </h4>
          <DataTable
            headers={["Method", "Host", "URI"]}
            rows={data.http_requests.map((r) => [
              <span
                key="m"
                className={`px-2 py-0.5 rounded text-xs font-bold ${
                  r.method === "GET"
                    ? "bg-green-100 text-green-700"
                    : r.method === "POST"
                      ? "bg-blue-100 text-blue-700"
                      : "bg-gray-100 text-gray-700"
                }`}
              >
                {r.method}
              </span>,
              <span key="h" className="font-mono text-xs">
                {r.host}
              </span>,
              <span key="u" className="font-mono text-xs text-gray-600">
                {r.uri}
              </span>,
            ])}
          />
        </div>
      )}

      {/* Empty state */}
      {!data.tcp_conversations &&
        (!data.dns_queries || data.dns_queries.length === 0) &&
        (!data.http_requests || data.http_requests.length === 0) && (
          <div className="text-center py-6 text-gray-400 text-sm">
            No significant network traffic captured by tshark.
            <br />
            <span className="text-xs">
              The VM uses host-only networking — all connection attempts are
              logged as IOCs.
            </span>
          </div>
        )}
    </div>
  );
}

/* ═══════════════════════════════════════════════════════════════════════════
   HANDLE SECTION
   ═══════════════════════════════════════════════════════════════════════════ */

function HandleSection({ data }: { data: string }) {
  const lines = data.split("\n").filter((l) => l.trim());
  return (
    <div className="pt-4">
      <pre className="bg-gray-900 text-green-400 rounded-lg p-4 text-xs overflow-x-auto max-h-80 overflow-y-auto font-mono leading-relaxed">
        {lines.length > 200
          ? lines.slice(0, 200).join("\n") + "\n\n... truncated ..."
          : data}
      </pre>
      <p className="text-xs text-gray-400 mt-2">{lines.length} lines</p>
    </div>
  );
}

/* ═══════════════════════════════════════════════════════════════════════════
   TCPVCON SECTION
   ═══════════════════════════════════════════════════════════════════════════ */

function TcpvconSection({ data }: { data: TcpvconRow[] }) {
  if (data.length === 0) {
    return (
      <div className="pt-4 text-center py-6 text-gray-400 text-sm">
        No active connections captured.
      </div>
    );
  }
  const headers = Object.keys(data[0]);
  return (
    <div className="pt-4">
      <DataTable
        headers={headers}
        rows={data.map((row) =>
          headers.map((h) => (
            <span key={h} className="font-mono text-xs">
              {row[h]}
            </span>
          )),
        )}
        mono
      />
    </div>
  );
}

/* ═══════════════════════════════════════════════════════════════════════════
   COLLECTOR STATUS BADGES
   ═══════════════════════════════════════════════════════════════════════════ */

function CollectorBadges({
  metadata,
}: {
  metadata: { collectors: { collector: string; status: string }[] };
}) {
  return (
    <div className="flex flex-wrap gap-2">
      {metadata.collectors.map((c) => {
        const color =
          c.status === "ok"
            ? "bg-green-50 text-green-700 border-green-200"
            : c.status === "no_data"
              ? "bg-amber-50 text-amber-700 border-amber-200"
              : c.status === "unavailable"
                ? "bg-gray-100 text-gray-500 border-gray-200"
                : "bg-red-50 text-red-700 border-red-200";
        const icon =
          c.status === "ok"
            ? "✅"
            : c.status === "no_data"
              ? "⚠️"
              : c.status === "unavailable"
                ? "⬜"
                : "❌";
        return (
          <span
            key={c.collector}
            className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg border text-xs font-medium ${color}`}
          >
            <span>{icon}</span>
            {c.collector}
          </span>
        );
      })}
    </div>
  );
}

/* ═══════════════════════════════════════════════════════════════════════════
   MAIN REPORTS PAGE
   ═══════════════════════════════════════════════════════════════════════════ */

export default function ReportsPage() {
  const [reports, setReports] = useState<AnalysisResult[]>([]);
  const [selected, setSelected] = useState<AnalysisResult | null>(null);
  const [reportData, setReportData] = useState<ReportData | null>(null);
  const [activeTab, setActiveTab] = useState<"report" | "ai">("report");
  const [loading, setLoading] = useState(true);
  const [detailLoading, setDetailLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchData = async () => {
    setLoading(true);
    setError(null);
    try {
      const reportsResp = await listReports();
      let allReports: AnalysisResult[] = [];
      if (reportsResp.status === "ok" && reportsResp.data) {
        allReports =
          (reportsResp.data as { reports: AnalysisResult[] }).reports || [];
      }

      // Also check current analysis
      const statusResp = await getAnalysisStatus();
      if (
        statusResp.status === "ok" &&
        statusResp.data &&
        "analysis_id" in statusResp.data
      ) {
        const current = statusResp.data as AnalysisResult;
        if (!allReports.find((r) => r.analysis_id === current.analysis_id)) {
          allReports.unshift(current);
        }
      }

      setReports(allReports);
      if (allReports.length > 0 && !selected) {
        await selectReport(allReports[0]);
      }
    } catch {
      setError(
        "Cannot connect to IsoLens gateway. Is it running on port 6969?",
      );
    } finally {
      setLoading(false);
    }
  };

  const selectReport = async (report: AnalysisResult) => {
    setSelected(report);
    setReportData(null);
    setDetailLoading(true);
    setActiveTab("report");
    try {
      const resp = await getReportData(report.analysis_id);
      if (resp.status === "ok" && resp.data) {
        setReportData(resp.data as ReportData);
      }
    } catch {
      // Could not load report data
    } finally {
      setDetailLoading(false);
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

  const rd = reportData; // shorthand

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900">Analysis Reports</h1>
        <button
          onClick={fetchData}
          className="inline-flex items-center gap-2 text-sm text-gray-600 hover:text-violet-600 transition-colors"
        >
          <IoRefreshOutline className="w-4 h-4" />
          Refresh
        </button>
      </div>

      {/* Loading */}
      {loading && (
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-12 text-center">
          <div className="animate-spin w-8 h-8 border-4 border-violet-200 border-t-violet-500 rounded-full mx-auto mb-3" />
          <p className="text-sm text-gray-500">Loading reports...</p>
        </div>
      )}

      {/* Error */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-xl p-4 flex items-center gap-3">
          <IoAlertCircleOutline className="w-5 h-5 text-red-500 shrink-0" />
          <p className="text-sm text-red-700">{error}</p>
        </div>
      )}

      {/* Empty */}
      {!loading && !error && reports.length === 0 && (
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-12 text-center">
          <IoDocumentTextOutline className="w-12 h-12 text-gray-300 mx-auto mb-3" />
          <p className="text-gray-500">No analysis reports yet.</p>
          <p className="text-sm text-gray-400 mt-1">
            Submit a sample from the{" "}
            <a href="/scan" className="text-violet-600 hover:text-violet-700">
              Scan
            </a>{" "}
            page to generate a report.
          </p>
        </div>
      )}

      {/* Main layout */}
      {!loading && reports.length > 0 && (
        <div className="grid grid-cols-1 lg:grid-cols-5 gap-6">
          {/* ── Report list sidebar ── */}
          <div className="lg:col-span-1 space-y-2">
            <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-3">
              Analyses ({reports.length})
            </h3>
            <div className="space-y-1.5 max-h-[calc(100vh-200px)] overflow-y-auto">
              {reports.map((report) => (
                <button
                  key={report.analysis_id}
                  onClick={() => selectReport(report)}
                  className={`w-full text-left p-3 rounded-lg border transition-all ${
                    selected?.analysis_id === report.analysis_id
                      ? "border-violet-300 bg-violet-50 shadow-sm"
                      : "border-gray-200 bg-white hover:bg-gray-50"
                  }`}
                >
                  <p className="text-sm font-medium text-gray-800 truncate">
                    {report.sample_name || "Unknown"}
                  </p>
                  <div className="flex items-center gap-2 mt-1">
                    <span
                      className={`inline-block px-2 py-0.5 rounded text-xs font-medium border ${statusColor(report.status)}`}
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
          </div>

          {/* ── Detail panel ── */}
          <div className="lg:col-span-4 space-y-4">
            {selected ? (
              <>
                {/* Tab switcher */}
                <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
                  <div className="flex border-b border-gray-200">
                    <button
                      onClick={() => setActiveTab("report")}
                      className={`flex-1 px-6 py-3.5 text-sm font-semibold transition-colors flex items-center justify-center gap-2 ${
                        activeTab === "report"
                          ? "text-violet-700 border-b-2 border-violet-500 bg-violet-50/50"
                          : "text-gray-500 hover:text-gray-700 hover:bg-gray-50"
                      }`}
                    >
                      <IoDocumentTextOutline className="w-4 h-4" />
                      Report
                    </button>
                    <button
                      onClick={() => setActiveTab("ai")}
                      className={`flex-1 px-6 py-3.5 text-sm font-semibold transition-colors flex items-center justify-center gap-2 ${
                        activeTab === "ai"
                          ? "text-violet-700 border-b-2 border-violet-500 bg-violet-50/50"
                          : "text-gray-500 hover:text-gray-700 hover:bg-gray-50"
                      }`}
                    >
                      <IoSparklesOutline className="w-4 h-4" />
                      AI Summary
                      <span className="text-[10px] font-normal bg-amber-100 text-amber-700 px-1.5 py-0.5 rounded-full">
                        Coming Soon
                      </span>
                    </button>
                  </div>

                  {/* ═══ REPORT TAB ═══ */}
                  {activeTab === "report" && (
                    <div className="p-6">
                      {detailLoading ? (
                        <div className="text-center py-12">
                          <div className="animate-spin w-8 h-8 border-4 border-violet-200 border-t-violet-500 rounded-full mx-auto mb-3" />
                          <p className="text-sm text-gray-500">
                            Loading report data...
                          </p>
                        </div>
                      ) : (
                        <div className="space-y-2">
                          {/* ── Overview header ── */}
                          <div className="flex items-start justify-between mb-4">
                            <div>
                              <h2 className="text-xl font-bold text-gray-900">
                                {selected.sample_name}
                              </h2>
                              <p className="text-xs text-gray-400 mt-0.5 font-mono">
                                {selected.analysis_id}
                              </p>
                            </div>
                            <span
                              className={`inline-block px-3 py-1 rounded-full text-xs font-medium border ${statusColor(selected.status)}`}
                            >
                              {selected.status === "complete" && (
                                <IoCheckmarkCircleOutline className="w-3.5 h-3.5 inline mr-1" />
                              )}
                              {selected.status}
                            </span>
                          </div>

                          {/* Stats grid */}
                          <div className="grid grid-cols-2 md:grid-cols-5 gap-3 mb-6">
                            <Stat
                              label="Timeout"
                              value={`${selected.timeout}s`}
                              icon={<IoTimeOutline className="w-4 h-4" />}
                            />
                            <Stat
                              label="Sysmon Events"
                              value={
                                rd?.sysmon?.sample_events ??
                                selected.sysmon_events ??
                                0
                              }
                              icon={<IoBugOutline className="w-4 h-4" />}
                            />
                            <Stat
                              label="Procmon Rows"
                              value={
                                rd?.procmon?.sample_events?.toLocaleString() ??
                                "—"
                              }
                              icon={<IoEyeOutline className="w-4 h-4" />}
                            />
                            <Stat
                              label="Files Collected"
                              value={selected.files_collected?.length || 0}
                              icon={<IoFolderOpenOutline className="w-4 h-4" />}
                            />
                            <Stat
                              label="Screenshots"
                              value={rd?.screenshots?.length ?? 0}
                              icon={<IoImageOutline className="w-4 h-4" />}
                            />
                          </div>

                          {/* Timestamps */}
                          <div className="flex flex-wrap gap-4 text-xs text-gray-500 mb-4 pb-4 border-b border-gray-100">
                            {selected.started_at && (
                              <span>
                                🕐 Started:{" "}
                                {new Date(selected.started_at).toLocaleString()}
                              </span>
                            )}
                            {selected.completed_at && (
                              <span>
                                ✅ Completed:{" "}
                                {new Date(
                                  selected.completed_at,
                                ).toLocaleString()}
                              </span>
                            )}
                            {rd?.sysmon?.sample_process && (
                              <span>
                                🎯 Process:{" "}
                                <code className="bg-gray-100 px-1 rounded">
                                  {rd.sysmon.sample_process}
                                </code>
                              </span>
                            )}
                          </div>

                          {selected.error && (
                            <div className="bg-red-50 border border-red-200 rounded-lg p-3 mb-4">
                              <p className="text-sm text-red-700">
                                ❌ {selected.error}
                              </p>
                            </div>
                          )}
                        </div>
                      )}
                    </div>
                  )}

                  {/* ═══ AI TAB ═══ */}
                  {activeTab === "ai" && (
                    <div className="p-6">
                      <div className="text-center py-16">
                        <div className="w-20 h-20 mx-auto mb-6 bg-gradient-to-br from-violet-100 to-purple-100 rounded-2xl flex items-center justify-center">
                          <IoSparklesOutline className="w-10 h-10 text-violet-500" />
                        </div>
                        <h3 className="text-xl font-bold text-gray-900 mb-2">
                          AI-Powered Threat Intelligence
                        </h3>
                        <p className="text-gray-500 max-w-md mx-auto mb-4">
                          Automatic threat classification, MITRE ATT&CK mapping,
                          risk scoring, natural language summaries, and IOC
                          extraction will be generated here by the AI engine.
                        </p>
                        <span className="inline-flex items-center gap-2 px-4 py-2 bg-amber-50 text-amber-700 border border-amber-200 rounded-full text-sm font-medium">
                          <IoAlertCircleOutline className="w-4 h-4" />
                          Coming Soon
                        </span>
                        <div className="mt-8 grid grid-cols-2 md:grid-cols-4 gap-3 max-w-2xl mx-auto opacity-50">
                          {[
                            { label: "Threat Classification", icon: "🎯" },
                            { label: "MITRE ATT&CK Map", icon: "🗺️" },
                            { label: "Risk Score", icon: "📊" },
                            { label: "IOC Extraction", icon: "🔍" },
                          ].map((item) => (
                            <div
                              key={item.label}
                              className="bg-white border border-gray-200 rounded-lg p-3 text-center"
                            >
                              <span className="text-2xl">{item.icon}</span>
                              <p className="text-xs text-gray-500 mt-1">
                                {item.label}
                              </p>
                            </div>
                          ))}
                        </div>
                      </div>
                    </div>
                  )}
                </div>

                {/* ═══════ REPORT TAB CONTENT (outside the card) ═══════ */}
                {activeTab === "report" && !detailLoading && rd && (
                  <div className="space-y-4">
                    {/* Collector Status */}
                    {rd.metadata?.collectors && (
                      <Section
                        title="Collector Status"
                        icon={<IoServerOutline className="w-4 h-4" />}
                        badge={rd.metadata.collectors.length}
                        accentColor="slate"
                        defaultOpen={false}
                      >
                        <div className="pt-4">
                          <CollectorBadges metadata={rd.metadata} />
                        </div>
                      </Section>
                    )}

                    {/* Screenshots */}
                    {rd.screenshots && rd.screenshots.length > 0 && (
                      <Section
                        title={`Screenshots (${rd.screenshots.length})`}
                        icon={<IoImageOutline className="w-4 h-4" />}
                        badge={rd.screenshots.length}
                        accentColor="violet"
                      >
                        <div className="pt-2">
                          <p className="text-xs text-gray-400 mb-2">
                            Scroll horizontally to browse. Click to open. Hover
                            over the opened image to auto-advance.
                          </p>
                          <ScreenshotGallery
                            analysisId={selected.analysis_id}
                            screenshots={rd.screenshots}
                          />
                        </div>
                      </Section>
                    )}

                    {/* Sysmon */}
                    {rd.sysmon && (
                      <Section
                        title="Sysmon — System Monitor Events"
                        icon={<IoShieldCheckmarkOutline className="w-4 h-4" />}
                        badge={`${rd.sysmon.sample_events} events`}
                        accentColor="violet"
                      >
                        <SysmonSection data={rd.sysmon} />
                      </Section>
                    )}

                    {/* Procmon */}
                    {rd.procmon && (
                      <Section
                        title="Procmon — Process Monitor Activity"
                        icon={<IoEyeOutline className="w-4 h-4" />}
                        badge={`${rd.procmon.sample_events?.toLocaleString()} events`}
                        accentColor="amber"
                      >
                        <ProcmonSection data={rd.procmon} />
                      </Section>
                    )}

                    {/* Network */}
                    {rd.network && (
                      <Section
                        title="Network — Packet Capture (tshark)"
                        icon={<IoGitNetworkOutline className="w-4 h-4" />}
                        accentColor="blue"
                      >
                        <NetworkSection data={rd.network} />
                      </Section>
                    )}

                    {/* Handle */}
                    {rd.handle && (
                      <Section
                        title="Handle — Open File & Registry Handles"
                        icon={<IoKeyOutline className="w-4 h-4" />}
                        accentColor="rose"
                        defaultOpen={false}
                      >
                        <HandleSection data={rd.handle} />
                      </Section>
                    )}

                    {/* Tcpvcon */}
                    {rd.tcpvcon && rd.tcpvcon.length > 0 && (
                      <Section
                        title="TCP/UDP Connections (tcpvcon)"
                        icon={<IoGlobeOutline className="w-4 h-4" />}
                        badge={`${rd.tcpvcon.length} connections`}
                        accentColor="sky"
                        defaultOpen={false}
                      >
                        <TcpvconSection data={rd.tcpvcon} />
                      </Section>
                    )}

                    {/* Collected files listing */}
                    {selected.files_collected &&
                      selected.files_collected.length > 0 && (
                        <Section
                          title="All Collected Files"
                          icon={<IoFolderOpenOutline className="w-4 h-4" />}
                          badge={selected.files_collected.length}
                          accentColor="emerald"
                          defaultOpen={false}
                        >
                          <div className="pt-4 space-y-1 max-h-60 overflow-y-auto">
                            {selected.files_collected.map((file, idx) => (
                              <div
                                key={idx}
                                className="flex items-center gap-2 px-3 py-1.5 rounded-md hover:bg-gray-50 transition-colors"
                              >
                                <IoDocumentTextOutline className="w-3.5 h-3.5 text-gray-400 shrink-0" />
                                <span className="text-gray-700 font-mono text-xs truncate">
                                  {file}
                                </span>
                              </div>
                            ))}
                          </div>
                        </Section>
                      )}

                    {/* No data state */}
                    {!rd.sysmon &&
                      !rd.procmon &&
                      !rd.network &&
                      !rd.handle &&
                      !rd.tcpvcon && (
                        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-8 text-center">
                          <IoDocumentTextOutline className="w-10 h-10 text-gray-300 mx-auto mb-3" />
                          <p className="text-gray-500">
                            No detailed collector data available for this
                            analysis.
                          </p>
                          <p className="text-xs text-gray-400 mt-1">
                            This could mean the analysis is still running, or
                            the report directory has no parsed outputs.
                          </p>
                        </div>
                      )}
                  </div>
                )}
              </>
            ) : (
              <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-12 text-center">
                <p className="text-gray-500">Select a report to view details</p>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
