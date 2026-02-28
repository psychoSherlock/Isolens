"use client";

import { useEffect, useState } from "react";
import {
  IoChevronDownOutline,
  IoChevronUpOutline,
  IoAlertCircleOutline,
} from "react-icons/io5";
import { getVersion, ping, getVMInfo } from "@/lib/api";

/* ── Toggle Switch ─────────────────────────────────────── */

function ToggleSwitch({ enabled, label }: { enabled: boolean; label: string }) {
  const [isOn, setIsOn] = useState(enabled);
  return (
    <div className="flex items-center justify-between">
      <span className="text-sm text-gray-700">{label}</span>
      <div className="flex items-center gap-2">
        <button
          onClick={() => setIsOn(!isOn)}
          className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
            isOn ? "bg-violet-500" : "bg-gray-300"
          }`}
        >
          <span
            className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
              isOn ? "translate-x-6" : "translate-x-1"
            }`}
          />
        </button>
        <span className="text-sm text-gray-600">{isOn ? "On" : "Off"}</span>
      </div>
    </div>
  );
}

/* ── Collapsible Section ───────────────────────────────── */

function CollapsibleSection({
  title,
  defaultOpen = false,
  comingSoon = false,
  children,
}: {
  title: string;
  defaultOpen?: boolean;
  comingSoon?: boolean;
  children: React.ReactNode;
}) {
  const [isOpen, setIsOpen] = useState(defaultOpen);

  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="w-full px-6 py-4 flex items-center justify-between hover:bg-gray-50 transition-colors"
      >
        <div className="flex items-center gap-2">
          <h3 className="text-base font-semibold text-gray-800">{title}</h3>
          {comingSoon && (
            <span className="text-[10px] font-medium bg-amber-100 text-amber-700 px-2 py-0.5 rounded-full">
              Coming Soon
            </span>
          )}
        </div>
        {isOpen ? (
          <IoChevronUpOutline className="w-5 h-5 text-gray-500" />
        ) : (
          <IoChevronDownOutline className="w-5 h-5 text-gray-500" />
        )}
      </button>
      {isOpen && (
        <div className={`px-6 pb-5 border-t border-gray-100 ${comingSoon ? "opacity-50" : ""}`}>
          {children}
        </div>
      )}
    </div>
  );
}

/* ── Page ──────────────────────────────────────────────── */

export default function SettingsPage() {
  const [timeout, setLocalTimeout] = useState(60);
  const [screenshotInterval, setScreenshotInterval] = useState(5);

  // Live data
  const [gatewayVersion, setGatewayVersion] = useState("—");
  const [gatewayReachable, setGatewayReachable] = useState(false);
  const [vmName, setVMName] = useState("—");
  const [vmOS, setVMOS] = useState("—");
  const [vmMemory, setVMMemory] = useState("—");

  useEffect(() => {
    (async () => {
      try {
        const [verResp, pingResp] = await Promise.all([getVersion(), ping()]);
        if (verResp.status === "ok" && verResp.data) {
          setGatewayVersion((verResp.data as { version: string }).version);
        }
        setGatewayReachable(pingResp.status === "ok");
      } catch {
        setGatewayReachable(false);
      }

      try {
        const infoResp = await getVMInfo("WindowsSandbox", true);
        if (infoResp.status === "ok" && infoResp.data) {
          const info = (infoResp.data as { info: Record<string, string> }).info;
          setVMName(info.name || "WindowsSandbox");
          setVMOS(info.ostype || "—");
          setVMMemory(info.memory ? `${info.memory} MB` : "—");
        }
      } catch {
        // VM info unavailable
      }
    })();
  }, []);

  return (
    <div className="max-w-4xl">
      <div className="flex items-center gap-3 mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Settings</h1>
        <span className="text-xs font-medium bg-amber-100 text-amber-700 px-2.5 py-1 rounded-full">
          Persistence — Coming Soon
        </span>
      </div>

      <div className="bg-amber-50 border border-amber-200 rounded-xl p-4 flex items-start gap-3 mb-6">
        <IoAlertCircleOutline className="w-5 h-5 text-amber-500 mt-0.5 shrink-0" />
        <p className="text-sm text-amber-700">
          Settings are currently session-only and will reset when the page is
          reloaded. Server-side settings persistence will be added in a future
          update.
        </p>
      </div>

      <div className="space-y-4">
        {/* Analysis Settings */}
        <CollapsibleSection title="Analysis Settings" defaultOpen={true}>
          <div className="pt-4 space-y-4">
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-700">
                Default Analysis Timeout
              </span>
              <div className="flex items-center gap-2">
                <input
                  type="number"
                  value={timeout}
                  onChange={(e) => setLocalTimeout(Number(e.target.value))}
                  className="w-20 px-3 py-1.5 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-violet-500"
                />
                <span className="text-sm text-gray-600">seconds</span>
              </div>
            </div>

            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-700">
                Screenshot Capture Interval
              </span>
              <div className="flex items-center gap-2">
                <input
                  type="number"
                  value={screenshotInterval}
                  onChange={(e) => setScreenshotInterval(Number(e.target.value))}
                  className="w-16 px-3 py-1.5 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-violet-500"
                />
                <span className="text-sm text-gray-600">seconds</span>
              </div>
            </div>

            <ToggleSwitch enabled={true} label="Network Capture" />
            <ToggleSwitch enabled={true} label="Auto-Restore Snapshot" />
          </div>
        </CollapsibleSection>

        {/* VM Configuration — live data */}
        <CollapsibleSection title="VM Configuration" defaultOpen={true}>
          <div className="pt-4 space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-700">VM Name:</span>
              <span className="text-sm text-gray-600">{vmName}</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-700">OS Type:</span>
              <span className="text-sm text-gray-600">{vmOS}</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-700">RAM:</span>
              <span className="text-sm text-gray-600">{vmMemory}</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-700">Shared Folder:</span>
              <span className="text-sm text-gray-600">SandboxShare/</span>
            </div>
          </div>
        </CollapsibleSection>

        {/* Gateway Configuration — live data */}
        <CollapsibleSection title="Gateway Configuration" defaultOpen={false}>
          <div className="pt-4 space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-700">Gateway Version:</span>
              <span className="text-sm text-gray-600">{gatewayVersion}</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-700">API Port:</span>
              <span className="text-sm text-gray-600">6969</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-700">Status:</span>
              <span
                className={`text-sm font-medium ${
                  gatewayReachable ? "text-green-600" : "text-red-500"
                }`}
              >
                {gatewayReachable ? "Connected" : "Unreachable"}
              </span>
            </div>
          </div>
        </CollapsibleSection>

        {/* Storage Settings — coming soon */}
        <CollapsibleSection title="Storage Settings" defaultOpen={false} comingSoon>
          <div className="pt-4 space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-700">Sample Storage:</span>
              <span className="text-sm text-gray-600">core/storage/samples/</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-700">Log Storage:</span>
              <span className="text-sm text-gray-600">core/storage/logs/</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-700">Report Storage:</span>
              <span className="text-sm text-gray-600">core/storage/reports/</span>
            </div>
          </div>
        </CollapsibleSection>

        {/* User Preferences — coming soon */}
        <CollapsibleSection title="User Preferences" defaultOpen={false} comingSoon>
          <div className="pt-4 space-y-4">
            <div>
              <label className="block text-sm text-gray-700 mb-2">Theme:</label>
              <select
                disabled
                className="w-28 px-3 py-1.5 border border-gray-300 rounded-lg text-sm bg-white opacity-50"
              >
                <option>Light</option>
                <option>Dark</option>
              </select>
            </div>
          </div>
        </CollapsibleSection>
      </div>

      {/* Action Buttons */}
      <div className="mt-8 flex flex-col items-center gap-3">
        <button
          disabled
          className="px-8 py-2.5 bg-gray-300 text-gray-500 rounded-full font-medium cursor-not-allowed shadow-sm"
        >
          Save Settings{" "}
          <span className="text-[10px] bg-amber-100 text-amber-700 px-1.5 py-0.5 rounded-full ml-1">
            Soon
          </span>
        </button>
      </div>
    </div>
  );
}
