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
  uuid?: string;
  os?: string;
  state?: string;
  state_changed?: string;
  memory_mb?: number;
  cpus?: number;
  vram_mb?: number;
  chipset?: string;
  firmware?: string;
  graphics_controller?: string;
  accelerate_3d?: boolean;
  vrde?: boolean;
  vrde_port?: number;
  vrde_auth_type?: string;
  snapshot?: string;
  snapshot_uuid?: string;
  network?: {
    slot: number;
    type: string;
    mac: string;
    cable: boolean;
    attachment: string;
  }[];
  shared_folders?: { name: string; path: string }[];
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
  body?: Record<string, unknown>,
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
    `/api/vms/ip?vm=${encodeURIComponent(vm)}`,
  );
}

/**
 * Returns the URL for a live VM screenshot PNG.
 * Append a timestamp query param to bust browser cache.
 */
export function vmScreenURL(vm = "WindowsSandbox"): string {
  return `/api/vms/screen?vm=${encodeURIComponent(vm)}&t=${Date.now()}`;
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
    { vm, name, dry_run: false, raise_on_error: true },
  );
}

export async function restoreCurrentSnapshot(vm: string) {
  return post<{ success: boolean; message: string }>(
    "/api/vms/snapshot/restore-current",
    { vm, dry_run: false, raise_on_error: true },
  );
}

// ─── Analysis ─────────────────────────────────────────────────────────────

export async function submitAnalysis(
  file: File,
  timeout = 60,
  screenshotInterval = 5,
): Promise<ApiResponse<AnalysisResult>> {
  const formData = new FormData();
  formData.append("file", file);
  const res = await fetch(
    `/api/analysis/submit?timeout=${timeout}&screenshot_interval=${screenshotInterval}`,
    { method: "POST", body: formData },
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
    `/api/analysis/report/${encodeURIComponent(analysisId)}/screenshots`,
  );
}

export function screenshotURL(analysisId: string, filename: string): string {
  return `/api/analysis/report/${encodeURIComponent(analysisId)}/file/screenshots/${encodeURIComponent(filename)}`;
}

export async function listReports() {
  return get<{ reports: AnalysisResult[] }>("/api/analysis/reports/list");
}

export async function clearAllReports() {
  const res = await fetch("/api/analysis/reports/clear", { method: "DELETE" });
  return res.json() as Promise<
    ApiResponse<{ deleted: number; message: string }>
  >;
}

// ─── Report Data (detailed collector output) ─────────────────────────────

export interface SysmonProcess {
  image: string;
  pid: string;
  parent: string;
  cmd: string;
  user: string;
  time: string;
}

export interface SysmonNetConn {
  image: string;
  proto: string;
  src: string;
  dst: string;
  dst_host: string;
}

export interface SysmonRegEvent {
  type: string;
  key: string;
  details: string;
}

export interface SysmonData {
  total_events: number;
  sample_events: number;
  sample_process: string;
  sample_pids: string[];
  processes_created: SysmonProcess[];
  network_connections: SysmonNetConn[];
  dns_queries: string[];
  files_created: string[];
  registry_events: SysmonRegEvent[];
  dlls_loaded: string[];
}

export interface ProcmonData {
  sample_process: string;
  total_rows: number;
  sample_events: number;
  file_activity: {
    notable: Record<string, string[]>;
    all_ops: Record<string, number>;
  };
  registry_activity: {
    notable: Record<string, string[]>;
    all_ops: Record<string, number>;
  };
  network_activity: { op: string; path: string; result: string }[];
  process_activity: { op: string; path: string; detail: string }[];
}

export interface NetworkData {
  tcp_conversations?: string;
  dns_queries?: string[];
  http_requests?: { host: string; uri: string; method: string }[];
  tcp_error?: string;
  dns_error?: string;
  http_error?: string;
}

export interface TcpvconRow {
  [key: string]: string;
}

export interface CollectorMeta {
  collector: string;
  status: string;
  files: string[];
  error?: string;
}

export interface ReportData {
  manifest: AnalysisResult | null;
  metadata: { collectors: CollectorMeta[]; files: string[] } | null;
  sysmon: SysmonData | null;
  procmon: ProcmonData | null;
  network: NetworkData | null;
  handle: string | null;
  tcpvcon: TcpvconRow[] | null;
  screenshots: string[];
}

export async function getReportData(analysisId: string) {
  return get<ReportData>(
    `/api/analysis/report/${encodeURIComponent(analysisId)}/data`,
  );
}
