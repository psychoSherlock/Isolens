import React from "react";
import {
  IoServerOutline,
  IoHardwareChipOutline,
  IoGlobeOutline,
  IoDocumentTextOutline,
  IoAnalyticsOutline,
  IoShieldCheckmarkOutline,
  IoSparklesOutline,
} from "react-icons/io5";

interface AIPipelineAnimationProps {
  progress?: {
    current_action: string;
    completed_agents: number;
    total_agents: number;
  } | null;
}

export default function AIPipelineAnimation({ progress }: AIPipelineAnimationProps) {
  // Agents definition
  const agents = [
    { id: "sysmon", label: "Sysmon Agent", icon: IoServerOutline, color: "text-blue-500", bg: "bg-blue-50" },
    { id: "procmon", label: "Procmon Agent", icon: IoHardwareChipOutline, color: "text-indigo-500", bg: "bg-indigo-50" },
    { id: "network", label: "Network Agent", icon: IoGlobeOutline, color: "text-sky-500", bg: "bg-sky-50" },
    { id: "handle", label: "Handle Agent", icon: IoDocumentTextOutline, color: "text-violet-500", bg: "bg-violet-50" },
    { id: "tcp", label: "TCP Agent", icon: IoAnalyticsOutline, color: "text-purple-500", bg: "bg-purple-50" },
  ];

  const pct = progress ? Math.round((progress.completed_agents / Math.max(1, progress.total_agents)) * 100) : 0;
  
  // Calculate if we're in the summarizer phase
  const isSummarizing = progress?.current_action?.toLowerCase().includes("summariz");

  return (
    <div className="flex flex-col items-center justify-center p-8 bg-white rounded-lg border border-slate-200 mt-6 relative overflow-hidden min-h-[500px] shadow-sm">
      <div className="absolute inset-0 bg-gradient-to-br from-slate-50 via-white to-blue-50/30"></div>

      {/* Header */}
      <div className="relative z-10 text-center mb-10">
        <h3 className="text-xl font-black text-slate-800 tracking-tight mb-2 flex items-center justify-center gap-2">
          <IoSparklesOutline className="w-5 h-5 text-blue-500 animate-[pulse_2s_ease-in-out_infinite]" />
          AI Threat Pipeline Active
        </h3>
        <p className="text-sm font-medium text-slate-500">
          {progress?.current_action || "Initializing AI Agents..."}
        </p>
      </div>

      {/* Pipeline Visualization */}
      <div className="relative z-10 w-full max-w-4xl flex items-center justify-between px-4 lg:px-12 h-64">
        
        {/* SVG Data Flows (Background layer) */}
        <div className="absolute inset-0 pointer-events-none">
          <svg className="w-full h-full" preserveAspectRatio="none">
            <defs>
              <linearGradient id="flow-gradient" x1="0%" y1="0%" x2="100%" y2="0%">
                <stop offset="0%" stopColor="#3b82f6" stopOpacity="0.2" />
                <stop offset="50%" stopColor="#8b5cf6" stopOpacity="0.6" />
                <stop offset="100%" stopColor="#3b82f6" stopOpacity="0.2" />
              </linearGradient>
              
              {/* Particle animation definition */}
              <style>
                {`
                  .particle-flow {
                    stroke-dasharray: 10 20;
                    animation: flow 1.5s linear infinite;
                  }
                  .particle-flow-slow {
                    stroke-dasharray: 15 30;
                    animation: flow 2s linear infinite;
                  }
                  @keyframes flow {
                    to {
                      stroke-dashoffset: -30;
                    }
                  }
                  
                  .pulse-glow {
                    animation: ping-slow 3s cubic-bezier(0, 0, 0.2, 1) infinite;
                  }
                  @keyframes ping-slow {
                    75%, 100% {
                      transform: scale(1.5);
                      opacity: 0;
                    }
                  }
                `}
              </style>
            </defs>

            {/* Connecting lines from 5 agents to Summarizer */}
            {[10, 30, 50, 70, 90].map((yPct, i) => (
              <g key={`flow-${i}`}>
                {/* Static track */}
                <path
                  d={`M 20% ${yPct}% C 40% ${yPct}%, 50% 50%, 75% 50%`}
                  fill="none"
                  stroke="#e2e8f0"
                  strokeWidth="2"
                  className="transition-colors duration-500"
                />
                
                {/* Flowing particles (only fast before summarizing) */}
                <path
                  d={`M 20% ${yPct}% C 40% ${yPct}%, 50% 50%, 75% 50%`}
                  fill="none"
                  stroke="url(#flow-gradient)"
                  strokeWidth="3"
                  strokeLinecap="round"
                  className={isSummarizing ? "particle-flow-slow opacity-30" : "particle-flow"}
                  style={{ animationDelay: `${i * 0.2}s` }}
                />
              </g>
            ))}
          </svg>
        </div>

        {/* 1. Left Column: Specialized Agents */}
        <div className="relative flex flex-col justify-between h-full w-1/4 z-10">
          {agents.map((agent, i) => {
            const Icon = agent.icon;
            // Highlight agent if completed
            const isDone = progress && progress.completed_agents > i;
            
            return (
              <div key={agent.id} className="flex items-center gap-3 relative group">
                {/* Node */}
                <div className={`w-10 h-10 rounded-full flex items-center justify-center shrink-0 border-2 transition-all duration-500 shadow-sm relative bg-white
                  ${isDone ? "border-green-400" : (isSummarizing ? "border-slate-200" : "border-blue-400")}
                `}>
                  {/* Pulse ring when active */}
                  {!isDone && !isSummarizing && (
                     <div className="absolute inset-0 rounded-full border-2 border-blue-400 opacity-50 pulse-glow"></div>
                  )}
                  
                  <Icon className={`w-5 h-5 transition-colors ${isDone ? "text-green-500" : (isSummarizing ? "text-slate-400" : agent.color)}`} />
                </div>
                
                {/* Label */}
                <span className={`text-[11px] font-bold uppercase tracking-wider transition-colors
                  ${isDone ? "text-green-600" : (isSummarizing ? "text-slate-400" : "text-slate-700")}
                `}>
                  {agent.label}
                </span>
              </div>
            );
          })}
        </div>

        {/* 2. Middle Column: Threat Summarizer */}
        <div className="relative flex flex-col items-center justify-center w-2/4 z-10">
          <div className="relative flex flex-col items-center">
            
            <div className={`w-20 h-20 rounded-full flex items-center justify-center border-4 shadow-lg transition-all duration-700 bg-white relative z-10
              ${isSummarizing ? "border-purple-500 scale-110" : "border-slate-200 scale-100"}
            `}>
              {/* Massive active pulse when summarizing */}
              {isSummarizing && (
                <>
                  <div className="absolute inset-0 rounded-full border-4 border-purple-400 opacity-60 pulse-glow"></div>
                  <div className="absolute inset-0 rounded-full bg-purple-100 opacity-40 animate-pulse"></div>
                </>
              )}
              
              <IoSparklesOutline className={`w-10 h-10 transition-colors duration-700 ${isSummarizing ? "text-purple-600 animate-spin-slow" : "text-slate-400"}`} />
            </div>
            
            <div className="mt-4 text-center">
              <span className={`text-sm font-black uppercase tracking-widest transition-colors ${isSummarizing ? "text-purple-700" : "text-slate-500"}`}>
                Threat Summarizer
              </span>
              <p className="text-[10px] text-slate-400 font-bold uppercase tracking-widest mt-1">Main Agent</p>
            </div>
          </div>
        </div>

        {/* 3. Right Column: Output Report */}
        <div className="relative flex flex-col items-center justify-center w-1/4 z-10">
          <div className={`w-14 h-14 rounded-xl flex items-center justify-center border-2 transition-all duration-700 shadow-md bg-white
            ${pct === 100 ? "border-blue-500 scale-110 shadow-blue-200" : "border-slate-200 opacity-60"}
          `}>
            <IoShieldCheckmarkOutline className={`w-7 h-7 ${pct === 100 ? "text-blue-500" : "text-slate-300"}`} />
          </div>
          <span className={`text-xs font-bold uppercase mt-3 transition-colors ${pct === 100 ? "text-blue-600" : "text-slate-400"}`}>
            Final Report
          </span>
        </div>

      </div>

      {/* Overall Progress Bar Footer */}
      <div className="relative z-10 w-full max-w-lg mt-10">
        <div className="flex justify-between items-end mb-2">
          <span className="text-[11px] font-bold text-slate-400 uppercase tracking-widest">
            Pipeline Progress
          </span>
          <span className="text-[11px] font-black font-mono text-slate-600 bg-slate-100 px-2 py-0.5 rounded border border-slate-200">
            {pct}%
          </span>
        </div>
        <div className="w-full h-2 bg-slate-100 rounded-full overflow-hidden shadow-inner">
          <div 
            className="h-full bg-slate-800 transition-all duration-500 ease-out"
            style={{ width: `${pct || 5}%` }}
          />
        </div>
      </div>

    </div>
  );
}
