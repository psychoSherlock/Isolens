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
  IoTrashOutline,
  IoWarningOutline,
  IoInformationCircleOutline,
  IoSwapHorizontalOutline,
} from "react-icons/io5";
import {
  getAnalysisStatus,
  listReports,
  clearAllReports,
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
   COLLAPSIBLE PANEL
   ═══════════════════════════════════════════════════════════════════════════ */

function Panel({
  title,
  icon,
  count,
  defaultOpen = true,
  color = "violet",
  children,
}: {
  title: string;
  icon: React.ReactNode;
  count?: string | number;
  defaultOpen?: boolean;
  color?: string;
  children: React.ReactNode;
}) {
  const [open, setOpen] = useState(defaultOpen);
  const gradients: Record<string, string> = {
    violet: "from-violet-500 to-purple-600",
    blue: "from-blue-500 to-cyan-600",
    amber: "from-amber-500 to-orange-600",
    emerald: "from-emerald-500 to-teal-600",
    rose: "from-rose-500 to-pink-600",
    sky: "from-sky-500 to-blue-600",
    slate: "from-slate-500 to-gray-600",
    red: "from-red-500 to-rose-600",
  };
  const grad = gradients[color] || gradients.violet;

  return (
    <div className="bg-white rounded-2xl shadow-sm border border-gray-100 overflow-hidden">
      <button
        onClick={() => setOpen(!open)}
        className="w-full flex items-center gap-3 px-5 py-4 text-left hover:bg-gray-50/60 transition-colors group"
      >
        <div
          className={`w-9 h-9 rounded-xl bg-gradient-to-br ${grad} flex items-center justify-center text-white shadow-sm`}
        >
          {icon}
        </div>
        <span className="text-sm font-semibold text-gray-900 flex-1">
          {title}
        </span>
        {count !== undefined && (
          <span className="text-xs font-medium bg-gray-100 text-gray-600 px-2.5 py-1 rounded-full">
            {count}
          </span>
        )}
        <span className="text-gray-400 group-hover:text-gray-600 transition-colors">
          {open ? (
            <IoChevronUpOutline className="w-4 h-4" />
          ) : (
            <IoChevronDownOutline className="w-4 h-4" />
          )}
        </span>
      </button>
      {open && (
        <div className="px-5 pb-5 border-t border-gray-50">{children}</div>
      )}
    </div>
  );
}

/* ═══════════════════════════════════════════════════════════════════════════
   EMPTY STATE
   ═══════════════════════════════════════════════════════════════════════════ */

function NoData({ label, hint }: { label: string; hint?: string }) {
  return (
    <div className="flex items-center gap-3 py-6 px-4 rounded-xl bg-gray-50 border border-dashed border-gray-200 mt-3">
      <IoInformationCircleOutline className="w-5 h-5 text-gray-400 shrink-0" />
      <div>
        <p className="text-sm text-gray-500 font-medium">{label}</p>
        {hint && <p className="text-xs text-gray-400 mt-0.5">{hint}</p>}
      </div>
    </div>
  );
}

/* ═══════════════════════════════════════════════════════════════════════════
   MINI STAT
   ═══════════════════════════════════════════════════════════════════════════ */

function MiniStat({
  label,
  value,
  icon,
  accent = "violet",
}: {
  label: string;
  value: string | number;
  icon: React.ReactNode;
  accent?: string;
}) {
  const accents: Record<string, string> = {
    violet: "bg-violet-50 text-violet-600",
    blue: "bg-blue-50 text-blue-600",
    amber: "bg-amber-50 text-amber-600",
    rose: "bg-rose-50 text-rose-600",
    emerald: "bg-emerald-50 text-emerald-600",
    red: "bg-red-50 text-red-600",
    sky: "bg-sky-50 text-sky-600",
  };
  const cls = accents[accent] || accents.violet;
  return (
    <div className="flex items-center gap-3 bg-white rounded-xl border border-gray-100 px-4 py-3">
      <div
        className={`w-8 h-8 rounded-lg ${cls} flex items-center justify-center`}
      >
        {icon}
      </div>
      <div className="min-w-0">
        <p className="text-[11px] text-gray-500 uppercase tracking-wider font-medium truncate">
          {label}
        </p>
        <p className="text-sm font-bold text-gray-900 truncate">{value}</p>
      </div>
    </div>
  );
}

/* ═══════════════════════════════════════════════════════════════════════════
   FILE PATH TAG
   ═══════════════════════════════════════════════════════════════════════════ */

function FPath({ path }: { path: string }) {
  const suspicious =
    /\.(exe|bat|cmd|ps1|vbs|enc|bin|dat|dll)$/i.test(path) ||
    /hidden|payload|exfil|staging|svchost_update/i.test(path);
  return (
    <span
      className={`font-mono text-xs inline-block max-w-full truncate ${suspicious ? "text-red-600 font-semibold" : "text-gray-600"}`}
      title={path}
    >
      {suspicious && (
        <IoWarningOutline className="w-3 h-3 inline mr-0.5 -mt-0.5 text-red-500" />
      )}
      {path}
    </span>
  );
}

/* ═══════════════════════════════════════════════════════════════════════════
   DATA GRID
   ═══════════════════════════════════════════════════════════════════════════ */

function DataGrid({
  headers,
  rows,
  maxRows = 80,
}: {
  headers: string[];
  rows: (string | React.ReactNode)[][];
  maxRows?: number;
}) {
  const [showAll, setShowAll] = useState(false);
  const visible = showAll ? rows : rows.slice(0, maxRows);

  return (
    <div className="overflow-x-auto rounded-xl border border-gray-100">
      <table className="w-full text-sm">
        <thead>
          <tr className="bg-gray-50/80">
            {headers.map((h, i) => (
              <th
                key={i}
                className="text-left px-4 py-2.5 text-[11px] font-semibold text-gray-500 uppercase tracking-wider border-b border-gray-100"
              >
                {h}
              </th>
            ))}
          </tr>
        </thead>
        <tbody className="divide-y divide-gray-50">
          {visible.map((row, ri) => (
            <tr key={ri} className="hover:bg-violet-50/30 transition-colors">
              {row.map((cell, ci) => (
                <td
                  key={ci}
                  className="px-4 py-2.5 text-gray-700 max-w-sm truncate"
                >
                  {cell}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
      {rows.length > maxRows && !showAll && (
        <div className="px-4 py-2 bg-gray-50/50 border-t border-gray-100">
          <button
            onClick={() => setShowAll(true)}
            className="text-xs text-violet-600 hover:text-violet-700 font-medium"
          >
            Show all {rows.length} rows →
          </button>
        </div>
      )}
    </div>
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

  useEffect(() => {
    return () => {
      if (hoverTimerRef.current) clearInterval(hoverTimerRef.current);
    };
  }, []);

  if (screenshots.length === 0) return null;

  return (
    <>
      <div className="relative group mt-3">
        <button
          onClick={() =>
            scrollRef.current?.scrollBy({ left: -320, behavior: "smooth" })
          }
          className="absolute left-0 top-1/2 -translate-y-1/2 z-10 w-8 h-8 bg-white/95 border border-gray-200 shadow-lg rounded-full flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity"
        >
          <IoChevronBack className="w-4 h-4 text-gray-600" />
        </button>
        <button
          onClick={() =>
            scrollRef.current?.scrollBy({ left: 320, behavior: "smooth" })
          }
          className="absolute right-0 top-1/2 -translate-y-1/2 z-10 w-8 h-8 bg-white/95 border border-gray-200 shadow-lg rounded-full flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity"
        >
          <IoChevronForward className="w-4 h-4 text-gray-600" />
        </button>

        <div
          ref={scrollRef}
          className="flex gap-3 overflow-x-auto py-2 px-1"
          style={{ scrollbarWidth: "thin" }}
        >
          {screenshots.map((name, idx) => (
            <button
              key={name}
              onClick={() => setLightboxIdx(idx)}
              className="group/t relative flex-shrink-0 w-44 aspect-video rounded-xl overflow-hidden border-2 border-gray-200 hover:border-violet-400 transition-all hover:shadow-lg hover:scale-[1.02]"
            >
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img
                src={screenshotURL(analysisId, name)}
                alt={`Screenshot ${idx + 1}`}
                className="w-full h-full object-cover"
                loading="lazy"
                onError={(e) => {
                  (e.target as HTMLImageElement).style.display = "none";
                }}
              />
              <div className="absolute inset-0 bg-gradient-to-t from-black/50 via-transparent to-transparent opacity-0 group-hover/t:opacity-100 transition-opacity" />
              <div className="absolute top-1.5 right-1.5 w-5 h-5 bg-black/60 backdrop-blur rounded-full flex items-center justify-center text-white text-[9px] font-bold">
                {idx + 1}
              </div>
            </button>
          ))}
        </div>
      </div>

      {/* Lightbox */}
      {lightboxIdx !== null && (
        <div
          className="fixed inset-0 z-50 bg-black/95 flex flex-col items-center justify-center"
          onClick={() => {
            setLightboxIdx(null);
            stopHoverAdvance();
          }}
        >
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

          <div
            className="relative max-w-6xl max-h-[80vh] mx-4 cursor-pointer"
            onClick={(e) => e.stopPropagation()}
            onMouseEnter={startHoverAdvance}
            onMouseLeave={stopHoverAdvance}
          >
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img
              src={screenshotURL(analysisId, screenshots[lightboxIdx])}
              alt={screenshots[lightboxIdx]}
              className="max-w-full max-h-[80vh] rounded-xl shadow-2xl"
            />
            <div className="absolute bottom-3 inset-x-0 text-center pointer-events-none">
              <span className="bg-black/50 text-white/70 text-xs px-3 py-1 rounded-full">
                Hover to auto-advance • ← → keys
              </span>
            </div>
          </div>

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
                  {/* eslint-disable-next-line @next/next/no-img-element */}
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
    <div className="space-y-5 mt-4">
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
        <MiniStat
          label="Total Events"
          value={data.total_events?.toLocaleString() || "0"}
          icon={<IoLayersOutline className="w-4 h-4" />}
          accent="violet"
        />
        <MiniStat
          label="Sample Events"
          value={data.sample_events?.toLocaleString() || "0"}
          icon={<IoBugOutline className="w-4 h-4" />}
          accent="red"
        />
        <MiniStat
          label="Sample PIDs"
          value={data.sample_pids?.join(", ") || "—"}
          icon={<IoTerminalOutline className="w-4 h-4" />}
          accent="amber"
        />
        <MiniStat
          label="DLLs Loaded"
          value={data.dlls_loaded?.length || 0}
          icon={<IoHardwareChipOutline className="w-4 h-4" />}
          accent="sky"
        />
      </div>

      {data.processes_created?.length > 0 && (
        <div>
          <h4 className="text-xs font-bold text-gray-500 uppercase tracking-wider mb-2 flex items-center gap-2">
            <IoTerminalOutline className="w-3.5 h-3.5 text-violet-500" />
            Process Creation ({data.processes_created.length})
          </h4>
          <DataGrid
            headers={["Time", "Image", "PID", "Parent", "User", "Command"]}
            rows={data.processes_created.map((p) => [
              <span
                key="t"
                className="text-xs text-gray-500 whitespace-nowrap font-mono"
              >
                {p.time ? new Date(p.time).toLocaleTimeString() : "—"}
              </span>,
              <FPath key="i" path={p.image} />,
              <span
                key="p"
                className="font-mono text-xs font-bold text-violet-700"
              >
                {p.pid}
              </span>,
              <FPath key="pp" path={p.parent} />,
              <span key="u" className="text-xs text-gray-600">
                {p.user}
              </span>,
              <span
                key="c"
                className="font-mono text-xs text-gray-500 truncate max-w-xs block"
              >
                {p.cmd}
              </span>,
            ])}
          />
        </div>
      )}

      {data.network_connections?.length > 0 && (
        <div>
          <h4 className="text-xs font-bold text-gray-500 uppercase tracking-wider mb-2 flex items-center gap-2">
            <IoGlobeOutline className="w-3.5 h-3.5 text-blue-500" />
            Network Connections ({data.network_connections.length})
          </h4>
          <DataGrid
            headers={["Image", "Protocol", "Source", "Destination", "Host"]}
            rows={data.network_connections.map((c) => [
              <FPath key="i" path={c.image} />,
              <span
                key="pr"
                className="text-xs font-semibold bg-blue-50 text-blue-700 px-2 py-0.5 rounded"
              >
                {c.proto}
              </span>,
              <span key="s" className="font-mono text-xs">
                {c.src}
              </span>,
              <span
                key="d"
                className="font-mono text-xs font-bold text-red-600"
              >
                {c.dst}
              </span>,
              <span key="h" className="text-xs text-gray-500">
                {c.dst_host || "—"}
              </span>,
            ])}
          />
        </div>
      )}

      {data.dns_queries?.length > 0 && (
        <div>
          <h4 className="text-xs font-bold text-gray-500 uppercase tracking-wider mb-2">
            DNS Queries ({data.dns_queries.length})
          </h4>
          <div className="flex flex-wrap gap-2 mt-1">
            {data.dns_queries.map((q) => (
              <span
                key={q}
                className="px-3 py-1.5 bg-sky-50 text-sky-700 border border-sky-200 rounded-lg text-xs font-mono"
              >
                {q}
              </span>
            ))}
          </div>
        </div>
      )}

      {data.files_created?.length > 0 && (
        <div>
          <h4 className="text-xs font-bold text-gray-500 uppercase tracking-wider mb-2 flex items-center gap-2">
            <IoFolderOpenOutline className="w-3.5 h-3.5 text-amber-500" />
            Files Created ({data.files_created.length})
          </h4>
          <div className="space-y-1 max-h-48 overflow-y-auto bg-gray-50 rounded-xl p-3 border border-gray-100">
            {data.files_created.map((f, i) => (
              <div key={i} className="flex items-center gap-2 py-0.5">
                <IoDocumentTextOutline className="w-3.5 h-3.5 text-gray-400 shrink-0" />
                <FPath path={f} />
              </div>
            ))}
          </div>
        </div>
      )}

      {data.registry_events?.length > 0 && (
        <div>
          <h4 className="text-xs font-bold text-gray-500 uppercase tracking-wider mb-2 flex items-center gap-2">
            <IoKeyOutline className="w-3.5 h-3.5 text-rose-500" />
            Registry Events ({data.registry_events.length})
          </h4>
          <DataGrid
            headers={["Type", "Key", "Details"]}
            rows={data.registry_events.map((r) => [
              <span
                key="t"
                className={`text-xs font-semibold px-2 py-0.5 rounded-md ${r.type.includes("Set") ? "bg-amber-50 text-amber-700" : r.type.includes("Delete") ? "bg-red-50 text-red-700" : "bg-gray-100 text-gray-600"}`}
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
          />
        </div>
      )}

      {data.dlls_loaded?.length > 0 && (
        <div>
          <h4 className="text-xs font-bold text-gray-500 uppercase tracking-wider mb-2">
            DLLs Loaded ({data.dlls_loaded.length})
          </h4>
          <div className="flex flex-wrap gap-1.5 max-h-36 overflow-y-auto">
            {data.dlls_loaded.map((d, i) => {
              const name = d.split("\\").pop() || d;
              const isCrypto = /crypt|rsa|aes|bcrypt/i.test(name);
              const isNet = /ws2|winsock|winhttp|dnsapi|iphlp/i.test(name);
              const color = isCrypto
                ? "bg-red-50 text-red-600 border-red-200"
                : isNet
                  ? "bg-blue-50 text-blue-600 border-blue-200"
                  : "bg-gray-50 text-gray-600 border-gray-100";
              return (
                <span
                  key={i}
                  className={`px-2 py-0.5 rounded-md border text-[11px] font-mono ${color}`}
                  title={d}
                >
                  {name}
                </span>
              );
            })}
          </div>
        </div>
      )}

      {data.sample_events === 0 && (
        <NoData label="No sample-related events detected by Sysmon." />
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
    <div className="space-y-5 mt-4">
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
        <MiniStat
          label="Total Rows"
          value={data.total_rows?.toLocaleString() || "0"}
          icon={<IoLayersOutline className="w-4 h-4" />}
          accent="amber"
        />
        <MiniStat
          label="Sample Events"
          value={data.sample_events?.toLocaleString() || "0"}
          icon={<IoBugOutline className="w-4 h-4" />}
          accent="red"
        />
        <MiniStat
          label="File Operations"
          value={Object.values(fileOps)
            .reduce((a: number, b: number) => a + b, 0)
            .toLocaleString()}
          icon={<IoFolderOpenOutline className="w-4 h-4" />}
          accent="emerald"
        />
        <MiniStat
          label="Registry Ops"
          value={Object.values(regOps)
            .reduce((a: number, b: number) => a + b, 0)
            .toLocaleString()}
          icon={<IoKeyOutline className="w-4 h-4" />}
          accent="rose"
        />
      </div>

      {/* Two-column bar charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {Object.keys(fileOps).length > 0 && (
          <div className="bg-gradient-to-br from-amber-50 to-orange-50 rounded-xl p-4 border border-amber-100">
            <h4 className="text-xs font-bold text-amber-800 uppercase tracking-wider mb-3">
              File Operations
            </h4>
            <div className="space-y-1.5">
              {Object.entries(fileOps)
                .sort(([, a], [, b]) => (b as number) - (a as number))
                .slice(0, 10)
                .map(([op, count]) => {
                  const max = Math.max(...(Object.values(fileOps) as number[]));
                  const pct = Math.round(((count as number) / max) * 100);
                  return (
                    <div key={op} className="flex items-center gap-2">
                      <span className="text-xs text-amber-700 w-28 truncate font-medium">
                        {op}
                      </span>
                      <div className="flex-1 h-4 bg-white/60 rounded-full overflow-hidden">
                        <div
                          className="h-full bg-gradient-to-r from-amber-400 to-orange-400 rounded-full"
                          style={{ width: `${pct}%` }}
                        />
                      </div>
                      <span className="text-xs font-bold text-amber-800 w-12 text-right">
                        {(count as number).toLocaleString()}
                      </span>
                    </div>
                  );
                })}
            </div>
          </div>
        )}

        {Object.keys(regOps).length > 0 && (
          <div className="bg-gradient-to-br from-rose-50 to-pink-50 rounded-xl p-4 border border-rose-100">
            <h4 className="text-xs font-bold text-rose-800 uppercase tracking-wider mb-3">
              Registry Operations
            </h4>
            <div className="space-y-1.5">
              {Object.entries(regOps)
                .sort(([, a], [, b]) => (b as number) - (a as number))
                .slice(0, 10)
                .map(([op, count]) => {
                  const max = Math.max(...(Object.values(regOps) as number[]));
                  const pct = Math.round(((count as number) / max) * 100);
                  return (
                    <div key={op} className="flex items-center gap-2">
                      <span className="text-xs text-rose-700 w-28 truncate font-medium">
                        {op}
                      </span>
                      <div className="flex-1 h-4 bg-white/60 rounded-full overflow-hidden">
                        <div
                          className="h-full bg-gradient-to-r from-rose-400 to-pink-400 rounded-full"
                          style={{ width: `${pct}%` }}
                        />
                      </div>
                      <span className="text-xs font-bold text-rose-800 w-12 text-right">
                        {(count as number).toLocaleString()}
                      </span>
                    </div>
                  );
                })}
            </div>
          </div>
        )}
      </div>

      {/* Notable file activity */}
      {Object.keys(fileNotable).length > 0 && (
        <div>
          <h4 className="text-xs font-bold text-gray-500 uppercase tracking-wider mb-2 flex items-center gap-2">
            <IoAlertCircleOutline className="w-3.5 h-3.5 text-red-500" />
            Notable File Activity
          </h4>
          {Object.entries(fileNotable).map(([op, paths]) => (
            <div key={op} className="mb-3">
              <span className="inline-block text-[10px] font-bold text-gray-500 uppercase bg-gray-100 px-2 py-0.5 rounded mb-1.5">
                {op} ({(paths as string[]).length})
              </span>
              <div className="space-y-0.5 bg-gray-50 rounded-xl p-3 max-h-40 overflow-y-auto border border-gray-100">
                {(paths as string[]).map((p, i) => (
                  <div key={i} className="flex items-center gap-2">
                    <IoDocumentTextOutline className="w-3 h-3 text-gray-400 shrink-0" />
                    <FPath path={p} />
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Notable registry activity */}
      {Object.keys(regNotable).length > 0 && (
        <div>
          <h4 className="text-xs font-bold text-gray-500 uppercase tracking-wider mb-2 flex items-center gap-2">
            <IoAlertCircleOutline className="w-3.5 h-3.5 text-red-500" />
            Notable Registry Activity
          </h4>
          {Object.entries(regNotable).map(([op, paths]) => (
            <div key={op} className="mb-3">
              <span className="inline-block text-[10px] font-bold text-gray-500 uppercase bg-gray-100 px-2 py-0.5 rounded mb-1.5">
                {op} ({(paths as string[]).length})
              </span>
              <div className="space-y-0.5 bg-gray-50 rounded-xl p-3 max-h-40 overflow-y-auto border border-gray-100">
                {(paths as string[]).map((p, i) => (
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

      {data.network_activity?.length > 0 && (
        <div>
          <h4 className="text-xs font-bold text-gray-500 uppercase tracking-wider mb-2 flex items-center gap-2">
            <IoGlobeOutline className="w-3.5 h-3.5 text-blue-500" />
            Network Activity ({data.network_activity.length})
          </h4>
          <DataGrid
            headers={["Operation", "Endpoint", "Result"]}
            rows={data.network_activity.map((n) => [
              <span key="o" className="font-semibold text-xs">
                {n.op}
              </span>,
              <span key="p" className="font-mono text-xs">
                {n.path}
              </span>,
              <span
                key="r"
                className={`text-xs font-bold px-2 py-0.5 rounded-md ${n.result === "SUCCESS" ? "bg-green-50 text-green-700" : "bg-red-50 text-red-700"}`}
              >
                {n.result}
              </span>,
            ])}
          />
        </div>
      )}

      {data.process_activity?.length > 0 && (
        <div>
          <h4 className="text-xs font-bold text-gray-500 uppercase tracking-wider mb-2 flex items-center gap-2">
            <IoTerminalOutline className="w-3.5 h-3.5 text-slate-500" />
            Process / Thread Activity ({data.process_activity.length})
          </h4>
          <DataGrid
            headers={["Operation", "Path", "Detail"]}
            rows={data.process_activity.map((p) => [
              <span key="o" className="font-semibold text-xs">
                {p.op}
              </span>,
              <FPath key="p" path={p.path} />,
              <span
                key="d"
                className="text-xs text-gray-500 truncate max-w-xs block"
              >
                {p.detail}
              </span>,
            ])}
          />
        </div>
      )}
    </div>
  );
}

/* ═══════════════════════════════════════════════════════════════════════════
   NETWORK SECTION — TABBED
   ═══════════════════════════════════════════════════════════════════════════ */

function NetworkSection({ data }: { data: NetworkData }) {
  const [tab, setTab] = useState<"tcp" | "dns" | "http">("tcp");
  const hasTcp = !!data.tcp_conversations;
  const hasDns = data.dns_queries && data.dns_queries.length > 0;
  const hasHttp = data.http_requests && data.http_requests.length > 0;

  return (
    <div className="mt-4">
      <div className="flex gap-1 bg-gray-100 p-1 rounded-xl mb-4">
        {[
          { key: "tcp" as const, label: "TCP Conversations", has: hasTcp },
          {
            key: "dns" as const,
            label: `DNS (${data.dns_queries?.length || 0})`,
            has: hasDns,
          },
          {
            key: "http" as const,
            label: `HTTP (${data.http_requests?.length || 0})`,
            has: hasHttp,
          },
        ].map((t) => (
          <button
            key={t.key}
            onClick={() => setTab(t.key)}
            className={`flex-1 px-3 py-2 rounded-lg text-xs font-semibold transition-colors ${
              tab === t.key
                ? "bg-white text-gray-900 shadow-sm"
                : "text-gray-500 hover:text-gray-700"
            } ${!t.has ? "opacity-40" : ""}`}
          >
            {t.label}
          </button>
        ))}
      </div>

      {tab === "tcp" &&
        (hasTcp ? (
          <pre className="bg-gray-900 text-green-400 rounded-xl p-4 text-xs overflow-x-auto max-h-72 overflow-y-auto font-mono leading-relaxed">
            {data.tcp_conversations}
          </pre>
        ) : (
          <NoData label="No TCP conversation data captured." />
        ))}

      {tab === "dns" &&
        (hasDns ? (
          <div className="flex flex-wrap gap-2">
            {data.dns_queries!.map((q) => (
              <span
                key={q}
                className="px-3 py-1.5 bg-sky-50 text-sky-700 border border-sky-200 rounded-lg text-xs font-mono"
              >
                {q}
              </span>
            ))}
          </div>
        ) : (
          <NoData label="No DNS queries captured." />
        ))}

      {tab === "http" &&
        (hasHttp ? (
          <DataGrid
            headers={["Method", "Host", "URI"]}
            rows={data.http_requests!.map((r) => [
              <span
                key="m"
                className={`text-xs font-bold px-2 py-0.5 rounded-md ${r.method === "GET" ? "bg-green-50 text-green-700" : r.method === "POST" ? "bg-blue-50 text-blue-700" : "bg-gray-100 text-gray-700"}`}
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
        ) : (
          <NoData label="No HTTP requests captured." />
        ))}

      {!hasTcp && !hasDns && !hasHttp && (
        <NoData
          label="No network traffic captured."
          hint="The VM uses host-only networking — connection attempts are logged as IOCs."
        />
      )}
    </div>
  );
}

/* ═══════════════════════════════════════════════════════════════════════════
   HANDLE SECTION — TERMINAL STYLE
   ═══════════════════════════════════════════════════════════════════════════ */

function HandleSection({ data }: { data: string }) {
  const lines = data.split("\n").filter((l) => l.trim());
  return (
    <div className="mt-4">
      <div className="bg-gray-900 rounded-xl overflow-hidden border border-gray-800">
        <div className="flex items-center gap-2 px-4 py-2 bg-gray-800/50 border-b border-gray-700">
          <div className="flex gap-1.5">
            <div className="w-3 h-3 rounded-full bg-red-500/80" />
            <div className="w-3 h-3 rounded-full bg-yellow-500/80" />
            <div className="w-3 h-3 rounded-full bg-green-500/80" />
          </div>
          <span className="text-gray-400 text-xs font-mono ml-2">
            handle_snapshot.txt — {lines.length} lines
          </span>
        </div>
        <pre className="text-green-400 p-4 text-xs overflow-x-auto max-h-72 overflow-y-auto font-mono leading-relaxed">
          {lines.length > 200
            ? lines.slice(0, 200).join("\n") + "\n\n… truncated …"
            : data}
        </pre>
      </div>
    </div>
  );
}

/* ═══════════════════════════════════════════════════════════════════════════
   TCPVCON SECTION
   ═══════════════════════════════════════════════════════════════════════════ */

function TcpvconSection({ data }: { data: TcpvconRow[] }) {
  if (data.length === 0)
    return <NoData label="No active connections captured." />;
  const headers = Object.keys(data[0]);
  return (
    <div className="mt-4">
      <DataGrid
        headers={headers}
        rows={data.map((row) =>
          headers.map((h) => (
            <span key={h} className="font-mono text-xs">
              {row[h]}
            </span>
          )),
        )}
      />
    </div>
  );
}

/* ═══════════════════════════════════════════════════════════════════════════
   COLLECTOR BADGES
   ═══════════════════════════════════════════════════════════════════════════ */

function CollectorBadges({
  metadata,
}: {
  metadata: { collectors: { collector: string; status: string }[] };
}) {
  return (
    <div className="flex flex-wrap gap-2 mt-3">
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
            className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl border text-xs font-medium ${color}`}
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
  const [showClearConfirm, setShowClearConfirm] = useState(false);
  const [clearing, setClearing] = useState(false);

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

  const handleClearAll = async () => {
    setClearing(true);
    try {
      const resp = await clearAllReports();
      if (resp.status === "ok") {
        setReports([]);
        setSelected(null);
        setReportData(null);
        setShowClearConfirm(false);
      } else {
        setError(resp.error?.message || "Failed to clear reports");
      }
    } catch {
      setError("Failed to clear reports");
    } finally {
      setClearing(false);
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

  const rd = reportData;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900">Analysis Reports</h1>
        <div className="flex items-center gap-3">
          {reports.length > 0 && (
            <button
              onClick={() => setShowClearConfirm(true)}
              className="inline-flex items-center gap-2 text-sm text-red-500 hover:text-red-700 transition-colors"
            >
              <IoTrashOutline className="w-4 h-4" />
              Clear All
            </button>
          )}
          <button
            onClick={fetchData}
            className="inline-flex items-center gap-2 text-sm text-gray-600 hover:text-violet-600 transition-colors"
          >
            <IoRefreshOutline className="w-4 h-4" />
            Refresh
          </button>
        </div>
      </div>

      {/* Clear confirmation */}
      {showClearConfirm && (
        <div className="bg-red-50 border border-red-200 rounded-2xl p-5">
          <div className="flex items-start gap-3">
            <IoAlertCircleOutline className="w-6 h-6 text-red-500 shrink-0 mt-0.5" />
            <div className="flex-1">
              <p className="text-sm font-medium text-red-800">
                Delete all {reports.length} report
                {reports.length !== 1 ? "s" : ""}?
              </p>
              <p className="text-xs text-red-600 mt-1">
                This will permanently remove all analysis reports and associated
                data.
              </p>
              <div className="flex gap-3 mt-3">
                <button
                  onClick={handleClearAll}
                  disabled={clearing}
                  className="inline-flex items-center gap-2 bg-red-600 hover:bg-red-700 disabled:opacity-50 text-white text-sm font-medium px-4 py-2 rounded-xl transition-colors"
                >
                  <IoTrashOutline className="w-4 h-4" />
                  {clearing ? "Deleting..." : "Yes, Delete All"}
                </button>
                <button
                  onClick={() => setShowClearConfirm(false)}
                  disabled={clearing}
                  className="text-sm text-gray-600 hover:text-gray-800 px-4 py-2 rounded-xl border border-gray-300 hover:bg-gray-50 transition-colors"
                >
                  Cancel
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {loading && (
        <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-12 text-center">
          <div className="animate-spin w-8 h-8 border-4 border-violet-200 border-t-violet-500 rounded-full mx-auto mb-3" />
          <p className="text-sm text-gray-500">Loading reports...</p>
        </div>
      )}

      {error && (
        <div className="bg-red-50 border border-red-200 rounded-2xl p-4 flex items-center gap-3">
          <IoAlertCircleOutline className="w-5 h-5 text-red-500 shrink-0" />
          <p className="text-sm text-red-700">{error}</p>
        </div>
      )}

      {!loading && !error && reports.length === 0 && (
        <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-12 text-center">
          <IoDocumentTextOutline className="w-12 h-12 text-gray-300 mx-auto mb-3" />
          <p className="text-gray-500">No analysis reports yet.</p>
          <p className="text-sm text-gray-400 mt-1">
            Submit a sample from the{" "}
            <a href="/scan" className="text-violet-600 hover:text-violet-700">
              Scan
            </a>{" "}
            page.
          </p>
        </div>
      )}

      {/* Main layout */}
      {!loading && reports.length > 0 && (
        <div className="grid grid-cols-1 lg:grid-cols-5 gap-6">
          {/* Sidebar */}
          <div className="lg:col-span-1 space-y-2">
            <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-3">
              Analyses ({reports.length})
            </h3>
            <div className="space-y-1.5 max-h-[calc(100vh-200px)] overflow-y-auto">
              {reports.map((report) => (
                <button
                  key={report.analysis_id}
                  onClick={() => selectReport(report)}
                  className={`w-full text-left p-3 rounded-xl border transition-all ${
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
                      className={`inline-block px-2 py-0.5 rounded-lg text-xs font-medium border ${statusColor(report.status)}`}
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

          {/* Detail panel */}
          <div className="lg:col-span-4 space-y-4">
            {selected ? (
              <>
                {/* Tab switcher */}
                <div className="bg-white rounded-2xl shadow-sm border border-gray-100 overflow-hidden">
                  <div className="flex border-b border-gray-100">
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

                          <div className="grid grid-cols-2 md:grid-cols-5 gap-3 mb-6">
                            <MiniStat
                              label="Timeout"
                              value={`${selected.timeout}s`}
                              icon={<IoTimeOutline className="w-4 h-4" />}
                              accent="violet"
                            />
                            <MiniStat
                              label="Sysmon Events"
                              value={
                                rd?.sysmon?.sample_events ??
                                selected.sysmon_events ??
                                0
                              }
                              icon={<IoBugOutline className="w-4 h-4" />}
                              accent="red"
                            />
                            <MiniStat
                              label="Procmon Rows"
                              value={
                                rd?.procmon?.sample_events?.toLocaleString() ??
                                "—"
                              }
                              icon={<IoEyeOutline className="w-4 h-4" />}
                              accent="amber"
                            />
                            <MiniStat
                              label="Files Collected"
                              value={selected.files_collected?.length || 0}
                              icon={<IoFolderOpenOutline className="w-4 h-4" />}
                              accent="emerald"
                            />
                            <MiniStat
                              label="Screenshots"
                              value={rd?.screenshots?.length ?? 0}
                              icon={<IoImageOutline className="w-4 h-4" />}
                              accent="sky"
                            />
                          </div>

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
                            {(rd?.sysmon?.sample_process ||
                              rd?.procmon?.sample_process) && (
                              <span>
                                🎯 Process:{" "}
                                <code className="bg-gray-100 px-1 rounded">
                                  {rd?.sysmon?.sample_process ||
                                    rd?.procmon?.sample_process}
                                </code>
                              </span>
                            )}
                          </div>

                          {selected.error && (
                            <div className="bg-red-50 border border-red-200 rounded-xl p-3 mb-4">
                              <p className="text-sm text-red-700">
                                ❌ {selected.error}
                              </p>
                            </div>
                          )}
                        </div>
                      )}
                    </div>
                  )}

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
                          risk scoring, and IOC extraction.
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
                              className="bg-white border border-gray-200 rounded-xl p-3 text-center"
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

                {/* Report sections (always visible with empty states) */}
                {activeTab === "report" && !detailLoading && rd && (
                  <div className="space-y-4">
                    {rd.metadata?.collectors && (
                      <Panel
                        title="Collector Status"
                        icon={<IoServerOutline className="w-4 h-4" />}
                        count={rd.metadata.collectors.length}
                        color="slate"
                        defaultOpen={false}
                      >
                        <CollectorBadges metadata={rd.metadata} />
                      </Panel>
                    )}

                    <Panel
                      title={`Screenshots (${rd.screenshots?.length || 0})`}
                      icon={<IoImageOutline className="w-4 h-4" />}
                      count={rd.screenshots?.length || 0}
                      color="violet"
                    >
                      {rd.screenshots && rd.screenshots.length > 0 ? (
                        <div>
                          <p className="text-xs text-gray-400 mb-1 mt-3">
                            Click to open. Hover to auto-advance. Use ← → keys.
                          </p>
                          <ScreenshotGallery
                            analysisId={selected.analysis_id}
                            screenshots={rd.screenshots}
                          />
                        </div>
                      ) : (
                        <NoData
                          label="No screenshots captured."
                          hint="Screenshots may not have been collected during this analysis."
                        />
                      )}
                    </Panel>

                    <Panel
                      title="Sysmon — System Monitor"
                      icon={<IoShieldCheckmarkOutline className="w-4 h-4" />}
                      count={
                        rd.sysmon
                          ? `${rd.sysmon.sample_events} events`
                          : "no data"
                      }
                      color="violet"
                    >
                      {rd.sysmon ? (
                        <SysmonSection data={rd.sysmon} />
                      ) : (
                        <NoData
                          label="No Sysmon data collected."
                          hint="Sysmon may not be installed or configured in the sandbox VM."
                        />
                      )}
                    </Panel>

                    <Panel
                      title="Procmon — Process Monitor"
                      icon={<IoEyeOutline className="w-4 h-4" />}
                      count={
                        rd.procmon
                          ? `${rd.procmon.sample_events?.toLocaleString()} events`
                          : "no data"
                      }
                      color="amber"
                    >
                      {rd.procmon ? (
                        <ProcmonSection data={rd.procmon} />
                      ) : (
                        <NoData
                          label="No Procmon data collected."
                          hint="Process Monitor data was not available for this analysis."
                        />
                      )}
                    </Panel>

                    <Panel
                      title="Network — Packet Capture"
                      icon={<IoGitNetworkOutline className="w-4 h-4" />}
                      count={
                        rd.network
                          ? `${(rd.network.dns_queries?.length || 0) + (rd.network.http_requests?.length || 0)} items`
                          : "no data"
                      }
                      color="blue"
                    >
                      {rd.network ? (
                        <NetworkSection data={rd.network} />
                      ) : (
                        <NoData
                          label="No network capture data."
                          hint="tshark may not be installed or the collector didn't produce output."
                        />
                      )}
                    </Panel>

                    <Panel
                      title="Handle — Open Handles"
                      icon={<IoKeyOutline className="w-4 h-4" />}
                      count={
                        rd.handle
                          ? `${rd.handle.split("\n").filter((l: string) => l.trim()).length} lines`
                          : "no data"
                      }
                      color="rose"
                      defaultOpen={false}
                    >
                      {rd.handle ? (
                        <HandleSection data={rd.handle} />
                      ) : (
                        <NoData
                          label="No handle snapshot data."
                          hint="Handle.exe may not be available in the VM."
                        />
                      )}
                    </Panel>

                    <Panel
                      title="TCP/UDP Connections (tcpvcon)"
                      icon={<IoSwapHorizontalOutline className="w-4 h-4" />}
                      count={
                        rd.tcpvcon
                          ? `${rd.tcpvcon.length} connections`
                          : "no data"
                      }
                      color="sky"
                      defaultOpen={false}
                    >
                      {rd.tcpvcon && rd.tcpvcon.length > 0 ? (
                        <TcpvconSection data={rd.tcpvcon} />
                      ) : (
                        <NoData
                          label="No active TCP/UDP connections captured."
                          hint="tcpvcon may not be available or no connections were active."
                        />
                      )}
                    </Panel>

                    {selected.files_collected &&
                      selected.files_collected.length > 0 && (
                        <Panel
                          title="All Collected Files"
                          icon={<IoFolderOpenOutline className="w-4 h-4" />}
                          count={selected.files_collected.length}
                          color="emerald"
                          defaultOpen={false}
                        >
                          <div className="mt-3 space-y-1 max-h-60 overflow-y-auto">
                            {selected.files_collected.map((file, idx) => (
                              <div
                                key={idx}
                                className="flex items-center gap-2 px-3 py-1.5 rounded-lg hover:bg-gray-50 transition-colors"
                              >
                                <IoDocumentTextOutline className="w-3.5 h-3.5 text-gray-400 shrink-0" />
                                <span className="text-gray-700 font-mono text-xs truncate">
                                  {file}
                                </span>
                              </div>
                            ))}
                          </div>
                        </Panel>
                      )}
                  </div>
                )}
              </>
            ) : (
              <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-12 text-center">
                <p className="text-gray-500">Select a report to view details</p>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
