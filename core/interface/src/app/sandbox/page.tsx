"use client";

import { useEffect, useState, useCallback, useRef } from "react";
import {
  IoStopCircle,
  IoRefresh,
  IoCheckmarkCircle,
  IoCloseCircle,
  IoPlayOutline,
  IoAlertCircleOutline,
  IoTrashOutline,
  IoDesktopOutline,
  IoExpandOutline,
  IoContractOutline,
} from "react-icons/io5";
import {
  listVMs,
  listRunningVMs,
  getVMInfo,
  getVMIP,
  startVM,
  poweroffVM,
  getAgentStatus,
  checkVM,
  cleanupAgent,
  getAnalysisStatus,
  vmScreenURL,
  type VMEntry,
  type VMInfo,
  type AgentStatus,
  type AnalysisResult,
} from "@/lib/api";

export default function SandboxPage() {
  // VM state
  const [vms, setVMs] = useState<VMEntry[]>([]);
  const [runningVMs, setRunningVMs] = useState<VMEntry[]>([]);
  const [selectedVM, setSelectedVM] = useState<string>("WindowsSandbox");
  const [vmInfo, setVMInfo] = useState<VMInfo | null>(null);
  const [vmIP, setVMIP] = useState<string>("");
  const [vmState, setVMState] = useState<string>("unknown");

  // Agent
  const [agentStatus, setAgentStatus] = useState<AgentStatus | null>(null);
  const [agentReachable, setAgentReachable] = useState(false);

  // Analysis
  const [currentAnalysis, setCurrentAnalysis] = useState<AnalysisResult | null>(
    null,
  );

  // UI
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  // Live preview
  const [previewEnabled, setPreviewEnabled] = useState(false);
  const [previewExpanded, setPreviewExpanded] = useState(false);
  const [previewSrc, setPreviewSrc] = useState<string>("");
  const previewTimerRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const fetchAll = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      // Fetch VMs list
      const vmsResp = await listVMs();
      if (vmsResp.status === "ok" && vmsResp.data) {
        setVMs((vmsResp.data as { vms: VMEntry[] }).vms || []);
      }

      // Fetch running VMs
      const runResp = await listRunningVMs();
      if (runResp.status === "ok" && runResp.data) {
        const running = (runResp.data as { vms: VMEntry[] }).vms || [];
        setRunningVMs(running);
        const isRunning = running.some(
          (v) => v.name === selectedVM || v.uuid === selectedVM,
        );
        setVMState(isRunning ? "running" : "poweroff");
      }

      // Fetch VM info
      try {
        const infoResp = await getVMInfo(selectedVM);
        if (infoResp.status === "ok" && infoResp.data) {
          setVMInfo((infoResp.data as { info: VMInfo }).info);
        }
      } catch {
        // VM info failed
      }

      // Fetch VM IP
      try {
        const ipResp = await getVMIP(selectedVM);
        if (ipResp.status === "ok" && ipResp.data) {
          const ifaces = (
            ipResp.data as { interfaces: Record<string, string>[] }
          ).interfaces;
          if (ifaces && ifaces.length > 0) {
            const firstIP = Object.values(ifaces[0])[0] || "";
            setVMIP(firstIP);
          }
        }
      } catch {
        setVMIP("");
      }

      // Agent status
      try {
        const agentResp = await getAgentStatus();
        if (agentResp.status === "ok" && agentResp.data) {
          setAgentStatus(agentResp.data as AgentStatus);
          setAgentReachable(true);
        } else {
          setAgentReachable(false);
        }
      } catch {
        setAgentReachable(false);
        setAgentStatus(null);
      }

      // Current analysis
      try {
        const analysisResp = await getAnalysisStatus();
        if (
          analysisResp.status === "ok" &&
          analysisResp.data &&
          "analysis_id" in analysisResp.data
        ) {
          setCurrentAnalysis(analysisResp.data as AnalysisResult);
        }
      } catch {
        // no analysis
      }
    } catch {
      setError("Cannot connect to IsoLens gateway.");
    } finally {
      setLoading(false);
    }
  }, [selectedVM]);

  const isRunning = vmState === "running";

  useEffect(() => {
    fetchAll();
    const interval = setInterval(fetchAll, 10000);
    return () => clearInterval(interval);
  }, [fetchAll]);

  // Live preview polling
  useEffect(() => {
    if (previewEnabled && isRunning) {
      // Initial frame
      setPreviewSrc(vmScreenURL(selectedVM));
      previewTimerRef.current = setInterval(() => {
        setPreviewSrc(vmScreenURL(selectedVM));
      }, 2000);
    } else {
      if (previewTimerRef.current) {
        clearInterval(previewTimerRef.current);
        previewTimerRef.current = null;
      }
      if (!isRunning) setPreviewSrc("");
    }
    return () => {
      if (previewTimerRef.current) {
        clearInterval(previewTimerRef.current);
        previewTimerRef.current = null;
      }
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [previewEnabled, isRunning, selectedVM]);

  const showSuccess = (msg: string) => {
    setSuccessMsg(msg);
    window.setTimeout(() => setSuccessMsg(null), 4000);
  };

  const handleStart = async () => {
    setActionLoading("start");
    setError(null);
    try {
      const resp = await startVM(selectedVM, true);
      if (resp.status === "ok") {
        showSuccess("VM starting...");
        window.setTimeout(fetchAll, 3000);
      } else {
        setError(resp.error?.message || "Failed to start VM");
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed");
    }
    setActionLoading(null);
  };

  const handleStop = async () => {
    setActionLoading("stop");
    setError(null);
    try {
      const resp = await poweroffVM(selectedVM);
      if (resp.status === "ok") {
        showSuccess("VM powered off");
        setVMState("poweroff");
        window.setTimeout(fetchAll, 2000);
      } else {
        setError(resp.error?.message || "Failed to stop VM");
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed");
    }
    setActionLoading(null);
  };

  const handleCheckVM = async () => {
    setActionLoading("check");
    setError(null);
    try {
      const resp = await checkVM();
      if (resp.status === "ok") {
        showSuccess("VM agent is ready!");
      } else {
        setError(resp.error?.message || "VM check failed");
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed");
    }
    setActionLoading(null);
  };

  const handleCleanup = async () => {
    setActionLoading("cleanup");
    setError(null);
    try {
      const resp = await cleanupAgent();
      if (resp.status === "ok") {
        showSuccess("Agent artifacts cleaned up");
      } else {
        setError(resp.error?.message || "Cleanup failed");
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed");
    }
    setActionLoading(null);
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900">
          Sandbox Environment
        </h1>
        <button
          onClick={fetchAll}
          disabled={loading}
          className="inline-flex items-center gap-2 text-sm text-gray-600 hover:text-violet-600 transition-colors"
        >
          <IoRefresh className={`w-4 h-4 ${loading ? "animate-spin" : ""}`} />
          Refresh
        </button>
      </div>

      {/* Error / Success banners */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-xl p-4 flex items-center gap-3">
          <IoAlertCircleOutline className="w-5 h-5 text-red-500 shrink-0" />
          <p className="text-sm text-red-700">{error}</p>
        </div>
      )}
      {successMsg && (
        <div className="bg-green-50 border border-green-200 rounded-xl p-4 flex items-center gap-3">
          <IoCheckmarkCircle className="w-5 h-5 text-green-500 shrink-0" />
          <p className="text-sm text-green-700">{successMsg}</p>
        </div>
      )}

      {/* ── Top: Live Preview (left) + Status (right) ── */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Live VM Preview — takes 2/3 width */}
        <div className="lg:col-span-2 bg-white rounded-xl shadow-sm border border-gray-200 p-4 flex flex-col">
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center gap-2">
              <IoDesktopOutline className="w-5 h-5 text-violet-500" />
              <h3 className="text-base font-semibold text-gray-900">
                Live VM Preview
              </h3>
            </div>
            <div className="flex items-center gap-2">
              {previewEnabled && isRunning && (
                <button
                  onClick={() => setPreviewExpanded(true)}
                  className="p-1.5 text-gray-400 hover:text-violet-600 transition-colors"
                  title="Fullscreen"
                >
                  <IoExpandOutline className="w-4 h-4" />
                </button>
              )}
              <button
                onClick={() => setPreviewEnabled(!previewEnabled)}
                disabled={!isRunning}
                className={`text-xs font-medium px-3 py-1.5 rounded-lg transition-colors ${
                  previewEnabled && isRunning
                    ? "bg-violet-100 text-violet-700 hover:bg-violet-200"
                    : "bg-gray-100 text-gray-500 hover:bg-gray-200 disabled:opacity-50 disabled:cursor-not-allowed"
                }`}
              >
                {previewEnabled && isRunning ? "Stop" : "Start"} Preview
              </button>
            </div>
          </div>

          <div className="flex-1 flex items-center justify-center min-h-0">
            {!isRunning ? (
              <div className="flex flex-col items-center justify-center py-10 text-gray-400">
                <IoDesktopOutline className="w-12 h-12 mb-3 opacity-40" />
                <p className="text-sm">VM is not running</p>
                <p className="text-xs mt-1">
                  Start the VM to enable live preview
                </p>
              </div>
            ) : !previewEnabled ? (
              <div className="flex flex-col items-center justify-center py-10 text-gray-400">
                <IoDesktopOutline className="w-12 h-12 mb-3 opacity-40" />
                <p className="text-sm">Preview paused</p>
                <p className="text-xs mt-1">
                  Click &quot;Start Preview&quot; to see the VM display
                </p>
              </div>
            ) : previewSrc ? (
              <div className="relative w-full rounded-lg bg-black overflow-hidden">
                {/* eslint-disable-next-line @next/next/no-img-element */}
                <img
                  src={previewSrc}
                  alt="Live VM Screenshot"
                  className="w-full h-auto object-contain"
                  onError={() => {}}
                />
                <div className="absolute top-2 right-2 flex items-center gap-1.5 bg-black/60 text-green-400 text-xs font-mono px-2 py-1 rounded">
                  <span className="w-2 h-2 bg-green-400 rounded-full animate-pulse" />
                  LIVE
                </div>
              </div>
            ) : (
              <div className="flex items-center justify-center py-10">
                <div className="animate-spin w-6 h-6 border-2 border-violet-200 border-t-violet-500 rounded-full" />
              </div>
            )}
          </div>
          <p className="text-[11px] text-gray-400 mt-2 text-center">
            Refreshes every 2s via VBoxManage
          </p>
        </div>

        {/* Sandbox Status — compact right column (1/3 width) */}
        <div className="lg:col-span-1 bg-white rounded-xl shadow-sm border border-gray-200 p-5 flex flex-col">
          {/* Status indicator */}
          <div className="flex items-center gap-3 mb-4">
            <div className="relative w-10 h-10 flex items-center justify-center shrink-0">
              <div className="absolute inset-0 rounded-full border-[3px] border-gray-200" />
              {isRunning ? (
                <>
                  <div className="absolute inset-0 rounded-full border-[3px] border-t-green-500 animate-spin" />
                  <div className="w-5 h-5 bg-green-500 rounded-full" />
                </>
              ) : (
                <div className="w-5 h-5 bg-gray-400 rounded-full" />
              )}
            </div>
            <div className="min-w-0">
              <p className="text-sm font-semibold text-gray-900">
                Sandbox:{" "}
                <span
                  className={isRunning ? "text-green-600" : "text-gray-500"}
                >
                  {isRunning ? "Running" : "Stopped"}
                </span>
              </p>
              <p className="text-xs text-gray-500 truncate">
                {selectedVM}
                {vmIP && ` · ${vmIP}`}
              </p>
            </div>
          </div>

          {/* VM selector */}
          {vms.length > 1 && (
            <div className="mb-3">
              <select
                value={selectedVM}
                onChange={(e) => setSelectedVM(e.target.value)}
                className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm text-gray-700 bg-white focus:outline-none focus:ring-2 focus:ring-violet-300"
              >
                {vms.map((vm) => (
                  <option key={vm.uuid} value={vm.name}>
                    {vm.name}
                  </option>
                ))}
              </select>
            </div>
          )}

          {/* Controls */}
          <div className="flex flex-col gap-2">
            {isRunning ? (
              <button
                onClick={handleStop}
                disabled={actionLoading === "stop"}
                className="inline-flex items-center justify-center gap-2 bg-red-500 hover:bg-red-600 disabled:opacity-50 text-white text-sm font-medium px-4 py-2 rounded-lg transition-colors w-full"
              >
                <IoStopCircle className="w-4 h-4" />
                {actionLoading === "stop" ? "Stopping..." : "Power Off"}
              </button>
            ) : (
              <button
                onClick={handleStart}
                disabled={actionLoading === "start"}
                className="inline-flex items-center justify-center gap-2 bg-green-500 hover:bg-green-600 disabled:opacity-50 text-white text-sm font-medium px-4 py-2 rounded-lg transition-colors w-full"
              >
                <IoPlayOutline className="w-4 h-4" />
                {actionLoading === "start" ? "Starting..." : "Start VM"}
              </button>
            )}
            <button
              onClick={handleCheckVM}
              disabled={!!actionLoading}
              className="inline-flex items-center justify-center gap-2 bg-white border border-gray-300 hover:bg-gray-50 disabled:opacity-50 text-gray-700 text-sm font-medium px-4 py-2 rounded-lg transition-colors w-full"
            >
              <IoCheckmarkCircle className="w-4 h-4" />
              {actionLoading === "check" ? "Checking..." : "Check Agent"}
            </button>
            <button
              onClick={handleCleanup}
              disabled={!!actionLoading}
              className="inline-flex items-center justify-center gap-2 bg-white border border-gray-300 hover:bg-gray-50 disabled:opacity-50 text-gray-700 text-sm font-medium px-4 py-2 rounded-lg transition-colors w-full"
            >
              <IoTrashOutline className="w-4 h-4" />
              {actionLoading === "cleanup" ? "Cleaning..." : "Cleanup"}
            </button>
          </div>

          {/* Agent quick-status */}
          <div className="mt-auto pt-4 border-t border-gray-100">
            <div className="flex items-center gap-2 text-xs">
              {agentReachable ? (
                <>
                  <IoCheckmarkCircle className="w-4 h-4 text-green-500 shrink-0" />
                  <span className="text-green-600 font-medium">
                    Agent Connected
                  </span>
                </>
              ) : (
                <>
                  <IoCloseCircle className="w-4 h-4 text-red-400 shrink-0" />
                  <span className="text-red-500 font-medium">
                    Agent Unreachable
                  </span>
                </>
              )}
            </div>
            {agentStatus && (
              <div className="text-[11px] text-gray-400 mt-1 ml-6 space-y-0.5">
                <p>State: {agentStatus.state}</p>
                {agentStatus.version && <p>v{agentStatus.version}</p>}
              </div>
            )}
          </div>
        </div>
      </div>

      {/* ── Fullscreen overlay ───────────────────── */}
      {previewExpanded && previewSrc && (
        <div className="fixed inset-0 z-50 bg-black flex flex-col items-center justify-center">
          <div className="absolute top-4 right-4 z-10 flex items-center gap-3">
            <div className="flex items-center gap-1.5 bg-black/60 text-green-400 text-xs font-mono px-2 py-1 rounded">
              <span className="w-2 h-2 bg-green-400 rounded-full animate-pulse" />
              LIVE
            </div>
            <button
              onClick={() => setPreviewExpanded(false)}
              className="p-2 bg-white/10 hover:bg-white/20 text-white rounded-full transition-colors"
              title="Exit Fullscreen"
            >
              <IoContractOutline className="w-5 h-5" />
            </button>
          </div>
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img
            src={previewSrc}
            alt="Live VM Screenshot — Fullscreen"
            className="max-w-full max-h-full object-contain"
            onError={() => {}}
          />
        </div>
      )}

      {/* ── Two-column cards ─────────────────────── */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Current Analysis */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">
            Current Analysis
          </h3>
          {currentAnalysis && currentAnalysis.status === "running" ? (
            <>
              <p className="text-base font-mono text-gray-800 mb-3">
                {currentAnalysis.sample_name}
              </p>
              <div className="mb-1 flex items-center gap-2">
                <span className="text-sm text-gray-500">Running</span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2.5 mb-3">
                <div
                  className="bg-violet-500 h-2.5 rounded-full animate-pulse"
                  style={{ width: "60%" }}
                />
              </div>
              <p className="text-sm text-gray-500">
                Timeout: {currentAnalysis.timeout}s
              </p>
            </>
          ) : currentAnalysis && currentAnalysis.status === "complete" ? (
            <>
              <p className="text-base font-mono text-gray-800 mb-2">
                {currentAnalysis.sample_name}
              </p>
              <p className="text-sm text-green-600 font-medium">✓ Complete</p>
              <p className="text-xs text-gray-500 mt-1">
                {currentAnalysis.sysmon_events} sysmon events,{" "}
                {currentAnalysis.files_collected?.length || 0} files
              </p>
              <a
                href="/reports"
                className="inline-block mt-3 text-sm text-violet-600 hover:text-violet-700 font-medium"
              >
                View Report →
              </a>
            </>
          ) : (
            <p className="text-sm text-gray-500">No active analysis</p>
          )}
        </div>

        {/* Agent + Shared Folder */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-3">
            Agent &amp; Shared Folder
          </h3>
          <div className="space-y-3">
            <div className="flex items-center gap-2">
              {agentReachable ? (
                <>
                  <IoCheckmarkCircle className="w-5 h-5 text-green-500" />
                  <span className="text-sm font-medium text-green-600">
                    Agent Connected
                  </span>
                </>
              ) : (
                <>
                  <IoCloseCircle className="w-5 h-5 text-red-400" />
                  <span className="text-sm font-medium text-red-500">
                    Agent Unreachable
                  </span>
                </>
              )}
            </div>
            {agentStatus && (
              <div className="text-xs text-gray-500 space-y-0.5 ml-7">
                <p>State: {agentStatus.state}</p>
                {agentStatus.version && <p>Version: {agentStatus.version}</p>}
                {agentStatus.hostname && <p>Host: {agentStatus.hostname}</p>}
              </div>
            )}
            <div className="border-t border-gray-100 pt-3 flex items-center gap-2">
              <IoCheckmarkCircle className="w-5 h-5 text-green-500" />
              <span className="text-sm font-medium text-gray-800">
                SandboxShare/
              </span>
              <span className="text-xs text-gray-400 ml-1">Mounted (R/W)</span>
            </div>
          </div>
        </div>
      </div>

      {/* ── VM Info ──────────────────────────── */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">
          Sandbox VM Info
        </h3>
        {vmInfo ? (
          <dl className="space-y-2.5 text-sm">
            {/* Identity */}
            <div className="flex justify-between">
              <dt className="text-gray-500 font-medium">VM Name:</dt>
              <dd className="text-gray-800 font-mono">
                {vmInfo.name || selectedVM}
              </dd>
            </div>
            {vmInfo.os && (
              <div className="flex justify-between">
                <dt className="text-gray-500 font-medium">OS Type:</dt>
                <dd className="text-gray-800">{vmInfo.os as string}</dd>
              </div>
            )}
            {vmInfo.uuid && (
              <div className="flex justify-between">
                <dt className="text-gray-500 font-medium">UUID:</dt>
                <dd className="text-gray-800 font-mono text-xs mt-0.5">
                  {(vmInfo.uuid as string).slice(0, 18)}…
                </dd>
              </div>
            )}
            {vmInfo.state && (
              <div className="flex justify-between">
                <dt className="text-gray-500 font-medium">State:</dt>
                <dd
                  className={`font-medium ${vmInfo.state === "running" ? "text-green-600" : "text-gray-600"}`}
                >
                  {vmInfo.state as string}
                </dd>
              </div>
            )}

            {/* Divider */}
            <div className="border-t border-gray-100 my-1" />

            {/* Resources */}
            {vmInfo.memory_mb && (
              <div className="flex justify-between">
                <dt className="text-gray-500 font-medium">RAM:</dt>
                <dd className="text-gray-800">
                  {vmInfo.memory_mb as number} MB
                </dd>
              </div>
            )}
            {vmInfo.cpus && (
              <div className="flex justify-between">
                <dt className="text-gray-500 font-medium">CPUs:</dt>
                <dd className="text-gray-800">{vmInfo.cpus as number}</dd>
              </div>
            )}
            {vmInfo.vram_mb && (
              <div className="flex justify-between">
                <dt className="text-gray-500 font-medium">Video RAM:</dt>
                <dd className="text-gray-800">{vmInfo.vram_mb as number} MB</dd>
              </div>
            )}

            {/* Hardware */}
            {vmInfo.chipset && (
              <div className="flex justify-between">
                <dt className="text-gray-500 font-medium">Chipset:</dt>
                <dd className="text-gray-800 uppercase">
                  {vmInfo.chipset as string}
                </dd>
              </div>
            )}
            {vmInfo.firmware && (
              <div className="flex justify-between">
                <dt className="text-gray-500 font-medium">Firmware:</dt>
                <dd className="text-gray-800 uppercase">
                  {vmInfo.firmware as string}
                </dd>
              </div>
            )}
            {vmInfo.graphics_controller && (
              <div className="flex justify-between">
                <dt className="text-gray-500 font-medium">Graphics:</dt>
                <dd className="text-gray-800">
                  {vmInfo.graphics_controller as string}
                </dd>
              </div>
            )}

            {/* Divider */}
            <div className="border-t border-gray-100 my-1" />

            {/* VRDE */}
            {vmInfo.vrde !== undefined && (
              <div className="flex justify-between">
                <dt className="text-gray-500 font-medium">Remote Display:</dt>
                <dd
                  className={`font-medium ${vmInfo.vrde ? "text-green-600" : "text-gray-500"}`}
                >
                  {vmInfo.vrde
                    ? `On (port ${vmInfo.vrde_port || "N/A"})`
                    : "Off"}
                </dd>
              </div>
            )}

            {/* Snapshot */}
            {vmInfo.snapshot && (
              <div className="flex justify-between">
                <dt className="text-gray-500 font-medium">Snapshot:</dt>
                <dd className="text-gray-800">{vmInfo.snapshot as string}</dd>
              </div>
            )}

            {/* Network */}
            {vmIP && (
              <div className="flex justify-between">
                <dt className="text-gray-500 font-medium">IP Address:</dt>
                <dd className="text-gray-800 font-mono">{vmIP}</dd>
              </div>
            )}
            {Array.isArray(vmInfo.network) &&
              (
                vmInfo.network as Array<{
                  slot: number;
                  type: string;
                  attachment: string;
                }>
              ).length > 0 && (
                <div>
                  <dt className="text-gray-500 font-medium mb-1.5">
                    Network Adapters:
                  </dt>
                  <dd className="space-y-1">
                    {(
                      vmInfo.network as Array<{
                        slot: number;
                        type: string;
                        mac: string;
                        attachment: string;
                      }>
                    ).map((nic, i) => (
                      <div
                        key={i}
                        className="flex items-center gap-2 text-xs bg-gray-50 rounded-md px-2.5 py-1.5"
                      >
                        <span className="text-gray-400 font-mono">
                          NIC {nic.slot}
                        </span>
                        <span className="text-gray-700 font-medium">
                          {nic.type}
                        </span>
                        {nic.attachment && (
                          <span className="text-gray-500">
                            → {nic.attachment}
                          </span>
                        )}
                      </div>
                    ))}
                  </dd>
                </div>
              )}

            {/* Shared Folders */}
            {Array.isArray(vmInfo.shared_folders) &&
              (vmInfo.shared_folders as Array<{ name: string; path: string }>)
                .length > 0 && (
                <div>
                  <dt className="text-gray-500 font-medium mb-1.5">
                    Shared Folders:
                  </dt>
                  <dd className="space-y-1">
                    {(
                      vmInfo.shared_folders as Array<{
                        name: string;
                        path: string;
                      }>
                    ).map((sf, i) => (
                      <div
                        key={i}
                        className="text-xs bg-gray-50 rounded-md px-2.5 py-1.5"
                      >
                        <span className="text-gray-700 font-medium">
                          {sf.name}
                        </span>
                        <span className="text-gray-400 ml-2">→ {sf.path}</span>
                      </div>
                    ))}
                  </dd>
                </div>
              )}
          </dl>
        ) : (
          <p className="text-sm text-gray-500">
            {loading ? "Loading..." : "VM info unavailable"}
          </p>
        )}
      </div>
    </div>
  );
}
