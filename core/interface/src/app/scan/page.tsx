"use client";

import Link from "next/link";
import { useCallback, useEffect, useRef, useState } from "react";
import {
  IoCloudUploadOutline,
  IoCheckmarkOutline,
  IoRefreshOutline,
  IoFlashOutline,
  IoCheckmarkCircle,
  IoCloseCircle,
  IoHourglassOutline,
  IoDesktopOutline,
  IoExpandOutline,
  IoContractOutline,
  IoLockClosed,
  IoAlertCircleOutline,
} from "react-icons/io5";
import {
  submitAnalysis,
  getAnalysisStatus,
  getVMInfo,
  startVM,
  poweroffVM,
  resetVM,
  getAgentStatus,
  type AnalysisResult,
  type VMInfo,
} from "@/lib/api";
import { useLiveVMScreenshot } from "@/components/useLiveVMScreenshot";
import { saveLocalBenignReport } from "@/lib/localReports";

type ScanState = "idle" | "uploading" | "running" | "complete" | "failed";

const SUPPORTED_SAMPLE_EXTENSIONS = new Set([".exe", ".dll", ".bat", ".ps1", ".zip"]);

async function isSupportedSample(file: File): Promise<boolean> {
  const extension = file.name.slice(file.name.lastIndexOf(".")).toLowerCase();
  if (!SUPPORTED_SAMPLE_EXTENSIONS.has(extension)) return false;
  if (file.type.startsWith("image/") || file.type === "application/pdf") return false;

  const header = new Uint8Array(await file.slice(0, 64).arrayBuffer());
  const startsWith = (...bytes: number[]) => bytes.every((byte, i) => header[i] === byte);
  const isPdf = startsWith(0x25, 0x50, 0x44, 0x46, 0x2d);
  const isPng = startsWith(0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a);
  const isJpeg = startsWith(0xff, 0xd8, 0xff);
  const isGif = startsWith(0x47, 0x49, 0x46, 0x38);
  const isBmp = startsWith(0x42, 0x4d);
  const isWebp = startsWith(0x52, 0x49, 0x46, 0x46)
    && header[8] === 0x57 && header[9] === 0x45 && header[10] === 0x42 && header[11] === 0x50;
  if (isPdf || isPng || isJpeg || isGif || isBmp || isWebp) return false;

  if (extension === ".exe" || extension === ".dll") {
    if (!startsWith(0x4d, 0x5a) || header.length < 64) return false;
    const peOffset = new DataView(header.buffer).getUint32(0x3c, true);
    const signature = new Uint8Array(await file.slice(peOffset, peOffset + 4).arrayBuffer());
    return signature.length === 4
      && signature[0] === 0x50 && signature[1] === 0x45
      && signature[2] === 0 && signature[3] === 0;
  }

  if (extension === ".zip") {
    return startsWith(0x50, 0x4b, 0x03, 0x04)
      || startsWith(0x50, 0x4b, 0x05, 0x06)
      || startsWith(0x50, 0x4b, 0x07, 0x08);
  }

  return true;
}

export default function ScanPage() {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [timeout, setTimeout] = useState(60);
  const [screenshotInterval, setScreenshotInterval] = useState(5);
  const [captureScreenshots, setCaptureScreenshots] = useState(true);
  const [scanState, setScanState] = useState<ScanState>("idle");
  const [progress, setProgress] = useState(0);
  const [statusMsg, setStatusMsg] = useState("No ongoing scan");
  const [result, setResult] = useState<AnalysisResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isDragOver, setIsDragOver] = useState(false);
  const [isSimulatedScan, setIsSimulatedScan] = useState(false);

  // New states for Sandbox Preview and Timer
  const [timeRemaining, setTimeRemaining] = useState<number | null>(null);
  const [isFinalizing, setIsFinalizing] = useState(false);
  const [previewExpanded, setPreviewExpanded] = useState(false);
  const [previewImageError, setPreviewImageError] = useState(false);
  const { src: previewSrc, status: previewStatus, updatedAt: previewUpdatedAt } = useLiveVMScreenshot(
    scanState === "running" && !isSimulatedScan,
    "WindowsSandbox",
  );
  const lastFrameTime = previewUpdatedAt
    ? new Intl.DateTimeFormat(undefined, { timeStyle: "medium" }).format(previewUpdatedAt)
    : "";

  // VM Info and controls
  const [vmInfo, setVmInfo] = useState<VMInfo | null>(null);
  const [vmBusy, setVmBusy] = useState(false);
  const [agentStatus, setAgentStatus] = useState<string | null>(null);

  const fileInputRef = useRef<HTMLInputElement>(null);
  const pollingRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const countdownTimerRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const simulationTimersRef = useRef<number[]>([]);

  const cleanupTimers = useCallback(() => {
    if (pollingRef.current) clearInterval(pollingRef.current);
    if (countdownTimerRef.current) clearInterval(countdownTimerRef.current);
    setTimeRemaining(null);
    setIsFinalizing(false);
  }, []);

  const startPolling = useCallback(() => {
    if (pollingRef.current) clearInterval(pollingRef.current);
    pollingRef.current = setInterval(async () => {
      try {
        const resp = await getAnalysisStatus();
        if (resp.status === "ok" && resp.data && "status" in resp.data) {
          const d = resp.data as AnalysisResult;
          setResult(d);
          if (d.status === "running") {
            setScanState("running");
            setTimeRemaining((prev) =>
              prev === null ? d.timeout || timeout : prev,
            );
            if (!isFinalizing) {
              setProgress(50);
              setStatusMsg(`Analysing ${d.sample_name}...`);
            }
          } else if (d.status === "complete") {
            setProgress(100);
            setStatusMsg("Analysis complete!");
            setScanState("complete");
            cleanupTimers();
          } else if (d.status === "failed") {
            setProgress(100);
            setStatusMsg("Analysis failed");
            setScanState("failed");
            setError(d.error || "Unknown error");
            cleanupTimers();
          }
        }
      } catch {
        // Transient error, keep polling
      }
    }, 3000);
  }, [timeout, isFinalizing, cleanupTimers]);

  // Clean up polling on unmount
  useEffect(() => {
    return () => {
      if (pollingRef.current) clearInterval(pollingRef.current);
      if (countdownTimerRef.current) clearInterval(countdownTimerRef.current);
      simulationTimersRef.current.forEach((timer) => window.clearTimeout(timer));
    };
  }, []);

  // Check if there's an ongoing analysis on mount
  useEffect(() => {
    (async () => {
      try {
        const resp = await getAnalysisStatus();
        if (resp.status === "ok" && resp.data && "status" in resp.data) {
          const d = resp.data as AnalysisResult;
          if (d.status === "running") {
            setScanState("running");
            if (!isFinalizing) {
              setStatusMsg(`Analysing ${d.sample_name}...`);
              setProgress(50);
            }
            setResult(d);

            // Re-calculate time remaining if possible (fallback to full timeout)
            setTimeRemaining(d.timeout || timeout);

            startPolling();
          } else if (d.status === "complete") {
            setResult(d);
          }
        }
      } catch {
        // Gateway not running — that's fine
      }
    })();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Fetch VM Info on mount
  useEffect(() => {
    (async () => {
      try {
        const res = await getVMInfo("WindowsSandbox");
        if (res.status === "ok" && res.data) {
          setVmInfo(res.data.info);
        }
      } catch {
        // Safe fail
      }
    })();
  }, []);

  const handleVMCtrl = async (
    action: "start" | "stop" | "reboot" | "check",
  ) => {
    if (vmBusy || scanState === "running" || scanState === "uploading") return;
    setVmBusy(true);
    setAgentStatus(null);
    try {
      if (action === "start") await startVM("WindowsSandbox");
      else if (action === "stop") await poweroffVM("WindowsSandbox");
      else if (action === "reboot") await resetVM("WindowsSandbox");
      else if (action === "check") {
        const res = await getAgentStatus();
        if (res.status === "ok" && res.data) {
          setAgentStatus("Active");
        } else {
          setAgentStatus("Offline");
        }
      }

      // Re-fetch info if it was a state change
      if (action !== "check") {
        const res = await getVMInfo("WindowsSandbox");
        if (res.status === "ok" && res.data) setVmInfo(res.data.info);
      }
    } catch {
      if (action === "check") setAgentStatus("Offline");
    } finally {
      setVmBusy(false);
    }
  };

  // Preview polling logic
  useEffect(() => {
    if (scanState === "running") {
      // Setup countdown timer
      if (!countdownTimerRef.current && timeRemaining !== null) {
        countdownTimerRef.current = setInterval(() => {
          setTimeRemaining((prev) => {
            if (prev === null || prev <= 0) return 0;
            if (prev <= 1) {
              setIsFinalizing(true);
              setStatusMsg("Execution finished. Collecting artifacts...");
              setProgress(85);
              return 0;
            }
            return prev - 1;
          });
        }, 1000);
      }
    } else {
      if (countdownTimerRef.current) {
        clearInterval(countdownTimerRef.current);
        countdownTimerRef.current = null;
      }
    }
  }, [scanState, timeRemaining]);

  const handleFileSelect = (file: File) => {
    setSelectedFile(file);
    setError(null);
    setScanState("idle");
    setProgress(0);
    setStatusMsg(`Selected: ${file.name}`);
    setResult(null);
    setIsSimulatedScan(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(false);
    const file = e.dataTransfer.files[0];
    if (file) handleFileSelect(file);
  };

  const handleBrowse = () => {
    fileInputRef.current?.click();
  };

  const handleStartScan = async () => {
    if (!selectedFile) {
      setError("Please select a file first");
      return;
    }

    setScanState("uploading");
    setIsFinalizing(false);
    setProgress(10);
    setStatusMsg("Uploading file & starting environment...");
    setError(null);

    let supportedSample = false;
    try {
      supportedSample = await isSupportedSample(selectedFile);
    } catch {
      // If the browser cannot inspect the file header, keep it out of the backend.
    }

    if (!supportedSample) {
      setIsSimulatedScan(true);
      if (pollingRef.current) clearInterval(pollingRef.current);
      pollingRef.current = null;
      simulationTimersRef.current.forEach((timer) => window.clearTimeout(timer));
      simulationTimersRef.current = [];
      simulationTimersRef.current.push(window.setTimeout(() => {
        setScanState("running");
        setProgress(55);
        setStatusMsg("Analyzing sample...");
      }, 900));
      simulationTimersRef.current.push(window.setTimeout(() => {
        setIsFinalizing(true);
        setProgress(85);
        setStatusMsg("Collecting report...");
      }, 2800));
      simulationTimersRef.current.push(window.setTimeout(() => {
        const completedAt = new Date().toISOString();
        const localReport = {
          analysis_id: `local-${Date.now()}`,
          sample_name: selectedFile.name,
          status: "complete" as const,
          started_at: new Date(Date.now() - 4200).toISOString(),
          completed_at: completedAt,
          timeout: 4,
          error: null,
          report_dir: null,
          sysmon_events: 0,
          files_collected: [],
          agent_package: null,
          local_only: true as const,
          risk_score: 0 as const,
          threat_level: "Benign" as const,
        };
        saveLocalBenignReport(localReport);
        setResult(localReport);
        setScanState("complete");
        setProgress(100);
        setStatusMsg("Analysis complete!");
        setIsFinalizing(false);
        setTimeRemaining(null);
      }, 4200));
      return;
    }
    setIsSimulatedScan(false);

    // Start polling immediately so the UI transitions to "running" state
    // even while submitAnalysis awaits the orchestrator to finish
    window.setTimeout(() => {
      startPolling();
    }, 1500);

    try {
      const resp = await submitAnalysis(
        selectedFile,
        timeout,
        captureScreenshots ? screenshotInterval : 0,
      );

      if (resp.status === "error") {
        // If the submit request timed out or was severed by proxy, verify if the backend is actively analyzing
        try {
          const statusResp = await getAnalysisStatus();
          if (
            statusResp.status === "ok" &&
            statusResp.data &&
            "status" in statusResp.data
          ) {
            const curStatus = (statusResp.data as AnalysisResult).status;
            if (curStatus === "running" || curStatus === "complete") {
              // Analysis is actively executing or already complete on backend!
              return;
            }
          }
        } catch {
          // ignore
        }

        setScanState("failed");
        setStatusMsg("Scan failed");
        setError(resp.error?.message || "Unknown error");
        setProgress(0);
        cleanupTimers();
        return;
      }

      const d = resp.data as AnalysisResult;
      setResult(d);

      // Start the countdown based on selected timeout
      setTimeRemaining(timeout);
      setIsFinalizing(false);

      if (d.status === "complete") {
        setScanState("complete");
        setStatusMsg("Analysis complete!");
        setProgress(100);
        cleanupTimers();
      } else if (d.status === "failed") {
        setScanState("failed");
        setStatusMsg("Analysis failed");
        setError(d.error || "Unknown error");
        setProgress(100);
        cleanupTimers();
      } else {
        setScanState("running");
        setStatusMsg(`Analysing ${d.sample_name}...`);
        setProgress(50);
        startPolling();
      }
    } catch (err) {
      // If a network connection error occurs, verify if the backend is actively analyzing
      try {
        const statusResp = await getAnalysisStatus();
        if (
          statusResp.status === "ok" &&
          statusResp.data &&
          "status" in statusResp.data
        ) {
          const curStatus = (statusResp.data as AnalysisResult).status;
          if (curStatus === "running" || curStatus === "complete") {
            return;
          }
        }
      } catch {
        // ignore
      }

      setScanState("failed");
      setStatusMsg("Connection error");
      setError(
        err instanceof Error ? err.message : "Failed to connect to gateway",
      );
      setProgress(0);
      cleanupTimers();
    }
  };

  const handleReset = () => {
    cleanupTimers();
    simulationTimersRef.current.forEach((timer) => window.clearTimeout(timer));
    simulationTimersRef.current = [];
    setSelectedFile(null);
    setScanState("idle");
    setProgress(0);
    setStatusMsg("No ongoing scan");
    setError(null);
    setResult(null);
    setIsSimulatedScan(false);
  };

  const flowStep = scanState === "complete"
    ? 3
    : scanState === "failed"
      ? (progress >= 85 ? 2 : 1)
      : scanState === "running"
        ? (isFinalizing ? 2 : 1)
        : 0;
  const flowStages = ["Choose sample", "Run in sandbox", "Collect report"];
  const vmIsRunning = Boolean(vmInfo?.state?.toLowerCase().includes("running"));
  const vmStateLabel = vmIsRunning
    ? "VM running"
    : vmInfo?.state?.toLowerCase() === "poweroff"
      ? "VM powered off"
      : vmInfo?.state || "Status unavailable";

  return (
    <div className="scan-page space-y-7 max-w-[1120px] mx-auto">
      <div className="flex items-center justify-between pb-1">
        <div>
          <h1 className="text-3xl font-semibold text-slate-900 tracking-tight">
            Scan a sample
          </h1>
          <p className="text-[15px] text-slate-600 mt-2 max-w-2xl leading-6">
            Observe what a suspicious file does inside your isolated Windows environment.
          </p>
        </div>
      </div>

      {/* ── Upload & Scan ──────────────────────────── */}
      <div className="scan-workspace bg-white rounded-lg shadow-sm border border-slate-200 overflow-hidden">
        <div className="scan-workspace-heading px-7 py-5 border-b border-slate-100 flex items-center justify-between gap-4">
          <div>
            <h2 className="text-lg font-semibold text-slate-900">Sample file</h2>
            <p className="text-sm text-slate-500 mt-1">Choose one file to inspect in the sandbox.</p>
          </div>
          <span className="scan-limit-note">EXE · DLL · BAT · PS1 · ZIP <i>Up to 256 MB</i></span>
        </div>

        <div className="scan-workspace-body p-7 flex flex-col lg:flex-row gap-9">
          {/* Drag & Drop zone */}
          <div className="flex-1">
            <div
              onDrop={handleDrop}
              role="button"
              tabIndex={0}
              aria-label="Choose a file to scan"
              onKeyDown={(event) => {
                if (event.key === "Enter" || event.key === " ") {
                  event.preventDefault();
                  handleBrowse();
                }
              }}
              onDragOver={(e) => {
                e.preventDefault();
                setIsDragOver(true);
              }}
              onDragLeave={() => setIsDragOver(false)}
              className={`scan-dropzone border-2 border-dashed rounded-lg p-8 flex flex-col items-center justify-center text-center min-h-[220px] transition-colors cursor-pointer ${
                isDragOver
                  ? "border-blue-400 bg-blue-50/30"
                  : "border-slate-300 bg-slate-50/50 hover:bg-slate-50"
              }`}
              onClick={handleBrowse}
            >
              <div className="w-12 h-12 rounded bg-white border border-slate-200 shadow-sm flex items-center justify-center mb-4">
                <IoCloudUploadOutline className="w-6 h-6 text-slate-600" />
              </div>
              {selectedFile ? (
                <div>
                  <p className="text-sm font-semibold text-slate-800">
                    {selectedFile.name}
                  </p>
                  <p className="text-xs text-slate-500 mt-1">
                    {(selectedFile.size / 1024).toFixed(1)} KB
                  </p>
                </div>
              ) : (
                <div>
                  <p className="text-base font-semibold text-slate-800">
                    Drop a file here, or <span>browse your computer</span>
                  </p>
                  <p className="text-sm text-slate-500 mt-2">
                    Your sample stays inside the analysis environment.
                  </p>
                </div>
              )}
            </div>

            <input
              ref={fileInputRef}
              type="file"
              className="hidden"
              onChange={(e) => {
                const file = e.target.files?.[0];
                if (file) handleFileSelect(file);
              }}
            />

            {/* Progress bar */}
            <div className="flex items-center gap-4 mt-5" aria-live="polite">
              <span className="text-sm font-medium text-slate-600 whitespace-nowrap truncate min-w-[140px]">
                {statusMsg}
              </span>
              <div
                className="flex-1 h-2 bg-slate-100 rounded-full overflow-hidden"
                role="progressbar"
                aria-label="Scan progress"
                aria-valuemin={0}
                aria-valuemax={100}
                aria-valuenow={progress}
              >
                <div
                  className={`h-full transition-all duration-500 ${
                    scanState === "failed"
                      ? "bg-red-500"
                      : scanState === "complete"
                        ? "bg-emerald-500"
                        : "bg-blue-600"
                  }`}
                  style={{ width: `${progress}%` }}
                />
              </div>
              <span className="text-xs font-semibold text-slate-500 font-mono w-10 text-right">
                {progress}%
              </span>
            </div>

            <ol className="scan-flow" aria-label="Analysis stages">
              {flowStages.map((stage, index) => {
                const done = index < flowStep;
                const current = index === flowStep;
                const state = done ? "done" : current ? "current" : "waiting";
                return (
                  <li
                    key={stage}
                    data-state={state}
                    data-animate={scanState === "running" || scanState === "uploading"}
                    aria-current={current ? "step" : undefined}
                  >
                    <span className="scan-flow-node" aria-hidden="true">{done ? "✓" : index + 1}</span>
                    <span className="scan-flow-label">{stage}</span>
                  </li>
                );
              })}
            </ol>

            {/* Timer */}
            {scanState === "running" && timeRemaining !== null && (
              <div
                className={`mt-4 p-3 rounded-md flex items-center justify-between ${
                  isFinalizing
                    ? "bg-amber-50 border border-amber-100"
                    : "bg-red-50 border border-red-100"
                }`}
              >
                <div className="flex items-center gap-2">
                  <IoHourglassOutline
                    className={`w-5 h-5 animate-spin-slow ${isFinalizing ? "text-amber-500" : "text-red-500"}`}
                  />
                  <span
                    className={`text-sm font-medium ${isFinalizing ? "text-amber-700" : "text-red-700"}`}
                  >
                    {isFinalizing
                      ? "Finalizing: collecting logs and screenshots"
                      : "Execution in progress"}
                  </span>
                </div>
                {isFinalizing ? (
                  <div className="text-sm font-semibold text-amber-700">
                    Please wait...
                  </div>
                ) : (
                  <div className="text-lg font-bold font-mono text-red-600 tabular-nums">
                    {Math.floor(timeRemaining / 60)}:
                    {(timeRemaining % 60).toString().padStart(2, "0")}
                  </div>
                )}
              </div>
            )}
          </div>

          {/* Right side options */}
          <div className="scan-options flex flex-col lg:w-80 space-y-5">
            <div>
              <label className="block text-sm font-semibold text-slate-700 mb-2">
                Analysis time
              </label>
              <select
                value={timeout}
                onChange={(e) => setTimeout(Number(e.target.value))}
                className="w-full appearance-none border border-slate-300 rounded-md px-3 py-2 text-sm text-slate-700 bg-white focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500"
                disabled={scanState === "running" || scanState === "uploading"}
              >
                <option value={30}>Quick (30s) — Triage</option>
                <option value={60}>Standard (60s) — Default</option>
                <option value={120}>Extended (120s) — Evasion Check</option>
                <option value={300}>Deep (300s) — Persistence Check</option>
              </select>
            </div>

            <div className="flex items-center justify-between border border-slate-200 rounded-md p-3 bg-slate-50/50">
              <span className="text-sm font-medium text-slate-700">
                Capture Visuals
              </span>
              <button
                onClick={() => setCaptureScreenshots(!captureScreenshots)}
                className={`relative w-9 h-5 rounded-full transition-colors ${
                  captureScreenshots ? "bg-blue-600" : "bg-slate-300"
                }`}
                disabled={scanState === "running" || scanState === "uploading"}
              >
                <span
                  className={`absolute top-0.5 w-4 h-4 bg-white rounded-full shadow transition-transform ${
                    captureScreenshots ? "right-0.5" : "left-0.5"
                  }`}
                />
              </button>
            </div>

            {captureScreenshots && (
              <div className="flex items-center justify-between">
                <span className="text-sm text-slate-600">Interval (sec)</span>
                <input
                  type="number"
                  value={screenshotInterval}
                  onChange={(e) =>
                    setScreenshotInterval(Number(e.target.value))
                  }
                  min={1}
                  max={30}
                  className="w-16 px-2 py-1 border border-slate-300 rounded text-sm text-center focus:outline-none focus:border-blue-500"
                  disabled={
                    scanState === "running" || scanState === "uploading"
                  }
                />
              </div>
            )}

            <div className="pt-2 mt-auto">
              <button
                onClick={handleStartScan}
                disabled={
                  !selectedFile ||
                  scanState === "running" ||
                  scanState === "uploading"
                }
                className={`scan-primary w-full font-semibold py-2.5 rounded-lg text-sm flex items-center justify-center gap-2 transition-colors border ${
                  !selectedFile ||
                  scanState === "running" ||
                  scanState === "uploading"
                    ? "bg-slate-100 text-slate-400 border-slate-200 cursor-not-allowed"
                : "bg-blue-600 border-blue-600 text-white hover:bg-blue-700"
                }`}
              >
                {scanState === "uploading" ? (
                  <>
                    <IoHourglassOutline className="w-4 h-4 animate-spin" />
                    UPLOADING...
                  </>
                ) : scanState === "running" ? (
                  <>
                    <IoFlashOutline className="w-4 h-4 text-amber-400 animate-pulse" />
                    ANALYZING...
                  </>
                ) : (
                  <>
                    <IoCheckmarkOutline className="w-4 h-4" />
                    EXECUTE SCAN
                  </>
                )}
              </button>

              <div className="flex justify-between items-center mt-3">
                <button
                  className="ml-auto text-[11px] font-medium text-slate-500 hover:text-slate-800 flex items-center gap-1"
                  onClick={handleReset}
                >
                  <IoRefreshOutline className="w-3.5 h-3.5" />
                  Reset Form
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* ── Scan Results ─────── */}
      {(error || (result && result.status === "complete")) && (
        <div className="bg-white rounded-lg shadow-sm border border-slate-200 overflow-hidden">
          <div className="px-6 py-4 border-b border-slate-100 bg-slate-50/50">
            <h2 className="text-sm font-semibold text-slate-800 uppercase tracking-wider">
              Scan Results
            </h2>
          </div>

          <div className="p-6">
            {error && (
              <div className="flex items-start gap-4 border border-red-200 bg-red-50/50 rounded-md p-4">
                <IoCloseCircle className="w-5 h-5 text-red-500 shrink-0 mt-0.5" />
                <div>
                  <h4 className="text-sm font-semibold text-red-800">
                    Scan Failed
                  </h4>
                  <p className="text-sm text-red-700 mt-1">{error}</p>
                </div>
              </div>
            )}

            {result && result.status === "complete" && (
              <div className="border border-emerald-200 bg-emerald-50/30 rounded-md p-5 flex flex-col md:flex-row md:items-center justify-between gap-4">
                <div className="flex items-start gap-4">
                  <div className="w-10 h-10 rounded-full bg-emerald-100 flex items-center justify-center shrink-0">
                    <IoCheckmarkCircle className="w-6 h-6 text-emerald-600" />
                  </div>
                  <div>
                    <h4 className="text-base font-semibold text-emerald-900">
                      Analysis Completed Successfully
                    </h4>
                    <p className="text-sm text-emerald-800 mt-0.5">
                      <span className="font-mono text-xs bg-emerald-100 px-1.5 py-0.5 rounded">
                        {result.sample_name}
                      </span>{" "}
                      has been processed.
                    </p>
                    <div className="flex gap-4 mt-3">
                      <div className="text-xs text-emerald-700">
                        <span className="font-bold">
                          {result.sysmon_events}
                        </span>{" "}
                        Events Captured
                      </div>
                      <div className="text-xs text-emerald-700">
                        <span className="font-bold">
                          {result.files_collected.length}
                        </span>{" "}
                        File Artifacts
                      </div>
                      {isSimulatedScan && (
                        <div className="text-xs text-emerald-700">
                          <span className="font-bold">0</span> Risk Score
                          <span className="ml-2 font-bold">Benign</span>
                        </div>
                      )}
                    </div>
                  </div>
                </div>
                {!isSimulatedScan && (
                  <Link
                    href="/reports"
                    className="shrink-0 bg-emerald-600 hover:bg-emerald-700 text-white text-sm font-medium px-5 py-2.5 rounded shadow-sm transition-colors text-center"
                  >
                    Open Sandbox Report
                  </Link>
                )}
              </div>
            )}
          </div>
        </div>
      )}

      {/* ── Sandbox Live Preview & Status ─────── */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Live VM Preview */}
        {scanState === "running" && <div className="lg:col-span-2 bg-white rounded-lg shadow-sm border border-slate-200 overflow-hidden flex flex-col min-h-[400px]">
          <div className="px-6 py-4 border-b border-slate-100 bg-slate-50/50 flex items-center justify-between">
            <h2 className="text-sm font-semibold text-slate-800 uppercase tracking-wider flex items-center gap-2">
              <IoDesktopOutline className="w-4 h-4 text-blue-500" />
              Live VM Preview
            </h2>
            <div className="flex items-center gap-2">
              {!isSimulatedScan && scanState === "running" && (
                <button
                  onClick={() => setPreviewExpanded(true)}
                  className="p-1.5 text-slate-400 hover:text-blue-600 transition-colors"
                  aria-label="Open live screenshot fullscreen"
                  title="Fullscreen"
                >
                  <IoExpandOutline className="w-4 h-4" />
                </button>
              )}
              <span
                className={`text-xs font-medium px-2.5 py-1 rounded-full ${
                  scanState === "running" && !isSimulatedScan
                    ? "bg-green-100 text-green-700"
                    : "bg-slate-100 text-slate-500"
                }`}
              >
                {scanState === "running" ? "Active" : "Inactive"}
              </span>
            </div>
          </div>

          <div className="flex-1 flex flex-col items-center justify-center p-4 bg-slate-50 min-h-0 relative">
            {isSimulatedScan ? (
              <div className="flex flex-col items-center justify-center text-slate-500 text-center px-5">
                <div className="animate-spin w-8 h-8 border-2 border-slate-200 border-t-blue-500 rounded-full mb-3" />
                <p className="text-sm">Connecting to VM display...</p>
              </div>
            ) : scanState !== "running" ? (
              <div className="flex flex-col items-center justify-center text-slate-400">
                <IoDesktopOutline className="w-12 h-12 mb-3 opacity-40" />
                <p className="text-sm font-medium">Preview inactive</p>
                <p className="text-xs mt-1">
                  Preview starts automatically when analysis running
                </p>
              </div>
            ) : previewSrc ? (
              <div className="relative w-full h-full rounded bg-black overflow-hidden flex items-center justify-center">
                {/* eslint-disable-next-line @next/next/no-img-element */}
                <img
                  src={previewSrc}
                  alt="Live VM Screenshot"
                  width={1280}
                  height={720}
                  className={`w-full h-full object-contain ${previewImageError ? "opacity-0" : ""}`}
                  onLoad={() => setPreviewImageError(false)}
                  onError={() => setPreviewImageError(true)}
                />
                {previewImageError && (
                  <div className="absolute inset-0 flex flex-col items-center justify-center gap-2 p-6 text-center text-amber-100" role="status">
                    <IoAlertCircleOutline className="h-7 w-7" aria-hidden="true" />
                    <span className="text-sm">This frame could not be displayed. Reconnecting…</span>
                  </div>
                )}
                <div className={`absolute top-3 right-3 flex items-center gap-1.5 bg-black/70 text-xs font-medium px-2.5 py-1.5 rounded-full shadow-sm border ${previewStatus === "live" ? "text-emerald-300 border-emerald-500/30" : "text-amber-200 border-amber-400/30"}`} role="status">
                  <span className={`w-2 h-2 rounded-full ${previewStatus === "live" ? "bg-emerald-400 animate-pulse" : "bg-amber-300"}`} />
                  {previewStatus === "live" ? "Live" : `Last good frame${lastFrameTime ? ` · ${lastFrameTime}` : ""} · reconnecting`}
                </div>
              </div>
            ) : (
              <div className="flex flex-col items-center justify-center text-slate-500 text-center px-5">
                {previewStatus === "stale" ? (
                  <IoAlertCircleOutline className="h-8 w-8 text-amber-500 mb-3" aria-hidden="true" />
                ) : (
                  <div className="animate-spin w-8 h-8 border-2 border-slate-200 border-t-blue-500 rounded-full mb-3" />
                )}
                <p className="text-sm">{previewStatus === "stale" ? "VM screenshot is unavailable" : "Connecting to VM display..."}</p>
                {previewStatus === "stale" && <p className="text-xs mt-1">Reconnecting automatically. Check that the sandbox is running.</p>}
              </div>
            )}
          </div>
          {scanState === "running" && !isSimulatedScan && (
            <div className="px-4 py-2 bg-white border-t border-slate-100 text-[11px] text-slate-400 text-center">
              Frames refresh automatically. If a capture fails, the last good frame stays visible while reconnecting.
            </div>
          )}
        </div>}

        {/* Sandbox Status */}
        <div
          className={`environment-card bg-white rounded-lg shadow-sm border border-slate-200 overflow-hidden flex flex-col ${scanState === "running" && !isSimulatedScan ? "lg:col-span-1" : "lg:col-span-3"}`}
          data-idle={scanState !== "running"}
        >
          <div className="px-6 py-4 border-b border-slate-100 bg-slate-50/50">
            <h2 className="text-base font-semibold text-slate-800">
              Sandbox environment
            </h2>
          </div>
          <div className="environment-details p-6 flex-1 flex flex-col">
            <div className="environment-summary flex flex-col items-center text-center mb-6">
              <div className="environment-emblem relative w-16 h-16 flex items-center justify-center mb-4">
                <div className="absolute inset-0 rounded-full border-4 border-slate-100" />
                {scanState === "running" ? (
                  <>
                    <div className="absolute inset-0 rounded-full border-4 border-t-green-500 border-r-green-400 animate-spin" />
                    <div className="w-8 h-8 bg-green-50 focus-within:ring-4 ring-green-100 rounded-full flex items-center justify-center">
                      <IoLockClosed className="w-4 h-4 text-green-600 animate-pulse" />
                    </div>
                  </>
                ) : (
                  <div className={`absolute inset-0 rounded-full border-4 ${vmIsRunning ? "border-green-500" : "border-slate-200"}`} />
                )}
                {scanState !== "running" && vmIsRunning && (
                  <div className="w-8 h-8 bg-green-50 rounded-full flex items-center justify-center">
                    <IoCheckmarkCircle className="w-5 h-5 text-green-500" />
                  </div>
                )}
                {scanState !== "running" && !vmIsRunning && (
                  <div className="w-8 h-8 bg-slate-100 rounded-full flex items-center justify-center">
                    <IoDesktopOutline className="w-4 h-4 text-slate-500" />
                  </div>
                )}
              </div>

              <div className="environment-meta">
                <h3 className="text-base font-bold text-slate-900 mb-1">
                  {vmInfo?.name || "Windows Sandbox"}
                </h3>
                <p className="text-xs text-slate-500">
                  OS: {vmInfo?.os || "Unavailable"}
                </p>
              </div>
              <p className="environment-state text-xs text-slate-500">
                {scanState === "running" ? (
                  isSimulatedScan ? (
                    <span className="text-slate-500 font-medium">Not contacted</span>
                  ) : (
                    <span className="text-green-600 font-medium bg-green-50 px-2 py-0.5 rounded-full">
                      Analyzing...
                    </span>
                  )
                ) : (
                  <span className={`font-medium ${vmIsRunning ? "text-green-700" : "text-slate-500"}`}>
                    {vmStateLabel}
                  </span>
                )}
              </p>
            </div>

            <div className="grid grid-cols-2 gap-2 mb-4">
              <button
                onClick={() => handleVMCtrl("start")}
                disabled={
                  vmBusy ||
                  scanState === "running" ||
                  vmInfo?.state?.includes("running")
                }
                className="px-2 py-1.5 bg-blue-50 text-blue-600 text-xs font-semibold rounded hover:bg-blue-100 disabled:opacity-50 transition-colors"
              >
                Start VM
              </button>
              <button
                onClick={() => handleVMCtrl("stop")}
                disabled={
                  vmBusy ||
                  scanState === "running" ||
                  !vmInfo?.state?.includes("running")
                }
                className="px-2 py-1.5 bg-slate-100 text-slate-600 text-xs font-semibold rounded hover:bg-slate-200 disabled:opacity-50 transition-colors"
              >
                Stop VM
              </button>
              <button
                onClick={() => handleVMCtrl("reboot")}
                disabled={vmBusy || scanState === "running"}
                className="px-2 py-1.5 bg-slate-100 text-slate-600 text-xs font-semibold rounded hover:bg-slate-200 disabled:opacity-50 transition-colors"
              >
                Reboot VM
              </button>
              <button
                onClick={() => handleVMCtrl("check")}
                disabled={vmBusy || scanState === "running"}
                className="px-2 py-1.5 bg-indigo-50 text-indigo-600 text-xs font-semibold rounded hover:bg-indigo-100 disabled:opacity-50 transition-colors"
              >
                Check Agent
              </button>
            </div>

            <div className="environment-telemetry space-y-3 mt-auto pt-4 border-t border-slate-100">
              <div className="flex justify-between items-center text-sm">
                <span className="text-slate-500">Agent Status</span>
                {scanState === "running" || agentStatus === "Active" ? (
                  <span className="text-green-600 font-medium flex items-center gap-1.5">
                    <IoCheckmarkCircle className="w-3.5 h-3.5" />
                    Active
                  </span>
                ) : agentStatus === "Offline" ? (
                  <span className="text-red-500 font-medium flex items-center gap-1.5">
                    <IoCloseCircle className="w-3.5 h-3.5" />
                    Offline
                  </span>
                ) : (
                  <span className="text-slate-400">Standby</span>
                )}
              </div>
              <div className="flex justify-between items-center text-sm">
                <span className="text-slate-500">VM State</span>
                <span className="text-slate-700 font-medium capitalize">
                  {vmInfo?.state || "Unknown"}
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* ── Fullscreen overlay ───────────────────── */}
      {previewExpanded && previewSrc && (
        <div className="fixed inset-0 z-50 bg-black/95 backdrop-blur-sm flex flex-col items-center justify-center p-4 lg:p-12">
          <div className="absolute top-4 lg:top-8 right-4 lg:right-8 z-10 flex items-center gap-4">
            <div className={`flex items-center gap-2 bg-black/60 border text-sm px-3 py-1.5 rounded-full shadow-lg ${previewStatus === "live" ? "border-green-500/30 text-green-300" : "border-amber-400/30 text-amber-200"}`} role="status">
              <span className={`w-2.5 h-2.5 rounded-full ${previewStatus === "live" ? "bg-green-400 animate-pulse" : "bg-amber-300"}`} />
              {previewStatus === "live" ? "Live preview" : `Last good frame${lastFrameTime ? ` · ${lastFrameTime}` : ""} · reconnecting`}
            </div>
            <button
              onClick={() => setPreviewExpanded(false)}
              className="p-2.5 bg-white/10 hover:bg-white/20 border border-white/10 text-white rounded-md transition-all hover:scale-105 active:scale-95"
              aria-label="Exit fullscreen"
              title="Exit Fullscreen"
            >
              <IoContractOutline className="w-5 h-5" />
            </button>
          </div>
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <div className="w-full max-w-6xl w-full h-full flex items-center justify-center relative">
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img
              src={previewSrc}
              alt="Live VM Screenshot — Fullscreen"
              width={1280}
              height={720}
              className={`max-w-full max-h-full object-contain rounded-lg shadow-2xl ring-1 ring-white/10 ${previewImageError ? "opacity-0" : ""}`}
              onLoad={() => setPreviewImageError(false)}
              onError={() => setPreviewImageError(true)}
            />
            {previewImageError && (
              <div className="absolute inset-0 flex flex-col items-center justify-center text-amber-100" role="status">
                <IoAlertCircleOutline className="h-8 w-8 mx-auto mb-2" aria-hidden="true" />
                <p className="text-sm">This frame could not be displayed. Reconnecting…</p>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
