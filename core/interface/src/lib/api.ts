/**
 * IsoLens API client — wraps all gateway endpoints.
 *
 * The Next.js rewrite in next.config.ts proxies /api/* → http://localhost:6969/api/*
 * so we can use relative URLs.
 */

// ─── Types ────────────────────────────────────────────────────────────────

export interface ApiResponse<T = Record<string, unknown>> {
  status: "ok" | "error";
  data: T | null;
  error: { message: string; details?: string } | null;
}

export interface VMEntry {
  name: string;
  uuid: string;
}

export interface VMInfo {
  name?: string;
  ostype?: string;
  memory?: string;
  VMState?: string;
  [key: string]: unknown;
}

export interface AnalysisResult {
  analysis_id: string;
  sample_name: string;
  status: "pending" | "running" | "complete" | "failed";
  started_at: string | null;
  completed_at: string | null;
  timeout: number;
  error: string | null;
  report_dir: string | null;
  sysmon_events: number;
  files_collected: string[];
  agent_package: string | null;
}

export interface AgentStatus {
  state: string;
  version?: string;
  hostname?: string;
  platform?: string;
  workdir?: string;
  share_dir?: string;
  pid?: number;
  uptime_seconds?: number;
  current_sample?: string;
}

export interface CollectorInfo {
  name: string;
  available: boolean;
  description?: string;
}

// ─── Helpers ──────────────────────────────────────────────────────────────

async function get<T>(url: string): Promise<ApiResponse<T>> {
  const res = await fetch(url);
  return res.json();
}

async function post<T>(
  url: string,
  body?: Record<string, unknown>
): Promise<ApiResponse<T>> {
  const res = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: body ? JSON.stringify(body) : undefined,
  });
  return res.json();
}

// ─── System ───────────────────────────────────────────────────────────────

export async function ping() {
  return get<{ message: string }>("/api/ping");
}

export async function getVersion() {
  return get<{ version: string }>("/api/version");
}

// ─── VMs ──────────────────────────────────────────────────────────────────

export async function listVMs() {
  return get<{ vms: VMEntry[] }>("/api/vms");
}

export async function listRunningVMs() {
  return get<{ vms: VMEntry[] }>("/api/vms/running");
}

export async function getVMIP(vm: string) {
  return get<{ vm: string; interfaces: Record<string, string>[] }>(
    `/api/vms/ip?vm=${encodeURIComponent(vm)}`
  );
}

export async function getVMInfo(vm: string, machinereadable = true) {
  return post<{ info: VMInfo }>("/api/vms/info", {
    vm,
    machinereadable,
    dry_run: false,
    raise_on_error: true,
  });
}

export async function startVM(vm: string, headless = false) {
  return post<{ success: boolean; message: string }>("/api/vms/start", {
    vm,
    headless,
    dry_run: false,
    raise_on_error: true,
  });
}

export async function poweroffVM(vm: string) {
  return post<{ success: boolean; message: string }>("/api/vms/poweroff", {
    vm,
    dry_run: false,
    raise_on_error: true,
  });
}

export async function pauseVM(vm: string) {
  return post<{ success: boolean; message: string }>("/api/vms/pause", {
    vm,
    dry_run: false,
    raise_on_error: true,
  });
}

export async function resumeVM(vm: string) {
  return post<{ success: boolean; message: string }>("/api/vms/resume", {
    vm,
    dry_run: false,
    raise_on_error: true,
  });
}

export async function restoreSnapshot(vm: string, name: string) {
  return post<{ success: boolean; message: string }>(
    "/api/vms/snapshot/restore",
    { vm, name, dry_run: false, raise_on_error: true }
  );
}

export async function restoreCurrentSnapshot(vm: string) {
  return post<{ success: boolean; message: string }>(
    "/api/vms/snapshot/restore-current",
    { vm, dry_run: false, raise_on_error: true }
  );
}

// ─── Analysis ─────────────────────────────────────────────────────────────

export async function submitAnalysis(
  file: File,
  timeout = 60,
  screenshotInterval = 5
): Promise<ApiResponse<AnalysisResult>> {
  const formData = new FormData();
  formData.append("file", file);
  const res = await fetch(
    `/api/analysis/submit?timeout=${timeout}&screenshot_interval=${screenshotInterval}`,
    { method: "POST", body: formData }
  );
  return res.json();
}

export async function getAnalysisStatus() {
  return get<AnalysisResult | { message: string }>("/api/analysis/status");
}

export async function checkVM() {
  return post<Record<string, unknown>>("/api/analysis/check-vm");
}

export async function cleanupAgent() {
  return post<Record<string, unknown>>("/api/analysis/cleanup");
}

// ─── Agent proxy ──────────────────────────────────────────────────────────

export async function getAgentStatus() {
  return get<AgentStatus>("/api/analysis/agent/status");
}

export async function getAgentCollectors() {
  return get<{ collectors: CollectorInfo[] }>("/api/analysis/agent/collectors");
}

export async function getAgentArtifacts() {
  return get<{ artifacts: string[] }>("/api/analysis/agent/artifacts");
}

// ─── Reports / Screenshots ───────────────────────────────────────────────

export async function listScreenshots(analysisId: string) {
  return get<{ screenshots: string[]; analysis_id: string }>(
    `/api/analysis/report/${encodeURIComponent(analysisId)}/screenshots`
  );
}

export function screenshotURL(analysisId: string, filename: string): string {
  return `/api/analysis/report/${encodeURIComponent(analysisId)}/file/screenshots/${encodeURIComponent(filename)}`;
}

export async function listReports() {
  return get<{ reports: AnalysisResult[] }>("/api/analysis/reports/list");
}
