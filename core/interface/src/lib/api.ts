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

async function parseApiResponse<T>(res: Response): Promise<ApiResponse<T>> {
  const contentType = res.headers.get("content-type") || "";
  if (!contentType.includes("application/json")) {
    const text = await res.text();
    return {
      status: "error",
      data: null,
      error: {
        message: `Gateway returned HTTP ${res.status}: ${res.statusText || "Unexpected response"}`,
        details: text.slice(0, 500),
      },
    };
  }

  try {
    const json = (await res.json()) as ApiResponse<T>;
    return json;
  } catch (err) {
    return {
      status: "error",
      data: null,
      error: {
        message: "Failed to parse JSON response from gateway",
        details: err instanceof Error ? err.message : String(err),
      },
    };
  }
}

async function get<T>(url: string): Promise<ApiResponse<T>> {
  const res = await fetch(url);
  return parseApiResponse<T>(res);
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
  return parseApiResponse<T>(res);
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

export async function resetVM(vm: string) {
  return post<{ success: boolean; message: string }>("/api/vms/reset", {
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
  return parseApiResponse<AnalysisResult>(res);
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
  return parseApiResponse<{ deleted: number; message: string }>(res);
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
  dns_queries?: (string | {
    domain?: string;
    query?: string;
    query_type?: string;
    resolved_ips?: string[];
    process_name?: string;
    pid?: string | number;
    timestamp?: string;
    is_noise?: boolean;
  })[];
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

export interface YaraMatch {
  rule: string;
  category: string;
  severity: "critical" | "high" | "medium" | "low" | string;
  mitre_technique?: string;
  description?: string;
  tags?: string[];
  matched_strings?: string[];
}

export interface YaraMitre {
  id: string;
  name: string;
  description?: string;
}

export interface YaraData {
  status: string;
  scanned_file?: string;
  engine: string;
  matched_rules_count: number;
  threat_level: "critical" | "high" | "medium" | "low" | "clean" | string;
  tags: string[];
  matches: YaraMatch[];
  mitre_attack: YaraMitre[];
}

export interface LstmData {
  verdict: "MALICIOUS" | "BENIGN" | string;
  confidence: number;
  p_malware: number;
  p_benign: number;
  sequence_length: number;
  recognized_apis_count: number;
  recognized_ratio: number;
  windows_evaluated: number;
  peak_window_range?: [number, number];
  sample_process?: string;
  unique_apis?: string[];
  source_type?: string;
  note?: string;
  inferred_from_behavior?: boolean;
}

export interface FlaggedWindow {
  filename: string;
  filepath?: string;
  original_size?: [number, number];
  window_bbox?: [number, number, number, number];
  ocr_text?: string;
  ocr_text_length?: number;
  verdict: string;
  is_malicious: boolean;
  threat_type: string;
  confidence: number;
  matched_keywords: string[];
  engine?: string;
}

export interface GuiData {
  sample?: string;
  total_screenshots: number;
  has_malicious_gui: boolean;
  highest_threat_type?: string;
  max_confidence?: number;
  flagged_count: number;
  flagged_windows: FlaggedWindow[];
}

export interface RiskBreakdownLayer {
  layer: string;
  points: number;
  confidence: number;
  summary: string;
  details?: unknown;
}

export interface RiskData {
  risk_score: number;
  threat_level: "Critical" | "High" | "Medium" | "Low" | "Benign" | string;
  max_score: number;
  raw_sum: number;
  total_layers_flagged: number;
  breakdown: RiskBreakdownLayer[];
  mitre_attack: { id: string; name: string; tactic?: string; description?: string }[];
}

export interface BehaviorSummary {
  sample_process?: string;
  summary: {
    total_files_created: number;
    total_files_written: number;
    total_sensitive_reads: number;
    total_general_reads: number;
    total_files_deleted: number;
    total_registry_modified: number;
    total_registry_created: number;
    total_registry_deleted: number;
    total_persistence_keys: number;
    total_defense_tampering_keys: number;
  };
  files?: {
    created?: string[];
    written?: string[];
    sensitive_reads?: string[];
    general_reads?: string[];
    deleted?: string[];
  };
  registry?: {
    persistence_keys?: string[];
    defense_tampering_keys?: string[];
    sensitive_queries?: string[];
  };
}

export interface NetworkDBFinding {
  severity: string;
  indicator: string;
  description: string;
}

export interface NetworkDBData {
  tool: string;
  verdict: "malicious" | "suspicious" | "benign" | "inconclusive" | string;
  confidence: number;
  summary: string;
  findings: NetworkDBFinding[];
  iocs: { type: string; value: string }[];
  details?: {
    matched_ips_count: number;
    matched_domains_count: number;
    matched_urls_count: number;
    malware_families: string[];
    threat_types: string[];
    tags: string[];
    total_domains_observed?: number;
    total_ips_observed?: number;
    total_urls_observed?: number;
  };
}

export interface ReportData {
  manifest: AnalysisResult | null;
  metadata: { collectors: CollectorMeta[]; files: string[] } | null;
  yara: YaraData | null;
  lstm: LstmData | null;
  behavior: BehaviorSummary | null;
  gui: GuiData | null;
  risk: RiskData | null;
  network_db: NetworkDBData | null;
  ai_report: AIReport | null;
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

export async function getYaraData(analysisId: string) {
  return get<YaraData>(
    `/api/analysis/report/${encodeURIComponent(analysisId)}/yara`,
  );
}

export async function getLstmData(analysisId: string) {
  return get<LstmData>(
    `/api/analysis/report/${encodeURIComponent(analysisId)}/lstm`,
  );
}

export async function getBehaviorData(analysisId: string) {
  return get<BehaviorSummary>(
    `/api/analysis/report/${encodeURIComponent(analysisId)}/behavior`,
  );
}

export async function getGuiData(analysisId: string) {
  return get<GuiData>(
    `/api/analysis/report/${encodeURIComponent(analysisId)}/gui`,
  );
}

export async function getRiskData(analysisId: string) {
  return get<RiskData>(
    `/api/analysis/report/${encodeURIComponent(analysisId)}/risk`,
  );
}

export async function getNetworkDBData(analysisId: string) {
  return get<NetworkDBData>(
    `/api/analysis/report/${encodeURIComponent(analysisId)}/network-db`,
  );
}

// ─── AI Analysis ──────────────────────────────────────────────────────────

export interface AIToolFinding {
  severity: string;
  indicator: string;
  description: string;
}

export interface AIToolIOC {
  type: string;
  value: string;
}

export interface AIToolResult {
  tool: string;
  agent_name: string;
  verdict: string;
  confidence: number;
  findings_count: number;
  iocs_count: number;
  summary: string;
  findings: AIToolFinding[];
  iocs: AIToolIOC[];
  raw_response: string;
  error: string | null;
}

export interface AIClassification {
  malware_type: string;
  malware_family: string;
  platform: string;
  confidence: number;
}

export interface AIFinding {
  source: string;
  severity: string;
  description: string;
}

export interface AIIOC {
  type: string;
  severity: string;
  value: string;
}

export interface AIMitreTechnique {
  id: string;
  name: string;
  tactic: string;
  description: string;
}

export interface AIRecommendation {
  priority: string;
  action: string;
}

export interface AIReport {
  analysis_id: string;
  model: string;
  started_at: string | null;
  completed_at: string | null;
  status: "pending" | "running" | "complete" | "failed";
  error: string | null;
  risk_score: number;
  threat_level: string;
  classification: AIClassification;
  executive_summary: string;
  detailed_analysis: string;
  key_findings: AIFinding[];
  iocs: AIIOC[];
  mitre_attack: AIMitreTechnique[];
  recommendations: AIRecommendation[];
  tool_results: AIToolResult[];
  raw_summary: string;
}

export async function runAIAnalysis(
  analysisId: string,
): Promise<ApiResponse<AIReport>> {
  // Provider fallback can take several minutes. Let the request finish instead
  // of aborting it on a fixed client-side deadline.
  const res = await fetch(
    `/api/analysis/report/${encodeURIComponent(analysisId)}/ai-analyze`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
    },
  );
  return parseApiResponse<AIReport>(res);
}

export async function getAIReport(analysisId: string) {
  return get<AIReport>(
    `/api/analysis/report/${encodeURIComponent(analysisId)}/ai-report`,
  );
}

export interface AIProgress {
  status: "pending" | "running" | "complete" | "failed";
  current_action: string;
  completed_agents: number;
  total_agents: number;
}

export async function getAIProgress(analysisId: string) {
  return get<AIProgress>(
    `/api/analysis/report/${encodeURIComponent(analysisId)}/ai-progress`,
  );
}
