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
} from "react-icons/io5";
import {
  submitAnalysis,
  getAnalysisStatus,
  type AnalysisResult,
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
  const fileInputRef = useRef<HTMLInputElement>(null);
  const pollingRef = useRef<ReturnType<typeof setInterval> | null>(null);

  // Clean up polling on unmount
  useEffect(() => {
    return () => {
      if (pollingRef.current) clearInterval(pollingRef.current);
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
            setStatusMsg(`Analysing ${d.sample_name}...`);
            setProgress(50);
            setResult(d);
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

  const startPolling = useCallback(() => {
    if (pollingRef.current) clearInterval(pollingRef.current);
    pollingRef.current = setInterval(async () => {
      try {
        const resp = await getAnalysisStatus();
        if (resp.status === "ok" && resp.data && "status" in resp.data) {
          const d = resp.data as AnalysisResult;
          setResult(d);
          if (d.status === "running") {
            setProgress(50);
            setStatusMsg(`Analysing ${d.sample_name}...`);
          } else if (d.status === "complete") {
            setProgress(100);
            setStatusMsg("Analysis complete!");
            setScanState("complete");
            if (pollingRef.current) clearInterval(pollingRef.current);
          } else if (d.status === "failed") {
            setProgress(100);
            setStatusMsg("Analysis failed");
            setScanState("failed");
            setError(d.error || "Unknown error");
            if (pollingRef.current) clearInterval(pollingRef.current);
          }
        }
      } catch {
        // Transient error, keep polling
      }
    }, 3000);
  }, []);

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
    setProgress(10);
    setStatusMsg("Uploading file...");
    setError(null);

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

      if (d.status === "complete") {
        setScanState("complete");
        setStatusMsg("Analysis complete!");
        setProgress(100);
      } else if (d.status === "failed") {
        setScanState("failed");
        setStatusMsg("Analysis failed");
        setError(d.error || "Unknown error");
        setProgress(100);
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
    }
  };

  const handleReset = () => {
    if (pollingRef.current) clearInterval(pollingRef.current);
    setSelectedFile(null);
    setScanState("idle");
    setProgress(0);
    setStatusMsg("No ongoing scan");
    setError(null);
    setResult(null);
  };

  const stateIcon = () => {
    switch (scanState) {
      case "running":
      case "uploading":
        return (
          <IoHourglassOutline className="w-5 h-5 text-violet-500 animate-pulse" />
        );
      case "complete":
        return <IoCheckmarkCircle className="w-5 h-5 text-green-500" />;
      case "failed":
        return <IoCloseCircle className="w-5 h-5 text-red-500" />;
      default:
        return <IoFlashOutline className="w-5 h-5 text-violet-500" />;
    }
  };

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-gray-900">Scan</h1>

      {/* ── Upload & Scan ──────────────────────────── */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-5">
          Upload &amp; Scan
        </h2>

        <div className="flex flex-col lg:flex-row gap-6">
          {/* Drag & Drop zone */}
          <div className="flex-1">
            <div
              onDrop={handleDrop}
              onDragOver={(e) => {
                e.preventDefault();
                setIsDragOver(true);
              }}
              onDragLeave={() => setIsDragOver(false)}
              className={`border-2 border-dashed rounded-xl p-8 flex flex-col items-center justify-center text-center min-h-[200px] transition-colors cursor-pointer ${
                isDragOver
                  ? "border-violet-400 bg-violet-100/60"
                  : "border-violet-200 bg-violet-50/40"
              }`}
              onClick={handleBrowse}
            >
              <div className="w-14 h-14 rounded-full bg-violet-100 flex items-center justify-center mb-4">
                <IoCloudUploadOutline className="w-7 h-7 text-violet-500" />
              </div>
              {selectedFile ? (
                <div>
                  <p className="text-sm font-medium text-gray-800">
                    {selectedFile.name}
                  </p>
                  <p className="text-xs text-gray-500 mt-1">
                    {(selectedFile.size / 1024).toFixed(1)} KB
                  </p>
                </div>
              ) : (
                <p className="text-sm text-gray-500">
                  Drop a file here or click to browse
                </p>
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
            <div className="flex items-center gap-3 mt-4">
              <span className="text-sm text-gray-500 whitespace-nowrap truncate max-w-[200px]">
                {statusMsg}
              </span>
              <div className="flex-1 h-2 bg-gray-200 rounded-full overflow-hidden">
                <div
                  className={`h-full rounded-full transition-all duration-500 ${
                    scanState === "failed"
                      ? "bg-red-500"
                      : scanState === "complete"
                        ? "bg-green-500"
                        : "bg-violet-500"
                  }`}
                  style={{ width: `${progress}%` }}
                />
              </div>
              <span className="text-sm text-gray-400">{progress}%</span>
            </div>
          </div>

          {/* Right side */}
          <div className="flex flex-col items-center justify-center lg:w-64 text-center">
            <p className="text-base text-gray-700 mb-1">
              <span className="font-bold">Drag</span> &amp;{" "}
              <span className="font-bold">Drop</span> file here or
            </p>
            <button
              onClick={handleBrowse}
              className="mt-3 w-full bg-violet-600 hover:bg-violet-700 text-white font-medium py-3 px-6 rounded-lg transition-colors text-sm"
            >
              Browse File
            </button>
            <p className="text-xs text-gray-400 mt-3">
              Supported: .exe, .dll, .bat, .ps1, .zip
            </p>
            <button
              onClick={handleReset}
              className="mt-2 p-1.5 hover:bg-gray-100 rounded-md transition-colors"
              title="Reset"
            >
              <IoRefreshOutline className="w-4 h-4 text-gray-400" />
            </button>
          </div>
        </div>
      </div>

      {/* ── Scan Status + Scan Options ─────── */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Scan Status */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">
            <span className="font-bold">Scan</span>{" "}
            <span className="font-normal text-gray-500">Status</span>
          </h3>

          <div className="flex items-center justify-between mb-5">
            <div className="flex items-center gap-2">
              {stateIcon()}
              <span className="text-sm text-gray-600">{statusMsg}</span>
            </div>
          </div>

          {error && (
            <div className="bg-red-50 border border-red-200 rounded-lg p-3 mb-4">
              <p className="text-sm text-red-700">{error}</p>
            </div>
          )}

          {result && result.status === "complete" && (
            <div className="bg-green-50 border border-green-200 rounded-lg p-4 space-y-2">
              <p className="text-sm font-medium text-green-800">
                ✓ Analysis complete
              </p>
              <p className="text-xs text-green-700">
                Sample: {result.sample_name}
              </p>
              <p className="text-xs text-green-700">
                Sysmon events: {result.sysmon_events}
              </p>
              <p className="text-xs text-green-700">
                Files collected: {result.files_collected.length}
              </p>
              <a
                href="/reports"
                className="inline-block mt-2 text-sm font-medium text-violet-600 hover:text-violet-700"
              >
                View Full Report →
              </a>
            </div>
          )}

          <div className="bg-violet-50/50 rounded-lg p-4 border border-violet-100 mt-4">
            <div className="flex items-center gap-2 mb-2">
              <IoInformationCircleOutline className="w-5 h-5 text-violet-500" />
              <h4 className="text-sm font-bold text-gray-800">
                Supported file types
              </h4>
            </div>
            <div className="flex items-center gap-1 text-sm text-gray-600 ml-7">
              <IoCheckmarkOutline className="w-4 h-4 text-violet-500 shrink-0" />
              <span>.exe, .dll, .bat, .ps1, .zip</span>
            </div>
            <div className="flex items-center gap-1 text-sm text-gray-600 ml-7 mt-1">
              <IoCheckmarkOutline className="w-4 h-4 text-violet-500 shrink-0" />
              <span>Max size limit: 256MB</span>
            </div>
          </div>
        </div>

        {/* Scan Options */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">
            Scan Options
          </h3>

          <div className="mb-5">
            <label className="block text-sm text-gray-700 mb-1.5">
              Analysis Timeout
            </label>
            <select
              value={timeout}
              onChange={(e) => setTimeout(Number(e.target.value))}
              className="w-full appearance-none border border-gray-300 rounded-lg px-4 py-2.5 pr-10 text-sm text-gray-700 bg-white focus:outline-none focus:ring-2 focus:ring-violet-300"
              disabled={scanState === "running" || scanState === "uploading"}
            >
              <option value={30}>30 seconds</option>
              <option value={60}>60 seconds</option>
              <option value={120}>120 seconds</option>
              <option value={300}>300 seconds</option>
            </select>
          </div>

          <div className="flex items-center justify-between mb-4">
            <span className="text-sm text-gray-700">Capture Screenshots</span>
            <button
              onClick={() => setCaptureScreenshots(!captureScreenshots)}
              className={`relative w-12 h-6 rounded-full transition-colors ${
                captureScreenshots ? "bg-violet-500" : "bg-gray-300"
              }`}
              disabled={scanState === "running" || scanState === "uploading"}
            >
              <span
                className={`absolute top-1 w-4 h-4 bg-white rounded-full shadow transition-transform ${
                  captureScreenshots ? "right-1" : "left-1"
                }`}
              />
            </button>
          </div>

          {captureScreenshots && (
            <div className="flex items-center justify-between mb-4">
              <span className="text-sm text-gray-700">Screenshot Interval</span>
              <div className="flex items-center gap-2">
                <input
                  type="number"
                  value={screenshotInterval}
                  onChange={(e) =>
                    setScreenshotInterval(Number(e.target.value))
                  }
                  min={1}
                  max={30}
                  className="w-16 px-3 py-1.5 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-violet-300"
                  disabled={
                    scanState === "running" || scanState === "uploading"
                  }
                />
                <span className="text-sm text-gray-500">sec</span>
              </div>
            </div>
          )}

          <div className="flex items-center justify-between mb-6">
            <span className="text-sm text-gray-700">Network Monitoring</span>
            <div className="relative w-12 h-6 bg-violet-500 rounded-full">
              <span className="absolute right-1 top-1 w-4 h-4 bg-white rounded-full shadow" />
            </div>
          </div>

          <button
            onClick={handleStartScan}
            disabled={
              !selectedFile ||
              scanState === "running" ||
              scanState === "uploading"
            }
            className={`w-full font-medium py-3 rounded-lg transition-colors text-sm ${
              !selectedFile ||
              scanState === "running" ||
              scanState === "uploading"
                ? "bg-gray-300 text-gray-500 cursor-not-allowed"
                : "bg-violet-600 hover:bg-violet-700 text-white"
            }`}
          >
            {scanState === "uploading"
              ? "Uploading..."
              : scanState === "running"
                ? "Analysis Running..."
                : "Start Scan"}
          </button>
        </div>
      </div>

      {/* ── Info banner ──────────────────────────── */}
      <div className="bg-violet-50/50 rounded-xl border border-violet-100 p-5">
        <div className="flex items-center gap-2 mb-2">
          <IoInformationCircleOutline className="w-5 h-5 text-violet-500" />
          <h4 className="text-sm font-bold text-gray-800">
            Supported file types
          </h4>
        </div>
        <p className="text-sm text-gray-600 ml-7">
          .exe, .dll, .bat, .ps1, .zip — Max size: 256MB
        </p>
      </div>
    </div>
  );
}
