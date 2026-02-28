"use client";

import {
  IoCloudUploadOutline,
  IoFolderOpenOutline,
  IoInformationCircleOutline,
  IoCheckmarkOutline,
  IoPause,
  IoEllipsisHorizontal,
  IoRefreshOutline,
  IoFlashOutline,
} from "react-icons/io5";

export default function ScanPage() {
  return (
    <div className="space-y-6">
      {/* Page Title */}
      <h1 className="text-2xl font-bold text-gray-900">Scan</h1>

      {/* ── Upload & Scan ──────────────────────────────── */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-5">Upload &amp; Scan</h2>

        <div className="flex flex-col lg:flex-row gap-6">
          {/* Drag & Drop zone */}
          <div className="flex-1">
            <div className="border-2 border-dashed border-violet-200 bg-violet-50/40 rounded-xl p-8 flex flex-col items-center justify-center text-center min-h-[200px]">
              {/* Cloud icon */}
              <div className="w-14 h-14 rounded-full bg-violet-100 flex items-center justify-center mb-4">
                <IoCloudUploadOutline className="w-7 h-7 text-violet-500" />
              </div>
              {/* Small preview thumbnails */}
              <div className="flex gap-2 mb-3">
                <div className="w-10 h-10 rounded-md bg-violet-100 border border-violet-200 flex items-center justify-center text-xs text-violet-500 font-medium">
                  3
                </div>
                <div className="w-10 h-10 rounded-md bg-violet-100 border border-violet-200 flex items-center justify-center">
                  <IoFolderOpenOutline className="w-4 h-4 text-violet-500" />
                </div>
              </div>
            </div>

            {/* Progress bar */}
            <div className="flex items-center gap-3 mt-4">
              <span className="text-sm text-gray-500 whitespace-nowrap">No ongoing scan</span>
              <div className="flex-1 h-2 bg-gray-200 rounded-full overflow-hidden">
                <div className="h-full bg-violet-500 rounded-full" style={{ width: "0%" }} />
              </div>
              <span className="text-sm text-gray-400">0%</span>
            </div>
          </div>

          {/* Right side: Drag text + Browse */}
          <div className="flex flex-col items-center justify-center lg:w-64 text-center">
            <p className="text-base text-gray-700 mb-1">
              <span className="font-bold">Drag</span> &amp; <span className="font-bold">Drop</span> file here or
            </p>
            <button className="mt-3 w-full bg-violet-600 hover:bg-violet-700 text-white font-medium py-3 px-6 rounded-lg transition-colors text-sm">
              Browse File
            </button>
            <p className="text-xs text-gray-400 mt-3">Supported file types: exe, dll, bat, ps1</p>
            <button className="mt-2 p-1.5 hover:bg-gray-100 rounded-md transition-colors">
              <IoRefreshOutline className="w-4 h-4 text-gray-400" />
            </button>
          </div>
        </div>
      </div>

      {/* ── Quick Scan Status + Scan Options ───────────── */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Quick Scan Status */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">
            <span className="font-bold">QuickScan</span>
            <span className="font-normal text-gray-500">Status</span>
          </h3>

          <div className="flex items-center justify-between mb-5">
            <div className="flex items-center gap-2">
              <IoFlashOutline className="w-5 h-5 text-violet-500" />
              <span className="text-sm text-gray-600">No ongoing scan</span>
            </div>
            <div className="flex gap-2">
              <button className="w-8 h-8 rounded-md border border-gray-200 hover:bg-gray-50 flex items-center justify-center transition-colors">
                <IoPause className="w-4 h-4 text-gray-400" />
              </button>
              <button className="w-8 h-8 rounded-md border border-gray-200 hover:bg-gray-50 flex items-center justify-center transition-colors">
                <IoEllipsisHorizontal className="w-4 h-4 text-gray-400" />
              </button>
            </div>
          </div>

          {/* Supported file types (inside card) */}
          <div className="bg-violet-50/50 rounded-lg p-4 border border-violet-100">
            <div className="flex items-center gap-2 mb-2">
              <IoInformationCircleOutline className="w-5 h-5 text-violet-500" />
              <h4 className="text-sm font-bold text-gray-800">Supported file types</h4>
            </div>
            <div className="flex items-center gap-1 text-sm text-gray-600 ml-7">
              <IoCheckmarkOutline className="w-4 h-4 text-violet-500 shrink-0" />
              <span>.exe, .dll, .bat, .ps1, .ps1, .zip</span>
              <IoCheckmarkOutline className="w-4 h-4 text-violet-500 ml-2 shrink-0" />
            </div>
            <div className="flex items-center gap-1 text-sm text-gray-600 ml-7 mt-1">
              <IoCheckmarkOutline className="w-4 h-4 text-violet-500 shrink-0" />
              <span>Max size limit: 256MB</span>
            </div>
          </div>
        </div>

        {/* Scan Options */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Scan Options</h3>

          {/* Analysis Timeout dropdown */}
          <div className="mb-5">
            <div className="relative">
              <select className="w-full appearance-none border border-gray-300 rounded-lg px-4 py-2.5 pr-10 text-sm text-gray-700 bg-white focus:outline-none focus:ring-2 focus:ring-violet-300">
                <option>Analysis Timeout</option>
                <option>30 seconds</option>
                <option>60 seconds</option>
                <option>120 seconds</option>
                <option>300 seconds</option>
              </select>
              <svg className="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400 pointer-events-none" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
              </svg>
            </div>
          </div>

          {/* Toggle: Capture Screenshots */}
          <div className="flex items-center justify-between mb-4">
            <span className="text-sm text-gray-700">Capture Screenshots</span>
            <button className="relative w-12 h-6 bg-violet-500 rounded-full transition-colors" aria-label="Toggle capture screenshots">
              <span className="absolute right-1 top-1 w-4 h-4 bg-white rounded-full shadow transition-transform" />
            </button>
          </div>

          {/* Toggle: Network Monitoring */}
          <div className="flex items-center justify-between mb-6">
            <span className="text-sm text-gray-700">Network Monitoring</span>
            <button className="relative w-12 h-6 bg-violet-500 rounded-full transition-colors" aria-label="Toggle network monitoring">
              <span className="absolute right-1 top-1 w-4 h-4 bg-white rounded-full shadow transition-transform" />
            </button>
          </div>

          {/* Start Scan button */}
          <button className="w-full bg-violet-600 hover:bg-violet-700 text-white font-medium py-3 rounded-lg transition-colors text-sm">
            Start Scan
          </button>
        </div>
      </div>

      {/* ── Supported file types (bottom banner) ─────── */}
      <div className="bg-violet-50/50 rounded-xl border border-violet-100 p-5">
        <div className="flex items-center gap-2 mb-2">
          <IoInformationCircleOutline className="w-5 h-5 text-violet-500" />
          <h4 className="text-sm font-bold text-gray-800">Supported file types</h4>
        </div>
        <p className="text-sm text-gray-600 ml-7">
          Supported file types: .exe, .dll, .bat, .ps1, .zip
        </p>
        <p className="text-sm text-gray-600 ml-7 mt-1">
          Max size limit: 256MB
        </p>
      </div>
    </div>
  );
}
