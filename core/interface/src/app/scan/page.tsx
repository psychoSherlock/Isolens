"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import {
  IoCloudUploadOutline,
  IoInformationCircleOutline,
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
} from "react-icons/io5";
import {
  submitAnalysis,
  getAnalysisStatus,
  vmScreenURL,
  getVMInfo,
  startVM,
  poweroffVM,
  resetVM,
  getAgentStatus,
  type AnalysisResult,
  type VMInfo,
} from "@/lib/api";

type ScanState = "idle" | "uploading" | "running" | "complete" | "failed";

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

  // New states for Sandbox Preview and Timer
  const [timeRemaining, setTimeRemaining] = useState<number | null>(null);
  const [isFinalizing, setIsFinalizing] = useState(false);
  const [previewSrc, setPreviewSrc] = useState<string>("");
  const [previewExpanded, setPreviewExpanded] = useState(false);

  // VM Info and controls
  const [vmInfo, setVmInfo] = useState<VMInfo | null>(null);
  const [vmBusy, setVmBusy] = useState(false);
  const [agentStatus, setAgentStatus] = useState<string | null>(null);

  const fileInputRef = useRef<HTMLInputElement>(null);
  const pollingRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const previewTimerRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const countdownTimerRef = useRef<ReturnType<typeof setInterval> | null>(null);

  // Clean up polling on unmount
  useEffect(() => {
    return () => {
      if (pollingRef.current) clearInterval(pollingRef.current);
      if (previewTimerRef.current) clearInterval(previewTimerRef.current);
      if (countdownTimerRef.current) clearInterval(countdownTimerRef.current);
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
  }, [timeout, isFinalizing]);

  const cleanupTimers = () => {
    if (pollingRef.current) clearInterval(pollingRef.current);
    if (previewTimerRef.current) clearInterval(previewTimerRef.current);
    if (countdownTimerRef.current) clearInterval(countdownTimerRef.current);
    setTimeRemaining(null);
    setIsFinalizing(false);
  };

  // Preview polling logic
  useEffect(() => {
    if (scanState === "running") {
      // Setup preview polling
      if (!previewTimerRef.current) {
        setPreviewSrc(vmScreenURL("WindowsSandbox"));
        previewTimerRef.current = setInterval(() => {
          setPreviewSrc(vmScreenURL("WindowsSandbox"));
        }, 2000);
      }

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
      if (previewTimerRef.current) {
        clearInterval(previewTimerRef.current);
        previewTimerRef.current = null;
      }
      if (countdownTimerRef.current) {
        clearInterval(countdownTimerRef.current);
        countdownTimerRef.current = null;
      }
      if (scanState !== "failed" && scanState !== "complete") {
        setPreviewSrc("");
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
        setScanState("failed");
        setStatusMsg("Scan failed");
        setError(resp.error?.message || "Unknown error");
        setProgress(0);
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
    setSelectedFile(null);
    setScanState("idle");
    setProgress(0);
    setStatusMsg("No ongoing scan");
    setError(null);
    setResult(null);
    setPreviewSrc("");
  };

  const stateIcon = () => {
    switch (scanState) {
      case "running":
      case "uploading":
        return (
          <IoHourglassOutline className="w-5 h-5 text-blue-500 animate-pulse" />
        );
      case "complete":
        return <IoCheckmarkCircle className="w-5 h-5 text-green-500" />;
      case "failed":
        return <IoCloseCircle className="w-5 h-5 text-red-500" />;
      default:
        return <IoFlashOutline className="w-5 h-5 text-blue-500" />;
    }
  };

  return (
    <div className="space-y-6 max-w-5xl mx-auto">
      <div className="flex items-center justify-between pb-4 border-b border-slate-200">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 tracking-tight">
            New Scan
          </h1>
          <p className="text-sm text-slate-500 mt-1">
            Submit a suspicious file for dynamic behavioral analysis
          </p>
        </div>
      </div>

      {/* ── Upload & Scan ──────────────────────────── */}
      <div className="bg-white rounded-lg shadow-sm border border-slate-200 overflow-hidden">
        <div className="px-6 py-4 border-b border-slate-100 bg-slate-50/50">
          <h2 className="text-sm font-semibold text-slate-800 uppercase tracking-wider">
            File Submission
          </h2>
        </div>

        <div className="p-6 flex flex-col lg:flex-row gap-8">
          {/* Drag & Drop zone */}
          <div className="flex-1">
            <div
              onDrop={handleDrop}
              onDragOver={(e) => {
                e.preventDefault();
                setIsDragOver(true);
              }}
              onDragLeave={() => setIsDragOver(false)}
              className={`border-2 border-dashed rounded-lg p-8 flex flex-col items-center justify-center text-center min-h-[220px] transition-colors cursor-pointer ${
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
                  <p className="text-sm font-medium text-slate-700">
                    Click to upload or drag and drop
                  </p>
                  <p className="text-xs text-slate-500 mt-1">
                    Executable formats & macros up to 256MB
                  </p>
                </div>
              )}
            </div>

            <input
              ref={fileInputRef}
              type="file"
              className="hidden"
              accept=".exe,.dll,.bat,.ps1,.zip"
              onChange={(e) => {
                const file = e.target.files?.[0];
                if (file) handleFileSelect(file);
              }}
            />

            {/* Progress bar */}
            <div className="flex items-center gap-4 mt-5">
              <span className="text-sm font-medium text-slate-600 whitespace-nowrap truncate min-w-[140px]">
                {statusMsg}
              </span>
              <div className="flex-1 h-1.5 bg-slate-100 rounded-full overflow-hidden">
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
          <div className="flex flex-col lg:w-72 space-y-5">
            <div>
              <label className="block text-xs font-semibold text-slate-600 uppercase tracking-wider mb-2">
                Timeout Profile
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
                className={`w-full font-semibold py-2.5 rounded text-sm flex items-center justify-center gap-2 transition-colors border ${
                  !selectedFile ||
                  scanState === "running" ||
                  scanState === "uploading"
                    ? "bg-slate-100 text-slate-400 border-slate-200 cursor-not-allowed"
                    : "bg-slate-900 border-slate-900 text-white hover:bg-slate-800"
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
                <span className="text-[11px] text-slate-400">
                  VM State: Ready
                </span>
                <button
                  onClick={handleReset}
                  className="text-[11px] font-medium text-slate-500 hover:text-slate-800 flex items-center gap-1"
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
                    </div>
                  </div>
                </div>
                <a
                  href="/reports"
                  className="shrink-0 bg-emerald-600 hover:bg-emerald-700 text-white text-sm font-medium px-5 py-2.5 rounded shadow-sm transition-colors text-center"
                >
                  Open Sandbox Report
                </a>
              </div>
            )}
          </div>
        </div>
      )}

      {/* ── Sandbox Live Preview & Status ─────── */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Live VM Preview */}
        <div className="lg:col-span-2 bg-white rounded-lg shadow-sm border border-slate-200 overflow-hidden flex flex-col min-h-[400px]">
          <div className="px-6 py-4 border-b border-slate-100 bg-slate-50/50 flex items-center justify-between">
            <h2 className="text-sm font-semibold text-slate-800 uppercase tracking-wider flex items-center gap-2">
              <IoDesktopOutline className="w-4 h-4 text-blue-500" />
              Live VM Preview
            </h2>
            <div className="flex items-center gap-2">
              {scanState === "running" && (
                <button
                  onClick={() => setPreviewExpanded(true)}
                  className="p-1.5 text-slate-400 hover:text-blue-600 transition-colors"
                  title="Fullscreen"
                >
                  <IoExpandOutline className="w-4 h-4" />
                </button>
              )}
              <span
                className={`text-xs font-medium px-2.5 py-1 rounded-full ${
                  scanState === "running"
                    ? "bg-green-100 text-green-700"
                    : "bg-slate-100 text-slate-500"
                }`}
              >
                {scanState === "running" ? "Active" : "Inactive"}
              </span>
            </div>
          </div>

          <div className="flex-1 flex flex-col items-center justify-center p-4 bg-slate-50 min-h-0 relative">
            {scanState !== "running" ? (
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
                  className="w-full h-full object-contain"
                  onError={() => {}}
                />
                <div className="absolute top-3 right-3 flex items-center gap-1.5 bg-black/60 text-green-400 text-xs font-mono px-2 py-1 rounded shadow-sm border border-green-500/30">
                  <span className="w-2 h-2 bg-green-500 rounded-full animate-pulse shadow-[0_0_8px_rgba(34,197,94,0.6)]" />
                  LIVE
                </div>
              </div>
            ) : (
              <div className="flex flex-col items-center justify-center text-slate-500">
                <div className="animate-spin w-8 h-8 border-2 border-slate-200 border-t-blue-500 rounded-full mb-3" />
                <p className="text-sm">Connecting to VM display...</p>
              </div>
            )}
          </div>
          {scanState === "running" && (
            <div className="px-4 py-2 bg-white border-t border-slate-100 text-[11px] text-slate-400 text-center">
              Frames refreshing automatically every 2s
            </div>
          )}
        </div>

        {/* Sandbox Status */}
        <div className="lg:col-span-1 bg-white rounded-lg shadow-sm border border-slate-200 overflow-hidden flex flex-col">
          <div className="px-6 py-4 border-b border-slate-100 bg-slate-50/50">
            <h2 className="text-sm font-semibold text-slate-800 uppercase tracking-wider">
              Environment Status
            </h2>
          </div>
          <div className="p-6 flex-1 flex flex-col">
            <div className="flex flex-col items-center text-center mb-6">
              <div className="relative w-16 h-16 flex items-center justify-center mb-4">
                <div className="absolute inset-0 rounded-full border-4 border-slate-100" />
                {scanState === "running" ? (
                  <>
                    <div className="absolute inset-0 rounded-full border-4 border-t-green-500 border-r-green-400 animate-spin" />
                    <div className="w-8 h-8 bg-green-50 focus-within:ring-4 ring-green-100 rounded-full flex items-center justify-center">
                      <IoLockClosed className="w-4 h-4 text-green-600 animate-pulse" />
                    </div>
                  </>
                ) : (
                  <div className="absolute inset-0 rounded-full border-4 border-green-500" />
                )}
                {scanState !== "running" && (
                  <div className="w-8 h-8 bg-green-50 rounded-full flex items-center justify-center">
                    <IoCheckmarkCircle className="w-5 h-5 text-green-500" />
                  </div>
                )}
              </div>

              <h3 className="text-base font-bold text-slate-900 mb-1">
                {vmInfo?.name || "Windows Sandbox"}
              </h3>
              <p className="text-xs text-slate-500 mb-3">
                OS:{" "}
                <span className="font-medium text-slate-700">
                  {vmInfo?.os || "Unknown"}
                </span>
              </p>
              <p className="text-sm text-slate-500">
                {scanState === "running" ? (
                  <span className="text-green-600 font-medium bg-green-50 px-2 py-0.5 rounded-full">
                    Analyzing...
                  </span>
                ) : scanState === "idle" ? (
                  <span className="text-green-600 font-medium">
                    Up and running
                  </span>
                ) : scanState === "failed" ? (
                  <span className="text-red-500 font-medium">
                    Execution Failed
                  </span>
                ) : (
                  <span className="text-green-600 font-medium">Done</span>
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

            <div className="space-y-3 mt-auto pt-4 border-t border-slate-100">
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
            <div className="flex items-center gap-2 bg-black/60 border border-green-500/30 text-green-400 text-sm font-mono px-3 py-1.5 rounded-md shadow-lg">
              <span className="w-2.5 h-2.5 bg-green-500 rounded-full animate-pulse shadow-[0_0_8px_rgba(34,197,94,0.6)]" />
              LIVE PREVIEW
            </div>
            <button
              onClick={() => setPreviewExpanded(false)}
              className="p-2.5 bg-white/10 hover:bg-white/20 border border-white/10 text-white rounded-md transition-all hover:scale-105 active:scale-95"
              title="Exit Fullscreen"
            >
              <IoContractOutline className="w-5 h-5" />
            </button>
          </div>
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <div className="w-full max-w-6xl w-full h-full flex items-center justify-center relative">
            <img
              src={previewSrc}
              alt="Live VM Screenshot — Fullscreen"
              className="max-w-full max-h-full object-contain rounded-lg shadow-2xl ring-1 ring-white/10"
              onError={() => {}}
            />
          </div>
        </div>
      )}
    </div>
  );
}
