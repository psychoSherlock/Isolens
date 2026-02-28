"use client";

import { useEffect, useState, useCallback } from "react";
import {
  IoStopCircle,
  IoPause,
  IoRefresh,
  IoCheckmarkCircle,
  IoCloseCircle,
  IoPlayOutline,
  IoTimeOutline,
  IoAlertCircleOutline,
  IoTrashOutline,
} from "react-icons/io5";
import {
  listVMs,
  listRunningVMs,
  getVMInfo,
  getVMIP,
  startVM,
  poweroffVM,
  restoreCurrentSnapshot,
  getAgentStatus,
  checkVM,
  cleanupAgent,
  getAnalysisStatus,
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

  useEffect(() => {
    fetchAll();
    const interval = setInterval(fetchAll, 10000);
    return () => clearInterval(interval);
  }, [fetchAll]);

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

  const handleRestore = async () => {
    setActionLoading("restore");
    setError(null);
    try {
      const resp = await restoreCurrentSnapshot(selectedVM);
      if (resp.status === "ok") {
        showSuccess("Snapshot restored");
        window.setTimeout(fetchAll, 2000);
      } else {
        setError(resp.error?.message || "Failed to restore snapshot");
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

  const isRunning = vmState === "running";

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

      {/* ── Status Banner ────────────────────────── */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
        <div className="flex items-center gap-4 mb-5">
          <div className="relative w-14 h-14 flex items-center justify-center">
            <div className="absolute inset-0 rounded-full border-4 border-gray-200" />
            {isRunning ? (
              <>
                <div className="absolute inset-0 rounded-full border-4 border-t-green-500 animate-spin" />
                <div className="w-8 h-8 bg-green-500 rounded-full" />
              </>
            ) : (
              <div className="w-8 h-8 bg-gray-400 rounded-full" />
            )}
          </div>
          <div>
            <h2 className="text-xl font-semibold text-gray-900">
              Sandbox Status:{" "}
              <span
                className={`font-bold ${isRunning ? "text-green-600" : "text-gray-500"}`}
              >
                {isRunning ? "Running" : "Stopped"}
              </span>
            </h2>
            <p className="text-sm text-gray-500">
              VM: {selectedVM}
              {vmIP && ` — ${vmIP}`}
            </p>
          </div>
        </div>

        {/* VM selector */}
        {vms.length > 1 && (
          <div className="mb-4">
            <select
              value={selectedVM}
              onChange={(e) => setSelectedVM(e.target.value)}
              className="border border-gray-300 rounded-lg px-3 py-2 text-sm text-gray-700 bg-white focus:outline-none focus:ring-2 focus:ring-violet-300"
            >
              {vms.map((vm) => (
                <option key={vm.uuid} value={vm.name}>
                  {vm.name}
                </option>
              ))}
            </select>
          </div>
        )}

        {/* Control buttons */}
        <div className="flex flex-wrap gap-3">
          {isRunning ? (
            <button
              onClick={handleStop}
              disabled={actionLoading === "stop"}
              className="inline-flex items-center gap-2 bg-red-500 hover:bg-red-600 disabled:opacity-50 text-white text-sm font-medium px-5 py-2.5 rounded-lg transition-colors"
            >
              <IoStopCircle className="w-4 h-4" />
              {actionLoading === "stop" ? "Stopping..." : "Power Off"}
            </button>
          ) : (
            <button
              onClick={handleStart}
              disabled={actionLoading === "start"}
              className="inline-flex items-center gap-2 bg-green-500 hover:bg-green-600 disabled:opacity-50 text-white text-sm font-medium px-5 py-2.5 rounded-lg transition-colors"
            >
              <IoPlayOutline className="w-4 h-4" />
              {actionLoading === "start" ? "Starting..." : "Start VM"}
            </button>
          )}
          <button
            onClick={handleRestore}
            disabled={!!actionLoading}
            className="inline-flex items-center gap-2 bg-white border border-gray-300 hover:bg-gray-50 disabled:opacity-50 text-gray-700 text-sm font-medium px-5 py-2.5 rounded-lg transition-colors"
          >
            <IoRefresh className="w-4 h-4" />
            {actionLoading === "restore" ? "Restoring..." : "Restore Snapshot"}
          </button>
          <button
            onClick={handleCheckVM}
            disabled={!!actionLoading}
            className="inline-flex items-center gap-2 bg-white border border-gray-300 hover:bg-gray-50 disabled:opacity-50 text-gray-700 text-sm font-medium px-5 py-2.5 rounded-lg transition-colors"
          >
            <IoCheckmarkCircle className="w-4 h-4" />
            {actionLoading === "check" ? "Checking..." : "Check Agent"}
          </button>
          <button
            onClick={handleCleanup}
            disabled={!!actionLoading}
            className="inline-flex items-center gap-2 bg-white border border-gray-300 hover:bg-gray-50 disabled:opacity-50 text-gray-700 text-sm font-medium px-5 py-2.5 rounded-lg transition-colors"
          >
            <IoTrashOutline className="w-4 h-4" />
            {actionLoading === "cleanup" ? "Cleaning..." : "Cleanup Artifacts"}
          </button>
        </div>
      </div>

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
        <div className="space-y-6">
          <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-3">
              Agent Connection Status
            </h3>
            <div className="flex items-center gap-2">
              {agentReachable ? (
                <>
                  <IoCheckmarkCircle className="w-6 h-6 text-green-500" />
                  <span className="text-base font-medium text-green-600">
                    Connected
                  </span>
                </>
              ) : (
                <>
                  <IoCloseCircle className="w-6 h-6 text-red-400" />
                  <span className="text-base font-medium text-red-500">
                    Unreachable
                  </span>
                </>
              )}
            </div>
            {agentStatus && (
              <div className="mt-2 text-xs text-gray-500 space-y-1 ml-8">
                <p>State: {agentStatus.state}</p>
                {agentStatus.version && <p>Version: {agentStatus.version}</p>}
                {agentStatus.hostname && <p>Host: {agentStatus.hostname}</p>}
              </div>
            )}
          </div>

          <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-3">
              Shared Folder Status
            </h3>
            <div className="flex items-center gap-2">
              <IoCheckmarkCircle className="w-6 h-6 text-green-500" />
              <span className="text-base font-medium text-gray-800">
                SandboxShare/
              </span>
            </div>
            <p className="text-sm text-gray-400 mt-1 ml-8">
              Mounted (Read/Write)
            </p>
          </div>
        </div>
      </div>

      {/* ── VM Info ──────────────────────────── */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">
            Sandbox VM Info
          </h3>
          {vmInfo ? (
            <dl className="space-y-3 text-sm">
              <div className="flex justify-between">
                <dt className="text-gray-500 font-medium">VM Name:</dt>
                <dd className="text-gray-800">{vmInfo.name || selectedVM}</dd>
              </div>
              {vmInfo.ostype && (
                <div className="flex justify-between">
                  <dt className="text-gray-500 font-medium">OS:</dt>
                  <dd className="text-gray-800">{vmInfo.ostype}</dd>
                </div>
              )}
              {vmInfo.memory && (
                <div className="flex justify-between">
                  <dt className="text-gray-500 font-medium">RAM:</dt>
                  <dd className="text-gray-800">{vmInfo.memory} MB</dd>
                </div>
              )}
              {vmInfo.VMState && (
                <div className="flex justify-between">
                  <dt className="text-gray-500 font-medium">State:</dt>
                  <dd className="text-gray-800">{vmInfo.VMState}</dd>
                </div>
              )}
              {vmIP && (
                <div className="flex justify-between">
                  <dt className="text-gray-500 font-medium">Network:</dt>
                  <dd className="text-gray-800 text-right">
                    Host Only Adapter
                    <br />
                    {vmIP}
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

        {/* Pause/Resume — Coming Soon */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 opacity-60">
          <div className="flex items-center gap-3 mb-4">
            <h3 className="text-lg font-semibold text-gray-900">
              Advanced VM Controls
            </h3>
            <span className="text-xs font-normal bg-amber-100 text-amber-700 px-2 py-0.5 rounded-full">
              Coming Soon
            </span>
          </div>
          <p className="text-sm text-gray-500 mb-3">
            Pause/Resume, Save State, Named Snapshots, and real-time activity
            log will be available here.
          </p>
          <div className="flex gap-3">
            <button
              disabled
              className="inline-flex items-center gap-2 bg-gray-200 text-gray-400 text-sm font-medium px-5 py-2.5 rounded-lg cursor-not-allowed"
            >
              <IoPause className="w-4 h-4" />
              Pause
            </button>
            <button
              disabled
              className="inline-flex items-center gap-2 bg-gray-200 text-gray-400 text-sm font-medium px-5 py-2.5 rounded-lg cursor-not-allowed"
            >
              <IoTimeOutline className="w-4 h-4" />
              Save State
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
