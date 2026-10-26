import type { AnalysisResult } from "./api";

const LOCAL_REPORTS_KEY = "isolens.local-benign-reports.v1";
let volatileLocalReports: LocalBenignReport[] = [];

export type LocalBenignReport = AnalysisResult & {
  local_only: true;
  risk_score: 0;
  threat_level: "Benign";
};

export function readLocalBenignReports(): LocalBenignReport[] {
  if (typeof window === "undefined") return [];

  try {
    const value: unknown = JSON.parse(window.localStorage.getItem(LOCAL_REPORTS_KEY) || "[]");
    if (!Array.isArray(value)) return [];
    const persisted = value.filter((item): item is LocalBenignReport =>
      Boolean(
        item
        && typeof item === "object"
        && (item as LocalBenignReport).local_only === true
        && typeof (item as LocalBenignReport).analysis_id === "string"
        && (item as LocalBenignReport).analysis_id.startsWith("local-")
        && (item as LocalBenignReport).risk_score === 0
        && (item as LocalBenignReport).threat_level === "Benign",
      ),
    );
    return [
      ...volatileLocalReports,
      ...persisted.filter((item) =>
        !volatileLocalReports.some((localReport) => localReport.analysis_id === item.analysis_id),
      ),
    ];
  } catch {
    return [...volatileLocalReports];
  }
}

export function saveLocalBenignReport(report: LocalBenignReport): void {
  if (typeof window === "undefined") return;
  volatileLocalReports = [
    report,
    ...volatileLocalReports.filter((item) => item.analysis_id !== report.analysis_id),
  ];
  try {
    const reports = readLocalBenignReports().filter((item) => item.analysis_id !== report.analysis_id);
    window.localStorage.setItem(LOCAL_REPORTS_KEY, JSON.stringify([report, ...reports]));
  } catch {
    // Storage may be unavailable in private browsing or under a strict policy.
  }
}

export function clearLocalBenignReports(): void {
  volatileLocalReports = [];
  if (typeof window !== "undefined") {
    try {
      window.localStorage.removeItem(LOCAL_REPORTS_KEY);
    } catch {
      // Ignore storage access failures; volatile entries have still been cleared.
    }
  }
}

export function isLocalBenignReport(report: AnalysisResult | null): report is LocalBenignReport {
  return Boolean(report && report.analysis_id.startsWith("local-"));
}
