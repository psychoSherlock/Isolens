"use client";

import { useState } from "react";
import { IoChevronDownOutline, IoChevronUpOutline } from "react-icons/io5";

// Toggle Switch Component
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

// Collapsible Section Component
function CollapsibleSection({
  title,
  defaultOpen = false,
  children,
}: {
  title: string;
  defaultOpen?: boolean;
  children: React.ReactNode;
}) {
  const [isOpen, setIsOpen] = useState(defaultOpen);

  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="w-full px-6 py-4 flex items-center justify-between hover:bg-gray-50 transition-colors"
      >
        <h3 className="text-base font-semibold text-gray-800">{title}</h3>
        {isOpen ? (
          <IoChevronUpOutline className="w-5 h-5 text-gray-500" />
        ) : (
          <IoChevronDownOutline className="w-5 h-5 text-gray-500" />
        )}
      </button>
      {isOpen && <div className="px-6 pb-5 border-t border-gray-100">{children}</div>}
    </div>
  );
}

export default function SettingsPage() {
  const [timeout, setTimeout] = useState(300);
  const [screenshotInterval, setScreenshotInterval] = useState(3);
  const [theme, setTheme] = useState("Light");
  const [reportView, setReportView] = useState("List");
  const [itemsPerPage, setItemsPerPage] = useState(10);

  return (
    <div className="max-w-4xl">
      {/* Page Title */}
      <h1 className="text-2xl font-bold text-gray-900 mb-6">Settings</h1>

      <div className="space-y-4">
        {/* Analysis Settings */}
        <CollapsibleSection title="Analysis Settings" defaultOpen={true}>
          <div className="pt-4 space-y-4">
            {/* Default Analysis Timeout */}
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-700">Default Analysis Timeout</span>
              <div className="flex items-center gap-2">
                <input
                  type="number"
                  value={timeout}
                  onChange={(e) => setTimeout(Number(e.target.value))}
                  className="w-20 px-3 py-1.5 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-violet-500"
                />
                <span className="text-sm text-gray-600">seconds</span>
              </div>
            </div>

            {/* Screenshot Capture Interval */}
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-700">Screenshot Capture Interval</span>
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

            {/* Toggle Switches */}
            <ToggleSwitch enabled={true} label="Network Capture" />
            <ToggleSwitch enabled={true} label="Auto-Restore Snapshot" />
          </div>
        </CollapsibleSection>

        {/* VM Configuration */}
        <CollapsibleSection title="VM Configuration" defaultOpen={true}>
          <div className="pt-4 space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-700">VM Name:</span>
              <span className="text-sm text-gray-600">Isolens_VM1</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-700">Clean Snapshot:</span>
              <span className="text-sm text-gray-600">Clean State (14 Apr 2024)</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-700">Shared Folder Path:</span>
              <span className="text-sm text-gray-600">C:\SandboxShare\</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-700">Host-Only Adapter:</span>
              <span className="text-sm text-gray-600">VBoxNet0</span>
            </div>
          </div>
        </CollapsibleSection>

        {/* Gateway Configuration */}
        <CollapsibleSection title="Gateway Configuration" defaultOpen={false}>
          <div className="pt-4 space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-700">API Host:</span>
              <span className="text-sm text-gray-600">127.0.0.1</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-700">API Port:</span>
              <span className="text-sm text-gray-600">8000</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-700">Debug Mode:</span>
              <span className="text-sm text-gray-600">Disabled</span>
            </div>
          </div>
        </CollapsibleSection>

        {/* Storage Settings */}
        <CollapsibleSection title="Storage Settings" defaultOpen={false}>
          <div className="pt-4 space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-700">Sample Storage Path:</span>
              <span className="text-sm text-gray-600">/storage/samples/</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-700">Log Storage Path:</span>
              <span className="text-sm text-gray-600">/storage/logs/</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-700">Max Storage Size:</span>
              <span className="text-sm text-gray-600">10 GB</span>
            </div>
          </div>
        </CollapsibleSection>

        {/* User Preferences */}
        <CollapsibleSection title="User Preferences" defaultOpen={true}>
          <div className="pt-4 space-y-4">
            <div className="grid grid-cols-2 gap-6">
              {/* Theme */}
              <div>
                <label className="block text-sm text-gray-700 mb-2">Theme:</label>
                <select
                  value={theme}
                  onChange={(e) => setTheme(e.target.value)}
                  className="w-28 px-3 py-1.5 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-violet-500 bg-white"
                >
                  <option value="Light">Light</option>
                  <option value="Dark">Dark</option>
                  <option value="System">System</option>
                </select>
              </div>

              {/* Default Report View - Checkbox style */}
              <div>
                <label className="block text-sm text-gray-700 mb-2">Default Report View:</label>
                <div className="flex items-center gap-2">
                  <span className="text-sm text-gray-600">List</span>
                  <input
                    type="checkbox"
                    checked={reportView === "List"}
                    onChange={() => setReportView(reportView === "List" ? "Grid" : "List")}
                    className="w-4 h-4 text-violet-600 border-gray-300 rounded focus:ring-violet-500"
                  />
                </div>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-6">
              {/* Default Report View - Radio */}
              <div>
                <label className="block text-sm text-gray-700 mb-2">Default Report View:</label>
                <div className="flex items-center gap-4">
                  <label className="flex items-center gap-2">
                    <input
                      type="radio"
                      name="reportView"
                      checked={reportView === "List"}
                      onChange={() => setReportView("List")}
                      className="w-4 h-4 text-violet-600 border-gray-300 focus:ring-violet-500"
                    />
                    <span className="text-sm text-gray-600">List</span>
                  </label>
                  <label className="flex items-center gap-2">
                    <input
                      type="radio"
                      name="reportView"
                      checked={reportView === "Grid"}
                      onChange={() => setReportView("Grid")}
                      className="w-4 h-4 text-violet-600 border-gray-300 focus:ring-violet-500"
                    />
                    <span className="text-sm text-gray-600">Grid</span>
                  </label>
                </div>
              </div>

              {/* Items Per Page */}
              <div>
                <label className="block text-sm text-gray-700 mb-2">Items Per Page:</label>
                <select
                  value={itemsPerPage}
                  onChange={(e) => setItemsPerPage(Number(e.target.value))}
                  className="w-20 px-3 py-1.5 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-violet-500 bg-white"
                >
                  <option value={10}>10</option>
                  <option value={25}>25</option>
                  <option value={50}>50</option>
                  <option value={100}>100</option>
                </select>
              </div>
            </div>
          </div>
        </CollapsibleSection>
      </div>

      {/* Action Buttons */}
      <div className="mt-8 flex flex-col items-center gap-3">
        <button className="px-8 py-2.5 bg-violet-500 text-white rounded-full font-medium hover:bg-violet-600 transition-colors shadow-sm">
          Save Settings
        </button>
        <button className="px-8 py-2.5 border border-gray-300 text-gray-700 rounded-full font-medium hover:bg-gray-50 transition-colors">
          Reset to Defaults
        </button>
      </div>
    </div>
  );
}
