"use client";

import { useEffect, useState } from "react";
import {
  IoDocumentTextOutline,
  IoMailOutline,
  IoConstructOutline,
  IoChevronForwardOutline,
  IoRemoveOutline,
  IoBarChartOutline,
  IoLogoGithub,
} from "react-icons/io5";
import { getVersion } from "@/lib/api";

/* ── FAQ Accordion ─────────────────────────────────────── */

function FAQItem({
  question,
  answer,
  defaultOpen = false,
}: {
  question: string;
  answer?: string;
  defaultOpen?: boolean;
}) {
  const [isOpen, setIsOpen] = useState(defaultOpen);

  return (
    <div className="border-b border-gray-100 last:border-b-0">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="w-full py-3 flex items-center justify-between hover:bg-gray-50 transition-colors px-4"
      >
        <span className="text-sm text-gray-700 text-left">{question}</span>
        {isOpen ? (
          <IoRemoveOutline className="w-5 h-5 text-gray-500 flex-shrink-0" />
        ) : (
          <IoChevronForwardOutline className="w-5 h-5 text-gray-500 flex-shrink-0" />
        )}
      </button>
      {isOpen && answer && (
        <div className="px-4 pb-4 text-sm text-gray-600">{answer}</div>
      )}
    </div>
  );
}

/* ── Page ──────────────────────────────────────────────── */

export default function HelpSupportPage() {
  const [version, setVersion] = useState("—");

  useEffect(() => {
    (async () => {
      try {
        const resp = await getVersion();
        if (resp.status === "ok" && resp.data) {
          setVersion((resp.data as { version: string }).version);
        }
      } catch {
        setVersion("unavailable");
      }
    })();
  }, []);

  return (
    <div className="max-w-4xl">
      <h1 className="text-2xl font-bold text-gray-900 mb-1">Help & Support</h1>
      <p className="text-sm text-gray-600 mb-6">
        Documentation, FAQs, and project information for IsoLens.
      </p>

      {/* Documentation and Contact Us Row */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
        {/* Documentation Section */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-5">
          <h3 className="text-base font-semibold text-gray-800 mb-4">
            Documentation
          </h3>

          <div className="bg-gray-50 rounded-lg p-4 mb-3">
            <div className="flex items-start gap-3">
              <div className="p-2 bg-violet-100 rounded-lg">
                <IoDocumentTextOutline className="w-5 h-5 text-violet-600" />
              </div>
              <div className="flex-1">
                <h4 className="text-sm font-semibold text-gray-800 mb-1">
                  Getting Started Guide
                </h4>
                <p className="text-xs text-gray-600 mb-3">
                  Learn the basics: upload a suspicious file on the{" "}
                  <a href="/scan" className="text-violet-600">
                    Scan
                  </a>{" "}
                  page, monitor progress, then review the report.
                </p>
              </div>
            </div>
          </div>

          <div className="bg-gray-50 rounded-lg p-4">
            <div className="flex items-start gap-3">
              <div className="p-2 bg-violet-100 rounded-lg">
                <IoBarChartOutline className="w-5 h-5 text-violet-600" />
              </div>
              <div className="flex-1">
                <h4 className="text-sm font-semibold text-gray-800 mb-1">
                  How to Interpret Reports
                </h4>
                <p className="text-xs text-gray-600 mb-3">
                  Reports show Sysmon events, collected artifacts, and
                  screenshots captured during execution. AI threat intelligence
                  summaries are coming soon.
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* Contact Us Section */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-5">
          <div className="flex items-center gap-2 mb-4">
            <h3 className="text-base font-semibold text-gray-800">
              Contact Us
            </h3>
            <span className="text-[10px] font-medium bg-amber-100 text-amber-700 px-2 py-0.5 rounded-full">
              Coming Soon
            </span>
          </div>

          <div className="bg-gray-50 rounded-lg p-4 mb-3 opacity-60">
            <div className="flex items-start gap-3">
              <div className="p-2 bg-violet-100 rounded-lg">
                <IoMailOutline className="w-5 h-5 text-violet-600" />
              </div>
              <div className="flex-1">
                <h4 className="text-sm font-semibold text-gray-800 mb-1">
                  Contact Support
                </h4>
                <p className="text-xs text-gray-600 mb-3">
                  In-app messaging will be available in a future update.
                </p>
              </div>
            </div>
          </div>

          <div className="bg-gray-50 rounded-lg p-4">
            <div className="flex items-start gap-3">
              <div className="p-2 bg-violet-100 rounded-lg">
                <IoConstructOutline className="w-5 h-5 text-violet-600" />
              </div>
              <div className="flex-1">
                <h4 className="text-sm font-semibold text-gray-800 mb-1">
                  Troubleshooting Tips
                </h4>
                <p className="text-xs text-gray-600">
                  <strong>Gateway not connecting?</strong> Ensure the gateway is
                  running on port 6969.
                  <br />
                  <strong>Agent unreachable?</strong> Start the VM from the{" "}
                  <a href="/sandbox" className="text-violet-600">
                    Sandbox
                  </a>{" "}
                  page and verify the agent is running.
                  <br />
                  <strong>Scan stuck?</strong> Check the{" "}
                  <a href="/sandbox" className="text-violet-600">
                    Sandbox
                  </a>{" "}
                  page for VM/agent status.
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* FAQs Section */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-100 mb-6">
        <div className="px-5 py-4 border-b border-gray-100">
          <h3 className="text-base font-semibold text-gray-800">FAQs</h3>
        </div>
        <div className="divide-y divide-gray-100">
          <FAQItem
            question="What file types are supported for scanning?"
            answer="IsoLens supports executable files (.exe, .dll, .bat, .ps1, .zip). The maximum file size is 256MB."
            defaultOpen={true}
          />
          <FAQItem
            question="How long does the analysis take?"
            answer="Analysis typically takes 2-5 minutes depending on the configured timeout (default 60 seconds for execution monitoring) plus artifact collection time."
          />
          <FAQItem
            question="What data is collected during analysis?"
            answer="IsoLens collects Sysmon logs (process creation, network, file, registry events), network capture (tshark), process handles, TCP connections, screenshots, and optionally Procmon logs."
          />
          <FAQItem
            question="How are screenshots captured?"
            answer="Screenshots are captured in two ways: the host uses VBoxManage screenshotpng at configurable intervals, and the in-VM agent captures via PowerShell with System.Drawing."
          />
          <FAQItem
            question="Is IsoLens safe to use?"
            answer="IsoLens runs malware inside an isolated VirtualBox VM with host-only networking. The VM is restored to a clean snapshot after each analysis. It's designed for academic/educational use."
          />
        </div>
      </div>

      {/* About IsoLens — with live version */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-5 mb-6">
        <h3 className="text-base font-semibold text-gray-800 mb-4">
          About IsoLens
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="flex items-center justify-between">
            <span className="text-sm text-gray-600">Gateway Version:</span>
            <span className="text-sm text-gray-800 font-mono">{version}</span>
          </div>
          <div className="flex items-center justify-between">
            <span className="text-sm text-gray-600">Developed as part of:</span>
            <span className="text-sm text-gray-800">S6 Mini Project</span>
          </div>
          <div className="flex items-center justify-between">
            <span className="text-sm text-gray-600">Source Code:</span>
            <a
              href="https://github.com"
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-1 text-sm text-violet-600 hover:text-violet-700"
            >
              <IoLogoGithub className="w-4 h-4" />
              GitHub Repository
            </a>
          </div>
        </div>
      </div>
    </div>
  );
}
