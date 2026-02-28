"use client";

import { useState } from "react";
import {
  IoDocumentTextOutline,
  IoMailOutline,
  IoConstructOutline,
  IoChevronForwardOutline,
  IoChevronDownOutline,
  IoRemoveOutline,
  IoBarChartOutline,
} from "react-icons/io5";

// FAQ Accordion Item Component
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

export default function HelpSupportPage() {
  return (
    <div className="max-w-4xl">
      {/* Page Title */}
      <h1 className="text-2xl font-bold text-gray-900 mb-1">Help & Support</h1>
      <p className="text-sm text-gray-600 mb-6">
        Provides documentation, FAQs, and user info about IsoLens project for users.
      </p>

      {/* Documentation and Contact Us Row */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
        {/* Documentation Section */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-5">
          <h3 className="text-base font-semibold text-gray-800 mb-4">Documentation</h3>

          {/* Getting Started Guide Card */}
          <div className="bg-gray-50 rounded-lg p-4 mb-3">
            <div className="flex items-start gap-3">
              <div className="p-2 bg-violet-100 rounded-lg">
                <IoDocumentTextOutline className="w-5 h-5 text-violet-600" />
              </div>
              <div className="flex-1">
                <h4 className="text-sm font-semibold text-gray-800 mb-1">Getting Started Guide</h4>
                <p className="text-xs text-gray-600 mb-3">
                  Learn the basics of using IsoLens including how to upload and scan files.
                </p>
                <button className="flex items-center gap-1 text-sm text-violet-600 hover:text-violet-700 font-medium">
                  Read Guide
                  <IoChevronForwardOutline className="w-4 h-4" />
                </button>
              </div>
            </div>
          </div>

          {/* How to Interpret Reports Card */}
          <div className="bg-gray-50 rounded-lg p-4">
            <div className="flex items-start gap-3">
              <div className="p-2 bg-violet-100 rounded-lg">
                <IoBarChartOutline className="w-5 h-5 text-violet-600" />
              </div>
              <div className="flex-1">
                <h4 className="text-sm font-semibold text-gray-800 mb-1">How to Interpret Reports</h4>
                <p className="text-xs text-gray-600 mb-3">
                  Understand the scan report elements and risk scores.
                </p>
                <button className="flex items-center gap-1 text-sm text-violet-600 hover:text-violet-700 font-medium">
                  Read Guide
                  <IoChevronForwardOutline className="w-4 h-4" />
                </button>
              </div>
            </div>
          </div>
        </div>

        {/* Contact Us Section */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-5">
          <h3 className="text-base font-semibold text-gray-800 mb-4">Contact Us</h3>

          {/* Contact Support Card */}
          <div className="bg-gray-50 rounded-lg p-4 mb-3">
            <div className="flex items-start gap-3">
              <div className="p-2 bg-violet-100 rounded-lg">
                <IoMailOutline className="w-5 h-5 text-violet-600" />
              </div>
              <div className="flex-1">
                <h4 className="text-sm font-semibold text-gray-800 mb-1">Contact Support</h4>
                <p className="text-xs text-gray-600 mb-3">
                  Need further assistance? Send us a message and we'll get back to you shortly.
                </p>
                <button className="text-sm text-violet-600 hover:text-violet-700 font-medium">
                  Send Message
                </button>
              </div>
            </div>
          </div>

          {/* Troubleshooting Tips Card */}
          <div className="bg-gray-50 rounded-lg p-4">
            <div className="flex items-start gap-3">
              <div className="p-2 bg-violet-100 rounded-lg">
                <IoConstructOutline className="w-5 h-5 text-violet-600" />
              </div>
              <div className="flex-1">
                <h4 className="text-sm font-semibold text-gray-800 mb-1">Troubleshooting Tips</h4>
                <p className="text-xs text-gray-600 mb-3">
                  Find solutions to common issues and scan problems.
                </p>
                <button className="flex items-center gap-1 text-sm text-violet-600 hover:text-violet-700 font-medium">
                  Read Guide
                  <IoChevronForwardOutline className="w-4 h-4" />
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* FAQs Section */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-100 mb-6">
        <div className="px-5 py-4 border-b border-gray-100 flex items-center justify-between">
          <h3 className="text-base font-semibold text-gray-800">FAQs</h3>
          <IoChevronForwardOutline className="w-5 h-5 text-gray-400" />
        </div>
        <div className="divide-y divide-gray-100">
          <div className="px-5 py-3 flex flex-wrap gap-2">
            <button className="px-4 py-2 bg-gray-100 rounded-lg text-sm text-gray-700 hover:bg-gray-200 transition-colors">
              What is IsoLens?
            </button>
            <button className="px-4 py-2 bg-gray-100 rounded-lg text-sm text-gray-700 hover:bg-gray-200 transition-colors">
              How do I use IsoLens?
            </button>
          </div>
          <FAQItem
            question="What file types are supported for scanning?"
            answer="IsoLens supports executable files (.exe, .dll, .bat, .ps1, .zip). The maximum file size limit is 256MB."
            defaultOpen={true}
          />
          <FAQItem
            question="How long does the analysis take?"
            answer="Analysis typically takes 3-5 minutes depending on the file complexity and configured timeout settings."
          />
        </div>
      </div>

      {/* About IsoLens Section */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-5 mb-6">
        <h3 className="text-base font-semibold text-gray-800 mb-4">About IsoLens</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="flex items-center justify-between">
            <span className="text-sm text-gray-600">Version:</span>
            <span className="text-sm text-gray-800">1.0.0</span>
          </div>
          <div className="flex items-center justify-between">
            <span className="text-sm text-gray-600">Developed as part of:</span>
            <span className="text-sm text-gray-800">S6 Mini Project</span>
          </div>
          <div className="flex items-center justify-between">
            <span className="text-sm text-gray-600">Contributors:</span>
            <span className="text-sm text-violet-600 hover:text-violet-700 cursor-pointer">openai</span>
          </div>
          <div className="flex items-center justify-between">
            <span className="text-sm text-gray-600">Source Code:</span>
            <span className="text-sm text-violet-600 hover:text-violet-700 cursor-pointer">
              Visit our Github Repository
            </span>
          </div>
        </div>
      </div>

      {/* Action Buttons */}
      <div className="flex flex-col items-center gap-3">
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
