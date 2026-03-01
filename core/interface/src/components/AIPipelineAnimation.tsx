"use client";

import React, { useEffect, useState } from "react";
import {
  IoServerOutline,
  IoHardwareChipOutline,
  IoGlobeOutline,
  IoDocumentTextOutline,
  IoAnalyticsOutline,
  IoSparklesOutline,
  IoShieldCheckmarkOutline,
  IoCheckmarkCircle,
} from "react-icons/io5";

/* ─── Props ─────────────────────────────────────────────────────── */

interface AIPipelineAnimationProps {
  progress?: {
    current_action: string;
    completed_agents: number;
    total_agents: number;
  } | null;
  onComplete?: () => void;
}

/* ─── Agent config ──────────────────────────────────────────────── */

const AGENTS = [
  { id: "sysmon",  label: "Sysmon Analyzer",   sub: "Process & event logs",    Icon: IoServerOutline,      color: "#3b82f6" },
  { id: "procmon", label: "Procmon Analyzer",   sub: "File & registry ops",     Icon: IoHardwareChipOutline, color: "#6366f1" },
  { id: "network", label: "Network Analyzer",   sub: "Traffic & C2 detection",  Icon: IoGlobeOutline,        color: "#0ea5e9" },
  { id: "handle",  label: "Handle Analyzer",    sub: "Mutex & file handles",    Icon: IoDocumentTextOutline, color: "#8b5cf6" },
  { id: "tcpvcon", label: "TCPVcon Analyzer",   sub: "Active connections",      Icon: IoAnalyticsOutline,    color: "#a855f7" },
];

/* ─── SVG layout ────────────────────────────────────────────────── */

const VW = 1000;
const VH = 600;

// Agent nodes
const AGENT_CX  = 95;    // x-centre of agent circles
const AGENT_R   = 30;    // radius — bigger than before

// Central summariser
const CENTER_CX = 490;
const CENTER_CY = VH / 2;  // 300
const CENTER_R  = 52;

// Report node (right)
const REPORT_CX = 880;
const REPORT_CY = CENTER_CY;
const REPORT_R  = 38;

// Distribute 5 agents evenly across full height
const AGENT_CYS = AGENTS.map((_, i) => {
  const spacing = VH / (AGENTS.length + 1);
  return Math.round(spacing * (i + 1));
});

// Bezier from agent right-edge → summariser left-edge (smooth S curve)
const agentPath = (ay: number) =>
  `M ${AGENT_CX + AGENT_R} ${ay} ` +
  `C ${AGENT_CX + AGENT_R + 120} ${ay}, ` +
  `${CENTER_CX - CENTER_R - 120} ${CENTER_CY}, ` +
  `${CENTER_CX - CENTER_R} ${CENTER_CY}`;

// Horizontal bezier from summariser right-edge → report left-edge  
const reportPath =
  `M ${CENTER_CX + CENTER_R} ${CENTER_CY} ` +
  `C ${CENTER_CX + CENTER_R + 90} ${CENTER_CY}, ` +
  `${REPORT_CX - REPORT_R - 90} ${REPORT_CY}, ` +
  `${REPORT_CX - REPORT_R} ${REPORT_CY}`;

/* ─── Component ─────────────────────────────────────────────────── */

export default function AIPipelineAnimation({
  progress,
  onComplete,
}: AIPipelineAnimationProps) {
  const completedAgents = progress?.completed_agents ?? 0;
  const totalAgents     = progress?.total_agents     ?? 6;

  // drawnLines[i] = true only after agent i has responded (completedAgents > i)
  const [drawnLines, setDrawnLines] = useState<boolean[]>(
    Array(AGENTS.length).fill(false)
  );

  // Track which line draw animation has started (prevents re-triggering)
  const [lineKeys, setLineKeys] = useState<number[]>(
    Array(AGENTS.length).fill(0)
  );

  const [summarizerActive,  setSummarizerActive]  = useState(false);
  const [summarizerDone,    setSummarizerDone]     = useState(false);

  // reportLineDraw: the center→report line is animating
  const [reportLineDraw, setReportLineDraw] = useState(false);
  // reportNodeLit: report node lights up after line has drawn
  const [reportNodeLit,  setReportNodeLit]  = useState(false);
  // countdown before onComplete fires
  const [countdown, setCountdown]           = useState<number | null>(null);

  /* ── Drive paths from backend progress only ── */
  useEffect(() => {
    setDrawnLines((prev) =>
      prev.map((drawn, i) => {
        const shouldDraw = completedAgents > i;
        if (shouldDraw && !drawn) {
          // bump the key to force CSS animation restart
          setLineKeys((k) => {
            const next = [...k];
            next[i] = k[i] + 1;
            return next;
          });
        }
        return drawn || shouldDraw;
      })
    );

    if (completedAgents >= 5) setSummarizerActive(true);

    if (completedAgents >= totalAgents && totalAgents > 0) {
      setSummarizerDone(true);
    }
  }, [completedAgents, totalAgents]);

  /* ── After summariser done → draw center→report line → countdown ── */
  useEffect(() => {
    if (!summarizerDone) return;

    // Small delay let summariser lights settle, then start line draw
    const lineDelay = setTimeout(() => {
      setReportLineDraw(true);

      // After the line draw animation finishes (1.2s), light up report node
      const litDelay = setTimeout(() => {
        setReportNodeLit(true);

        // Then start 3-second countdown
        let n = 3;
        setCountdown(n);
        const iv = setInterval(() => {
          n -= 1;
          if (n <= 0) {
            clearInterval(iv);
            setCountdown(null);
            onComplete?.();
          } else {
            setCountdown(n);
          }
        }, 1000);

        return () => clearInterval(iv);
      }, 1300); // wait for line draw to complete

      return () => clearTimeout(litDelay);
    }, 500);

    return () => clearTimeout(lineDelay);
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [summarizerDone]);

  const pct = totalAgents > 0 ? Math.round((completedAgents / totalAgents) * 100) : 0;
  const isSummarizingActive = summarizerActive && !summarizerDone;

  return (
    <div className="flex flex-col items-center bg-white rounded-xl border border-slate-200 shadow-sm mt-6 overflow-hidden">
      {/* ── Inline CSS ── */}
      <style>{`
        @keyframes drawPath {
          from { stroke-dashoffset: 1; }
          to   { stroke-dashoffset: 0; }
        }
        @keyframes particleFlow {
          from { stroke-dashoffset: 0; }
          to   { stroke-dashoffset: -1; }
        }
        @keyframes pingRing {
          0%        { transform: scale(1);   opacity: 0.65; }
          70%, 100% { transform: scale(1.8); opacity: 0; }
        }
        @keyframes spinSlow {
          from { transform: rotate(0deg); }
          to   { transform: rotate(360deg); }
        }
        .ai-draw {
          stroke-dasharray: 1;
          stroke-dashoffset: 1;
          pathLength: 1;
          animation: drawPath 1.2s cubic-bezier(0.4, 0, 0.2, 1) forwards;
        }
        .ai-flow {
          stroke-dasharray: 0.07 0.10;
          stroke-dashoffset: 0;
          pathLength: 1;
          animation: particleFlow 1.6s linear infinite;
        }
        .ai-ping {
          transform-origin: center;
          animation: pingRing 2s ease-out infinite;
        }
        .ai-spin {
          transform-origin: center;
          animation: spinSlow 4s linear infinite;
        }
      `}</style>

      {/* ── Header ── */}
      <div className="w-full px-8 pt-5 pb-3 border-b border-slate-100 text-center">
        <div className="flex items-center justify-center gap-2 mb-0.5">
          <IoSparklesOutline className="w-4 h-4 text-blue-500" />
          <h3 className="text-sm font-black text-slate-800 tracking-tight">
            {summarizerDone
              ? "Pipeline Complete"
              : isSummarizingActive
              ? "Synthesizing Threat Report"
              : "AI Threat Pipeline Active"}
          </h3>
        </div>
        <p className="text-[11px] text-slate-500">
          {progress?.current_action || "Initializing AI Agents…"}
        </p>
      </div>

      {/* ── SVG ── */}
      <div className="w-full px-3 py-2">
        <svg
          viewBox={`0 0 ${VW} ${VH}`}
          className="w-full"
          style={{ maxHeight: 420 }}
          preserveAspectRatio="xMidYMid meet"
        >
          <defs>
            {AGENTS.map((a) => (
              <linearGradient key={`g-${a.id}`} id={`g-${a.id}`} x1="0%" y1="0%" x2="100%" y2="0%">
                <stop offset="0%" stopColor={a.color} stopOpacity="0.9" />
                <stop offset="100%" stopColor="#a855f7" stopOpacity="0.9" />
              </linearGradient>
            ))}
            <linearGradient id="g-report" x1="0%" y1="0%" x2="100%" y2="0%">
              <stop offset="0%" stopColor="#a855f7" stopOpacity="0.9" />
              <stop offset="100%" stopColor="#22c55e" stopOpacity="0.9" />
            </linearGradient>
            <filter id="glow">
              <feGaussianBlur in="SourceGraphic" stdDeviation="3.5" result="b" />
              <feMerge>
                <feMergeNode in="b" />
                <feMergeNode in="SourceGraphic" />
              </feMerge>
            </filter>
          </defs>

          {/* ── 5 Agent nodes + paths ── */}
          {AGENTS.map((agent, i) => {
            const Icon  = agent.Icon;
            const ay    = AGENT_CYS[i];
            const drawn = drawnLines[i];

            // active = this is the next agent to respond (in front of the queue)
            const isActive = !drawn && completedAgents === i;

            return (
              <g key={agent.id}>
                {/* Track (unlit path) */}
                <path
                  d={agentPath(ay)}
                  fill="none"
                  stroke="#f1f5f9"
                  strokeWidth="2.5"
                  strokeLinecap="round"
                />

                {/* Lit path — only after agent responds */}
                {drawn && (
                  <>
                    <path
                      key={`draw-${agent.id}-${lineKeys[i]}`}
                      d={agentPath(ay)}
                      fill="none"
                      stroke={`url(#g-${agent.id})`}
                      strokeWidth="2.5"
                      strokeLinecap="round"
                      pathLength="1"
                      className="ai-draw"
                      filter="url(#glow)"
                    />
                    {/* Flowing particles while summariser is working */}
                    {isSummarizingActive && (
                      <path
                        d={agentPath(ay)}
                        fill="none"
                        stroke={`url(#g-${agent.id})`}
                        strokeWidth="4"
                        strokeLinecap="round"
                        strokeOpacity="0.4"
                        pathLength="1"
                        className="ai-flow"
                        style={{ animationDelay: `${i * 0.2}s` }}
                      />
                    )}
                  </>
                )}

                {/* Ping ring while this agent is active */}
                {isActive && (
                  <circle
                    cx={AGENT_CX}
                    cy={ay}
                    r={AGENT_R}
                    fill="none"
                    stroke={agent.color}
                    strokeWidth="2"
                    strokeOpacity="0.45"
                    className="ai-ping"
                  />
                )}

                {/* Agent circle */}
                <circle
                  cx={AGENT_CX}
                  cy={ay}
                  r={AGENT_R}
                  fill="white"
                  stroke={drawn ? agent.color : isActive ? agent.color : "#e2e8f0"}
                  strokeWidth="2.5"
                  style={{ transition: "stroke 0.5s ease" }}
                />

                {/* Icon (foreignObject so we can use React icons at proper size) */}
                <foreignObject
                  x={AGENT_CX - 14}
                  y={ay - 14}
                  width={28}
                  height={28}
                >
                  <div
                    style={{
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "center",
                      width: "100%",
                      height: "100%",
                    }}
                  >
                    {drawn ? (
                      <IoCheckmarkCircle
                        style={{ width: 20, height: 20, color: agent.color }}
                      />
                    ) : (
                      <Icon
                        style={{
                          width: 18,
                          height: 18,
                          color: isActive ? agent.color : "#cbd5e1",
                          transition: "color 0.4s ease",
                        }}
                      />
                    )}
                  </div>
                </foreignObject>

                {/* Labels */}
                <text
                  x={AGENT_CX + AGENT_R + 12}
                  y={ay - 5}
                  fontSize="12"
                  fontWeight="700"
                  fill={drawn ? "#1e293b" : isActive ? "#1e293b" : "#94a3b8"}
                  style={{ transition: "fill 0.4s ease" }}
                >
                  {agent.label}
                </text>
                <text
                  x={AGENT_CX + AGENT_R + 12}
                  y={ay + 11}
                  fontSize="10"
                  fill={drawn || isActive ? "#64748b" : "#cbd5e1"}
                  style={{ transition: "fill 0.4s ease" }}
                >
                  {agent.sub}
                </text>
              </g>
            );
          })}

          {/* ── Center → Report track (always visible) ── */}
          <path
            d={reportPath}
            fill="none"
            stroke="#f1f5f9"
            strokeWidth="2.5"
            strokeLinecap="round"
          />

          {/* Center → Report lit path (animates after summariser done) */}
          {reportLineDraw && (
            <>
              <path
                d={reportPath}
                fill="none"
                stroke="url(#g-report)"
                strokeWidth="2.5"
                strokeLinecap="round"
                pathLength="1"
                className="ai-draw"
                filter="url(#glow)"
              />
              {reportNodeLit && (
                <path
                  d={reportPath}
                  fill="none"
                  stroke="url(#g-report)"
                  strokeWidth="4"
                  strokeLinecap="round"
                  strokeOpacity="0.4"
                  pathLength="1"
                  className="ai-flow"
                />
              )}
            </>
          )}

          {/* ── Central Summariser ── */}
          <g>
            {summarizerActive && (
              <circle
                cx={CENTER_CX}
                cy={CENTER_CY}
                r={CENTER_R + 12}
                fill="none"
                stroke={summarizerDone ? "#22c55e" : "#a855f7"}
                strokeWidth="1.5"
                strokeOpacity="0.18"
                className="ai-ping"
              />
            )}

            <circle
              cx={CENTER_CX}
              cy={CENTER_CY}
              r={CENTER_R}
              fill="white"
              stroke={
                summarizerDone
                  ? "#22c55e"
                  : isSummarizingActive
                  ? "#a855f7"
                  : "#e2e8f0"
              }
              strokeWidth="2.5"
              filter={summarizerActive ? "url(#glow)" : undefined}
              style={{ transition: "stroke 0.7s ease" }}
            />

            <foreignObject
              x={CENTER_CX - 20}
              y={CENTER_CY - 20}
              width={40}
              height={40}
            >
              <div
                style={{
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  width: "100%",
                  height: "100%",
                }}
              >
                <IoSparklesOutline
                  style={{
                    width: 30,
                    height: 30,
                    color: summarizerDone
                      ? "#22c55e"
                      : isSummarizingActive
                      ? "#a855f7"
                      : "#cbd5e1",
                    transition: "color 0.6s ease",
                    animation: isSummarizingActive
                      ? "spinSlow 4s linear infinite"
                      : "none",
                  }}
                />
              </div>
            </foreignObject>

            <text
              x={CENTER_CX}
              y={CENTER_CY + CENTER_R + 16}
              textAnchor="middle"
              fontSize="11"
              fontWeight="800"
              fill={summarizerDone ? "#16a34a" : isSummarizingActive ? "#7c3aed" : "#94a3b8"}
              letterSpacing="1"
              style={{ transition: "fill 0.6s ease" }}
            >
              THREAT SUMMARIZER
            </text>
            <text
              x={CENTER_CX}
              y={CENTER_CY + CENTER_R + 30}
              textAnchor="middle"
              fontSize="9.5"
              fill={isSummarizingActive ? "#a78bfa" : "#94a3b8"}
              style={{ transition: "fill 0.6s ease" }}
            >
              {summarizerDone
                ? "Analysis complete"
                : isSummarizingActive
                ? "Aggregating findings…"
                : "Awaiting agent data"}
            </text>
          </g>

          {/* ── Report Node ── */}
          <g>
            {reportNodeLit && (
              <circle
                cx={REPORT_CX}
                cy={REPORT_CY}
                r={REPORT_R + 12}
                fill="none"
                stroke="#22c55e"
                strokeWidth="1.5"
                strokeOpacity="0.18"
                className="ai-ping"
              />
            )}

            <circle
              cx={REPORT_CX}
              cy={REPORT_CY}
              r={REPORT_R}
              fill="white"
              stroke={reportNodeLit ? "#22c55e" : "#e2e8f0"}
              strokeWidth="2.5"
              filter={reportNodeLit ? "url(#glow)" : undefined}
              style={{ transition: "stroke 0.8s ease" }}
            />

            <foreignObject
              x={REPORT_CX - 17}
              y={REPORT_CY - 17}
              width={34}
              height={34}
            >
              <div
                style={{
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  width: "100%",
                  height: "100%",
                }}
              >
                <IoShieldCheckmarkOutline
                  style={{
                    width: 24,
                    height: 24,
                    color: reportNodeLit ? "#22c55e" : "#cbd5e1",
                    transition: "color 0.6s ease",
                  }}
                />
              </div>
            </foreignObject>

            {/* Countdown displayed inside the report node */}
            {countdown !== null && (
              <text
                x={REPORT_CX}
                y={REPORT_CY + 8}
                textAnchor="middle"
                fontSize="26"
                fontWeight="900"
                fill="#16a34a"
              >
                {countdown}
              </text>
            )}

            <text
              x={REPORT_CX}
              y={REPORT_CY + REPORT_R + 16}
              textAnchor="middle"
              fontSize="11"
              fontWeight="800"
              fill={reportNodeLit ? "#16a34a" : "#94a3b8"}
              letterSpacing="1"
              style={{ transition: "fill 0.6s ease" }}
            >
              FINAL REPORT
            </text>
          </g>
        </svg>
      </div>

      {/* ── Progress bar ── */}
      <div className="w-full px-8 pb-5">
        <div className="flex items-center justify-between mb-1.5">
          <span className="text-[10px] font-bold text-slate-400 uppercase tracking-widest">
            Pipeline Progress
          </span>
          <span className="text-[10px] font-black font-mono text-blue-600 bg-blue-50 border border-blue-100 px-2 py-0.5 rounded">
            {pct}%
          </span>
        </div>
        <div className="w-full h-2 bg-slate-100 rounded-full overflow-hidden">
          <div
            className="h-full rounded-full transition-all duration-700 ease-out relative"
            style={{
              width: `${Math.max(pct, 3)}%`,
              background: summarizerDone
                ? "linear-gradient(90deg,#22c55e,#16a34a)"
                : "linear-gradient(90deg,#3b82f6,#a855f7)",
            }}
          >
            <div className="absolute inset-0 bg-white/20 animate-pulse" />
          </div>
        </div>
      </div>
    </div>
  );
}
