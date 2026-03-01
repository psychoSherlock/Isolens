import { jsPDF } from "jspdf";
import autoTable from "jspdf-autotable";
import type { AIReport } from "./api";

/* ── colour helpers ── */
function riskColor(score: number): [number, number, number] {
  if (score >= 80) return [239, 68, 68];   // red
  if (score >= 60) return [249, 115, 22];  // orange
  if (score >= 40) return [234, 179, 8];   // yellow
  if (score >= 20) return [34, 197, 94];   // green
  return [107, 114, 128];                  // grey
}

function riskBgColor(score: number): [number, number, number] {
  if (score >= 80) return [254, 242, 242]; // red-50
  if (score >= 60) return [255, 247, 237]; // orange-50
  if (score >= 40) return [254, 252, 232]; // yellow-50
  if (score >= 20) return [240, 253, 244]; // green-50
  return [249, 250, 251];                  // grey-50
}

function severityColor(sev: string): [number, number, number] {
  const s = sev.toLowerCase();
  if (s === "critical") return [220, 38, 38];
  if (s === "high") return [239, 68, 68];
  if (s === "medium") return [245, 158, 11];
  if (s === "low") return [59, 130, 246];
  return [100, 116, 139];
}

/* ══════════════════════════════════════════════════════════════════════════
   DRAW RISK GAUGE — circular progress arc drawn with pure jsPDF primitives
   ══════════════════════════════════════════════════════════════════════════ */

function drawRiskGauge(doc: jsPDF, cx: number, cy: number, score: number, level: string) {
  const r = 22;
  const [cr, cg, cb] = riskColor(score);
  const [br, bg, bb] = riskBgColor(score);

  // Background circle fill
  doc.setFillColor(br, bg, bb);
  doc.circle(cx, cy, r + 4, "F");

  // Background ring (thin grey)
  doc.setDrawColor(220, 220, 220);
  doc.setLineWidth(3);
  doc.circle(cx, cy, r, "S");

  // Foreground arc — approximate with short line segments
  const pct = Math.min(score, 100) / 100;
  const startAngle = -Math.PI / 2;
  const endAngle = startAngle + 2 * Math.PI * pct;
  const segments = Math.max(4, Math.floor(pct * 60));

  doc.setDrawColor(cr, cg, cb);
  doc.setLineWidth(3.5);

  for (let i = 0; i < segments; i++) {
    const a1 = startAngle + (endAngle - startAngle) * (i / segments);
    const a2 = startAngle + (endAngle - startAngle) * ((i + 1) / segments);
    const x1 = cx + r * Math.cos(a1);
    const y1 = cy + r * Math.sin(a1);
    const x2 = cx + r * Math.cos(a2);
    const y2 = cy + r * Math.sin(a2);
    doc.line(x1, y1, x2, y2);
  }

  // Score text
  doc.setFontSize(18);
  doc.setTextColor(cr, cg, cb);
  doc.text(String(score), cx, cy + 2, { align: "center" });

  // /100 label
  doc.setFontSize(7);
  doc.setTextColor(148, 163, 184);
  doc.text("/ 100", cx, cy + 8, { align: "center" });

  // Level label below
  doc.setFontSize(9);
  doc.setTextColor(cr, cg, cb);
  doc.text(level.toUpperCase(), cx, cy + r + 12, { align: "center" });
}

/* ══════════════════════════════════════════════════════════════════════════
   DRAW SEVERITY PILL — coloured rounded rectangle with text
   ══════════════════════════════════════════════════════════════════════════ */

function drawSeverityPill(doc: jsPDF, x: number, y: number, label: string) {
  const [r, g, b] = severityColor(label);
  const w = doc.getTextWidth(label.toUpperCase()) + 8;
  doc.setFillColor(r, g, b);
  doc.roundedRect(x, y - 4, w, 6, 1.5, 1.5, "F");
  doc.setFontSize(7);
  doc.setTextColor(255, 255, 255);
  doc.text(label.toUpperCase(), x + 4, y, { baseline: "middle" });
}

/* ══════════════════════════════════════════════════════════════════════════
   MAIN PDF GENERATION
   ══════════════════════════════════════════════════════════════════════════ */

export function generatePDFReport(aiReport: AIReport, analysisId: string) {
  const doc = new jsPDF();
  const pageW = doc.internal.pageSize.getWidth();

  /* ── Title Bar ── */
  doc.setFillColor(15, 23, 42); // slate-900
  doc.rect(0, 0, pageW, 32, "F");

  doc.setFontSize(18);
  doc.setTextColor(255, 255, 255);
  doc.text("IsoLens", 14, 15);

  doc.setFontSize(10);
  doc.setTextColor(148, 163, 184);
  doc.text("AI Threat Analysis Report", 14, 23);

  doc.setFontSize(8);
  doc.setTextColor(148, 163, 184);
  doc.text(`ID: ${analysisId}`, pageW - 14, 15, { align: "right" });
  doc.text(
    `Generated: ${aiReport.completed_at ? new Date(aiReport.completed_at).toLocaleString() : new Date().toLocaleString()}`,
    pageW - 14,
    23,
    { align: "right" }
  );

  /* ── Risk Gauge + Classification Side-by-Side ── */
  const gaugeY = 60;

  // Risk gauge on the left
  drawRiskGauge(doc, 42, gaugeY, aiReport.risk_score, aiReport.threat_level);

  // Classification box on the right
  const classX = 90;
  const [cr, cg, cb] = riskColor(aiReport.risk_score);
  const [br, bg, bb] = riskBgColor(aiReport.risk_score);

  doc.setFillColor(br, bg, bb);
  doc.roundedRect(classX, gaugeY - 28, pageW - classX - 14, 56, 3, 3, "F");
  doc.setDrawColor(cr, cg, cb);
  doc.setLineWidth(0.5);
  doc.roundedRect(classX, gaugeY - 28, pageW - classX - 14, 56, 3, 3, "S");

  doc.setFontSize(8);
  doc.setTextColor(100, 116, 139);
  doc.text("CLASSIFICATION", classX + 8, gaugeY - 18);

  const classItems = [
    ["Malware Type", aiReport.classification.malware_type],
    ["Family", aiReport.classification.malware_family],
    ["Platform", aiReport.classification.platform],
    ["Confidence", `${aiReport.classification.confidence}%`],
  ];

  let classItemY = gaugeY - 10;
  classItems.forEach(([label, rawValue], i) => {
    doc.setFontSize(8);
    doc.setTextColor(100, 116, 139);
    doc.text(label, classX + 8, classItemY);

    let value = String(rawValue || "").toLowerCase() === "unknown" 
      ? "GENERIC" 
      : String(rawValue || "").toUpperCase();
      
    // Truncate if it's too long so it doesn't overflow the box
    if (i !== 3 && value.length > 22) {
      value = value.substring(0, 20) + "...";
    }

    doc.setFontSize(10);
    doc.setTextColor(15, 23, 42);
    doc.text(value, classX + 55, classItemY);
    classItemY += 12;
  });

  // Confidence bar
  const barX = classX + 76;
  const barY = classItemY - 16;
  const barW = 24; // smaller width so it doesn't break out of the box (ends at 210 max)
  doc.setFillColor(226, 232, 240);
  doc.roundedRect(barX, barY - 3, barW, 4, 1, 1, "F");
  doc.setFillColor(cr, cg, cb);
  doc.roundedRect(barX, barY - 3, Math.max(0.5, barW * (aiReport.classification.confidence / 100)), 4, 1, 1, "F");

  let y = gaugeY + 42;

  /* ── Section helper ── */
  function sectionTitle(title: string, yPos: number): number {
    if (yPos > doc.internal.pageSize.getHeight() - 30) {
      doc.addPage();
      yPos = 20;
    }
    doc.setFillColor(248, 250, 252);
    doc.rect(14, yPos - 5, pageW - 28, 10, "F");
    doc.setDrawColor(226, 232, 240);
    doc.setLineWidth(0.3);
    doc.line(14, yPos + 5, pageW - 14, yPos + 5);

    doc.setFontSize(11);
    doc.setTextColor(30, 41, 59);
    doc.text(title, 16, yPos + 2);

    return yPos + 14;
  }

  /* ── Executive Summary ── */
  if (aiReport.executive_summary) {
    y = sectionTitle("Executive Summary", y);
    doc.setFontSize(9);
    doc.setTextColor(51, 65, 85);
    const lines = doc.splitTextToSize(aiReport.executive_summary, pageW - 32);
    doc.text(lines, 16, y);
    y += lines.length * 4.2 + 10;
  }

  /* ── Key Findings ── */
  if (aiReport.key_findings && aiReport.key_findings.length > 0) {
    y = sectionTitle(`Key Findings (${aiReport.key_findings.length})`, y);

    autoTable(doc, {
      startY: y,
      head: [["SEVERITY", "DESCRIPTION", "SOURCE"]],
      body: aiReport.key_findings.map((f) => [
        f.severity.toUpperCase(),
        f.description,
        f.source || "—",
      ]),
      theme: "grid",
      headStyles: {
        fillColor: [241, 245, 249],
        textColor: [71, 85, 105],
        fontStyle: "bold",
        fontSize: 8,
      },
      bodyStyles: { fontSize: 8, textColor: [30, 41, 59] },
      columnStyles: {
        0: {
          cellWidth: 22,
          fontStyle: "bold",
          halign: "center",
        },
        1: { cellWidth: 120 },
        2: { cellWidth: 38, textColor: [100, 116, 139] },
      },
      didParseCell: function (data) {
        if (data.section === "body" && data.column.index === 0) {
          const sev = String(data.cell.raw).toLowerCase();
          if (sev === "critical" || sev === "high") {
            data.cell.styles.textColor = [220, 38, 38];
            data.cell.styles.fillColor = [254, 242, 242];
          } else if (sev === "medium") {
            data.cell.styles.textColor = [180, 83, 9];
            data.cell.styles.fillColor = [255, 251, 235];
          } else if (sev === "low") {
            data.cell.styles.textColor = [37, 99, 235];
            data.cell.styles.fillColor = [239, 246, 255];
          }
        }
      },
    });
    y = (doc as any).lastAutoTable.finalY + 12;
  }

  /* ── IOCs ── */
  if (aiReport.iocs && aiReport.iocs.length > 0) {
    y = sectionTitle(`Indicators of Compromise (${aiReport.iocs.length})`, y);

    autoTable(doc, {
      startY: y,
      head: [["TYPE", "SEVERITY", "INDICATOR VALUE"]],
      body: aiReport.iocs.map((ioc) => [
        ioc.type.toUpperCase(),
        ioc.severity.toUpperCase(),
        ioc.value,
      ]),
      theme: "grid",
      headStyles: {
        fillColor: [241, 245, 249],
        textColor: [71, 85, 105],
        fontStyle: "bold",
        fontSize: 8,
      },
      bodyStyles: { fontSize: 8, textColor: [30, 41, 59] },
      columnStyles: {
        0: { cellWidth: 28, fontStyle: "bold" },
        1: { cellWidth: 22, halign: "center" },
        2: { cellWidth: 130, font: "courier" },
      },
      didParseCell: function (data) {
        if (data.section === "body" && data.column.index === 1) {
          const sev = String(data.cell.raw).toLowerCase();
          if (sev === "critical" || sev === "high") {
            data.cell.styles.textColor = [220, 38, 38];
          } else if (sev === "medium") {
            data.cell.styles.textColor = [180, 83, 9];
          }
        }
      },
    });
    y = (doc as any).lastAutoTable.finalY + 12;
  }

  /* ── Recommendations ── */
  if (aiReport.recommendations && aiReport.recommendations.length > 0) {
    y = sectionTitle(`Recommendations (${aiReport.recommendations.length})`, y);

    autoTable(doc, {
      startY: y,
      head: [["PRIORITY", "ACTION"]],
      body: aiReport.recommendations.map((r) => [
        r.priority.toUpperCase(),
        r.action,
      ]),
      theme: "grid",
      headStyles: {
        fillColor: [241, 245, 249],
        textColor: [71, 85, 105],
        fontStyle: "bold",
        fontSize: 8,
      },
      bodyStyles: { fontSize: 8, textColor: [30, 41, 59] },
      columnStyles: {
        0: { cellWidth: 25, fontStyle: "bold", halign: "center" },
        1: { cellWidth: 155 },
      },
      didParseCell: function (data) {
        if (data.section === "body" && data.column.index === 0) {
          const pri = String(data.cell.raw).toLowerCase();
          if (pri === "critical" || pri === "high") {
            data.cell.styles.textColor = [220, 38, 38];
            data.cell.styles.fillColor = [254, 242, 242];
          } else if (pri === "medium") {
            data.cell.styles.textColor = [180, 83, 9];
            data.cell.styles.fillColor = [255, 251, 235];
          }
        }
      },
    });
    y = (doc as any).lastAutoTable.finalY + 12;
  }

  /* ── Per-Tool Agent Results ── */
  if (aiReport.tool_results && aiReport.tool_results.length > 0) {
    y = sectionTitle(`Agent Analysis Results (${aiReport.tool_results.length})`, y);

    aiReport.tool_results.forEach((tool) => {
      if (y > doc.internal.pageSize.getHeight() - 40) {
        doc.addPage();
        y = 20;
      }

      // Tool header
      doc.setFontSize(9);
      doc.setTextColor(15, 23, 42);
      doc.text(`▸ ${tool.tool}`, 16, y);

      // Verdict pill
      const verdict = (tool.verdict || "unknown").toUpperCase();
      drawSeverityPill(doc, 70, y, verdict);

      y += 8;

      // Summary text
      if (tool.summary) {
        doc.setFontSize(8);
        doc.setTextColor(71, 85, 105);
        const lines = doc.splitTextToSize(tool.summary, pageW - 36);
        doc.text(lines, 18, y);
        y += lines.length * 3.8 + 6;
      }
    });
  }

  /* ── Footer on every page ── */
  const totalPages = doc.getNumberOfPages();
  for (let i = 1; i <= totalPages; i++) {
    doc.setPage(i);
    const pageH = doc.internal.pageSize.getHeight();
    doc.setFillColor(248, 250, 252);
    doc.rect(0, pageH - 12, pageW, 12, "F");
    doc.setFontSize(7);
    doc.setTextColor(148, 163, 184);
    doc.text("IsoLens AI Threat Analysis — Confidential", 14, pageH - 5);
    doc.text(`Page ${i} of ${totalPages}`, pageW - 14, pageH - 5, { align: "right" });
  }

  doc.save(`IsoLens_AI_Report_${analysisId}.pdf`);
}
