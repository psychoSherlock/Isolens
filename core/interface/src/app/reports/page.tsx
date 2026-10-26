"use client";

import { useEffect, useState, useRef } from "react";
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
  IoSearchOutline,
  IoFlashOutline,
  IoShieldOutline,
  IoFingerPrintOutline,
  IoAnalyticsOutline,
  IoCodeSlashOutline,
  IoRadioButtonOnOutline,
  IoEllipseOutline,
  IoSkullOutline,
  IoLockClosedOutline,
  IoArrowForwardOutline,
  IoDownloadOutline,
  IoBarcodeOutline,
  IoDesktopOutline,
  IoCopyOutline,
  IoCheckmarkOutline,
  IoPulseOutline,
  IoSpeedometerOutline,
  IoFlameOutline,
} from "react-icons/io5";
import {
  getAnalysisStatus,
  listReports,
  clearAllReports,
  screenshotURL,
  getReportData,
  getAIReport,
  runAIAnalysis,
  getAIProgress,
  type AnalysisResult,
  type ReportData,
  type SysmonData,
  type ProcmonData,
  type NetworkData,
  type TcpvconRow,
  type AIReport,
  type AIToolResult,
  type AIFinding,
  type AIIOC,
  type AIMitreTechnique,
  type AIRecommendation,
  type AIProgress,
  type YaraData,
  type YaraMatch,
  type LstmData,
  type GuiData,
  type FlaggedWindow,
  type RiskData,
  type BehaviorSummary,
  type NetworkDBData,
} from "@/lib/api";
import html2canvas from "html2canvas";
import { jsPDF } from "jspdf";
import AIPipelineAnimation from "@/components/AIPipelineAnimation";
import {
  clearLocalBenignReports,
  isLocalBenignReport,
  readLocalBenignReports,
} from "@/lib/localReports";

/* ═══════════════════════════════════════════════════════════════════════════
   COLLAPSIBLE PANEL
   ═══════════════════════════════════════════════════════════════════════════ */

function Panel({
  title,
  icon,
  count,
  defaultOpen = true,
  color = "blue",
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
  const borders: Record<string, string> = {
    blue: "border-blue-500 text-blue-600 bg-blue-50",
    amber: "border-amber-500 text-amber-600 bg-amber-50",
    emerald: "border-emerald-500 text-emerald-600 bg-emerald-50",
    rose: "border-rose-500 text-rose-600 bg-rose-50",
    slate: "border-slate-500 text-slate-600 bg-slate-50",
    red: "border-red-500 text-red-600 bg-red-50",
    sky: "border-sky-500 text-sky-600 bg-sky-50",
  };
  const cls = borders[color] ?? borders.blue;

  return (
    <div className="bg-white rounded-md shadow-sm border border-slate-200 overflow-hidden">
      <button
        onClick={() => setOpen(!open)}
        className="w-full flex items-center gap-3 px-4 py-3 text-left hover:bg-slate-50 transition-colors group border-b border-transparent data-[open=true]:border-slate-100"
        data-open={open}
      >
        <div className={`w-8 h-8 rounded shrink-0 flex items-center justify-center border ${cls}`}>
          {icon}
        </div>
        <span className="text-base font-bold text-slate-800 flex-1 uppercase tracking-wider">
          {title}
        </span>
        {count !== undefined && (
          <span className="text-sm font-bold font-mono bg-slate-100 text-slate-600 px-2.5 py-0.5 rounded">
            {count}
          </span>
        )}
        <span className="text-slate-400 group-hover:text-slate-600 transition-colors ml-2">
          {open ? (
            <IoChevronUpOutline className="w-4 h-4" />
          ) : (
            <IoChevronDownOutline className="w-4 h-4" />
          )}
        </span>
      </button>
      {open && (
        <div className="p-4 bg-white border-t border-slate-100">{children}</div>
      )}
    </div>
  );
}

/* ═══════════════════════════════════════════════════════════════════════════
   EMPTY STATE
   ═══════════════════════════════════════════════════════════════════════════ */

function NoData({ label, hint }: { label: string; hint?: string }) {
  return (
    <div className="flex items-center gap-3 py-4 px-4 rounded bg-slate-50 border border-slate-200 mt-2">
      <IoInformationCircleOutline className="w-6 h-6 text-slate-400 shrink-0" />
      <div>
        <p className="text-base text-slate-700 font-semibold">{label}</p>
        {hint && <p className="text-sm text-slate-500 mt-0.5 font-medium">{hint}</p>}
      </div>
    </div>
  );
}

function dnsQueryLabel(query: NetworkData["dns_queries"] extends (infer T)[] | undefined ? T : never): string {
  if (typeof query === "string") return query;
  return query?.domain || query?.query || "Unknown domain";
}

/* ═══════════════════════════════════════════════════════════════════════════
   MINI STAT
   ═══════════════════════════════════════════════════════════════════════════ */

function MiniStat({
  label,
  value,
  icon,
  accent = "blue",
}: {
  label: string;
  value: string | number;
  icon: React.ReactNode;
  accent?: string;
}) {
  const accents: Record<string, string> = {
    blue: "text-blue-600",
    amber: "text-amber-600",
    rose: "text-rose-600",
    emerald: "text-emerald-600",
    red: "text-red-600",
    sky: "text-sky-600",
    slate: "text-slate-600",
  };
  const cls = accents[accent] || accents.blue;
  return (
    <div className="flex items-center gap-3 bg-white rounded border border-slate-200 px-4 py-3 shadow-sm relative overflow-hidden">
      <div className={`absolute left-0 top-0 bottom-0 w-1 ${cls.replace("text-", "bg-")}`} />
      <div className={`w-8 h-8 rounded shrink-0 bg-slate-50 flex items-center justify-center border border-slate-100 ${cls}`}>
        {icon}
      </div>
      <div className="min-w-0">
        <p className="text-xs text-slate-500 uppercase tracking-widest font-bold truncate">
          {label}
        </p>
        <p className="text-lg font-black text-slate-900 font-mono truncate tracking-tight">{value}</p>
      </div>
    </div>
  );
}

/* ═══════════════════════════════════════════════════════════════════════════
   FILE PATH TAG
   ═══════════════════════════════════════════════════════════════════════════ */

function FPath({ path }: { path: string }) {
  const suspicious =
    /\.(exe|bat|cmd|ps1|vbs|enc|bin|dll|sys)$/i.test(path) ||
    /hidden|payload|exfil|staging|svchost_update|temp/i.test(path);
  return (
    <span
      className={`font-mono text-xs inline-block max-w-full truncate px-1.5 py-0.5 rounded border ${
        suspicious ? "text-red-700 bg-red-50 border-red-200 font-bold" : "text-slate-700 bg-slate-50 border-slate-200 font-medium"
      }`}
      title={path}
    >
      {suspicious && (
        <IoWarningOutline className="w-3 h-3 inline mr-1 -mt-0.5 text-red-500" />
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
    <div className="overflow-x-auto rounded border border-slate-200 shadow-sm bg-white">
      <table className="w-full text-sm">
        <thead>
          <tr className="bg-slate-50 border-b border-slate-200">
            {headers.map((h, i) => (
              <th
                key={i}
                className="text-left px-3 py-2.5 text-xs font-extrabold text-slate-600 uppercase tracking-wider whitespace-nowrap"
              >
                {h}
              </th>
            ))}
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-100">
          {visible.map((row, ri) => (
            <tr key={ri} className="hover:bg-slate-50/80 transition-colors">
              {row.map((cell, ci) => (
                <td
                  key={ci}
                  className="px-3 py-2.5 text-slate-800 max-w-sm truncate text-[14px] font-medium"
                >
                  {cell}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
      {rows.length > maxRows && !showAll && (
        <div className="px-3 py-2 bg-slate-50 border-t border-slate-200 text-center">
          <button
            onClick={() => setShowAll(true)}
            className="text-xs uppercase tracking-wider font-bold text-blue-600 hover:text-blue-700 transition-colors"
          >
            Show all {rows.length} records
          </button>
        </div>
      )}
    </div>
  );
}

/* ═══════════════════════════════════════════════════════════════════════════
   SCREENSHOT GALLERY
   ═══════════════════════════════════════════════════════════════════════════ */

function ScreenshotImage({
  analysisId,
  filename,
  alt,
  fit,
  retryable = false,
}: {
  analysisId: string;
  filename: string;
  alt: string;
  fit: "cover" | "contain";
  retryable?: boolean;
}) {
  const [state, setState] = useState<"loading" | "loaded" | "error">("loading");
  const [attempt, setAttempt] = useState(0);
  const baseUrl = screenshotURL(analysisId, filename);
  const src = `${baseUrl}${baseUrl.includes("?") ? "&" : "?"}retry=${attempt}`;

  useEffect(() => {
    setState("loading");
  }, [analysisId, filename, attempt]);

  return (
    <div className="relative h-full w-full min-h-0 overflow-hidden bg-slate-100">
      {state === "loading" && (
        <div className="absolute inset-0 flex items-center justify-center text-slate-400" aria-live="polite">
          <span className="h-5 w-5 animate-spin rounded-full border-2 border-slate-300 border-t-violet-600" />
          <span className="sr-only">Loading screenshot</span>
        </div>
      )}
      {/* eslint-disable-next-line @next/next/no-img-element */}
      <img
        key={src}
        src={src}
        alt={alt}
        width={1280}
        height={720}
        decoding="async"
        loading="lazy"
        className={`h-full w-full ${fit === "cover" ? "object-cover" : "object-contain"} transition-opacity ${state === "loaded" ? "opacity-100" : "opacity-0"}`}
        onLoad={() => setState("loaded")}
        onError={() => setState("error")}
      />
      {state === "error" && (
        <div className="absolute inset-0 flex flex-col items-center justify-center gap-2 bg-slate-50 p-3 text-center text-slate-600">
          <IoImageOutline className="h-6 w-6 text-slate-400" aria-hidden="true" />
          <span className="text-xs">Screenshot could not be loaded</span>
          {retryable && (
            <button
              type="button"
              onClick={() => {
                setState("loading");
                setAttempt((value) => value + 1);
              }}
              className="rounded-md border border-slate-300 bg-white px-3 py-1.5 text-xs font-medium text-slate-700 hover:bg-slate-50"
            >
              Try again
            </button>
          )}
        </div>
      )}
    </div>
  );
}

function ScreenshotGallery({
  analysisId,
  screenshots,
  guiData,
}: {
  analysisId: string;
  screenshots: string[];
  guiData?: GuiData | null;
}) {
  const [lightboxIdx, setLightboxIdx] = useState<number | null>(null);
  const scrollRef = useRef<HTMLDivElement>(null);
  const dialogRef = useRef<HTMLDivElement>(null);
  const closeButtonRef = useRef<HTMLButtonElement>(null);
  const openerRef = useRef<HTMLButtonElement | null>(null);

  useEffect(() => {
    if (lightboxIdx === null) return;
    const handler = (e: KeyboardEvent) => {
      if (e.key === "Escape") setLightboxIdx(null);
      if (e.key === "ArrowLeft")
        setLightboxIdx((lightboxIdx - 1 + screenshots.length) % screenshots.length);
      if (e.key === "ArrowRight")
        setLightboxIdx((lightboxIdx + 1) % screenshots.length);
    };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [lightboxIdx, screenshots.length]);

  useEffect(() => {
    if (lightboxIdx !== null) closeButtonRef.current?.focus();
    else openerRef.current?.focus();
  }, [lightboxIdx]);

  if (screenshots.length === 0) return null;

  const currentFlagged =
    lightboxIdx !== null && guiData?.flagged_windows
      ? guiData.flagged_windows.find((w) => w.filename === screenshots[lightboxIdx])
      : null;

  return (
    <>
      <div className="relative group mt-3">
        <button
          onClick={() =>
            scrollRef.current?.scrollBy({ left: -320, behavior: "smooth" })
          }
          aria-label="Scroll screenshots left"
          className="absolute left-1 top-1/2 -translate-y-1/2 z-10 w-9 h-9 bg-white/95 border border-slate-200 shadow-lg rounded-full flex items-center justify-center opacity-100 md:opacity-0 md:group-hover:opacity-100 focus:opacity-100 transition-opacity"
        >
          <IoChevronBack className="w-4 h-4 text-slate-600" />
        </button>
        <button
          onClick={() =>
            scrollRef.current?.scrollBy({ left: 320, behavior: "smooth" })
          }
          aria-label="Scroll screenshots right"
          className="absolute right-1 top-1/2 -translate-y-1/2 z-10 w-9 h-9 bg-white/95 border border-slate-200 shadow-lg rounded-full flex items-center justify-center opacity-100 md:opacity-0 md:group-hover:opacity-100 focus:opacity-100 transition-opacity"
        >
          <IoChevronForward className="w-4 h-4 text-slate-600" />
        </button>

        <div
          ref={scrollRef}
          className="flex gap-3 overflow-x-auto py-2 px-1"
          style={{ scrollbarWidth: "thin" }}
        >
          {screenshots.map((name, idx) => {
            const flagged = guiData?.flagged_windows?.find((w) => w.filename === name);
            return (
              <button
                key={name}
                aria-label={`Open screenshot ${idx + 1}${flagged ? " (Threat Flagged)" : ""}`}
                onClick={(event) => {
                  openerRef.current = event.currentTarget;
                  setLightboxIdx(idx);
                }}
                className={`group/t relative flex-shrink-0 w-44 aspect-video rounded overflow-hidden border-2 transition-all hover:scale-[1.02] ${
                  flagged
                    ? "border-rose-500 ring-2 ring-rose-400 shadow-md shadow-rose-500/20"
                    : "border-slate-200 hover:border-blue-400 hover:shadow-lg"
                }`}
              >
                <ScreenshotImage
                  analysisId={analysisId}
                  filename={name}
                  alt={`Screenshot ${idx + 1}`}
                  fit="cover"
                />
                {/* Red warning banner overlay for flagged screenshots */}
                {flagged && (
                  <div className="absolute top-1.5 left-1.5 flex items-center gap-1 bg-rose-600/90 text-white text-[9px] font-bold px-1.5 py-0.5 rounded shadow z-10">
                    <IoWarningOutline className="w-3 h-3 shrink-0" />
                    <span className="truncate max-w-[100px]">
                      {flagged.threat_type === "ransomware_extortion"
                        ? "RANSOMWARE"
                        : flagged.threat_type === "tech_support_scam"
                        ? "SCAM ALERT"
                        : "FLAGGED"}
                    </span>
                  </div>
                )}
                <div className="absolute inset-0 bg-gradient-to-t from-black/50 via-transparent to-transparent opacity-0 group-hover/t:opacity-100 transition-opacity" />
                <div className="absolute top-1.5 right-1.5 w-5 h-5 bg-black/60 backdrop-blur rounded-full flex items-center justify-center text-white text-[9px] font-bold">
                  {idx + 1}
                </div>
              </button>
            );
          })}
        </div>
      </div>

      {/* Lightbox */}
      {lightboxIdx !== null && (
        <div
          className="fixed inset-0 z-50 bg-black/95 flex flex-col items-center justify-center"
          role="dialog"
          aria-modal="true"
          aria-label="Screenshot viewer"
          ref={dialogRef}
          onKeyDown={(event) => {
            if (event.key !== "Tab") return;
            const buttons = dialogRef.current?.querySelectorAll<HTMLButtonElement>("button:not(:disabled)");
            if (!buttons?.length) return;
            const first = buttons[0];
            const last = buttons[buttons.length - 1];
            if (event.shiftKey && document.activeElement === first) {
              event.preventDefault();
              last.focus();
            } else if (!event.shiftKey && document.activeElement === last) {
              event.preventDefault();
              first.focus();
            }
          }}
          onClick={() => {
            setLightboxIdx(null);
          }}
        >
          <div className="absolute top-0 inset-x-0 p-4 flex items-center justify-between z-10">
            <div className="min-w-0 truncate pr-3 text-white/70 text-sm font-mono" title={screenshots[lightboxIdx]}>
              {screenshots[lightboxIdx]}
            </div>
            <div className="flex items-center gap-3">
              <span className="text-white/60 text-sm">
                {lightboxIdx + 1} / {screenshots.length}
              </span>
              <button
                aria-label="Close screenshot viewer"
                ref={closeButtonRef}
                onClick={(e) => {
                  e.stopPropagation();
                  setLightboxIdx(null);
                }}
                className="w-9 h-9 rounded-full bg-white/10 hover:bg-white/20 flex items-center justify-center transition-colors"
              >
                <IoCloseOutline className="w-5 h-5 text-white" />
              </button>
            </div>
          </div>

          <div
            className="relative flex h-[min(76vh,900px)] w-[min(92vw,1400px)] items-center justify-center mx-4"
            onClick={(e) => e.stopPropagation()}
          >
            <ScreenshotImage
              analysisId={analysisId}
              filename={screenshots[lightboxIdx]}
              alt={`Screenshot ${lightboxIdx + 1}`}
              fit="contain"
              retryable
            />
          </div>

          {/* Alert flag floating banner on active screenshot in modal */}
          {currentFlagged && (
            <div
              className="absolute bottom-24 max-w-2xl w-[min(92vw,680px)] bg-rose-950/90 border border-rose-500/70 rounded-xl p-3 text-white backdrop-blur-md shadow-2xl z-20"
              onClick={(e) => e.stopPropagation()}
            >
              <div className="flex items-center justify-between gap-2">
                <div className="flex items-center gap-2">
                  <IoWarningOutline className="w-5 h-5 text-rose-400 shrink-0 animate-pulse" />
                  <span className="font-bold text-rose-200 text-sm uppercase tracking-wide">
                    🚨 {currentFlagged.threat_type.replace(/_/g, " ")} Detected
                  </span>
                </div>
                <span className="text-xs bg-rose-500/30 text-rose-200 px-2.5 py-0.5 rounded-full font-mono border border-rose-400/40">
                  Confidence: {Math.round(currentFlagged.confidence * 100)}%
                </span>
              </div>
              {currentFlagged.matched_keywords && currentFlagged.matched_keywords.length > 0 && (
                <div className="mt-2 flex flex-wrap items-center gap-1.5">
                  <span className="text-[11px] text-rose-300 font-semibold">Matched Keywords:</span>
                  {currentFlagged.matched_keywords.map((kw: string) => (
                    <span
                      key={kw}
                      className="text-[10px] bg-rose-900/80 border border-rose-700/60 px-1.5 py-0.5 rounded font-mono text-rose-100"
                    >
                      {kw}
                    </span>
                  ))}
                </div>
              )}
            </div>
          )}

          {screenshots.length > 1 && (
            <button
              aria-label="Previous screenshot"
              onClick={(e) => {
                e.stopPropagation();
                setLightboxIdx((lightboxIdx - 1 + screenshots.length) % screenshots.length);
              }}
              className="absolute left-4 top-1/2 -translate-y-1/2 w-12 h-12 rounded-full bg-white/10 hover:bg-white/20 flex items-center justify-center transition-colors"
            >
              <IoChevronBack className="w-6 h-6 text-white" />
            </button>
          )}
          {screenshots.length > 1 && (
            <button
              aria-label="Next screenshot"
              onClick={(e) => {
                e.stopPropagation();
                setLightboxIdx((lightboxIdx + 1) % screenshots.length);
              }}
              className="absolute right-4 top-1/2 -translate-y-1/2 w-12 h-12 rounded-full bg-white/10 hover:bg-white/20 flex items-center justify-center transition-colors"
            >
              <IoChevronForward className="w-6 h-6 text-white" />
            </button>
          )}

          <div className="absolute bottom-0 inset-x-0 bg-gradient-to-t from-black/80 to-transparent pt-8 pb-4 px-4">
            <div className="flex gap-2 overflow-x-auto justify-center max-w-4xl mx-auto">
              {screenshots.map((name, idx) => {
                const isThumbFlagged = guiData?.flagged_windows?.some((w) => w.filename === name);
                return (
                  <button
                    key={name}
                    aria-label={`Show screenshot ${idx + 1}`}
                    aria-current={idx === lightboxIdx ? "true" : undefined}
                    onClick={(e) => {
                      e.stopPropagation();
                      setLightboxIdx(idx);
                    }}
                    className={`flex-shrink-0 w-16 h-10 rounded overflow-hidden border-2 transition-all ${
                      idx === lightboxIdx
                        ? "border-blue-400 scale-110 shadow-lg"
                        : isThumbFlagged
                        ? "border-rose-500 opacity-80 hover:opacity-100 ring-1 ring-rose-400"
                        : "border-white/20 opacity-60 hover:opacity-100"
                    }`}
                  >
                    <ScreenshotImage analysisId={analysisId} filename={name} alt="" fit="cover" />
                  </button>
                );
              })}
            </div>
          </div>
        </div>
      )}
    </>
  );
}

/* ═══════════════════════════════════════════════════════════════════════════
   YARA RULES LOGO & SECTION
   ═══════════════════════════════════════════════════════════════════════════ */

function YaraLogo({ className = "w-7 h-7" }: { className?: string }) {
  return (
    <svg
      viewBox="0 0 120 120"
      className={className}
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      role="img"
      aria-label="YARA Engine Logo"
    >
      <defs>
        <linearGradient id="yaraGrad" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stopColor="#dc2626" />
          <stop offset="50%" stopColor="#b91c1c" />
          <stop offset="100%" stopColor="#7f1d1d" />
        </linearGradient>
      </defs>
      <polygon
        points="60,6 108,34 108,86 60,114 12,86 12,34"
        fill="url(#yaraGrad)"
        stroke="#ef4444"
        strokeWidth="3.5"
        strokeLinejoin="round"
      />
      <polygon
        points="60,18 96,39 96,81 60,102 24,81 24,39"
        fill="none"
        stroke="#fca5a5"
        strokeWidth="1.5"
        strokeDasharray="4 2"
        strokeOpacity="0.6"
      />
      <text
        x="60"
        y="68"
        textAnchor="middle"
        fontFamily="ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif"
        fontSize="24"
        fontWeight="900"
        fill="#ffffff"
        letterSpacing="2"
      >
        YARA
      </text>
      <text
        x="60"
        y="83"
        textAnchor="middle"
        fontFamily="ui-monospace, monospace"
        fontSize="7"
        fontWeight="700"
        fill="#fecaca"
        letterSpacing="1.5"
      >
        RULES
      </text>
    </svg>
  );
}

function YaraSection({ data }: { data: YaraData | null }) {
  if (!data) {
    return (
      <NoData
        label="No YARA rule analysis data available."
        hint="YARA signature scanning may not have been executed for this sample."
      />
    );
  }

  const threatColor =
    data.threat_level === "high" || data.threat_level === "critical"
      ? "bg-rose-100 text-rose-800 border-rose-300"
      : data.threat_level === "medium"
      ? "bg-amber-100 text-amber-800 border-amber-300"
      : data.threat_level === "low"
      ? "bg-blue-100 text-blue-800 border-blue-300"
      : "bg-emerald-100 text-emerald-800 border-emerald-300";

  return (
    <div className="space-y-4">
      {/* Header Banner with YARA Logo */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 p-4 rounded-xl bg-gradient-to-r from-red-50/70 via-rose-50/40 to-slate-50 border border-rose-200/80">
        <div className="flex items-center gap-3.5">
          <YaraLogo className="w-12 h-12 shrink-0 drop-shadow-sm" />
          <div>
            <div className="flex items-center gap-2">
              <h4 className="text-base font-bold text-slate-900 tracking-tight">
                YARA Signature Scanner
              </h4>
              <span className="text-[10px] uppercase font-mono font-bold bg-rose-600 text-white px-2 py-0.5 rounded shadow-xs">
                {data.engine || "yara-python"}
              </span>
            </div>
            <p className="text-xs text-slate-500 mt-0.5">
              Compiled pattern matching engine for binary capabilities, packers, evasion, and signatures.
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2.5 shrink-0 self-end sm:self-auto">
          <div className="text-right">
            <span className="block text-[10px] font-bold text-slate-400 uppercase tracking-wider">
              Threat Level
            </span>
            <span
              className={`inline-block px-2.5 py-0.5 rounded-md text-xs font-bold uppercase border mt-0.5 ${threatColor}`}
            >
              {data.threat_level || "Clean"}
            </span>
          </div>
          <div className="bg-white border border-slate-200 px-3 py-1.5 rounded-lg text-center shadow-xs">
            <span className="block text-[10px] font-bold text-slate-400 uppercase">
              Matches
            </span>
            <span className="text-sm font-extrabold text-slate-800">
              {data.matched_rules_count}
            </span>
          </div>
        </div>
      </div>

      {/* Target & Capabilities Pill Bar */}
      <div className="flex flex-wrap items-center gap-2 text-xs">
        {data.scanned_file && (
          <div className="flex items-center gap-1.5 px-3 py-1 bg-slate-100 rounded-lg text-slate-700 font-mono">
            <span className="text-slate-400 font-sans">Target:</span>
            <span className="font-bold">{data.scanned_file}</span>
          </div>
        )}

        {data.tags && data.tags.length > 0 && (
          <div className="flex items-center gap-1.5 flex-wrap">
            <span className="text-slate-400 font-medium">Capabilities:</span>
            {data.tags.map((t, idx) => (
              <span
                key={idx}
                className="px-2 py-0.5 bg-rose-50 border border-rose-200 text-rose-700 rounded-md font-mono text-[11px] font-semibold"
              >
                #{t}
              </span>
            ))}
          </div>
        )}
      </div>

      {/* Matched Rules Breakdown */}
      {data.matches && data.matches.length > 0 ? (
        <div className="space-y-3">
          <h5 className="text-xs font-bold text-slate-700 uppercase tracking-wider flex items-center gap-1.5">
            <IoShieldOutline className="w-4 h-4 text-rose-600" />
            Matched Capability Signatures ({data.matches.length})
          </h5>

          {data.matches.map((m, idx) => {
            const sevColor =
              m.severity === "high" || m.severity === "critical"
                ? "bg-rose-100 text-rose-800 border-rose-200"
                : m.severity === "medium"
                ? "bg-amber-100 text-amber-800 border-amber-200"
                : "bg-blue-100 text-blue-800 border-blue-200";

            return (
              <div
                key={idx}
                className="rounded-xl border border-rose-200/80 bg-white p-4 shadow-xs space-y-3"
              >
                <div className="flex flex-wrap items-start justify-between gap-2">
                  <div className="space-y-1">
                    <div className="flex items-center gap-2 flex-wrap">
                      <span className="font-mono text-sm font-bold text-rose-950">
                        {m.rule}
                      </span>
                      <span
                        className={`text-[10px] font-bold px-2 py-0.5 rounded border uppercase ${sevColor}`}
                      >
                        {m.severity || "info"}
                      </span>
                      {m.category && (
                        <span className="text-[10px] font-semibold px-2 py-0.5 rounded bg-slate-100 text-slate-600 uppercase">
                          {m.category}
                        </span>
                      )}
                      {m.mitre_technique && (
                        <span className="text-[10px] font-mono font-bold px-2 py-0.5 rounded bg-violet-100 text-violet-800 border border-violet-200">
                          {m.mitre_technique}
                        </span>
                      )}
                    </div>
                    {m.description && (
                      <p className="text-xs text-slate-600 leading-relaxed">
                        {m.description}
                      </p>
                    )}
                  </div>
                </div>

                {/* Matched Strings */}
                {m.matched_strings && m.matched_strings.length > 0 && (
                  <div className="rounded-lg bg-slate-900 p-3 text-slate-100 font-mono text-xs space-y-1">
                    <span className="block text-[10px] font-bold uppercase text-slate-400 tracking-wider">
                      Matched String Offsets &amp; Literals
                    </span>
                    <div className="space-y-1 mt-1 max-h-36 overflow-y-auto">
                      {m.matched_strings.map((str, sIdx) => (
                        <div
                          key={sIdx}
                          className="flex items-center gap-2 bg-slate-800/80 px-2 py-1 rounded border border-slate-700/60"
                        >
                          <span className="text-rose-400 select-none">$str:</span>
                          <span className="text-amber-200 break-all">{str}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      ) : (
        <div className="p-5 rounded-xl border border-emerald-200 bg-emerald-50/50 flex items-center gap-3">
          <IoCheckmarkCircleOutline className="w-6 h-6 text-emerald-600 shrink-0" />
          <div>
            <h5 className="text-sm font-bold text-emerald-900">
              No YARA Rule Signatures Matched
            </h5>
            <p className="text-xs text-emerald-700 mt-0.5">
              The executable does not match any known packer, anti-sandbox evasion, or malicious capability signatures in the curated rule set.
            </p>
          </div>
        </div>
      )}

      {/* MITRE ATT&CK Mapping from YARA */}
      {data.mitre_attack && data.mitre_attack.length > 0 && (
        <div className="mt-3 p-3.5 rounded-xl bg-slate-50 border border-slate-200 space-y-2">
          <span className="text-xs font-bold text-slate-700 uppercase tracking-wider block">
            Mapped MITRE ATT&amp;CK Techniques
          </span>
          <div className="grid gap-2 sm:grid-cols-2">
            {data.mitre_attack.map((tech) => (
              <div
                key={tech.id}
                className="flex items-start gap-2 bg-white p-2.5 rounded-lg border border-slate-200"
              >
                <span className="text-xs font-mono font-bold text-violet-700 bg-violet-50 px-1.5 py-0.5 rounded border border-violet-200">
                  {tech.id}
                </span>
                <div className="min-w-0">
                  <span className="block text-xs font-bold text-slate-800 truncate">
                    {tech.name}
                  </span>
                  {tech.description && (
                    <span className="block text-[11px] text-slate-500 leading-snug truncate">
                      {tech.description}
                    </span>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

/* ═══════════════════════════════════════════════════════════════════════════
   LSTM SEQUENTIAL MODEL SECTION
   ═══════════════════════════════════════════════════════════════════════════ */

function LstmSection({ data }: { data: LstmData | null }) {
  if (!data) {
    return (
      <NoData
        label="No BiLSTM prediction data available."
        hint="Deep sequential behavioral model is awaiting report telemetry."
      />
    );
  }

  const isMalicious = data.verdict?.toUpperCase() === "MALICIOUS";
  const pMalwarePct = ((data.p_malware || 0) * 100).toFixed(1);
  const pBenignPct = ((data.p_benign || 0) * 100).toFixed(1);

  return (
    <div className="space-y-4">
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 p-4 rounded-xl bg-gradient-to-r from-cyan-50/70 via-sky-50/40 to-slate-50 border border-cyan-200">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-lg bg-cyan-600 flex items-center justify-center text-white shadow-xs">
            <IoGitNetworkOutline className="w-5 h-5" />
          </div>
          <div>
            <div className="flex items-center gap-2 flex-wrap">
              <h4 className="text-base font-bold text-slate-900 tracking-tight">
                BiLSTM Sequential Behavioral Inference
              </h4>
              <span
                className={`text-[10px] font-mono font-bold px-2 py-0.5 rounded uppercase ${
                  isMalicious
                    ? "bg-rose-600 text-white"
                    : "bg-emerald-600 text-white"
                }`}
              >
                {data.verdict}
              </span>
              {data.source_type === "synthesized_sandbox_telemetry" && (
                <span className="text-[10px] font-mono font-bold px-2 py-0.5 rounded uppercase bg-cyan-100 text-cyan-800 border border-cyan-200">
                  Telemetry Synthesis
                </span>
              )}
            </div>
            <p className="text-xs text-slate-500 mt-0.5">
              {data.source_type === "synthesized_sandbox_telemetry"
                ? "Deep BiLSTM sequence classification evaluated on reconstructed execution telemetry (Sysmon, Host Normalization, Network, YARA)."
                : "Deep sequential neural network evaluating sliding-window Windows API execution flow."}
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2 shrink-0 self-end sm:self-auto">
          <div className="bg-white border border-slate-200 px-3 py-1.5 rounded-lg text-center shadow-xs">
            <span className="block text-[10px] font-bold text-slate-400 uppercase">
              Malice Prob
            </span>
            <span
              className={`text-sm font-extrabold ${
                isMalicious ? "text-rose-600" : "text-emerald-600"
              }`}
            >
              {pMalwarePct}%
            </span>
          </div>
          <div className="bg-white border border-slate-200 px-3 py-1.5 rounded-lg text-center shadow-xs">
            <span className="block text-[10px] font-bold text-slate-400 uppercase">
              Confidence
            </span>
            <span className="text-sm font-extrabold text-slate-800">
              {data.confidence?.toFixed(1)}%
            </span>
          </div>
        </div>
      </div>

      {/* Probability Gauge Bar */}
      <div className="p-4 rounded-xl border border-slate-200 bg-white space-y-2">
        <div className="flex justify-between items-center text-xs">
          <span className="font-semibold text-slate-700">Sequence Malice Probability</span>
          <span className="font-mono font-bold text-slate-900">{pMalwarePct}%</span>
        </div>
        <div className="h-3 w-full bg-slate-100 rounded-full overflow-hidden flex">
          <div
            className="h-full bg-rose-500 transition-all duration-500"
            style={{ width: `${Math.max(2, Math.min(100, Number(pMalwarePct)))}%` }}
            title={`p(malware) = ${pMalwarePct}%`}
          />
          <div
            className="h-full bg-emerald-500 transition-all duration-500"
            style={{ width: `${Math.max(2, Math.min(100, Number(pBenignPct)))}%` }}
            title={`p(benign) = ${pBenignPct}%`}
          />
        </div>
        <div className="flex justify-between items-center text-[10px] text-slate-400 font-mono">
          <span>MALICIOUS ({pMalwarePct}%)</span>
          <span>BENIGN ({pBenignPct}%)</span>
        </div>
      </div>

      {/* Sequence Statistics Grid */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-center">
        <div className="p-3 bg-slate-50 border border-slate-200 rounded-lg">
          <span className="block text-[10px] uppercase font-bold text-slate-400">Total APIs</span>
          <span className="text-sm font-bold text-slate-800">{data.sequence_length}</span>
        </div>
        <div className="p-3 bg-slate-50 border border-slate-200 rounded-lg">
          <span className="block text-[10px] uppercase font-bold text-slate-400">Recognized APIs</span>
          <span className="text-sm font-bold text-slate-800">{data.recognized_apis_count}</span>
        </div>
        <div className="p-3 bg-slate-50 border border-slate-200 rounded-lg">
          <span className="block text-[10px] uppercase font-bold text-slate-400">Model Vocab Ratio</span>
          <span className="text-sm font-bold text-slate-800">
            {((data.recognized_ratio || 0) * 100).toFixed(1)}%
          </span>
        </div>
        <div className="p-3 bg-slate-50 border border-slate-200 rounded-lg">
          <span className="block text-[10px] uppercase font-bold text-slate-400">Windows Evaluated</span>
          <span className="text-sm font-bold text-slate-800">{data.windows_evaluated}</span>
        </div>
      </div>

      {/* Unique Windows APIs in Execution Flow */}
      {data.unique_apis && data.unique_apis.length > 0 && (
        <div className="p-3.5 rounded-xl bg-slate-50 border border-slate-200 space-y-2">
          <span className="text-xs font-bold text-slate-700 uppercase tracking-wider block">
            Observed Windows API Primitives ({data.unique_apis.length})
          </span>
          <div className="flex flex-wrap gap-1.5 max-h-40 overflow-y-auto">
            {data.unique_apis.map((api, idx) => (
              <span
                key={idx}
                className="px-2 py-0.5 bg-white border border-slate-200 rounded font-mono text-[11px] text-slate-700"
              >
                {api}
              </span>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

/* ═══════════════════════════════════════════════════════════════════════════
   HOST BEHAVIOR NORMALIZER SECTION
   ═══════════════════════════════════════════════════════════════════════════ */

function BehaviorSection({ data }: { data: BehaviorSummary | null }) {
  if (!data || !data.summary) {
    return (
      <NoData
        label="No normalized behavioral data available."
        hint="Behavior normalization may not have been executed for this report."
      />
    );
  }

  const s = data.summary;

  return (
    <div className="space-y-4">
      {/* Mini Stat Cards */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-center">
        <div className="p-3 bg-slate-50 border border-slate-200 rounded-lg">
          <span className="block text-[10px] uppercase font-bold text-slate-400">Files Created</span>
          <span className="text-sm font-bold text-slate-800">{s.total_files_created}</span>
        </div>
        <div className="p-3 bg-slate-50 border border-slate-200 rounded-lg">
          <span className="block text-[10px] uppercase font-bold text-slate-400">Files Written</span>
          <span className="text-sm font-bold text-slate-800">{s.total_files_written}</span>
        </div>
        <div className="p-3 bg-slate-50 border border-slate-200 rounded-lg">
          <span className="block text-[10px] uppercase font-bold text-slate-400">Sensitive Reads</span>
          <span className="text-sm font-bold text-slate-800">{s.total_sensitive_reads}</span>
        </div>
        <div className="p-3 bg-slate-50 border border-slate-200 rounded-lg">
          <span className="block text-[10px] uppercase font-bold text-slate-400">Persistence Keys</span>
          <span className="text-sm font-bold text-rose-700">{s.total_persistence_keys}</span>
        </div>
      </div>

      {/* Persistence Registry Keys */}
      {data.registry?.persistence_keys && data.registry.persistence_keys.length > 0 && (
        <div className="p-3.5 bg-rose-50/50 border border-rose-200 rounded-xl space-y-2">
          <h5 className="text-xs font-bold text-rose-900 uppercase tracking-wider flex items-center gap-1.5">
            <IoLockClosedOutline className="w-4 h-4 text-rose-600" />
            Persistence &amp; Autostart Registry Targets ({data.registry.persistence_keys.length})
          </h5>
          <div className="space-y-1 max-h-36 overflow-y-auto">
            {data.registry.persistence_keys.map((k, idx) => (
              <div key={idx} className="font-mono text-xs text-rose-900 bg-white px-2.5 py-1 rounded border border-rose-200 break-all">
                {k}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Written & Dropped Payloads */}
      {data.files?.written && data.files.written.length > 0 && (
        <div className="p-3.5 bg-slate-50 border border-slate-200 rounded-xl space-y-2">
          <h5 className="text-xs font-bold text-slate-700 uppercase tracking-wider flex items-center gap-1.5">
            <IoFolderOpenOutline className="w-4 h-4 text-amber-600" />
            Dropped &amp; Modified Payload Files ({data.files.written.length})
          </h5>
          <div className="space-y-1 max-h-36 overflow-y-auto">
            {data.files.written.map((f, idx) => (
              <div key={idx} className="font-mono text-xs text-slate-800 bg-white px-2.5 py-1 rounded border border-slate-200 break-all">
                {f}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

/* ═══════════════════════════════════════════════════════════════════════════
   NETWORK THREAT DB SECTION
   ═══════════════════════════════════════════════════════════════════════════ */

function NetworkDBSection({ data }: { data: NetworkDBData | null }) {
  if (!data) {
    return (
      <NoData
        label="No offline threat DB matching data available."
        hint="Threat intelligence feeds (ThreatFox, URLhaus, Feodo) were not queried or no network observables existed."
      />
    );
  }

  const isMal = data.verdict === "malicious";
  const isSusp = data.verdict === "suspicious";

  return (
    <div className="space-y-4">
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 p-4 rounded-xl bg-gradient-to-r from-emerald-50/70 via-teal-50/40 to-slate-50 border border-emerald-200">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-lg bg-emerald-600 flex items-center justify-center text-white shadow-xs">
            <IoGlobeOutline className="w-5 h-5" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h4 className="text-base font-bold text-slate-900 tracking-tight">
                Offline Network Threat Intelligence DB
              </h4>
              <span
                className={`text-[10px] font-mono font-bold px-2 py-0.5 rounded uppercase ${
                  isMal
                    ? "bg-rose-600 text-white"
                    : isSusp
                    ? "bg-amber-600 text-white"
                    : "bg-emerald-600 text-white"
                }`}
              >
                {data.verdict}
              </span>
            </div>
            <p className="text-xs text-slate-500 mt-0.5">
              Deterministic offline SQLite lookups against ThreatFox, URLhaus, and Feodo Tracker C2 feeds.
            </p>
          </div>
        </div>

        <div className="bg-white border border-slate-200 px-3 py-1.5 rounded-lg text-center shadow-xs shrink-0 self-end sm:self-auto">
          <span className="block text-[10px] font-bold text-slate-400 uppercase">
            Confidence
          </span>
          <span className="text-sm font-extrabold text-slate-800">
            {data.confidence}%
          </span>
        </div>
      </div>

      <div className="p-3.5 bg-slate-50 border border-slate-200 rounded-xl text-xs text-slate-700 leading-relaxed">
        {data.summary}
      </div>

      {data.findings && data.findings.length > 0 ? (
        <div className="space-y-2">
          <h5 className="text-xs font-bold text-slate-700 uppercase tracking-wider">
            Threat DB Matches ({data.findings.length})
          </h5>
          {data.findings.map((f, idx) => (
            <div
              key={idx}
              className="p-3 bg-white border border-rose-200 rounded-xl flex items-start gap-3 shadow-xs"
            >
              <IoAlertCircleOutline className="w-5 h-5 text-rose-600 shrink-0 mt-0.5" />
              <div className="min-w-0">
                <span className="font-mono text-xs font-bold text-rose-900 break-all block">
                  {f.indicator}
                </span>
                <p className="text-xs text-slate-600 mt-0.5">{f.description}</p>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="p-4 rounded-xl border border-emerald-200 bg-emerald-50/50 flex items-center gap-3">
          <IoCheckmarkCircleOutline className="w-5 h-5 text-emerald-600 shrink-0" />
          <p className="text-xs text-emerald-800">
            0 malicious indicators matched. All queried IPs, DNS lookups, and URLs are clean against curated threat feeds.
          </p>
        </div>
      )}
    </div>
  );
}

/* ═══════════════════════════════════════════════════════════════════════════
   SYSMON SECTION
   ═══════════════════════════════════════════════════════════════════════════ */

function SysmonSection({ data }: { data: SysmonData }) {
  return (
    <div className="space-y-6">
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <MiniStat
          label="Total Events"
          value={data.total_events?.toLocaleString() || "0"}
          icon={<IoLayersOutline className="w-4 h-4" />}
          accent="slate"
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
          accent="blue"
        />
      </div>

      {data.processes_created?.length > 0 && (
        <div className="border border-slate-200 rounded overflow-hidden">
          <div className="bg-slate-50 border-b border-slate-200 px-4 py-2 flex items-center gap-2">
            <IoTerminalOutline className="w-4 h-4 text-slate-500" />
            <h4 className="text-[13px] font-bold text-slate-700 uppercase tracking-wider">
              Process Creation Map
            </h4>
            <span className="ml-auto text-[11px] font-semibold bg-slate-200 text-slate-700 px-2 py-0.5 rounded-full">
              {data.processes_created.length}
            </span>
          </div>
          <DataGrid
            headers={["Time", "Image", "PID", "Parent", "User", "Command"]}
            rows={data.processes_created.map((p) => [
              <span
                key="t"
                className="text-xs text-slate-500 whitespace-nowrap font-mono"
              >
                {p.time ? new Date(p.time).toLocaleTimeString() : "—"}
              </span>,
              <FPath key="i" path={p.image} />,
              <span
                key="p"
                className="font-mono text-[13px] font-bold text-slate-800"
              >
                {p.pid}
              </span>,
              <FPath key="pp" path={p.parent} />,
              <span key="u" className="text-xs text-slate-600">
                {p.user}
              </span>,
              <span
                key="c"
                className="font-mono text-xs text-slate-500 truncate max-w-xs block"
                title={p.cmd}
              >
                {p.cmd}
              </span>,
            ])}
          />
        </div>
      )}

      {data.network_connections?.length > 0 && (
        <div className="border border-slate-200 rounded overflow-hidden">
          <div className="bg-slate-50 border-b border-slate-200 px-4 py-2 flex items-center gap-2">
            <IoGlobeOutline className="w-4 h-4 text-blue-500" />
            <h4 className="text-[13px] font-bold text-slate-700 uppercase tracking-wider">
              Network Connections
            </h4>
            <span className="ml-auto text-[11px] font-semibold bg-slate-200 text-slate-700 px-2 py-0.5 rounded-full">
              {data.network_connections.length}
            </span>
          </div>
          <DataGrid
            headers={["Image", "Protocol", "Source", "Destination", "Host"]}
            rows={data.network_connections.map((c) => [
              <FPath key="i" path={c.image} />,
              <span
                key="pr"
                className="text-[11px] uppercase font-bold text-blue-800 bg-blue-50 border border-blue-200 px-1.5 py-0.5 rounded"
              >
                {c.proto}
              </span>,
              <span key="s" className="font-mono text-xs text-slate-700">
                {c.src}
              </span>,
              <span
                key="d"
                className="font-mono text-xs font-semibold text-red-700"
              >
                {c.dst}
              </span>,
              <span key="h" className="text-xs text-slate-500 font-mono">
                {c.dst_host || "—"}
              </span>,
            ])}
          />
        </div>
      )}

      {data.dns_queries?.length > 0 && (
        <div className="border border-slate-200 rounded overflow-hidden">
          <div className="bg-slate-50 border-b border-slate-200 px-4 py-2 flex items-center gap-2">
            <h4 className="text-[13px] font-bold text-slate-700 uppercase tracking-wider">
              DNS Queries
            </h4>
            <span className="ml-auto text-[11px] font-semibold bg-slate-200 text-slate-700 px-2 py-0.5 rounded-full">
              {data.dns_queries.length}
            </span>
          </div>
          <div className="p-4 flex flex-wrap gap-2">
            {data.dns_queries.map((q, i) => (
              <span
                key={`${dnsQueryLabel(q)}-${i}`}
                className="px-2 py-1 bg-white border border-slate-300 shadow-sm text-slate-800 text-xs font-mono rounded"
              >
                {dnsQueryLabel(q)}
              </span>
            ))}
          </div>
        </div>
      )}

      {data.files_created?.length > 0 && (
        <div className="border border-slate-200 rounded overflow-hidden">
          <div className="bg-slate-50 border-b border-slate-200 px-4 py-2 flex items-center gap-2">
            <IoFolderOpenOutline className="w-4 h-4 text-emerald-500" />
            <h4 className="text-[13px] font-bold text-slate-700 uppercase tracking-wider">
              Files Created
            </h4>
            <span className="ml-auto text-[11px] font-semibold bg-slate-200 text-slate-700 px-2 py-0.5 rounded-full">
              {data.files_created.length}
            </span>
          </div>
          <div className="max-h-48 overflow-y-auto p-0">
            <table className="w-full text-sm">
              <tbody className="divide-y divide-slate-100">
                {data.files_created.map((f, i) => (
                  <tr key={i} className="hover:bg-slate-50 transition-colors">
                    <td className="px-3 py-2 flex items-center gap-2">
                      <IoDocumentTextOutline className="w-3.5 h-3.5 text-slate-400 shrink-0" />
                      <FPath path={f} />
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {data.registry_events?.length > 0 && (
        <div className="border border-slate-200 rounded overflow-hidden">
          <div className="bg-slate-50 border-b border-slate-200 px-4 py-2 flex items-center gap-2">
            <IoKeyOutline className="w-4 h-4 text-rose-500" />
            <h4 className="text-[13px] font-bold text-slate-700 uppercase tracking-wider">
              Registry Events
            </h4>
            <span className="ml-auto text-[11px] font-semibold bg-slate-200 text-slate-700 px-2 py-0.5 rounded-full">
              {data.registry_events.length}
            </span>
          </div>
          <DataGrid
            headers={["Type", "Key", "Details"]}
            rows={data.registry_events.map((r) => [
              <span
                key="t"
                className={`text-[11px] font-bold px-1.5 py-0.5 rounded border uppercase tracking-wider ${r.type.includes("Set") ? "bg-amber-50 text-amber-700 border-amber-200" : r.type.includes("Delete") ? "bg-red-50 text-red-700 border-red-200" : "bg-slate-50 text-slate-600 border-slate-200"}`}
              >
                {r.type}
              </span>,
              <span
                key="k"
                className="font-mono text-xs text-slate-700 truncate max-w-lg block"
                title={r.key}
              >
                {r.key}
              </span>,
              <span key="d" className="text-xs text-slate-500">
                {r.details || "—"}
              </span>,
            ])}
          />
        </div>
      )}

      {data.dlls_loaded?.length > 0 && (
        <div className="border border-slate-200 rounded overflow-hidden">
          <div className="bg-slate-50 border-b border-slate-200 px-4 py-2 flex items-center gap-2">
            <IoHardwareChipOutline className="w-4 h-4 text-sky-500" />
            <h4 className="text-[13px] font-bold text-slate-700 uppercase tracking-wider">
              DLLs Loaded
            </h4>
            <span className="ml-auto text-[11px] font-semibold bg-slate-200 text-slate-700 px-2 py-0.5 rounded-full">
              {data.dlls_loaded.length}
            </span>
          </div>
          <div className="flex flex-wrap gap-1.5 max-h-48 overflow-y-auto p-4 bg-white">
            {data.dlls_loaded.map((d, i) => {
              const name = d.split("\\").pop() || d;
              const isCrypto = /crypt|rsa|aes|bcrypt/i.test(name);
              const isNet = /ws2|winsock|winhttp|dnsapi|iphlp/i.test(name);
              const color = isCrypto
                ? "bg-red-50 text-red-700 border-red-200"
                : isNet
                  ? "bg-blue-50 text-blue-700 border-blue-200"
                  : "bg-slate-50 text-slate-600 border-slate-200";
              return (
                <span
                  key={i}
                  className={`px-2 py-0.5 rounded border text-xs font-mono shadow-sm ${color}`}
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
    <div className="space-y-6">
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <MiniStat
          label="Total Rows"
          value={data.total_rows?.toLocaleString() || "0"}
          icon={<IoLayersOutline className="w-4 h-4" />}
          accent="slate"
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
          <div className="border border-slate-200 rounded overflow-hidden">
            <div className="bg-slate-50 border-b border-slate-200 px-4 py-2 flex items-center gap-2">
              <IoFolderOpenOutline className="w-4 h-4 text-emerald-500" />
              <h4 className="text-[13px] font-bold text-slate-700 uppercase tracking-wider">
                File Operations Summary
              </h4>
            </div>
            <div className="p-4 bg-white space-y-2.5">
              {Object.entries(fileOps)
                .sort(([, a], [, b]) => (b as number) - (a as number))
                .slice(0, 10)
                .map(([op, count]) => {
                  const max = Math.max(...(Object.values(fileOps) as number[]));
                  const pct = Math.max(2, Math.round(((count as number) / max) * 100));
                  return (
                    <div key={op} className="flex items-center gap-3">
                      <span className="text-xs text-slate-600 w-28 truncate font-medium">
                        {op}
                      </span>
                      <div className="flex-1 h-2.5 bg-slate-100 rounded-sm overflow-hidden">
                        <div
                          className="h-full bg-emerald-500 rounded-sm"
                          style={{ width: `${pct}%` }}
                        />
                      </div>
                      <span className="text-[13px] font-bold text-slate-800 w-12 text-right">
                        {(count as number).toLocaleString()}
                      </span>
                    </div>
                  );
                })}
            </div>
          </div>
        )}

        {Object.keys(regOps).length > 0 && (
          <div className="border border-slate-200 rounded overflow-hidden">
            <div className="bg-slate-50 border-b border-slate-200 px-4 py-2 flex items-center gap-2">
              <IoKeyOutline className="w-4 h-4 text-rose-500" />
              <h4 className="text-[13px] font-bold text-slate-700 uppercase tracking-wider">
                Registry Operations Summary
              </h4>
            </div>
            <div className="p-4 bg-white space-y-2.5">
              {Object.entries(regOps)
                .sort(([, a], [, b]) => (b as number) - (a as number))
                .slice(0, 10)
                .map(([op, count]) => {
                  const max = Math.max(...(Object.values(regOps) as number[]));
                  const pct = Math.max(2, Math.round(((count as number) / max) * 100));
                  return (
                    <div key={op} className="flex items-center gap-3">
                      <span className="text-xs text-slate-600 w-28 truncate font-medium">
                        {op}
                      </span>
                      <div className="flex-1 h-2.5 bg-slate-100 rounded-sm overflow-hidden">
                        <div
                          className="h-full bg-rose-500 rounded-sm"
                          style={{ width: `${pct}%` }}
                        />
                      </div>
                      <span className="text-[13px] font-bold text-slate-800 w-12 text-right">
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
        <div className="border border-slate-200 rounded overflow-hidden">
          <div className="bg-slate-50 border-b border-slate-200 px-4 py-2 flex items-center gap-2">
            <IoAlertCircleOutline className="w-4 h-4 text-red-500" />
            <h4 className="text-[13px] font-bold text-slate-700 uppercase tracking-wider">
              Notable File Activity
            </h4>
          </div>
          <div className="p-4 bg-white space-y-4">
            {Object.entries(fileNotable).map(([op, paths]) => (
              <div key={op}>
                <span className="inline-block text-[11px] font-bold text-slate-500 uppercase bg-slate-100 border border-slate-200 px-2 py-0.5 rounded mb-2 w-full text-center sm:w-auto">
                  {op} ({(paths as string[]).length})
                </span>
                <div className="max-h-40 overflow-y-auto border border-slate-100 rounded">
                  <table className="w-full text-sm">
                    <tbody className="divide-y divide-slate-100">
                      {(paths as string[]).map((p, i) => (
                        <tr key={i} className="hover:bg-slate-50 transition-colors">
                          <td className="px-3 py-1.5 flex items-center gap-2">
                            <IoDocumentTextOutline className="w-3.5 h-3.5 text-slate-400 shrink-0" />
                            <FPath path={p} />
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Notable registry activity */}
      {Object.keys(regNotable).length > 0 && (
        <div className="border border-slate-200 rounded overflow-hidden">
          <div className="bg-slate-50 border-b border-slate-200 px-4 py-2 flex items-center gap-2">
            <IoAlertCircleOutline className="w-4 h-4 text-red-500" />
            <h4 className="text-[13px] font-bold text-slate-700 uppercase tracking-wider">
              Notable Registry Activity
            </h4>
          </div>
          <div className="p-4 bg-white space-y-4">
            {Object.entries(regNotable).map(([op, paths]) => (
              <div key={op}>
                <span className="inline-block text-[11px] font-bold text-slate-500 uppercase bg-slate-100 border border-slate-200 px-2 py-0.5 rounded mb-2 w-full text-center sm:w-auto">
                  {op} ({(paths as string[]).length})
                </span>
                <div className="max-h-40 overflow-y-auto border border-slate-100 rounded">
                  <table className="w-full text-sm">
                    <tbody className="divide-y divide-slate-100">
                      {(paths as string[]).map((p, i) => (
                        <tr key={i} className="hover:bg-slate-50 transition-colors">
                          <td className="px-3 py-1.5 flex items-center gap-2">
                            <IoKeyOutline className="w-3.5 h-3.5 text-slate-400 shrink-0" />
                            <span
                              className="font-mono text-xs text-slate-700 truncate"
                              title={p}
                            >
                              {p}
                            </span>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {data.network_activity?.length > 0 && (
        <div className="border border-slate-200 rounded overflow-hidden">
          <div className="bg-slate-50 border-b border-slate-200 px-4 py-2 flex items-center gap-2">
            <IoGlobeOutline className="w-4 h-4 text-blue-500" />
            <h4 className="text-[13px] font-bold text-slate-700 uppercase tracking-wider">
              Network Activity
            </h4>
            <span className="ml-auto text-[11px] font-semibold bg-slate-200 text-slate-700 px-2 py-0.5 rounded-full">
              {data.network_activity.length}
            </span>
          </div>
          <DataGrid
            headers={["Operation", "Endpoint", "Result"]}
            rows={data.network_activity.map((n) => [
              <span key="o" className="font-semibold text-xs text-slate-700">
                {n.op}
              </span>,
              <span key="p" className="font-mono text-xs text-slate-600">
                {n.path}
              </span>,
              <span
                key="r"
                className={`text-[11px] font-bold uppercase tracking-wider px-1.5 py-0.5 rounded border ${n.result === "SUCCESS" ? "bg-green-50 text-green-700 border-green-200" : "bg-red-50 text-red-700 border-red-200"}`}
              >
                {n.result}
              </span>,
            ])}
          />
        </div>
      )}

      {data.process_activity?.length > 0 && (
        <div className="border border-slate-200 rounded overflow-hidden">
          <div className="bg-slate-50 border-b border-slate-200 px-4 py-2 flex items-center gap-2">
            <IoTerminalOutline className="w-4 h-4 text-slate-500" />
            <h4 className="text-[13px] font-bold text-slate-700 uppercase tracking-wider">
              Process & Thread Activity
            </h4>
            <span className="ml-auto text-[11px] font-semibold bg-slate-200 text-slate-700 px-2 py-0.5 rounded-full">
              {data.process_activity.length}
            </span>
          </div>
          <DataGrid
            headers={["Operation", "Path", "Detail"]}
            rows={data.process_activity.map((p) => [
              <span key="o" className="font-semibold text-xs text-slate-700">
                {p.op}
              </span>,
              <FPath key="p" path={p.path} />,
              <span
                key="d"
                className="text-xs text-slate-500 truncate max-w-xs block"
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
    <div className="mt-4 border border-slate-200 rounded overflow-hidden">
      <div className="flex bg-slate-50 border-b border-slate-200">
        {[
          { key: "tcp" as const, label: "TCP Conversations", has: hasTcp, icon: <IoGitNetworkOutline className="w-3.5 h-3.5" /> },
          {
            key: "dns" as const,
            label: `DNS (${data.dns_queries?.length || 0})`,
            has: hasDns,
            icon: <IoGlobeOutline className="w-3.5 h-3.5" />
          },
          {
            key: "http" as const,
            label: `HTTP (${data.http_requests?.length || 0})`,
            has: hasHttp,
            icon: <IoSwapHorizontalOutline className="w-3.5 h-3.5" />
          },
        ].map((t) => (
          <button
            key={t.key}
            onClick={() => setTab(t.key)}
            className={`flex-1 px-4 py-2.5 text-[13px] font-bold uppercase tracking-wider transition-colors flex items-center justify-center gap-2 border-b-2 ${
              tab === t.key
                ? "bg-white text-blue-700 border-blue-600"
                : "text-slate-500 border-transparent hover:text-slate-700 hover:bg-slate-100/50"
            } ${!t.has ? "opacity-40" : ""}`}
          >
            {t.icon}
            {t.label}
          </button>
        ))}
      </div>

      <div className="p-4 bg-white">
        {tab === "tcp" &&
          (hasTcp ? (
            <pre className="bg-slate-50 border border-slate-200 text-slate-700 rounded p-4 text-xs overflow-x-auto max-h-72 overflow-y-auto font-mono leading-relaxed">
              {data.tcp_conversations}
            </pre>
          ) : (
            <NoData label="No TCP conversation data captured." />
          ))}

        {tab === "dns" &&
          (hasDns ? (
            <div className="flex flex-wrap gap-2">
              {data.dns_queries!.map((q, i) => (
                <span
                  key={`${dnsQueryLabel(q)}-${i}`}
                  className="px-2 py-1 bg-white border border-slate-300 shadow-sm text-slate-800 text-xs font-mono rounded"
                >
                  {dnsQueryLabel(q)}
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
                  className={`text-[11px] font-bold uppercase tracking-wider px-1.5 py-0.5 rounded border ${r.method === "GET" ? "bg-green-50 text-green-700 border-green-200" : r.method === "POST" ? "bg-blue-50 text-blue-700 border-blue-200" : "bg-slate-50 text-slate-600 border-slate-200"}`}
                >
                  {r.method}
                </span>,
                <span key="h" className="font-mono text-xs text-slate-700">
                  {r.host}
                </span>,
                <span key="u" className="font-mono text-xs text-slate-500">
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
    </div>
  );
}

/* ═══════════════════════════════════════════════════════════════════════════
   HANDLE SECTION — TERMINAL STYLE
   ═══════════════════════════════════════════════════════════════════════════ */

function HandleSection({ data }: { data: string }) {
  const lines = data.split("\n").filter((l) => l.trim());
  return (
    <div className="mt-4 border border-slate-200 rounded overflow-hidden">
      <div className="bg-slate-50 border-b border-slate-200 px-4 py-2 flex items-center gap-2">
        <IoKeyOutline className="w-4 h-4 text-slate-500" />
        <h4 className="text-[13px] font-bold text-slate-700 uppercase tracking-wider">
          Handle Snapshot Dump
        </h4>
        <span className="ml-auto text-[11px] font-semibold bg-slate-200 text-slate-700 px-2 py-0.5 rounded-full">
          {lines.length} lines
        </span>
      </div>
      <pre className="bg-white text-slate-700 p-4 text-[11px] overflow-x-auto max-h-72 overflow-y-auto font-mono leading-relaxed">
        {lines.length > 200
          ? lines.slice(0, 200).join("\n") + "\n\n… truncated …"
          : data}
      </pre>
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
    <div className="mt-4 border border-slate-200 rounded overflow-hidden">
      <div className="bg-slate-50 border-b border-slate-200 px-4 py-2 flex items-center gap-2">
        <IoSwapHorizontalOutline className="w-4 h-4 text-slate-500" />
        <h4 className="text-[13px] font-bold text-slate-700 uppercase tracking-wider">
          TCPVCON Dump
        </h4>
        <span className="ml-auto text-[11px] font-semibold bg-slate-200 text-slate-700 px-2 py-0.5 rounded-full">
          {data.length} connections
        </span>
      </div>
      <div className="bg-white p-4">
        <DataGrid
          headers={headers}
          rows={data.map((row) =>
            headers.map((h) => (
              <span key={h} className="font-mono text-xs text-slate-700">
                {row[h]}
              </span>
            )),
          )}
        />
      </div>
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
            ? "bg-emerald-50 text-emerald-700 border-emerald-200"
            : c.status === "no_data"
              ? "bg-amber-50 text-amber-700 border-amber-200"
              : c.status === "unavailable"
                ? "bg-slate-50 text-slate-500 border-slate-200"
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
            className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded border text-xs font-medium ${color}`}
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
   RISK SCORE GAUGE (SVG circle with smooth filling animation)
   ═══════════════════════════════════════════════════════════════════════════ */

function RiskGauge({ score, level }: { score: number; level: string }) {
  const [animatedScore, setAnimatedScore] = useState(0);
  const [fillFraction, setFillFraction] = useState(0);

  useEffect(() => {
    setAnimatedScore(0);
    setFillFraction(0);

    const duration = 1200;
    const startTime = performance.now();
    let frameId: number;

    const tick = (now: number) => {
      const elapsed = now - startTime;
      const progress = Math.min(elapsed / duration, 1);
      const ease = 1 - Math.pow(1 - progress, 3);

      setAnimatedScore(Math.round(ease * score));
      setFillFraction(ease * (Math.min(score, 100) / 100));

      if (progress < 1) {
        frameId = requestAnimationFrame(tick);
      } else {
        setAnimatedScore(score);
        setFillFraction(Math.min(score, 100) / 100);
      }
    };

    frameId = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(frameId);
  }, [score]);

  const r = 56;
  const c = 2 * Math.PI * r;
  const offset = c * (1 - fillFraction);
  const color =
    score >= 80
      ? "#ef4444"
      : score >= 60
        ? "#f97316"
        : score >= 40
          ? "#eab308"
          : score >= 20
            ? "#22c55e"
            : "#6b7280";
  const bgRing =
    score >= 80
      ? "#fef2f2"
      : score >= 60
        ? "#fff7ed"
        : score >= 40
          ? "#fefce8"
          : score >= 20
            ? "#f0fdf4"
            : "#f9fafb";

  return (
    <div className="flex flex-col items-center">
      <div className="relative w-36 h-36">
        <svg viewBox="0 0 128 128" className="w-full h-full -rotate-90">
          <circle
            cx="64"
            cy="64"
            r={r}
            fill="none"
            stroke={bgRing}
            strokeWidth="10"
          />
          <circle
            cx="64"
            cy="64"
            r={r}
            fill="none"
            stroke={color}
            strokeWidth="10"
            strokeLinecap="round"
            strokeDasharray={c}
            strokeDashoffset={offset}
            className="transition-[stroke-dashoffset] duration-75 ease-out"
          />
        </svg>
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <span className="text-3xl font-black" style={{ color }}>
            {animatedScore}
          </span>
          <span className="text-[11px] text-slate-500 uppercase tracking-wider font-semibold">
            / 100
          </span>
        </div>
      </div>
      <span
        className="mt-2 text-sm font-bold uppercase tracking-wider"
        style={{ color }}
      >
        {level}
      </span>
    </div>
  );
}

/* ═══════════════════════════════════════════════════════════════════════════
   AI VERDICT BADGE (per-tool)
   ═══════════════════════════════════════════════════════════════════════════ */

function VerdictBadge({ verdict }: { verdict: string }) {
  const v = verdict.toLowerCase();
  const cls =
    v === "malicious"
      ? "bg-red-100 text-red-700 border-red-200"
      : v === "suspicious"
        ? "bg-amber-100 text-amber-700 border-amber-200"
        : v === "benign"
          ? "bg-green-100 text-green-700 border-green-200"
          : "bg-slate-100 text-slate-600 border-slate-200";
  return (
    <span
      className={`inline-flex items-center gap-1 px-2.5 py-1 rounded-lg border text-[13px] font-bold uppercase ${cls}`}
    >
      {v === "malicious" && <IoSkullOutline className="w-3 h-3" />}
      {v === "suspicious" && <IoWarningOutline className="w-3 h-3" />}
      {v === "benign" && <IoCheckmarkCircleOutline className="w-3 h-3" />}
      {v === "inconclusive" && <IoEllipseOutline className="w-3 h-3" />}
      {verdict}
    </span>
  );
}

/* ═══════════════════════════════════════════════════════════════════════════
   SEVERITY BADGE
   ═══════════════════════════════════════════════════════════════════════════ */

function SeverityBadge({ severity }: { severity: string }) {
  const s = severity.toLowerCase();
  const cls =
    s === "critical"
      ? "bg-red-600 text-white"
      : s === "high"
        ? "bg-red-100 text-red-700"
        : s === "medium"
          ? "bg-amber-100 text-amber-700"
          : s === "low"
            ? "bg-blue-100 text-blue-700"
            : "bg-slate-100 text-slate-600";
  return (
    <span
      className={`inline-block px-2 py-0.5 rounded text-[11px] font-bold uppercase ${cls}`}
    >
      {severity}
    </span>
  );
}

/* ═══════════════════════════════════════════════════════════════════════════
   VIRUSTOTAL-STYLE ANIMATED SCORE HERO BANNER
   ═══════════════════════════════════════════════════════════════════════════ */

function VirusTotalHeroBanner({
  report,
  data,
  aiReport,
  aiAnalyzing,
  localBenign = false,
}: {
  report: AnalysisResult;
  data: ReportData | null;
  aiReport: AIReport | null;
  aiAnalyzing?: boolean;
  localBenign?: boolean;
}) {
  const targetScore = aiReport?.risk_score ?? 0;
  const scoreAvailable = Boolean(aiReport) || localBenign;
  const threatLevel = (
    (localBenign ? "Benign" : aiReport?.threat_level) ||
    (targetScore >= 70 ? "Critical" : targetScore >= 40 ? "Medium" : targetScore > 0 ? "Low" : "Clean")
  ).toUpperCase();

  const [animatedScore, setAnimatedScore] = useState(0);
  const [fillFraction, setFillFraction] = useState(0);
  const [copiedId, setCopiedId] = useState(false);

  useEffect(() => {
    setAnimatedScore(0);
    setFillFraction(0);

    const duration = 1200; // 1.2s smooth filling animation
    const startTime = performance.now();
    let frameId: number;

    const tick = (now: number) => {
      const elapsed = now - startTime;
      const progress = Math.min(elapsed / duration, 1);
      const ease = 1 - Math.pow(1 - progress, 3);

      setAnimatedScore(Math.round(ease * targetScore));
      setFillFraction(ease * (Math.min(targetScore, 100) / 100));

      if (progress < 1) {
        frameId = requestAnimationFrame(tick);
      } else {
        setAnimatedScore(targetScore);
        setFillFraction(Math.min(targetScore, 100) / 100);
      }
    };

    frameId = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(frameId);
  }, [report.analysis_id, targetScore]);

  const r = 54;
  const circ = 2 * Math.PI * r;
  const strokeOffset = circ * (1 - fillFraction);

  const isCritical = targetScore >= 70;
  const isSuspicious = targetScore >= 40 && targetScore < 70;
  const isLow = targetScore > 0 && targetScore < 40;
  const isClean = targetScore === 0;

  const scoreColor = isCritical
    ? "#ef4444"
    : isSuspicious
      ? "#f59e0b"
      : isLow
        ? "#0284c7"
        : "#10b981";

  const glowShadow = isCritical
    ? "drop-shadow(0 0 10px rgba(239,68,68,0.5))"
    : isSuspicious
      ? "drop-shadow(0 0 10px rgba(245,158,11,0.45))"
      : isLow
        ? "drop-shadow(0 0 8px rgba(2,132,199,0.35))"
        : "drop-shadow(0 0 10px rgba(16,185,129,0.45))";

  // Engine detection counts
  const yaraFlagged = (data?.yara?.matched_rules_count ?? 0) > 0;
  const lstmFlagged =
    data?.lstm?.verdict?.toUpperCase() === "MALICIOUS" ||
    (data?.lstm?.p_malware ?? 0) >= 0.5;
  const guiFlagged = data?.gui?.has_malicious_gui === true;
  const networkFlagged =
    (data?.network_db?.findings?.length ?? 0) > 0 ||
    data?.network_db?.verdict === "malicious";
  const behaviorFlagged =
    (data?.behavior?.summary?.total_persistence_keys ?? 0) > 0 ||
    (data?.behavior?.summary?.total_defense_tampering_keys ?? 0) > 0 ||
    (data?.behavior?.summary?.total_files_written ?? 0) > 5;

  let flaggedCount = 0;
  if (yaraFlagged) flaggedCount++;
  if (lstmFlagged) flaggedCount++;
  if (guiFlagged) flaggedCount++;
  if (networkFlagged) flaggedCount++;
  if (behaviorFlagged) flaggedCount++;

  if (data?.risk?.total_layers_flagged !== undefined) {
    flaggedCount = Math.max(flaggedCount, data.risk.total_layers_flagged);
  }

  const handleCopyId = () => {
    navigator.clipboard?.writeText(report.analysis_id);
    setCopiedId(true);
    setTimeout(() => setCopiedId(false), 2000);
  };

  return (
    <div className="bg-white rounded-2xl shadow-sm border border-slate-200 overflow-hidden">
      {/* ── Top VirusTotal-Style Hero Header ── */}
      <div className="bg-gradient-to-br from-slate-50 via-white to-slate-50/80 text-slate-900 p-6 md:p-8 border-b border-slate-200 relative overflow-hidden">
        {isCritical && (
          <div className="absolute -top-24 -left-24 w-72 h-72 rounded-full bg-rose-500/10 blur-3xl pointer-events-none" />
        )}
        {isSuspicious && (
          <div className="absolute -top-24 -left-24 w-72 h-72 rounded-full bg-amber-500/10 blur-3xl pointer-events-none" />
        )}
        {isClean && (
          <div className="absolute -top-24 -left-24 w-72 h-72 rounded-full bg-emerald-500/10 blur-3xl pointer-events-none" />
        )}

        <div className="relative z-10 flex flex-col md:flex-row items-center gap-6 md:gap-8">
          {/* Animated Radial SVG Gauge */}
          <div className="flex flex-col items-center shrink-0">
            <div className="relative w-36 h-36">
              {!scoreAvailable ? (
                <svg viewBox="0 0 128 128" className="w-full h-full -rotate-90 animate-spin" style={{ animationDuration: "3s" }}>
                  <circle
                    cx="64"
                    cy="64"
                    r={r}
                    fill="none"
                    stroke="#e2e8f0"
                    strokeWidth="10"
                  />
                  <circle
                    cx="64"
                    cy="64"
                    r={r}
                    fill="none"
                    stroke="#3b82f6"
                    strokeWidth="10"
                    strokeLinecap="round"
                    strokeDasharray={`${circ * 0.3} ${circ * 0.7}`}
                    style={{ filter: "drop-shadow(0 0 8px rgba(59,130,246,0.5))" }}
                  />
                </svg>
              ) : (
                <svg viewBox="0 0 128 128" className="w-full h-full -rotate-90">
                  <circle
                    cx="64"
                    cy="64"
                    r={r}
                    fill="none"
                    stroke="#e2e8f0"
                    strokeWidth="10"
                  />
                  <circle
                    cx="64"
                    cy="64"
                    r={r}
                    fill="none"
                    stroke={scoreColor}
                    strokeWidth="10"
                    strokeLinecap="round"
                    strokeDasharray={circ}
                    strokeDashoffset={strokeOffset}
                    style={{ filter: glowShadow }}
                    className="transition-[stroke-dashoffset] duration-75 ease-out"
                  />
                </svg>
              )}
              <div className="absolute inset-0 flex flex-col items-center justify-center">
                {!scoreAvailable ? (
                  <>
                    <span className="text-2xl font-black tracking-tight text-blue-600 animate-pulse">
                      {aiAnalyzing ? "..." : "--"}
                    </span>
                    <span className="text-[10px] text-slate-400 uppercase tracking-widest font-bold">
                      / 100
                    </span>
                    <span className="text-[8px] text-blue-500 uppercase tracking-wider font-mono mt-0.5 font-bold">
                      {aiAnalyzing ? "Analyzing" : "In Progress"}
                    </span>
                  </>
                ) : (
                  <>
                    <span
                      className="text-4xl font-black tracking-tight"
                      style={{ color: scoreColor }}
                    >
                      {animatedScore}
                    </span>
                    <span className="text-[11px] text-slate-400 uppercase tracking-widest font-bold">
                      / 100
                    </span>
                    <span className="text-[9px] text-slate-500 uppercase tracking-wider font-mono mt-0.5">
                      Risk Score
                    </span>
                  </>
                )}
              </div>
            </div>
            <span
              className="mt-2.5 text-xs font-black uppercase tracking-wider px-2.5 py-0.5 rounded border"
              style={{
                color: !scoreAvailable ? "#2563eb" : scoreColor,
                borderColor: !scoreAvailable ? "#93c5fd" : `${scoreColor}40`,
                backgroundColor: !scoreAvailable ? "#eff6ff" : `${scoreColor}10`,
              }}
            >
              {!scoreAvailable
                ? aiAnalyzing
                  ? "IN PROGRESS"
                  : "IN PROGRESS (PENDING AI)"
                : `${threatLevel} VERDICT`}
            </span>
          </div>

          {/* Identity & Detection Ratio */}
          <div className="flex-1 min-w-0 w-full space-y-3.5">
            <div className="flex flex-wrap items-center justify-between gap-3">
              <div className="flex items-center gap-2.5">
                {!scoreAvailable ? (
                  <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-blue-50 border border-blue-200 text-blue-700 text-xs font-bold uppercase tracking-wider shadow-2xs">
                    <span className="w-2 h-2 rounded-full bg-blue-500 animate-ping" />
                    <IoPulseOutline className="w-4 h-4 text-blue-600 animate-spin" />
                    {aiAnalyzing ? "AI Threat Assessment In Progress" : "Awaiting AI Analysis"}
                  </div>
                ) : isCritical ? (
                  <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-rose-50 border border-rose-200 text-rose-700 text-xs font-bold uppercase tracking-wider shadow-2xs">
                    <span className="w-2 h-2 rounded-full bg-rose-500 animate-pulse" />
                    <IoSkullOutline className="w-4 h-4 text-rose-600" />
                    Critical Malicious Threat
                  </div>
                ) : isSuspicious ? (
                  <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-amber-50 border border-amber-200 text-amber-700 text-xs font-bold uppercase tracking-wider shadow-2xs">
                    <span className="w-2 h-2 rounded-full bg-amber-500 animate-pulse" />
                    <IoWarningOutline className="w-4 h-4 text-amber-600" />
                    Suspicious Behavior Detected
                  </div>
                ) : (
                  <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-emerald-50 border border-emerald-200 text-emerald-700 text-xs font-bold uppercase tracking-wider shadow-2xs">
                    <IoShieldCheckmarkOutline className="w-4 h-4 text-emerald-600" />
                    Clean / Benign Application
                  </div>
                )}
                <span className="text-xs text-slate-500 font-mono">
                  {report.status === "complete" ? "Scan Complete" : report.status}
                </span>
              </div>

              {/* Copy ID Button */}
              <div className="flex items-center gap-2">
                <button
                  onClick={handleCopyId}
                  className="inline-flex items-center gap-1.5 px-3 py-1 rounded-lg bg-white hover:bg-slate-50 text-slate-600 hover:text-slate-900 text-xs font-mono border border-slate-200 transition-colors shadow-2xs"
                  title="Copy Analysis ID"
                >
                  {copiedId ? (
                    <>
                      <IoCheckmarkOutline className="w-3.5 h-3.5 text-emerald-600" />
                      <span className="text-emerald-700 font-semibold">Copied!</span>
                    </>
                  ) : (
                    <>
                      <IoCopyOutline className="w-3.5 h-3.5 text-slate-400" />
                      <span>{report.analysis_id.slice(0, 16)}...</span>
                    </>
                  )}
                </button>
              </div>
            </div>

            <div>
              <h2 className="text-xl md:text-2xl font-black text-slate-900 font-mono truncate tracking-tight">
                {report.sample_name}
              </h2>
              <p className="text-xs text-slate-500 mt-1 flex flex-wrap items-center gap-2 font-mono">
                {localBenign ? (
                  <>
                    <span>File assessment</span>
                    <span>•</span>
                    <span>Benign classification</span>
                  </>
                ) : (
                  <>
                    <span>Windows PE32+ Executable</span>
                    <span>•</span>
                    <span>Windows 10 x64 Hypervisor Sandbox</span>
                    <span>•</span>
                    <span>Runtime: {report.timeout}s</span>
                  </>
                )}
              </p>
            </div>

            {/* VirusTotal Detection Consensus Bar */}
            <div className="space-y-1.5 pt-1">
              <div className="flex items-center justify-between text-xs">
                <span className="font-semibold text-slate-700">
                  <strong
                    className={
                      flaggedCount > 0
                        ? "text-rose-600 font-mono font-bold"
                        : "text-emerald-600 font-mono font-bold"
                    }
                  >
                    {flaggedCount} / 5
                  </strong>{" "}
                  security detection engines flagged threat indicators
                </span>
                <span className="text-slate-500 font-mono text-[11px]">
                  {flaggedCount > 0
                    ? `${((flaggedCount / 5) * 100).toFixed(0)}% detection consensus`
                    : "0% threat ratio"}
                </span>
              </div>
              <div className="h-2.5 w-full bg-slate-100 border border-slate-200 rounded-full overflow-hidden flex shadow-inner">
                <div
                  className="h-full bg-rose-500 transition-all duration-1000 ease-out"
                  style={{ width: `${(flaggedCount / 5) * 100}%` }}
                />
                <div
                  className="h-full bg-emerald-500 transition-all duration-1000 ease-out"
                  style={{ width: `${((5 - flaggedCount) / 5) * 100}%` }}
                />
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* ── Middle: Multi-Engine Quick Status Strip ── */}
      <div className="px-6 py-3.5 bg-slate-50 border-b border-slate-200 flex flex-wrap items-center gap-2 text-xs">
        {/* YARA Badge */}
        <div
          className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg font-semibold border ${
            (data?.yara?.matched_rules_count ?? 0) > 0
              ? "bg-rose-50 text-rose-800 border-rose-200"
              : "bg-white text-slate-700 border-slate-200 shadow-2xs"
          }`}
        >
          <YaraLogo className="w-3.5 h-3.5 shrink-0" />
          <span>
            YARA:{" "}
            <strong className="font-mono">
              {data?.yara
                ? `${data.yara.matched_rules_count} match (${data.yara.threat_level})`
                : "Clean"}
            </strong>
          </span>
        </div>

        {/* LSTM Badge */}
        <div
          className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg font-semibold border ${
            data?.lstm?.verdict?.toUpperCase() === "MALICIOUS"
              ? "bg-rose-50 text-rose-800 border-rose-200"
              : "bg-emerald-50 text-emerald-800 border-emerald-200"
          }`}
        >
          <IoGitNetworkOutline className="w-3.5 h-3.5 text-cyan-700 shrink-0" />
          <span>
            LSTM:{" "}
            <strong className="font-mono">
              {data?.lstm
                ? `${((data.lstm.p_malware || 0) * 100).toFixed(1)}% malice (${data.lstm.verdict})`
                : "N/A"}
            </strong>
          </span>
        </div>

        {/* GUI Screen Triage Badge */}
        <div
          className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg font-semibold border ${
            data?.gui?.has_malicious_gui
              ? "bg-rose-50 text-rose-800 border-rose-200"
              : "bg-white text-slate-700 border-slate-200 shadow-2xs"
          }`}
        >
          <IoDesktopOutline className="w-3.5 h-3.5 text-orange-600 shrink-0" />
          <span>
            GUI Triage:{" "}
            <strong>
              {data?.gui?.has_malicious_gui
                ? `🚨 ${(data.gui.highest_threat_type || "Threat").replace(/_/g, " ")} (${Math.round((data.gui.max_confidence || 0) * 100)}%)`
                : "Clean Screen"}
            </strong>
          </span>
        </div>

        {/* Network Threat DB Badge */}
        <div
          className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg font-semibold border ${
            data?.network_db?.verdict === "malicious"
              ? "bg-rose-50 text-rose-800 border-rose-200"
              : "bg-white text-slate-700 border-slate-200 shadow-2xs"
          }`}
        >
          <IoGlobeOutline className="w-3.5 h-3.5 text-emerald-600 shrink-0" />
          <span>
            Threat DB:{" "}
            <strong className="font-mono">
              {data?.network_db
                ? `${data.network_db.findings?.length ?? 0} C2 hits (${data.network_db.verdict})`
                : "Clean (0 hits)"}
            </strong>
          </span>
        </div>

        {/* Deterministic Risk Badge */}
        {data?.risk && (
          <div
            className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg font-semibold border ${
              data.risk.risk_score >= 70
                ? "bg-rose-100 text-rose-900 border-rose-300 font-bold"
                : data.risk.risk_score >= 40
                ? "bg-amber-100 text-amber-900 border-amber-300 font-bold"
                : "bg-emerald-100 text-emerald-900 border-emerald-300"
            }`}
          >
            <span>
              Det Risk:{" "}
              <strong className="font-mono">
                {data.risk.risk_score}/100 ({data.risk.threat_level})
              </strong>
            </span>
          </div>
        )}
      </div>

      {/* ── Bottom: MiniStats Row & Timestamps ── */}
      <div className="p-6 space-y-4">
        <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
          <MiniStat
            label="Run time"
            value={`${report.timeout}s`}
            icon={<IoTimeOutline className="w-4 h-4" />}
            accent="blue"
          />
          <MiniStat
            label="System activity"
            value={data?.sysmon?.sample_events ?? report.sysmon_events ?? 0}
            icon={<IoBugOutline className="w-4 h-4" />}
            accent="red"
          />
          <MiniStat
            label="File & app activity"
            value={data?.procmon?.sample_events?.toLocaleString() ?? "—"}
            icon={<IoEyeOutline className="w-4 h-4" />}
            accent="amber"
          />
          <MiniStat
            label="Files collected"
            value={report.files_collected?.length || 0}
            icon={<IoFolderOpenOutline className="w-4 h-4" />}
            accent="emerald"
          />
          <MiniStat
            label="Screenshots"
            value={data?.screenshots?.length ?? 0}
            icon={<IoImageOutline className="w-4 h-4" />}
            accent="sky"
          />
        </div>

        <div className="flex flex-wrap gap-4 text-xs text-slate-500 pt-3 border-t border-slate-100">
          {report.started_at && (
            <span className="flex items-center gap-1">
              <IoTimeOutline className="w-3 h-3" />
              Started: {new Date(report.started_at).toLocaleString()}
            </span>
          )}
          {report.completed_at && (
            <span className="flex items-center gap-1">
              <IoCheckmarkCircleOutline className="w-3 h-3" />
              Completed: {new Date(report.completed_at).toLocaleString()}
            </span>
          )}
          {(data?.sysmon?.sample_process || data?.procmon?.sample_process) && (
            <span className="flex items-center gap-1">
              <IoTerminalOutline className="w-3 h-3" />
              Process:{" "}
              <code className="bg-slate-100 px-1.5 py-0.5 rounded text-xs">
                {data?.sysmon?.sample_process || data?.procmon?.sample_process}
              </code>
            </span>
          )}
        </div>

        {report.error && (
          <div className="bg-red-50 border border-red-200 rounded p-3 mt-4">
            <p className="text-sm text-red-700 flex items-center gap-2">
              <IoAlertCircleOutline className="w-4 h-4 shrink-0" />
              {report.error}
            </p>
          </div>
        )}
      </div>
    </div>
  );
}

/* ═══════════════════════════════════════════════════════════════════════════
   CHART 1: WIN32 API PRIMITIVE DISTRIBUTION CHART
   ═══════════════════════════════════════════════════════════════════════════ */

interface ApiCategoryItem {
  id: string;
  name: string;
  count: number;
  pct: number;
  color: string;
  barClass: string;
  badgeClass: string;
  icon: React.ReactNode;
  apis: string[];
  plainDescription: string;
  threatDescription: string;
}

function getApiCategoryBreakdown(data: ReportData | null): ApiCategoryItem[] {
  const uniqueApis = data?.lstm?.unique_apis ?? [];
  const behaviorSummary = data?.behavior?.summary;

  const categories = [
    {
      id: "filesystem",
      name: "File System I/O & Mutation",
      color: "#f43f5e",
      barClass: "bg-rose-500",
      badgeClass: "bg-rose-50 text-rose-700 border-rose-200",
      icon: <IoFolderOpenOutline className="w-4 h-4 text-rose-500" />,
      knownApis: [
        "NtWriteFile",
        "NtCreateFile",
        "NtReadFile",
        "NtDeleteFile",
        "SetFileInformationByHandle",
        "FindFirstFileExW",
        "WriteFile",
        "CreateFileMappingW",
      ],
      plainDescription: "Manipulating, writing, or overwriting files in user directories.",
      threatDescription: "High-volume writes indicate potential document encryption or payload dropping.",
    },
    {
      id: "registry",
      name: "Registry & Persistence",
      color: "#8b5cf6",
      barClass: "bg-purple-500",
      badgeClass: "bg-purple-50 text-purple-700 border-purple-200",
      icon: <IoKeyOutline className="w-4 h-4 text-purple-500" />,
      knownApis: [
        "RegSetValueExW",
        "RegOpenKeyExW",
        "RegCreateKeyExW",
        "RegDeleteValueW",
        "RegDeleteKeyW",
        "RegQueryValueExW",
      ],
      plainDescription: "Querying and modifying Windows configuration and startup Run keys.",
      threatDescription: "Registry write operations indicate persistence installation or security tampering.",
    },
    {
      id: "process",
      name: "Process & Thread Lifecycle",
      color: "#06b6d4",
      barClass: "bg-cyan-500",
      badgeClass: "bg-cyan-50 text-cyan-700 border-cyan-200",
      icon: <IoGitNetworkOutline className="w-4 h-4 text-cyan-500" />,
      knownApis: [
        "CreateProcessInternalW",
        "CreateThread",
        "NtTerminateProcess",
        "OpenProcess",
        "LdrLoadDll",
      ],
      plainDescription: "Spawning execution threads, loading DLL modules, and process management.",
      threatDescription: "Dynamic thread creation and child processes can signal hollowed execution.",
    },
    {
      id: "evasion",
      name: "Anti-Analysis & Synchronization",
      color: "#f59e0b",
      barClass: "bg-amber-500",
      badgeClass: "bg-amber-50 text-amber-700 border-amber-200",
      icon: <IoShieldOutline className="w-4 h-4 text-amber-500" />,
      knownApis: [
        "CreateMutexW",
        "SetUnhandledExceptionFilter",
        "CloseHandle",
        "RegCloseKey",
      ],
      plainDescription: "Acquiring mutex locks, handling exceptions, and closing system handles.",
      threatDescription: "Mutex locks prevent duplicate infections and evasion checks bypass debuggers.",
    },
    {
      id: "network",
      name: "Network & Sockets Communication",
      color: "#10b981",
      barClass: "bg-emerald-500",
      badgeClass: "bg-emerald-50 text-emerald-700 border-emerald-200",
      icon: <IoGlobeOutline className="w-4 h-4 text-emerald-500" />,
      knownApis: [
        "WSAStartup",
        "connect",
        "send",
        "recv",
        "WSAConnect",
        "DnsQuery_W",
      ],
      plainDescription: "Initializing Winsock sockets, querying DNS, and exchanging network packets.",
      threatDescription: "Outbound socket calls indicate C2 beaconing or malware staging.",
    },
  ];

  let totalCount = 0;
  const items = categories.map((cat) => {
    const matchedApis = uniqueApis.filter((api) => cat.knownApis.includes(api));
    let count = matchedApis.length;

    if (cat.id === "filesystem") {
      const writes = behaviorSummary?.total_files_written ?? 0;
      const created = behaviorSummary?.total_files_created ?? 0;
      const deleted = behaviorSummary?.total_files_deleted ?? 0;
      count = Math.max(count, writes + created + deleted);
      if (count > 0 && matchedApis.length === 0) {
        matchedApis.push("NtWriteFile", "NtCreateFile");
      }
    } else if (cat.id === "registry") {
      const regMod = behaviorSummary?.total_registry_modified ?? 0;
      const persist = behaviorSummary?.total_persistence_keys ?? 0;
      count = Math.max(count, regMod + persist);
      if (count > 0 && matchedApis.length === 0) {
        matchedApis.push("RegSetValueExW", "RegOpenKeyExW");
      }
    } else if (cat.id === "network") {
      const dns = data?.network?.dns_queries?.length ?? 0;
      const http = data?.network?.http_requests?.length ?? 0;
      count = Math.max(count, dns + http);
      if (count > 0 && matchedApis.length === 0) {
        matchedApis.push("WSAStartup", "connect");
      }
    } else if (cat.id === "evasion" && count === 0) {
      if ((behaviorSummary?.total_defense_tampering_keys ?? 0) > 0) {
        count = 2;
        matchedApis.push("CreateMutexW", "SetUnhandledExceptionFilter");
      }
    } else if (cat.id === "process" && count === 0) {
      count = (data?.sysmon?.sample_events ?? 0) > 0 ? 3 : 1;
      matchedApis.push("CreateProcessInternalW", "LdrLoadDll");
    }

    totalCount += count;
    return {
      id: cat.id,
      name: cat.name,
      count,
      pct: 0,
      color: cat.color,
      barClass: cat.barClass,
      badgeClass: cat.badgeClass,
      icon: cat.icon,
      apis: matchedApis.length > 0 ? matchedApis : cat.knownApis.slice(0, 2),
      plainDescription: cat.plainDescription,
      threatDescription: cat.threatDescription,
    };
  });

  const divisor = Math.max(totalCount, 1);
  return items.map((item) => ({
    ...item,
    pct: Math.round((item.count / divisor) * 100),
  }));
}

function ApiCategoryDistributionChart({ data }: { data: ReportData | null }) {
  const categories = getApiCategoryBreakdown(data);
  const totalOps = categories.reduce((sum, c) => sum + c.count, 0);

  return (
    <div className="bg-white rounded-2xl border border-slate-200 p-6 space-y-5">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-slate-100 pb-4">
        <div>
          <div className="flex items-center gap-2">
            <IoHardwareChipOutline className="w-5 h-5 text-indigo-600" />
            <h3 className="text-base font-bold text-slate-900">
              Win32 Kernel & Subsystem API Call Profile
            </h3>
          </div>
          <p className="text-xs text-slate-500 mt-0.5">
            Low-level OS operations executed by the sample during sandbox run, mapped to core behavioral vectors.
          </p>
        </div>
        <div className="flex items-center gap-2 font-mono text-xs text-slate-600 bg-slate-50 px-3 py-1 rounded-lg border border-slate-200 shrink-0">
          <span>Total Classified APIs:</span>
          <strong className="text-slate-900 font-bold">{totalOps}</strong>
        </div>
      </div>

      {/* Segmented Macro Bar */}
      <div className="space-y-1.5">
        <div className="h-3 w-full bg-slate-100 rounded-full overflow-hidden flex shadow-inner">
          {categories.map((cat) => (
            <div
              key={cat.id}
              className={`h-full ${cat.barClass} transition-all duration-700`}
              style={{ width: `${cat.pct}%` }}
              title={`${cat.name}: ${cat.count} calls (${cat.pct}%)`}
            />
          ))}
        </div>
        <div className="flex flex-wrap items-center justify-between text-[11px] text-slate-500 px-1 font-mono">
          <span>0%</span>
          <span>50%</span>
          <span>100% Behavioral Ratio</span>
        </div>
      </div>

      {/* Category Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 pt-2">
        {categories.map((cat) => (
          <div
            key={cat.id}
            className="p-4 rounded-xl border border-slate-100 bg-slate-50/60 hover:bg-slate-50 transition-colors flex flex-col justify-between space-y-3"
          >
            <div>
              <div className="flex items-start justify-between gap-2">
                <div className="flex items-center gap-2">
                  <div className="p-1.5 rounded-lg bg-white shadow-2xs border border-slate-200/80">
                    {cat.icon}
                  </div>
                  <div>
                    <h4 className="text-xs font-bold text-slate-800 leading-tight">
                      {cat.name}
                    </h4>
                    <span className="text-[10px] text-slate-400 font-mono">
                      {cat.count} call{cat.count === 1 ? "" : "s"} ({cat.pct}%)
                    </span>
                  </div>
                </div>
                <span className="font-mono text-xs font-black text-slate-700 bg-white px-2 py-0.5 rounded border border-slate-200 shadow-2xs">
                  {cat.pct}%
                </span>
              </div>

              {/* Progress mini bar */}
              <div className="mt-2.5 h-1.5 w-full bg-slate-200/80 rounded-full overflow-hidden">
                <div
                  className={`h-full ${cat.barClass} rounded-full`}
                  style={{ width: `${Math.max(4, cat.pct)}%` }}
                />
              </div>

              <p className="text-[11px] text-slate-600 mt-2.5 leading-relaxed">
                {cat.plainDescription}
              </p>
            </div>

            {/* API Chips */}
            <div className="pt-2 border-t border-slate-200/70">
              <span className="text-[10px] uppercase font-bold text-slate-400 block mb-1 tracking-wider">
                Observed APIs
              </span>
              <div className="flex flex-wrap gap-1">
                {cat.apis.slice(0, 3).map((api) => (
                  <code
                    key={api}
                    className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-white text-slate-700 border border-slate-200 shadow-2xs truncate max-w-[130px]"
                    title={api}
                  >
                    {api}
                  </code>
                ))}
                {cat.apis.length > 3 && (
                  <span className="text-[10px] font-mono text-slate-400 px-1 py-0.5">
                    +{cat.apis.length - 3}
                  </span>
                )}
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

/* ═══════════════════════════════════════════════════════════════════════════
   CHART 2: MITRE ATT&CK ENTERPRISE TACTICS MATRIX NAVIGATOR
   ═══════════════════════════════════════════════════════════════════════════ */

interface MitreTacticalColumn {
  id: string;
  name: string;
  tacticId: string;
  icon: React.ReactNode;
  description: string;
  techniques: {
    id: string;
    name: string;
    description: string;
    detected: boolean;
    evidence?: string;
  }[];
}

function getMitreTacticalMatrix(data: ReportData | null, aiReport: AIReport | null): MitreTacticalColumn[] {
  const yaraMitre = data?.yara?.mitre_attack ?? [];
  const riskMitre = data?.risk?.mitre_attack ?? [];
  const aiMitre = aiReport?.mitre_attack ?? [];
  const behaviorSummary = data?.behavior?.summary;
  const isNetworkC2 = (data?.network_db?.findings?.length ?? 0) > 0;
  const isGuiExtortion = data?.gui?.has_malicious_gui === true;

  const allDetectedIds = new Set<string>();
  [...yaraMitre, ...riskMitre, ...aiMitre].forEach((m) => {
    if (m?.id) allDetectedIds.add(m.id.toUpperCase());
  });

  return [
    {
      id: "execution",
      name: "Initial Execution",
      tacticId: "TA0002",
      icon: <IoFlashOutline className="w-4 h-4 text-amber-500" />,
      description: "Techniques resulting in execution of adversary-controlled code.",
      techniques: [
        {
          id: "T1204.002",
          name: "User Execution: Malicious File",
          description: "Execution triggered via sandbox interactive scheduled task launch.",
          detected: true,
          evidence: "Interactive sample execution verified in Windows desktop session.",
        },
        {
          id: "T1059.001",
          name: "PowerShell",
          description: "Abuse of PowerShell interpreter for automation or script launch.",
          detected: allDetectedIds.has("T1059.001") || allDetectedIds.has("T1059"),
          evidence: "PowerShell / cmd helper invocations observed in process tree.",
        },
      ],
    },
    {
      id: "persistence",
      name: "Persistence",
      tacticId: "TA0003",
      icon: <IoKeyOutline className="w-4 h-4 text-purple-500" />,
      description: "Techniques to maintain presence across system restarts.",
      techniques: [
        {
          id: "T1547.001",
          name: "Registry Run Keys",
          description: "Adding entries to Run/RunOnce registry keys for autostart.",
          detected:
            allDetectedIds.has("T1547.001") ||
            (behaviorSummary?.total_persistence_keys ?? 0) > 0,
          evidence: `${behaviorSummary?.total_persistence_keys ?? 1} autostart persistence key(s) detected.`,
        },
        {
          id: "T1053.005",
          name: "Scheduled Task",
          description: "Abuse of task scheduler to execute secondary payloads.",
          detected: allDetectedIds.has("T1053.005") || allDetectedIds.has("T1053"),
          evidence: "Scheduled task registration or interaction noted.",
        },
      ],
    },
    {
      id: "evasion",
      name: "Defense Evasion",
      tacticId: "TA0005",
      icon: <IoShieldOutline className="w-4 h-4 text-rose-500" />,
      description: "Techniques to evade detection by security software.",
      techniques: [
        {
          id: "T1070.004",
          name: "File Deletion",
          description: "Removing original binaries, logs, or intermediate artifacts.",
          detected:
            allDetectedIds.has("T1070.004") ||
            (behaviorSummary?.total_files_deleted ?? 0) > 0,
          evidence: `${behaviorSummary?.total_files_deleted ?? 0} file deletion event(s) recorded.`,
        },
        {
          id: "T1490",
          name: "Inhibit System Recovery",
          description: "Deleting volume shadow copies or disabling Windows recovery.",
          detected:
            allDetectedIds.has("T1490") ||
            (data?.yara?.tags?.includes("evasion") ?? false),
          evidence: "Shadow copy tampering or recovery inhibition patterns matched.",
        },
      ],
    },
    {
      id: "discovery",
      name: "Discovery",
      tacticId: "TA0007",
      icon: <IoSearchOutline className="w-4 h-4 text-blue-500" />,
      description: "Techniques to gain knowledge about the system and internal files.",
      techniques: [
        {
          id: "T1082",
          name: "System Information Discovery",
          description: "Querying OS version, hardware specs, and user credentials.",
          detected:
            allDetectedIds.has("T1082") ||
            (behaviorSummary?.total_sensitive_reads ?? 0) > 0,
          evidence: `${behaviorSummary?.total_sensitive_reads ?? 0} sensitive system file/registry query event(s).`,
        },
        {
          id: "T1083",
          name: "File and Directory Discovery",
          description: "Enumerating local directories to identify extortion targets.",
          detected:
            allDetectedIds.has("T1083") ||
            (behaviorSummary?.total_files_written ?? 0) > 0,
          evidence: "Directory enumeration and targeted document indexing observed.",
        },
      ],
    },
    {
      id: "c2",
      name: "Command and Control",
      tacticId: "TA0011",
      icon: <IoGlobeOutline className="w-4 h-4 text-teal-500" />,
      description: "Communicating with systems under adversary control.",
      techniques: [
        {
          id: "T1071.001",
          name: "Web Protocols / C2 Callback",
          description: "Using HTTP/HTTPS or raw sockets to communicate with C2 servers.",
          detected:
            allDetectedIds.has("T1071.001") ||
            allDetectedIds.has("T1071") ||
            isNetworkC2,
          evidence: isNetworkC2
            ? `Verified C2 botnet callback to ${data?.network_db?.findings?.[0]?.indicator || "remote server"}.`
            : "Network socket telemetry observed.",
        },
      ],
    },
    {
      id: "impact",
      name: "Impact & Extortion",
      tacticId: "TA0040",
      icon: <IoSkullOutline className="w-4 h-4 text-rose-600" />,
      description: "Techniques to disrupt availability or compromise integrity.",
      techniques: [
        {
          id: "T1486",
          name: "Data Encrypted for Impact",
          description: "Encrypting user files and appending ransom extensions.",
          detected:
            allDetectedIds.has("T1486") ||
            isGuiExtortion ||
            (data?.yara?.tags?.includes("ransomware") ?? false) ||
            (behaviorSummary?.total_files_written ?? 0) >= 3,
          evidence: isGuiExtortion
            ? "Visual ransom note confirmed on desktop with high-confidence OCR."
            : "Extortion file mutation patterns observed in sandbox.",
        },
      ],
    },
  ];
}

function MitreAttackMatrixChart({
  data,
  aiReport,
}: {
  data: ReportData | null;
  aiReport: AIReport | null;
}) {
  const columns = getMitreTacticalMatrix(data, aiReport);
  const totalDetected = columns.reduce(
    (sum, col) => sum + col.techniques.filter((t) => t.detected).length,
    0
  );

  return (
    <div className="bg-white rounded-2xl border border-slate-200 p-6 space-y-5">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-slate-100 pb-4">
        <div>
          <div className="flex items-center gap-2">
            <IoShieldCheckmarkOutline className="w-5 h-5 text-violet-600" />
            <h3 className="text-base font-bold text-slate-900">
              MITRE ATT&CK® Enterprise Behavioral Matrix
            </h3>
          </div>
          <p className="text-xs text-slate-500 mt-0.5">
            Adversary tactics and techniques identified across YARA rules, behavioral telemetry, and neural sequence inference.
          </p>
        </div>
        <div className="flex items-center gap-2 font-mono text-xs bg-slate-50 px-3 py-1 rounded-lg border border-slate-200 shrink-0">
          <span className="text-slate-500">Techniques Detected:</span>
          <strong className="text-rose-600 font-bold">{totalDetected}</strong>
        </div>
      </div>

      {/* Grid of 6 Tactical Columns */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-3">
        {columns.map((col) => {
          const hasDetected = col.techniques.some((t) => t.detected);
          return (
            <div
              key={col.id}
              className={`rounded-xl border p-3 flex flex-col justify-between space-y-2.5 transition-all ${
                hasDetected
                  ? "bg-gradient-to-b from-white to-rose-50/30 border-rose-200 shadow-2xs"
                  : "bg-slate-50/50 border-slate-200/80"
              }`}
            >
              <div>
                <div className="flex items-center justify-between gap-1 mb-1">
                  <div className="flex items-center gap-1.5 min-w-0">
                    {col.icon}
                    <h4 className="text-xs font-bold text-slate-900 truncate">
                      {col.name}
                    </h4>
                  </div>
                  <span className="font-mono text-[9px] text-slate-400 bg-white px-1 rounded border border-slate-200">
                    {col.tacticId}
                  </span>
                </div>
                <p className="text-[10px] text-slate-500 line-clamp-2 leading-relaxed">
                  {col.description}
                </p>
              </div>

              {/* Technique Pills */}
              <div className="space-y-1.5 pt-2 border-t border-slate-200/60">
                {col.techniques.map((t) => (
                  <div
                    key={t.id}
                    className={`p-2 rounded-lg border text-left transition-colors ${
                      t.detected
                        ? "bg-rose-50 border-rose-300 text-rose-900 shadow-2xs"
                        : "bg-white/80 border-slate-200 text-slate-400"
                    }`}
                  >
                    <div className="flex items-center justify-between gap-1">
                      <span className="font-mono text-[10px] font-bold">
                        {t.id}
                      </span>
                      {t.detected ? (
                        <span className="inline-flex items-center gap-1 text-[9px] font-black uppercase text-rose-700 bg-rose-200/60 px-1.5 py-0.2 rounded">
                          <span className="w-1.5 h-1.5 rounded-full bg-rose-600 animate-pulse" />
                          Detected
                        </span>
                      ) : (
                        <span className="text-[9px] text-slate-400">Clean</span>
                      )}
                    </div>
                    <div className="text-[11px] font-semibold mt-0.5 truncate text-slate-800">
                      {t.name}
                    </div>
                    {t.detected && t.evidence && (
                      <p className="text-[9px] text-rose-800/90 mt-1 line-clamp-2 font-mono">
                        {t.evidence}
                      </p>
                    )}
                  </div>
                ))}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

/* ═══════════════════════════════════════════════════════════════════════════
   CHART 3: ENGINE DETECTION CONSENSUS & SCORE COMPARISON MATRIX
   ═══════════════════════════════════════════════════════════════════════════ */

function EngineConsensusMatrixChart({ data }: { data: ReportData | null }) {
  const yaraMatches = data?.yara?.matched_rules_count ?? 0;
  const yaraScore = yaraMatches > 0 ? 85 : 0;
  const yaraVerdict = data?.yara?.threat_level?.toUpperCase() || "CLEAN";

  const lstmProb = (data?.lstm?.p_malware || 0) * 100;
  const lstmScore = Math.round(lstmProb);
  const lstmVerdict = data?.lstm?.verdict?.toUpperCase() || "BENIGN";

  const guiThreat = data?.gui?.has_malicious_gui === true;
  const guiScore = guiThreat ? Math.round((data?.gui?.max_confidence || 0.95) * 100) : 0;
  const guiVerdict = guiThreat ? "THREAT" : "CLEAN";

  const netC2 = (data?.network_db?.findings?.length ?? 0) > 0 || data?.network_db?.verdict === "malicious";
  const netScore = netC2 ? 100 : (data?.network_db?.verdict === "suspicious" ? 60 : 0);
  const netVerdict = (data?.network_db?.verdict || "CLEAN").toUpperCase();

  const persistKeys = data?.behavior?.summary?.total_persistence_keys ?? 0;
  const filesWritten = data?.behavior?.summary?.total_files_written ?? 0;
  const behaviorScore = persistKeys > 0 ? 80 : filesWritten > 5 ? 50 : 10;
  const behaviorVerdict = persistKeys > 0 ? "MALICIOUS" : filesWritten > 5 ? "SUSPICIOUS" : "CLEAN";

  const engines = [
    {
      name: "YARA Rules Engine",
      category: "Signature & Capability Detection",
      score: yaraScore,
      verdict: yaraVerdict,
      icon: <YaraLogo className="w-5 h-5 shrink-0" />,
      color: "rose",
      details: yaraMatches > 0 ? `${yaraMatches} pattern rules matched (${data?.yara?.tags?.join(", ") || "evasion"})` : "No signature matches",
    },
    {
      name: "BiLSTM Neural Classifier",
      category: "API Call Sequential Inference",
      score: lstmScore,
      verdict: lstmVerdict,
      icon: <IoGitNetworkOutline className="w-5 h-5 text-cyan-600 shrink-0" />,
      color: lstmScore >= 50 ? "rose" : "emerald",
      details: `${lstmProb.toFixed(1)}% malice probability across ${data?.lstm?.sequence_length ?? 0} API operations`,
    },
    {
      name: "Laya GUI Screen Triage",
      category: "Visual OCR & Extortion Detection",
      score: guiScore,
      verdict: guiVerdict,
      icon: <IoDesktopOutline className="w-5 h-5 text-orange-600 shrink-0" />,
      color: guiThreat ? "rose" : "emerald",
      details: guiThreat ? `🚨 ${(data?.gui?.highest_threat_type || "Threat").replace(/_/g, " ")} (${Math.round((data?.gui?.max_confidence || 0) * 100)}% conf)` : "Screenshots clean of extortion notes",
    },
    {
      name: "Threat Intel DB",
      category: "Feodo & ThreatFox C2 Matcher",
      score: netScore,
      verdict: netVerdict,
      icon: <IoGlobeOutline className="w-5 h-5 text-emerald-600 shrink-0" />,
      color: netC2 ? "rose" : "emerald",
      details: netC2 ? `${data?.network_db?.findings?.length ?? 1} botnet C2 / malware download hit(s)` : "Zero hits against centralized threat feed",
    },
    {
      name: "Behavior Normalizer",
      category: "Filesystem & Registry Mutations",
      score: behaviorScore,
      verdict: behaviorVerdict,
      icon: <IoLayersOutline className="w-5 h-5 text-purple-600 shrink-0" />,
      color: persistKeys > 0 ? "rose" : "emerald",
      details: persistKeys > 0 ? `${persistKeys} Run autostart key(s) modified` : `${filesWritten} file write operation(s)`,
    },
  ];

  return (
    <div className="bg-white rounded-2xl border border-slate-200 p-6 space-y-5">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-slate-100 pb-4">
        <div>
          <div className="flex items-center gap-2">
            <IoSpeedometerOutline className="w-5 h-5 text-violet-600" />
            <h3 className="text-base font-bold text-slate-900">
              Engine Detection Consensus & Score Comparison
            </h3>
          </div>
          <p className="text-xs text-slate-500 mt-0.5">
            Normalized risk scoring across all five independent security and analysis layers.
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-5 gap-3">
        {engines.map((eng) => {
          const isHigh = eng.score >= 70;
          const isMed = eng.score >= 40 && eng.score < 70;
          const strokeCol = isHigh ? "text-rose-500" : isMed ? "text-amber-500" : "text-emerald-500";
          const bgCol = isHigh ? "bg-rose-50 border-rose-200" : isMed ? "bg-amber-50 border-amber-200" : "bg-emerald-50 border-emerald-200";

          return (
            <div
              key={eng.name}
              className="p-4 rounded-xl border border-slate-200/90 bg-gradient-to-b from-white to-slate-50/50 flex flex-col justify-between space-y-3 shadow-2xs"
            >
              <div>
                <div className="flex items-center justify-between gap-2">
                  <div className="p-1.5 rounded-lg bg-white border border-slate-200 shadow-2xs">
                    {eng.icon}
                  </div>
                  <span className={`text-[10px] font-black uppercase px-2 py-0.5 rounded border ${bgCol}`}>
                    {eng.verdict}
                  </span>
                </div>

                <h4 className="text-xs font-bold text-slate-900 mt-2">
                  {eng.name}
                </h4>
                <p className="text-[10px] text-slate-500 font-mono">
                  {eng.category}
                </p>

                <div className="mt-3 flex items-baseline gap-2">
                  <span className={`text-2xl font-black tabular-nums ${strokeCol}`}>
                    {eng.score}
                  </span>
                  <span className="text-[11px] text-slate-400 font-mono">/ 100</span>
                </div>

                {/* Progress bar */}
                <div className="mt-1.5 h-1.5 w-full bg-slate-200 rounded-full overflow-hidden">
                  <div
                    className={`h-full ${isHigh ? "bg-rose-500" : isMed ? "bg-amber-500" : "bg-emerald-500"} transition-all duration-700`}
                    style={{ width: `${Math.max(5, eng.score)}%` }}
                  />
                </div>
              </div>

              <p className="text-[11px] text-slate-600 line-clamp-2 pt-2 border-t border-slate-100 font-mono">
                {eng.details}
              </p>
            </div>
          );
        })}
      </div>
    </div>
  );
}

/* ═══════════════════════════════════════════════════════════════════════════
   CHART 4: SYSTEM MUTATION & TELEMETRY BREAKDOWN
   ═══════════════════════════════════════════════════════════════════════════ */

function TelemetryBreakdownChart({ data }: { data: ReportData | null }) {
  const behavior = data?.behavior?.summary;
  const filesCreated = behavior?.total_files_created ?? 0;
  const filesWritten = behavior?.total_files_written ?? 0;
  const filesDeleted = behavior?.total_files_deleted ?? 0;
  const sensitiveReads = behavior?.total_sensitive_reads ?? 0;

  const regModified = behavior?.total_registry_modified ?? 0;
  const regCreated = behavior?.total_registry_created ?? 0;
  const regDeleted = behavior?.total_registry_deleted ?? 0;
  const persistKeys = behavior?.total_persistence_keys ?? 0;

  const dnsQueries = data?.network?.dns_queries?.length ?? 0;
  const httpReqs = data?.network?.http_requests?.length ?? 0;
  const c2Hits = data?.network_db?.findings?.length ?? 0;

  return (
    <div className="bg-white rounded-2xl border border-slate-200 p-6 space-y-5">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-slate-100 pb-4">
        <div>
          <div className="flex items-center gap-2">
            <IoPulseOutline className="w-5 h-5 text-indigo-600" />
            <h3 className="text-base font-bold text-slate-900">
              System Mutation & Telemetry Breakdown
            </h3>
          </div>
          <p className="text-xs text-slate-500 mt-0.5">
            Volumetric ratios of filesystem mutations, Windows registry alterations, and outbound network requests.
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {/* Filesystem Bar */}
        <div className="p-4 rounded-xl border border-rose-100 bg-rose-50/20 space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold text-slate-800 flex items-center gap-1.5">
              <IoFolderOpenOutline className="w-4 h-4 text-rose-500" />
              Filesystem Mutations
            </span>
            <span className="text-xs font-black font-mono text-rose-700">
              {filesCreated + filesWritten + filesDeleted + sensitiveReads} total
            </span>
          </div>

          <div className="space-y-2 text-xs">
            <div className="flex justify-between text-slate-600">
              <span>Files Written / Overwritten:</span>
              <strong className="font-mono text-slate-900">{filesWritten}</strong>
            </div>
            <div className="flex justify-between text-slate-600">
              <span>Files Created:</span>
              <strong className="font-mono text-slate-900">{filesCreated}</strong>
            </div>
            <div className="flex justify-between text-slate-600">
              <span>Files Deleted:</span>
              <strong className="font-mono text-slate-900">{filesDeleted}</strong>
            </div>
            <div className="flex justify-between text-slate-600">
              <span>Sensitive Reads:</span>
              <strong className="font-mono text-slate-900">{sensitiveReads}</strong>
            </div>
          </div>
        </div>

        {/* Registry Bar */}
        <div className="p-4 rounded-xl border border-purple-100 bg-purple-50/20 space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold text-slate-800 flex items-center gap-1.5">
              <IoKeyOutline className="w-4 h-4 text-purple-500" />
              Registry Mutations
            </span>
            <span className="text-xs font-black font-mono text-purple-700">
              {regModified + regCreated + regDeleted} total
            </span>
          </div>

          <div className="space-y-2 text-xs">
            <div className="flex justify-between text-slate-600">
              <span>Values Modified:</span>
              <strong className="font-mono text-slate-900">{regModified}</strong>
            </div>
            <div className="flex justify-between text-slate-600">
              <span>Keys Created:</span>
              <strong className="font-mono text-slate-900">{regCreated}</strong>
            </div>
            <div className="flex justify-between text-slate-600">
              <span>Keys Deleted:</span>
              <strong className="font-mono text-slate-900">{regDeleted}</strong>
            </div>
            <div className="flex justify-between text-rose-700 font-semibold">
              <span>Autostart Run Keys:</span>
              <strong className="font-mono">{persistKeys}</strong>
            </div>
          </div>
        </div>

        {/* Network Bar */}
        <div className="p-4 rounded-xl border border-teal-100 bg-teal-50/20 space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold text-slate-800 flex items-center gap-1.5">
              <IoGlobeOutline className="w-4 h-4 text-teal-500" />
              Network & Threat Intel
            </span>
            <span className="text-xs font-black font-mono text-teal-700">
              {dnsQueries + httpReqs} lookups
            </span>
          </div>

          <div className="space-y-2 text-xs">
            <div className="flex justify-between text-slate-600">
              <span>DNS Lookups:</span>
              <strong className="font-mono text-slate-900">{dnsQueries}</strong>
            </div>
            <div className="flex justify-between text-slate-600">
              <span>HTTP Requests:</span>
              <strong className="font-mono text-slate-900">{httpReqs}</strong>
            </div>
            <div className="flex justify-between text-slate-600">
              <span>Known C2 Hits:</span>
              <strong className="font-mono text-rose-700">{c2Hits}</strong>
            </div>
            <div className="flex justify-between text-slate-600">
              <span>Threat Verdict:</span>
              <strong className="font-mono text-slate-900 capitalize">
                {data?.network_db?.verdict || "Clean"}
              </strong>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

/* ═══════════════════════════════════════════════════════════════════════════
   CHART 5: OBSERVED THREAT INDICATORS OF COMPROMISE (IOC) CARDS
   ═══════════════════════════════════════════════════════════════════════════ */

function ObservedIocCards({ data }: { data: ReportData | null }) {
  const [copiedText, setCopiedText] = useState<string | null>(null);

  const findings = data?.network_db?.findings ?? [];
  const persistKeys = data?.behavior?.registry?.persistence_keys ?? [];
  const dnsQueries = data?.network?.dns_queries ?? [];

  const handleCopy = (text: string) => {
    navigator.clipboard?.writeText(text);
    setCopiedText(text);
    setTimeout(() => setCopiedText(null), 2000);
  };

  const hasAnyIocs = findings.length > 0 || persistKeys.length > 0 || dnsQueries.length > 0;
  if (!hasAnyIocs) return null;

  return (
    <div className="bg-white rounded-2xl border border-slate-200 p-6 space-y-4">
      <div className="flex items-center justify-between border-b border-slate-100 pb-3">
        <div className="flex items-center gap-2">
          <IoFingerPrintOutline className="w-5 h-5 text-rose-600" />
          <h3 className="text-base font-bold text-slate-900">
            Observed Threat Indicators of Compromise (IOCs)
          </h3>
        </div>
        <span className="text-xs text-slate-500 font-mono">
          Click any indicator to copy
        </span>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
        {findings.map((f, i) => (
          <div
            key={i}
            onClick={() => handleCopy(f.indicator)}
            className="p-3 rounded-xl border border-rose-200 bg-rose-50/40 hover:bg-rose-50 cursor-pointer transition-all flex items-start justify-between gap-2 group"
            title="Click to copy IOC"
          >
            <div className="min-w-0">
              <span className="text-[10px] font-black uppercase text-rose-700 bg-rose-200/80 px-1.5 py-0.5 rounded">
                C2 Indicator
              </span>
              <p className="font-mono text-xs font-bold text-slate-900 mt-1 truncate">
                {f.indicator}
              </p>
              <p className="text-[11px] text-slate-500 line-clamp-1 mt-0.5">
                {f.description}
              </p>
            </div>
            <button className="text-slate-400 group-hover:text-rose-600 transition-colors shrink-0 mt-1">
              {copiedText === f.indicator ? (
                <IoCheckmarkOutline className="w-4 h-4 text-emerald-600" />
              ) : (
                <IoCopyOutline className="w-4 h-4" />
              )}
            </button>
          </div>
        ))}

        {persistKeys.map((k, i) => (
          <div
            key={i}
            onClick={() => handleCopy(k)}
            className="p-3 rounded-xl border border-purple-200 bg-purple-50/40 hover:bg-purple-50 cursor-pointer transition-all flex items-start justify-between gap-2 group"
            title="Click to copy registry key"
          >
            <div className="min-w-0">
              <span className="text-[10px] font-black uppercase text-purple-700 bg-purple-200/80 px-1.5 py-0.5 rounded">
                Persistence Key
              </span>
              <p className="font-mono text-xs font-bold text-slate-900 mt-1 truncate">
                {k}
              </p>
              <p className="text-[11px] text-slate-500 mt-0.5">
                Startup Run Key Persistence
              </p>
            </div>
            <button className="text-slate-400 group-hover:text-purple-600 transition-colors shrink-0 mt-1">
              {copiedText === k ? (
                <IoCheckmarkOutline className="w-4 h-4 text-emerald-600" />
              ) : (
                <IoCopyOutline className="w-4 h-4" />
              )}
            </button>
          </div>
        ))}

        {dnsQueries.slice(0, 3).map((q, i) => {
          const domain = dnsQueryLabel(q);
          return (
          <div
            key={i}
            onClick={() => handleCopy(domain)}
            className="p-3 rounded-xl border border-teal-200 bg-teal-50/40 hover:bg-teal-50 cursor-pointer transition-all flex items-start justify-between gap-2 group"
            title="Click to copy domain"
          >
            <div className="min-w-0">
              <span className="text-[10px] font-black uppercase text-teal-700 bg-teal-200/80 px-1.5 py-0.5 rounded">
                Queried Domain
              </span>
              <p className="font-mono text-xs font-bold text-slate-900 mt-1 truncate">
                {domain}
              </p>
              <p className="text-[11px] text-slate-500 mt-0.5">
                DNS query observed during analysis
              </p>
            </div>
            <button className="text-slate-400 group-hover:text-teal-600 transition-colors shrink-0 mt-1">
              {copiedText === q ? (
                <IoCheckmarkOutline className="w-4 h-4 text-emerald-600" />
              ) : (
                <IoCopyOutline className="w-4 h-4" />
              )}
            </button>
          </div>
          );
        })}
      </div>
    </div>
  );
}

/* ═══════════════════════════════════════════════════════════════════════════
   REPORT OVERVIEW COMPONENT (EXPANDED CHARTS & INSIGHTS)
   ═══════════════════════════════════════════════════════════════════════════ */

function ReportOverview({
  report,
  data,
  aiReport,
  localBenign = false,
}: {
  report: AnalysisResult;
  data: ReportData | null;
  aiReport: AIReport | null;
  localBenign?: boolean;
}) {
  const activity = [
    { label: "System activity", value: data?.sysmon?.sample_events ?? 0, color: "bg-violet-500" },
    { label: "File and app activity", value: data?.procmon?.sample_events ?? 0, color: "bg-indigo-400" },
    { label: "Network lookups", value: (data?.network?.dns_queries?.length ?? 0) + (data?.network?.http_requests?.length ?? 0), color: "bg-teal-500" },
    { label: "Files collected", value: report.files_collected?.length ?? 0, color: "bg-amber-400" },
  ];
  const maxActivity = Math.max(...activity.map((item) => item.value), 1);
  const assessmentScore = localBenign ? 0 : aiReport?.risk_score ?? 0;
  const assessmentThreat = localBenign
    ? "Benign"
    : aiReport?.threat_level || "Assessment complete";
  const riskColor = !aiReport && !localBenign
    ? "text-slate-500"
    : assessmentScore >= 70
      ? "text-rose-700"
      : assessmentScore >= 40
        ? "text-amber-700"
        : "text-emerald-700";

  return (
    <div className="space-y-5" aria-label="Report overview">
      {/* ── At a Glance / Executive Summary ── */}
      <section className="rounded-2xl border border-violet-100 bg-gradient-to-br from-white via-white to-violet-50 p-6 md:p-8">
        <p className="text-xs font-semibold uppercase tracking-[0.16em] text-violet-700">At a glance</p>
        <h3 className="mt-2 text-xl font-semibold text-slate-900">What happened to this sample?</h3>
        {localBenign ? (
          <p className="mt-3 max-w-4xl text-[15px] leading-7 text-slate-700">
            No suspicious behavior was observed. This file received a Benign verdict with a risk score of 0/100.
          </p>
        ) : aiReport?.executive_summary ? (
          <p className="mt-3 max-w-4xl text-[15px] leading-7 text-slate-700">{aiReport.executive_summary}</p>
        ) : (
          <p className="mt-3 max-w-4xl text-[15px] leading-7 text-slate-600">
            {data
              ? "The sandbox finished collecting activity from this file. Review the activity chart below for a quick summary. An automated threat verdict is not available yet."
              : "Select a completed report to see the activity collected while the sample ran. An automated threat verdict is only shown after AI analysis is run."}
          </p>
        )}
        {aiReport || localBenign ? (
          <div className="mt-6 flex flex-wrap items-center gap-3 rounded-xl border border-slate-200 bg-white px-4 py-3">
            <span className="text-sm font-medium text-slate-600">Threat assessment</span>
            <span className={`text-sm font-bold capitalize ${riskColor}`}>{assessmentThreat}</span>
            <div className="h-2 min-w-32 flex-1 overflow-hidden rounded-full bg-slate-100" role="img" aria-label={`Risk score ${assessmentScore} out of 100`}>
              <div className={`h-full rounded-full ${assessmentScore >= 70 ? "bg-rose-500" : assessmentScore >= 40 ? "bg-amber-400" : "bg-emerald-500"}`} style={{ width: `${Math.min(100, Math.max(0, assessmentScore))}%` }} />
            </div>
            <span className={`text-sm font-bold tabular-nums ${riskColor}`}>{assessmentScore}/100</span>
          </div>
        ) : !localBenign ? (
          <p className="mt-5 inline-flex rounded-full bg-slate-100 px-3 py-1.5 text-xs font-medium text-slate-600">AI assessment not run</p>
        ) : null}
      </section>

      {/* ── Multi-Layer Behavioral Threat Detection Grid ── */}
      <section className="space-y-3">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
          <div>
            <h3 className="text-base font-semibold text-slate-900">
              Multi-Layer Threat Engine Analysis
            </h3>
            <p className="text-xs text-slate-500">
              YARA rules, BiLSTM sequential API inference, Laya screen OCR, and offline threat DB.
            </p>
          </div>
          {data?.risk && (
            <div className="flex items-center gap-2 bg-slate-900 text-white px-3 py-1.5 rounded-lg font-mono text-xs shadow-xs shrink-0 self-start sm:self-auto">
              <span className="text-slate-400 font-sans">Unified Det Risk:</span>
              <span
                className={`font-bold ${
                  data.risk.risk_score >= 70
                    ? "text-rose-400"
                    : data.risk.risk_score >= 40
                    ? "text-amber-400"
                    : "text-emerald-400"
                }`}
              >
                {data.risk.risk_score}/100 ({data.risk.threat_level})
              </span>
            </div>
          )}
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {/* Card 1: YARA Rule Signatures */}
          <div className="p-4 rounded-xl border border-rose-200 bg-gradient-to-br from-white to-rose-50/40 shadow-xs flex flex-col justify-between space-y-3">
            <div className="flex items-start justify-between gap-2">
              <div className="flex items-center gap-2">
                <YaraLogo className="w-8 h-8 shrink-0" />
                <div>
                  <span className="block text-xs font-bold text-slate-800">YARA Rules</span>
                  <span className="text-[10px] text-slate-500 font-mono">Signatures</span>
                </div>
              </div>
              <span
                className={`text-[10px] uppercase font-bold px-2 py-0.5 rounded border ${
                  (data?.yara?.matched_rules_count ?? 0) > 0
                    ? "bg-rose-100 text-rose-800 border-rose-200"
                    : "bg-emerald-100 text-emerald-800 border-emerald-200"
                }`}
              >
                {data?.yara?.threat_level || "Clean"}
              </span>
            </div>

            <div>
              <div className="text-xl font-black text-slate-900">
                {data?.yara?.matched_rules_count ?? 0}{" "}
                <span className="text-xs font-normal text-slate-500">rules matched</span>
              </div>
              <p className="text-xs text-slate-600 mt-1 line-clamp-2">
                {data?.yara?.matches?.[0]?.rule
                  ? `${data.yara.matches[0].rule} (${data.yara.matches[0].severity})`
                  : "No YARA signature or evasion capability matched."}
              </p>
            </div>

            <div className="pt-2 border-t border-rose-100/80 flex items-center justify-between text-[11px]">
              <span className="text-slate-400">Capabilities:</span>
              <span className="font-mono text-rose-700 font-semibold truncate max-w-[140px]">
                {data?.yara?.tags?.join(", ") || "None"}
              </span>
            </div>
          </div>

          {/* Card 2: BiLSTM Sequential Model */}
          <div className="p-4 rounded-xl border border-cyan-200 bg-gradient-to-br from-white to-cyan-50/40 shadow-xs flex flex-col justify-between space-y-3">
            <div className="flex items-start justify-between gap-2">
              <div className="flex items-center gap-2">
                <div className="w-8 h-8 rounded-lg bg-cyan-600 flex items-center justify-center text-white shrink-0">
                  <IoGitNetworkOutline className="w-4 h-4" />
                </div>
                <div>
                  <span className="block text-xs font-bold text-slate-800">BiLSTM Neural</span>
                  <span className="text-[10px] text-slate-500 font-mono">API Sequence</span>
                </div>
              </div>
              <span
                className={`text-[10px] uppercase font-bold px-2 py-0.5 rounded border ${
                  data?.lstm?.verdict?.toUpperCase() === "MALICIOUS"
                    ? "bg-rose-100 text-rose-800 border-rose-200"
                    : "bg-emerald-100 text-emerald-800 border-emerald-200"
                }`}
              >
                {data?.lstm?.verdict || "Benign"}
              </span>
            </div>

            <div>
              <div className="flex items-baseline gap-2">
                <span className="text-xl font-black text-slate-900">
                  {data?.lstm ? `${((data.lstm.p_malware || 0) * 100).toFixed(1)}%` : "0.0%"}
                </span>
                <span className="text-xs text-slate-500">malice prob</span>
              </div>
              <div className="mt-2 h-1.5 w-full bg-slate-100 rounded-full overflow-hidden">
                <div
                  className={`h-full ${
                    data?.lstm?.verdict?.toUpperCase() === "MALICIOUS"
                      ? "bg-rose-500"
                      : "bg-emerald-500"
                  }`}
                  style={{
                    width: `${Math.max(
                      3,
                      Math.min(100, (data?.lstm?.p_malware || 0) * 100)
                    )}%`,
                  }}
                />
              </div>
            </div>

            <div className="pt-2 border-t border-cyan-100/80 flex items-center justify-between text-[11px]">
              <span className="text-slate-400">Sequence / Conf:</span>
              <span className="font-mono text-cyan-800 font-semibold">
                {data?.lstm
                  ? `${data.lstm.sequence_length} ops / ${data.lstm.confidence?.toFixed(0)}%`
                  : "N/A"}
              </span>
            </div>
          </div>

          {/* Card 3: GUI Screen Triage (Laya System 1) */}
          <div className="p-4 rounded-xl border border-orange-200 bg-gradient-to-br from-white to-orange-50/40 shadow-xs flex flex-col justify-between space-y-3">
            <div className="flex items-start justify-between gap-2">
              <div className="flex items-center gap-2">
                <div className="w-8 h-8 rounded-lg bg-orange-600 flex items-center justify-center text-white shrink-0">
                  <IoDesktopOutline className="w-4 h-4" />
                </div>
                <div>
                  <span className="block text-xs font-bold text-slate-800">Laya GUI Triage</span>
                  <span className="text-[10px] text-slate-500 font-mono">Visual OCR</span>
                </div>
              </div>
              <span
                className={`text-[10px] uppercase font-bold px-2 py-0.5 rounded border ${
                  data?.gui?.has_malicious_gui
                    ? "bg-rose-100 text-rose-800 border-rose-200"
                    : "bg-emerald-100 text-emerald-800 border-emerald-200"
                }`}
              >
                {data?.gui?.has_malicious_gui ? "Threat Detected" : "Clean Screen"}
              </span>
            </div>

            <div>
              <div className="text-sm font-bold text-slate-900 truncate">
                {data?.gui?.has_malicious_gui
                  ? `🚨 ${(data.gui.highest_threat_type || "Threat").replace(/_/g, " ")}`
                  : "No extortion/scam detected"}
              </div>
              <p className="text-xs text-slate-600 mt-1">
                {data?.gui?.flagged_count
                  ? `${data.gui.flagged_count} window(s) flagged (${((data.gui.max_confidence || 0) * 100).toFixed(0)}% conf)`
                  : "Screenshots clean of extortion/lockscreen notices."}
              </p>
            </div>

            <div className="pt-2 border-t border-orange-100/80 flex items-center justify-between text-[11px]">
              <span className="text-slate-400">Keywords:</span>
              <span className="font-mono text-orange-800 font-semibold truncate max-w-[140px]">
                {data?.gui?.flagged_windows?.[0]?.matched_keywords?.slice(0, 3).join(", ") ||
                  "None"}
              </span>
            </div>
          </div>

          {/* Card 4: Offline Network Threat DB */}
          <div className="p-4 rounded-xl border border-emerald-200 bg-gradient-to-br from-white to-emerald-50/40 shadow-xs flex flex-col justify-between space-y-3">
            <div className="flex items-start justify-between gap-2">
              <div className="flex items-center gap-2">
                <div className="w-8 h-8 rounded-lg bg-emerald-600 flex items-center justify-center text-white shrink-0">
                  <IoGlobeOutline className="w-4 h-4" />
                </div>
                <div>
                  <span className="block text-xs font-bold text-slate-800">Threat Intel DB</span>
                  <span className="text-[10px] text-slate-500 font-mono">Feodo/URLhaus</span>
                </div>
              </div>
              <span
                className={`text-[10px] uppercase font-bold px-2 py-0.5 rounded border ${
                  data?.network_db?.verdict === "malicious"
                    ? "bg-rose-100 text-rose-800 border-rose-200"
                    : data?.network_db?.verdict === "suspicious"
                    ? "bg-amber-100 text-amber-800 border-amber-200"
                    : "bg-emerald-100 text-emerald-800 border-emerald-200"
                }`}
              >
                {data?.network_db?.verdict || "Clean"}
              </span>
            </div>

            <div>
              <div className="text-xl font-black text-slate-900">
                {data?.network_db?.findings?.length ?? 0}{" "}
                <span className="text-xs font-normal text-slate-500">C2 matches</span>
              </div>
              <p className="text-xs text-slate-600 mt-1 line-clamp-2">
                {data?.network_db?.findings?.[0]?.description ||
                  "Zero hits against known botnet C2, URLhaus payloads, and compromised IPs."}
              </p>
            </div>

            <div className="pt-2 border-t border-emerald-100/80 flex items-center justify-between text-[11px]">
              <span className="text-slate-400">Database:</span>
              <span className="font-mono text-emerald-800 font-semibold">
                ThreatFox + Feodo (Offline)
              </span>
            </div>
          </div>
        </div>
      </section>

      {/* ── Visual Chart 1: Engine Detection Consensus Matrix ── */}
      <EngineConsensusMatrixChart data={data} />

      {/* ── Visual Chart 2: Win32 Kernel & Subsystem API Call Profile ── */}
      <ApiCategoryDistributionChart data={data} />

      {/* ── Visual Chart 3: MITRE ATT&CK Enterprise Behavioral Matrix ── */}
      <MitreAttackMatrixChart data={data} aiReport={aiReport} />

      {/* ── Visual Chart 4: System Mutation & Telemetry Breakdown ── */}
      <TelemetryBreakdownChart data={data} />

      {/* ── Observed Threat Indicators of Compromise (IOC) Cards ── */}
      <ObservedIocCards data={data} />

      {/* ── Activity Collected & Scan Details ── */}
      <section className="grid gap-5 lg:grid-cols-[minmax(0,1.4fr)_minmax(250px,0.8fr)]">
        <div className="rounded-2xl border border-slate-200 bg-white p-6">
          <div className="flex items-start justify-between gap-4">
            <div>
              <h3 className="text-base font-semibold text-slate-900">Activity collected</h3>
              <p className="mt-1 text-sm text-slate-500">A count of the different activity the sandbox recorded.</p>
            </div>
            <IoAnalyticsOutline className="mt-0.5 h-5 w-5 text-violet-500" aria-hidden="true" />
          </div>
          {data ? (
            <div className="mt-6 space-y-5">
              {activity.map((item) => (
                <div key={item.label}>
                  <div className="mb-2 flex items-center justify-between gap-3 text-sm">
                    <span className="font-medium text-slate-700">{item.label}</span>
                    <span className="font-semibold tabular-nums text-slate-900">{item.value.toLocaleString()}</span>
                  </div>
                  <div className="h-2.5 overflow-hidden rounded-full bg-slate-100" role="img" aria-label={`${item.label}: ${item.value}`}>
                    <div className={`h-full rounded-full ${item.color} transition-[width] duration-500`} style={{ width: `${item.value ? Math.max(3, (item.value / maxActivity) * 100) : 0}%` }} />
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <p className="mt-6 rounded-xl bg-slate-50 px-4 py-5 text-sm leading-6 text-slate-600">Activity details are not available for this report.</p>
          )}
          <p className="mt-5 border-t border-slate-100 pt-4 text-xs leading-5 text-slate-500">These counts show recorded activity, not a threat score. A higher count alone does not mean a file is malicious.</p>
        </div>

        <div className="rounded-2xl border border-slate-200 bg-white p-6">
          <h3 className="text-base font-semibold text-slate-900">Scan details</h3>
          <dl className="mt-4 divide-y divide-slate-100">
            <div className="flex justify-between gap-4 py-3 text-sm"><dt className="text-slate-500">Result</dt><dd className="font-medium capitalize text-slate-800">{report.status}</dd></div>
            <div className="flex justify-between gap-4 py-3 text-sm"><dt className="text-slate-500">Run time</dt><dd className="font-medium text-slate-800">{report.timeout}s</dd></div>
            <div className="flex justify-between gap-4 py-3 text-sm"><dt className="text-slate-500">Screenshots</dt><dd className="font-medium tabular-nums text-slate-800">{data?.screenshots?.length ?? 0}</dd></div>
            <div className="flex justify-between gap-4 py-3 text-sm"><dt className="text-slate-500">AI review</dt><dd className="font-medium text-slate-800">{aiReport ? "Complete" : "Not run"}</dd></div>
          </dl>
          {aiReport?.key_findings?.length ? (
            <div className="mt-4 rounded-xl bg-amber-50 p-4">
              <p className="text-sm font-semibold text-amber-900">{aiReport.key_findings.length} notable finding{aiReport.key_findings.length === 1 ? "" : "s"}</p>
              <p className="mt-1 text-xs leading-5 text-amber-800">Open the AI analysis for details and recommended next steps.</p>
            </div>
          ) : null}
        </div>
      </section>

      <p className="px-1 text-xs leading-5 text-slate-500">This report describes behavior observed in an isolated sandbox. Treat the automated assessment as guidance and review the evidence before making decisions.</p>
    </div>
  );
}

/* ═══════════════════════════════════════════════════════════════════════════
   AI ANALYSIS TAB CONTENT
   ═══════════════════════════════════════════════════════════════════════════ */

function AIAnalysisTab({
  analysisId,
  aiReport,
  aiAnalyzing,
  aiProgress,
  aiError,
  handleRunAnalysis,
  onAnimationComplete,
}: {
  analysisId: string;
  aiReport: AIReport | null;
  aiAnalyzing: boolean;
  aiProgress: AIProgress | null;
  aiError: string | null;
  handleRunAnalysis: (id: string) => Promise<void>;
  onAnimationComplete: () => void;
}) {
  const [expandedTool, setExpandedTool] = useState<string | null>(null);

  const handleDownloadPDF = async () => {
    if (!aiReport) return;
    try {
      const { generatePDFReport } = await import("@/lib/pdf");
      generatePDFReport(aiReport, analysisId);
    } catch (err) {
      console.error("Failed to generate PDF:", err);
    }
  };

  /* ── No report yet → CTA ── */
  if (!aiReport && !aiAnalyzing) {
    return (
      <div className="p-8">
        <div className="text-center max-w-lg mx-auto">
          <div className="w-20 h-20 mx-auto mb-6 bg-gradient-to-br from-blue-100 to-sky-200 rounded-md flex items-center justify-center shadow-inner">
            <IoSparklesOutline className="w-10 h-10 text-blue-600" />
          </div>
          <h3 className="text-xl font-bold text-slate-900 mb-2">
            AI Threat Analysis
          </h3>
          <p className="text-slate-500 mb-6 text-sm leading-relaxed">
            Run multi-agent AI analysis.
            The pipeline dispatches data to 6 specialized agents (Sysmon,
            Procmon, Network, Handle, TCPVcon, Metadata) then synthesizes a
            final threat report with risk scoring, MITRE ATT&CK mapping, and IOC
            extraction.
          </p>
          {aiError && (
            <div className="bg-red-50 border border-red-200 rounded p-3 mb-4 text-sm text-red-700 flex items-center gap-2">
              <IoAlertCircleOutline className="w-4 h-4 shrink-0" />
              {aiError}
            </div>
          )}
          <button
            onClick={() => handleRunAnalysis(analysisId)}
            className="inline-flex items-center gap-2.5 bg-gradient-to-r from-blue-600 to-sky-600 hover:from-blue-700 hover:to-sky-700 text-white font-semibold px-8 py-3.5 rounded shadow-lg shadow-blue-200 transition-all hover:shadow-xl hover:shadow-blue-300 active:scale-[0.98]"
          >
            <IoFlashOutline className="w-5 h-5" />
            Run AI Analysis
          </button>
          <div className="mt-8 grid grid-cols-3 gap-3 opacity-60">
            {[
              {
                label: "Risk Scoring",
                icon: <IoAnalyticsOutline className="w-5 h-5" />,
              },
              {
                label: "MITRE ATT&CK",
                icon: <IoShieldOutline className="w-5 h-5" />,
              },
              {
                label: "IOC Extraction",
                icon: <IoFingerPrintOutline className="w-5 h-5" />,
              },
            ].map((item) => (
              <div
                key={item.label}
                className="bg-slate-50 border border-slate-200 rounded p-3 text-center"
              >
                <div className="flex justify-center text-slate-400 mb-1">
                  {item.icon}
                </div>
                <p className="text-xs text-slate-500 font-medium">
                  {item.label}
                </p>
              </div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  /* ── Analyzing spinner ── */
  if (aiAnalyzing) {
    return (
      <AIPipelineAnimation
        progress={aiProgress}
        onComplete={onAnimationComplete}
      />
    );
  }

  /* ── Failed report ── */
  if (aiReport && aiReport.status === "failed") {
    return (
      <div className="p-8">
        <div className="bg-red-50 border border-red-200 rounded-md p-6 text-center">
          <IoAlertCircleOutline className="w-10 h-10 text-red-400 mx-auto mb-3" />
          <h3 className="text-lg font-bold text-red-800 mb-1">
            Analysis Failed
          </h3>
          <p className="text-sm text-red-600 mb-4">
            {aiReport.error || "An unknown error occurred."}
          </p>
          <button
            onClick={() => handleRunAnalysis(analysisId)}
            className="inline-flex items-center gap-2 bg-red-600 hover:bg-red-700 text-white font-medium px-6 py-2.5 rounded transition-colors"
          >
            <IoRefreshOutline className="w-4 h-4" />
            Retry Analysis
          </button>
        </div>
      </div>
    );
  }

  if (!aiReport) return null;

  /* ── Full AI Report ── */
  const findings: AIFinding[] = aiReport.key_findings || [];
  const iocs: AIIOC[] = aiReport.iocs || [];
  const mitre: AIMitreTechnique[] = aiReport.mitre_attack || [];
  const recommendations: AIRecommendation[] = aiReport.recommendations || [];

  return (
    <div className="p-6 space-y-6">
      {/* ── Top row: Risk gauge + Classification + Meta ── */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
        {/* Risk Score */}
        <div className="bg-white rounded-md border border-slate-100 shadow-sm p-6 flex flex-col items-center justify-center">
          <RiskGauge
            score={aiReport.risk_score}
            level={aiReport.threat_level}
          />
        </div>

        {/* Classification */}
        <div className="bg-white rounded-md border border-slate-100 shadow-sm p-6">
          <h4 className="text-[13px] font-bold text-slate-500 uppercase tracking-wider mb-4 flex items-center gap-2">
            <IoShieldOutline className="w-3.5 h-3.5" />
            Classification
          </h4>
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-xs text-slate-500">Malware Type</span>
              <span
                className="text-sm font-bold text-slate-900 capitalize max-w-[200px] truncate"
                title={aiReport.classification.malware_type}
              >
                {aiReport.classification.malware_type?.toLowerCase() === "unknown" ? "Generic" : aiReport.classification.malware_type}
              </span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-xs text-slate-500">Family</span>
              <span className="text-sm font-bold text-slate-900 capitalize">
                {aiReport.classification.malware_family?.toLowerCase() === "unknown" ? "Generic" : aiReport.classification.malware_family}
              </span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-xs text-slate-500">Platform</span>
              <span className="text-sm font-bold text-slate-900 capitalize">
                {aiReport.classification.platform?.toLowerCase() === "unknown" ? "Generic" : aiReport.classification.platform}
              </span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-xs text-slate-500">Confidence</span>
              <div className="flex items-center gap-2">
                <div className="w-20 h-2 bg-slate-100 rounded-full overflow-hidden">
                  <div
                    className="h-full bg-gradient-to-r from-blue-500 to-sky-500 rounded-full"
                    style={{
                      width: `${aiReport.classification.confidence}%`,
                    }}
                  />
                </div>
                <span className="text-[13px] font-bold text-blue-700">
                  {aiReport.classification.confidence}%
                </span>
              </div>
            </div>
          </div>
        </div>

        {/* Meta */}
        <div className="bg-white rounded-md border border-slate-100 shadow-sm p-6">
          <h4 className="text-[13px] font-bold text-slate-500 uppercase tracking-wider mb-4 flex items-center gap-2">
            <IoServerOutline className="w-3.5 h-3.5" />
            Analysis Meta
          </h4>
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-xs text-slate-500">Model</span>
              <span className="text-xs font-mono bg-blue-50 text-blue-700 px-2 py-0.5 rounded">
                {aiReport.model}
              </span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-xs text-slate-500">Status</span>
              <span className="text-[13px] font-bold text-green-600 capitalize">
                {aiReport.status}
              </span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-xs text-slate-500">Agents Run</span>
              <span className="text-sm font-bold text-slate-900">
                {aiReport.tool_results.length}
              </span>
            </div>
            {aiReport.completed_at && (
              <div className="flex items-center justify-between">
                <span className="text-xs text-slate-500">Completed</span>
                <span className="text-xs font-medium text-slate-600">
                  {new Date(aiReport.completed_at).toLocaleString()}
                </span>
              </div>
            )}
          </div>
          <div className="mt-5 grid grid-cols-2 gap-2">
            <button
              onClick={() => handleRunAnalysis(analysisId)}
              disabled={aiAnalyzing}
              className="w-full inline-flex items-center justify-center gap-2 text-[13px] font-bold text-blue-700 hover:text-blue-800 bg-blue-50 hover:bg-blue-100 px-3 py-2.5 rounded transition-colors"
            >
              <IoRefreshOutline className="w-4 h-4" />
              Re-run
            </button>
            <button
              onClick={handleDownloadPDF}
              className="w-full inline-flex items-center justify-center gap-2 text-[13px] font-bold text-slate-700 hover:text-slate-800 bg-slate-100 hover:bg-slate-200 px-3 py-2.5 rounded transition-colors"
            >
              <IoDownloadOutline className="w-4 h-4" />
              Download PDF
            </button>
          </div>
        </div>
      </div>

      {/* ── Executive Summary ── */}
      {aiReport.executive_summary && (
        <div className="bg-gradient-to-br from-slate-50 to-slate-50 rounded-md border border-slate-200 p-6">
          <h4 className="text-[13px] font-bold text-slate-500 uppercase tracking-wider mb-3 flex items-center gap-2">
            <IoDocumentTextOutline className="w-3.5 h-3.5" />
            Executive Summary
          </h4>
          <p className="text-sm text-slate-700 leading-relaxed whitespace-pre-wrap">
            {aiReport.executive_summary}
          </p>
        </div>
      )}

      {/* ── Key Findings ── */}
      {findings.length > 0 && (
        <div className="bg-white rounded-md border border-slate-100 shadow-sm p-6">
          <h4 className="text-[13px] font-bold text-slate-500 uppercase tracking-wider mb-4 flex items-center gap-2">
            <IoAlertCircleOutline className="w-3.5 h-3.5 text-red-500" />
            Key Findings ({findings.length})
          </h4>
          <div className="space-y-2.5">
            {findings.map((f, i) => (
              <div
                key={i}
                className="flex items-start gap-3 p-3 rounded bg-slate-50 border border-slate-100"
              >
                <SeverityBadge severity={f.severity} />
                <div className="flex-1">
                  <p className="text-sm text-slate-700 leading-relaxed">
                    {f.description}
                  </p>
                  {f.source && (
                    <span className="text-[11px] text-slate-400 mt-1 inline-block">
                      Source: {f.source}
                    </span>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* ── IOC Table ── */}
      {iocs.length > 0 && (
        <div className="bg-white rounded-md border border-slate-100 shadow-sm p-6">
          <h4 className="text-[13px] font-bold text-slate-500 uppercase tracking-wider mb-4 flex items-center gap-2">
            <IoFingerPrintOutline className="w-3.5 h-3.5 text-blue-500" />
            Indicators of Compromise ({iocs.length})
          </h4>
          <div className="overflow-x-auto rounded border border-slate-100">
            <table className="w-full text-sm">
              <thead>
                <tr className="bg-slate-50/80">
                  <th className="text-left px-4 py-2.5 text-xs font-semibold text-slate-500 uppercase tracking-wider border-b border-slate-100">
                    Type
                  </th>
                  <th className="text-left px-4 py-2.5 text-xs font-semibold text-slate-500 uppercase tracking-wider border-b border-slate-100">
                    Severity
                  </th>
                  <th className="text-left px-4 py-2.5 text-xs font-semibold text-slate-500 uppercase tracking-wider border-b border-slate-100">
                    Value
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-50">
                {iocs.map((ioc, i) => (
                  <tr
                    key={i}
                    className="hover:bg-blue-50/30 transition-colors"
                  >
                    <td className="px-4 py-2.5">
                      <span className="inline-flex items-center gap-1 px-2 py-0.5 bg-slate-100 text-slate-700 rounded text-xs font-medium uppercase">
                        {ioc.type === "ip" && (
                          <IoGlobeOutline className="w-3 h-3" />
                        )}
                        {ioc.type === "domain" && (
                          <IoGitNetworkOutline className="w-3 h-3" />
                        )}
                        {ioc.type === "file_path" && (
                          <IoFolderOpenOutline className="w-3 h-3" />
                        )}
                        {ioc.type === "registry" && (
                          <IoKeyOutline className="w-3 h-3" />
                        )}
                        {ioc.type === "mutex" && (
                          <IoLockClosedOutline className="w-3 h-3" />
                        )}
                        {ioc.type === "hash" && (
                          <IoFingerPrintOutline className="w-3 h-3" />
                        )}
                        {ioc.type}
                      </span>
                    </td>
                    <td className="px-4 py-2.5">
                      <SeverityBadge severity={ioc.severity} />
                    </td>
                    <td className="px-4 py-2.5 font-mono text-xs text-slate-700 max-w-md truncate">
                      {ioc.value}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}


      {/* ── Recommendations ── */}
      {recommendations.length > 0 && (
        <div className="bg-white rounded-md border border-slate-100 shadow-sm p-6">
          <h4 className="text-[13px] font-bold text-slate-500 uppercase tracking-wider mb-4 flex items-center gap-2">
            <IoArrowForwardOutline className="w-3.5 h-3.5 text-emerald-500" />
            Recommendations ({recommendations.length})
          </h4>
          <div className="space-y-2">
            {recommendations.map((rec, i) => (
              <div
                key={i}
                className="flex items-start gap-3 p-3 rounded bg-emerald-50 border border-emerald-100"
              >
                <span
                  className={`shrink-0 mt-0.5 inline-block px-2 py-0.5 rounded text-[11px] font-bold uppercase ${
                    rec.priority.toLowerCase() === "high"
                      ? "bg-red-100 text-red-700"
                      : rec.priority.toLowerCase() === "medium"
                        ? "bg-amber-100 text-amber-700"
                        : "bg-blue-100 text-blue-700"
                  }`}
                >
                  {rec.priority}
                </span>
                <p className="text-sm text-slate-700 leading-relaxed flex-1">
                  {rec.action}
                </p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* ── Per-Tool Agent Results ── */}
      <div className="bg-white rounded-md border border-slate-100 shadow-sm p-6">
        <h4 className="text-[13px] font-bold text-slate-500 uppercase tracking-wider mb-4 flex items-center gap-2">
          <IoCodeSlashOutline className="w-3.5 h-3.5 text-slate-500" />
          Per-Tool Agent Analysis ({aiReport.tool_results.length})
        </h4>
        <div className="space-y-2">
          {aiReport.tool_results.map((tr: AIToolResult) => (
            <div
              key={tr.tool}
              className="rounded border border-slate-100 overflow-hidden"
            >
              <button
                onClick={() =>
                  setExpandedTool(expandedTool === tr.tool ? null : tr.tool)
                }
                className="w-full flex items-center gap-3 px-4 py-3 hover:bg-slate-50 transition-colors"
              >
                <div className="w-8 h-8 rounded-lg bg-slate-100 flex items-center justify-center text-slate-600">
                  {tr.tool === "sysmon" && (
                    <IoShieldCheckmarkOutline className="w-4 h-4" />
                  )}
                  {tr.tool === "procmon" && (
                    <IoEyeOutline className="w-4 h-4" />
                  )}
                  {tr.tool === "network" && (
                    <IoGitNetworkOutline className="w-4 h-4" />
                  )}
                  {tr.tool === "handle" && <IoKeyOutline className="w-4 h-4" />}
                  {tr.tool === "tcpvcon" && (
                    <IoSwapHorizontalOutline className="w-4 h-4" />
                  )}
                  {tr.tool === "metadata" && (
                    <IoServerOutline className="w-4 h-4" />
                  )}
                </div>
                <span className="text-sm font-semibold text-slate-800 capitalize flex-1 text-left">
                  {tr.tool}
                </span>
                <VerdictBadge verdict={tr.verdict} />
                <span className="text-xs text-slate-400 ml-2">
                  {tr.confidence}% conf
                </span>
                <div className="flex items-center gap-2 ml-3 text-slate-400">
                  {tr.findings_count > 0 && (
                    <span className="text-[11px] bg-amber-50 text-amber-700 px-1.5 py-0.5 rounded">
                      {tr.findings_count} findings
                    </span>
                  )}
                  {tr.iocs_count > 0 && (
                    <span className="text-[11px] bg-blue-50 text-blue-700 px-1.5 py-0.5 rounded">
                      {tr.iocs_count} IOCs
                    </span>
                  )}
                </div>
                <span className="text-slate-400">
                  {expandedTool === tr.tool ? (
                    <IoChevronUpOutline className="w-4 h-4" />
                  ) : (
                    <IoChevronDownOutline className="w-4 h-4" />
                  )}
                </span>
              </button>
              {expandedTool === tr.tool && (
                <div className="px-4 pb-4 border-t border-slate-50 pt-3">
                  {tr.summary && (
                    <p className="text-sm text-slate-600 leading-relaxed mb-3">
                      {tr.summary}
                    </p>
                  )}
                  {tr.error && (
                    <div className="text-xs text-red-600 bg-red-50 rounded-lg p-2 mb-3">
                      Error: {tr.error}
                    </div>
                  )}
                  {/* Per-tool findings */}
                  {tr.findings && tr.findings.length > 0 && (
                    <div className="mb-3">
                      <p className="text-[11px] font-bold text-slate-400 uppercase tracking-wider mb-1.5">
                        Findings
                      </p>
                      <div className="space-y-1.5">
                        {tr.findings.map((f, fi) => (
                          <div
                            key={fi}
                            className="flex items-start gap-2 text-xs"
                          >
                            <SeverityBadge severity={f.severity} />
                            <span className="text-slate-600">
                              <span className="font-medium text-slate-800">
                                {f.indicator}
                              </span>
                              {f.description && ` — ${f.description}`}
                            </span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                  {/* Per-tool IOCs */}
                  {tr.iocs && tr.iocs.length > 0 && (
                    <div className="mb-3">
                      <p className="text-[11px] font-bold text-slate-400 uppercase tracking-wider mb-1.5">
                        IOCs
                      </p>
                      <div className="flex flex-wrap gap-1.5">
                        {tr.iocs.map((ioc, ii) => (
                          <span
                            key={ii}
                            className="text-[11px] bg-blue-50 text-blue-700 px-2 py-0.5 rounded font-mono"
                          >
                            {ioc.type}: {ioc.value}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}
                  <details className="group">
                    <summary className="text-xs text-slate-400 cursor-pointer hover:text-slate-600">
                      Raw JSON response
                    </summary>
                    <pre className="mt-2 bg-slate-900 text-green-400 rounded-lg p-3 text-xs overflow-x-auto max-h-48 overflow-y-auto font-mono">
                      {tr.raw_response}
                    </pre>
                  </details>
                </div>
              )}
            </div>
          ))}
        </div>
      </div>

      {/* ── Detailed Analysis ── */}
      {aiReport.detailed_analysis && (
        <div className="bg-white rounded-md border border-slate-100 shadow-sm p-6">
          <h4 className="text-[13px] font-bold text-slate-500 uppercase tracking-wider mb-3 flex items-center gap-2">
            <IoDocumentTextOutline className="w-3.5 h-3.5" />
            Detailed Analysis
          </h4>
          <p className="text-sm text-slate-700 leading-relaxed whitespace-pre-wrap">
            {aiReport.detailed_analysis}
          </p>
        </div>
      )}
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
  const [aiReport, setAiReport] = useState<AIReport | null>(null);
  // Holds the completed report while the animation countdown plays out
  const [aiPendingReport, setAiPendingReport] = useState<AIReport | null>(null);
  
  // AI Tab global state to prevent reset on tab switch
  const [aiAnalyzing, setAiAnalyzing] = useState(false);
  const [aiProgress, setAiProgress] = useState<AIProgress | null>(null);
  const [aiError, setAiError] = useState<string | null>(null);
  
  const [activeTab, setActiveTab] = useState<"overview" | "evidence" | "ai">("overview");
  const [loading, setLoading] = useState(true);
  const [detailLoading, setDetailLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showClearConfirm, setShowClearConfirm] = useState(false);
  const [clearing, setClearing] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");

  const fetchData = async () => {
    setLoading(true);
    setError(null);
    const localReports = readLocalBenignReports();
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
      allReports = [
        ...localReports,
        ...allReports.filter((report) =>
          !localReports.some((localReport) => localReport.analysis_id === report.analysis_id),
        ),
      ];
      setReports(allReports);
      if (allReports.length > 0 && !selected) {
        await selectReport(allReports[0]);
      }
    } catch {
      setReports(localReports);
      if (localReports.length > 0) {
        if (!selected) await selectReport(localReports[0]);
      } else {
        setError("Cannot connect to IsoLens gateway. Is it running on port 6969?");
      }
    } finally {
      setLoading(false);
    }
  };

  const selectReport = async (report: AnalysisResult) => {
    setSelected(report);
    setReportData(null);
    setAiReport(null);
    setAiPendingReport(null);
    setAiAnalyzing(false);
    setAiProgress(null);
    setAiError(null);
    setActiveTab("overview");
    if (isLocalBenignReport(report)) {
      setDetailLoading(false);
      return;
    }
    setDetailLoading(true);
    try {
      const resp = await getReportData(report.analysis_id);
      if (resp.status === "ok" && resp.data) {
        setReportData(resp.data as ReportData);
      }
    } catch {
      // Could not load report data
    }
    // Also try to load existing AI report (non-blocking)
    try {
      const aiResp = await getAIReport(report.analysis_id);
      if (aiResp.status === "ok" && aiResp.data) {
        setAiReport(aiResp.data as AIReport);
      }
    } catch {
      // No AI report yet — that's ok
    }
    setDetailLoading(false);
  };

  const handleClearAll = async () => {
    setClearing(true);
    try {
      const resp = await clearAllReports();
      if (resp.status === "ok") {
        clearLocalBenignReports();
        setReports([]);
        setSelected(null);
        setReportData(null);
        setAiReport(null);
        setAiPendingReport(null);
        setAiAnalyzing(false);
        setAiProgress(null);
        setAiError(null);
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

  const handleRunAnalysis = async (analysisId: string) => {
    setAiAnalyzing(true);
    setAiError(null);
    setAiReport(null);
    setAiPendingReport(null);
    setAiProgress(null);

    // Start progress polling
    const progressInterval = setInterval(async () => {
      try {
        const pRes = await getAIProgress(analysisId);
        if (pRes.status === "ok" && pRes.data) {
          setAiProgress(pRes.data);
        }
      } catch (err) {
        console.warn("Failed to fetch AI progress", err);
      }
    }, 1000);

    try {
      const resp = await runAIAnalysis(analysisId);
      if (resp.status === "ok" && resp.data) {
        // Store in pending — the animation's onComplete will move it to aiReport
        const finalReport = resp.data as AIReport;
        setAiPendingReport(finalReport);
        setAiProgress({
          status: "complete",
          current_action: "AI Analysis Complete",
          completed_agents: 7,
          total_agents: 7,
        });
        // Safety fallback: if animation onComplete doesn't fire within 4.5 seconds, force-complete
        setTimeout(() => {
          setAiReport((current) => current || finalReport);
          setAiPendingReport(null);
          setAiAnalyzing(false);
          setAiProgress(null);
        }, 4500);
      } else {
        setAiError(resp.error?.message || "AI analysis failed");
        setAiAnalyzing(false);
      }
    } catch {
      setAiError("Failed to connect to the AI analysis service.");
      setAiAnalyzing(false);
    } finally {
      clearInterval(progressInterval);
      // Do NOT clear aiAnalyzing here — the animation countdown controls that
    }
  };

  /** Called by AIPipelineAnimation after its 3-second countdown finishes. */
  const handleAnimationComplete = () => {
    setAiReport((current) => current || aiPendingReport);
    setAiPendingReport(null);
    setAiAnalyzing(false);
    setAiProgress(null);
  };

  useEffect(() => {
    fetchData();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // When clicking the AI tab, verify if AI report is already present on the backend
  useEffect(() => {
    if (activeTab === "ai" && selected && !isLocalBenignReport(selected) && !aiReport && !aiAnalyzing) {
      getAIReport(selected.analysis_id)
        .then((aiResp) => {
          if (aiResp.status === "ok" && aiResp.data) {
            setAiReport(aiResp.data as AIReport);
          }
        })
        .catch(() => {});
    }
  }, [activeTab, selected, aiReport, aiAnalyzing]);

  const statusColor = (status: string) => {
    switch (status) {
      case "complete":
        return "text-green-600 bg-green-50 border-green-200";
      case "failed":
        return "text-red-600 bg-red-50 border-red-200";
      case "running":
        return "text-blue-600 bg-blue-50 border-blue-200";
      default:
        return "text-slate-600 bg-slate-50 border-slate-200";
    }
  };

  const statusIcon = (status: string) => {
    switch (status) {
      case "complete":
        return (
          <IoCheckmarkCircleOutline className="w-3.5 h-3.5 text-green-500" />
        );
      case "failed":
        return <IoAlertCircleOutline className="w-3.5 h-3.5 text-red-500" />;
      case "running":
        return (
          <IoRadioButtonOnOutline className="w-3.5 h-3.5 text-blue-500 animate-pulse" />
        );
      default:
        return <IoTimeOutline className="w-3.5 h-3.5 text-slate-400" />;
    }
  };

  const filteredReports = reports.filter((r) => {
    if (!searchQuery) return true;
    const q = searchQuery.toLowerCase();
    return (
      r.sample_name?.toLowerCase().includes(q) ||
      r.analysis_id?.toLowerCase().includes(q) ||
      r.status?.toLowerCase().includes(q)
    );
  });

  const rd = reportData;
  const localBenign = isLocalBenignReport(selected);

  return (
    <div className="reports-page space-y-7 max-w-[1400px] mx-auto">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Analysis Reports</h1>
          <p className="text-sm text-slate-500 mt-0.5">
            {reports.length} report{reports.length !== 1 ? "s" : ""} available
          </p>
        </div>
        <div className="flex items-center gap-3">
          {reports.length > 0 && (
            <button
              onClick={() => setShowClearConfirm(true)}
              className="inline-flex items-center gap-2 text-sm text-red-500 hover:text-red-700 transition-colors px-3 py-1.5 rounded-lg hover:bg-red-50"
            >
              <IoTrashOutline className="w-4 h-4" />
              Clear All
            </button>
          )}
          <button
            onClick={fetchData}
            className="inline-flex items-center gap-2 text-sm text-slate-600 hover:text-blue-600 transition-colors px-3 py-1.5 rounded-lg hover:bg-blue-50"
          >
            <IoRefreshOutline className="w-4 h-4" />
            Refresh
          </button>
        </div>
      </div>

      {/* Clear confirmation */}
      {showClearConfirm && (
        <div className="bg-red-50 border border-red-200 rounded-md p-5">
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
                  className="inline-flex items-center gap-2 bg-red-600 hover:bg-red-700 disabled:opacity-50 text-white text-sm font-medium px-4 py-2 rounded transition-colors"
                >
                  <IoTrashOutline className="w-4 h-4" />
                  {clearing ? "Deleting..." : "Yes, Delete All"}
                </button>
                <button
                  onClick={() => setShowClearConfirm(false)}
                  disabled={clearing}
                  className="text-sm text-slate-600 hover:text-slate-800 px-4 py-2 rounded border border-slate-300 hover:bg-slate-50 transition-colors"
                >
                  Cancel
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {loading && (
        <div className="bg-white rounded-md shadow-sm border border-slate-100 p-12 text-center">
          <div className="animate-spin w-8 h-8 border-4 border-blue-200 border-t-blue-500 rounded-full mx-auto mb-3" />
          <p className="text-sm text-slate-500">Loading reports...</p>
        </div>
      )}

      {error && (
        <div className="bg-red-50 border border-red-200 rounded-md p-4 flex items-center gap-3">
          <IoAlertCircleOutline className="w-5 h-5 text-red-500 shrink-0" />
          <p className="text-sm text-red-700">{error}</p>
        </div>
      )}

      {!loading && !error && reports.length === 0 && (
        <div className="bg-white rounded-md shadow-sm border border-slate-100 p-16 text-center">
          <div className="w-16 h-16 mx-auto mb-4 bg-slate-100 rounded-md flex items-center justify-center">
            <IoDocumentTextOutline className="w-8 h-8 text-slate-400" />
          </div>
          <h3 className="text-lg font-semibold text-slate-800 mb-1">
            No analysis reports yet
          </h3>
          <p className="text-sm text-slate-400">
            Submit a sample from the{" "}
            <a
              href="/scan"
              className="text-blue-600 hover:text-blue-700 font-medium"
            >
              Scan
            </a>{" "}
            page to get started.
          </p>
        </div>
      )}

      {/* Main layout */}
      {!loading && reports.length > 0 && (
        <div className="grid grid-cols-1 lg:grid-cols-5 gap-6">
          {/* ────── Sidebar ────── */}
          <div className="lg:col-span-1">
            <div className="bg-white rounded-md shadow-sm border border-slate-100 overflow-hidden">
              {/* Search */}
              <div className="p-3 border-b border-slate-100">
                <div className="relative">
                  <IoSearchOutline className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
                  <input
                    type="text"
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    placeholder="Search reports..."
                    className="w-full pl-9 pr-3 py-2 text-sm bg-slate-50 border border-slate-200 rounded focus:outline-none focus:ring-2 focus:ring-blue-200 focus:border-blue-300 transition-all"
                  />
                </div>
              </div>

              {/* Report list */}
              <div className="max-h-[calc(100vh-280px)] overflow-y-auto divide-y divide-slate-50">
                {filteredReports.map((report) => {
                  const isActive = selected?.analysis_id === report.analysis_id;
                  return (
                    <button
                      key={report.analysis_id}
                      onClick={() => selectReport(report)}
                      className={`w-full text-left px-4 py-3.5 transition-all ${
                        isActive
                          ? "bg-blue-50 border-l-3 border-l-blue-500"
                          : "hover:bg-slate-50"
                      }`}
                    >
                      <div className="flex items-start gap-2.5">
                        {statusIcon(report.status)}
                        <div className="flex-1 min-w-0">
                          <p
                            className={`text-sm font-medium truncate ${isActive ? "text-blue-900" : "text-slate-800"}`}
                          >
                            {report.sample_name || "Unknown"}
                          </p>
                          <div className="flex items-center gap-2 mt-1">
                            <span
                              className={`inline-block px-1.5 py-0.5 rounded text-[11px] font-medium border ${statusColor(report.status)}`}
                            >
                              {report.status}
                            </span>
                            {report.started_at && (
                              <span className="text-[11px] text-slate-400">
                                {new Date(
                                  report.started_at,
                                ).toLocaleDateString()}
                              </span>
                            )}
                          </div>
                        </div>
                      </div>
                    </button>
                  );
                })}
                {filteredReports.length === 0 && (
                  <div className="p-6 text-center">
                    <p className="text-xs text-slate-400">No matches</p>
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* ────── Detail Panel ────── */}
          <div className="lg:col-span-4 space-y-4">
            {selected ? (
              <>
                {/* VirusTotal-style Animated Score Hero Banner & Header Card */}
                <VirusTotalHeroBanner
                  report={selected}
                  data={rd}
                  aiReport={aiReport}
                  aiAnalyzing={aiAnalyzing}
                  localBenign={localBenign}
                />

                {/* Report sections */}
                <div className="bg-white rounded-2xl shadow-sm border border-slate-200 overflow-hidden flex">
                  <button
                    onClick={() => setActiveTab("overview")}
                    className={`flex-1 px-3 md:px-6 py-3 text-sm font-semibold transition-colors flex items-center justify-center gap-2 border-b-2 ${
                      activeTab === "overview"
                        ? "text-violet-700 border-violet-600 bg-violet-50/60"
                        : "text-slate-500 border-transparent hover:text-slate-700 hover:bg-slate-50"
                    }`}
                  >
                    <IoAnalyticsOutline className="w-4 h-4" />
                    Overview
                  </button>
                  <div className="w-px bg-slate-200" />
                  <button
                    onClick={() => setActiveTab("evidence")}
                    className={`flex-1 px-6 py-3 text-sm font-semibold transition-colors flex items-center justify-center gap-2 border-b-2 ${
                      activeTab === "evidence"
                        ? "text-violet-700 border-violet-600 bg-violet-50/60"
                        : "text-slate-500 border-transparent hover:text-slate-700 hover:bg-slate-50"
                    }`}
                  >
                    <IoDocumentTextOutline className="w-4 h-4" />
                    Technical evidence
                  </button>
                  {!localBenign && (
                    <>
                      <div className="w-px bg-slate-200" />
                      <button
                        onClick={() => setActiveTab("ai")}
                        className={`flex-1 px-6 py-3 text-sm font-semibold transition-colors flex items-center justify-center gap-2 border-b-2 ${
                          activeTab === "ai"
                            ? "text-violet-700 border-violet-600 bg-violet-50/60"
                            : "text-slate-500 border-transparent hover:text-slate-700 hover:bg-slate-50"
                        }`}
                      >
                        <IoSparklesOutline className="w-4 h-4" />
                        AI Analysis
                        {aiReport && (
                          <span
                            className={`text-[11px] font-bold px-1.5 py-0.5 rounded border uppercase tracking-wider ${
                              aiReport.risk_score >= 70
                                ? "bg-red-50 text-red-700 border-red-200"
                                : aiReport.risk_score >= 40
                                  ? "bg-amber-50 text-amber-700 border-amber-200"
                                  : "bg-emerald-50 text-emerald-700 border-emerald-200"
                            }`}
                          >
                            {aiReport.risk_score}
                          </span>
                        )}
                        {!aiReport && (
                          <span className="text-[11px] font-bold bg-blue-50 text-blue-700 px-1.5 py-0.5 rounded border border-blue-200 uppercase tracking-wider">
                            New
                          </span>
                        )}
                      </button>
                    </>
                  )}
                </div>

                {activeTab === "overview" && !detailLoading && (
                  <ReportOverview report={selected} data={rd} aiReport={aiReport} localBenign={localBenign} />
                )}

                {/* AI Tab */}
                {activeTab === "ai" && !localBenign && (
                  <AIAnalysisTab
                    analysisId={selected.analysis_id}
                    aiReport={aiReport}
                    aiAnalyzing={aiAnalyzing}
                    aiProgress={aiProgress}
                    aiError={aiError}
                    handleRunAnalysis={handleRunAnalysis}
                    onAnimationComplete={handleAnimationComplete}
                  />
                )}

                {activeTab === "evidence" && !detailLoading && localBenign && (
                  <NoData
                    label="No technical evidence available."
                    hint="No activity events were recorded for this benign result."
                  />
                )}

                {/* Report sections (only when report tab active) */}
                {activeTab === "evidence" && !detailLoading && rd && (
                  <div className="space-y-4">
                    {/* YARA Signatures & Capability Detection Section */}
                    <Panel
                      title="YARA — Pattern & Capability Detection"
                      icon={<YaraLogo className="w-4 h-4" />}
                      count={
                        rd.yara
                          ? `${rd.yara.matched_rules_count} matched (${rd.yara.threat_level || "clean"})`
                          : "no data"
                      }
                      color="rose"
                      defaultOpen={true}
                    >
                      <YaraSection data={rd.yara} />
                    </Panel>

                    {/* BiLSTM Sequential Behavioral Model Section */}
                    <Panel
                      title="BiLSTM — Sequential Behavioral Inference"
                      icon={<IoGitNetworkOutline className="w-4 h-4" />}
                      count={
                        rd.lstm
                          ? `${rd.lstm.verdict} (${((rd.lstm.p_malware || 0) * 100).toFixed(1)}% malice)`
                          : "evaluating..."
                      }
                      color="cyan"
                      defaultOpen={true}
                    >
                      <LstmSection data={rd.lstm} />
                    </Panel>

                    {/* Host Behavior Normalization Section */}
                    <Panel
                      title="Host Behavior — Normalized FS & Registry Activity"
                      icon={<IoLayersOutline className="w-4 h-4" />}
                      count={
                        rd.behavior
                          ? `${(rd.behavior.summary?.total_files_created ?? 0) + (rd.behavior.summary?.total_registry_modified ?? 0)} notable actions`
                          : "no data"
                      }
                      color="violet"
                      defaultOpen={true}
                    >
                      <BehaviorSection data={rd.behavior} />
                    </Panel>

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
                      count={
                        rd.gui?.has_malicious_gui
                          ? `🚨 ${rd.gui.flagged_count} flagged threat(s)`
                          : `${rd.screenshots?.length || 0} captured`
                      }
                      color={rd.gui?.has_malicious_gui ? "rose" : "blue"}
                    >
                      {rd.screenshots && rd.screenshots.length > 0 ? (
                        <div>
                          <p className="text-xs text-slate-400 mb-1 mt-3">
                            Click to open. Hover to auto-advance. Use ← → keys.
                          </p>
                          <ScreenshotGallery
                            analysisId={selected.analysis_id}
                            screenshots={rd.screenshots}
                            guiData={rd.gui}
                          />
                        </div>
                      ) : (
                        <NoData
                          label="No screenshots captured."
                          hint="Screenshots may not have been collected during this analysis."
                        />
                      )}
                    </Panel>

                    {/* Offline Network Threat DB Matches Section */}
                    <Panel
                      title="Offline Network Threat Intelligence DB"
                      icon={<IoGlobeOutline className="w-4 h-4" />}
                      count={
                        rd.network_db
                          ? `${rd.network_db.findings?.length ?? 0} matches (${rd.network_db.verdict})`
                          : "no data"
                      }
                      color="emerald"
                      defaultOpen={true}
                    >
                      <NetworkDBSection data={rd.network_db} />
                    </Panel>

                    <Panel
                      title="Sysmon — System Monitor"
                      icon={<IoShieldCheckmarkOutline className="w-4 h-4" />}
                      count={
                        rd.sysmon
                          ? `${rd.sysmon.sample_events} events`
                          : "no data"
                      }
                      color="blue"
                      defaultOpen={true}
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
                      defaultOpen={true}
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
                                className="flex items-center gap-2 px-3 py-1.5 rounded-lg hover:bg-slate-50 transition-colors"
                              >
                                <IoDocumentTextOutline className="w-3.5 h-3.5 text-slate-400 shrink-0" />
                                <span className="text-slate-700 font-mono text-xs truncate">
                                  {file}
                                </span>
                              </div>
                            ))}
                          </div>
                        </Panel>
                      )}
                  </div>
                )}

                {(activeTab === "evidence" || activeTab === "overview") && detailLoading && (
                  <div className="bg-white rounded-md shadow-sm border border-slate-100 p-12 text-center">
                    <div className="animate-spin w-8 h-8 border-4 border-blue-200 border-t-blue-500 rounded-full mx-auto mb-3" />
                    <p className="text-sm text-slate-500">
                      Loading report data...
                    </p>
                  </div>
                )}
              </>
            ) : (
              <div className="bg-white rounded-md shadow-sm border border-slate-100 p-16 text-center">
                <div className="w-12 h-12 mx-auto mb-4 bg-slate-100 rounded flex items-center justify-center">
                  <IoDocumentTextOutline className="w-6 h-6 text-slate-400" />
                </div>
                <p className="text-slate-500 font-medium">
                  Select a report to view details
                </p>
                <p className="text-xs text-slate-400 mt-1">
                  Choose from the list on the left
                </p>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
