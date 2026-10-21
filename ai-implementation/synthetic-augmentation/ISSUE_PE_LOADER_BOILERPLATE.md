# ⚠️ Technical Report: Windows PE Loader Boilerplate Issue in Procmon-to-LSTM Bridging

**Issue ID**: `ISSUE-2026-10-17-01`  
**Component**: `core/modules/procmon_lstm_bridge.py` & `core/modules/predict_lstm.py`  
**Status**: Root Cause Diagnosed & Documented; Solution Implementation in Progress  
**Author**: IsoLens Development Team  
**Date**: October 17, 2026  

---

## 1. Executive Summary

During standalone validation of the trained IsoLens LSTM classifier using Process Monitor (`procmon.csv`) logs captured from a live Windows 10 sandbox VM, both a malicious simulation executable (`malware_sim.exe`) and a legitimate simulation executable (`legit_sim.exe`) initially received identical classification results:

- **`legit_sim.exe`**: `BENIGN (99.98% confidence)`, $P(\text{Malware}) = 0.0002$
- **`malware_sim.exe`**: `BENIGN (99.98% confidence)`, $P(\text{Malware}) = 0.0002$

Investigation revealed that **the first 100 API calls extracted from both executables were 100% identical**. 

Because `extract_sequence_from_procmon_csv` naively sliced the first 100 mapped operations starting from the very first event in the process, it only recorded standard **Windows PE Loader and C Runtime (CRT) initialization**. The actual code inside `main()`—including shellcode allocation, thread injection, registry persistence, payload dropping, and command execution—occurred between events **#128 and #165**, which were completely omitted by the naive truncation.

When the full execution trace was evaluated, $P(\text{Malware})$ for `malware_sim.exe` jumped to **$45.66\%$** ($1,500\times$ higher than `legit_sim.exe` at $0.03\%$).

---

## 2. Root Cause Analysis

### 2.1 The Architectural Discrepancy: Cuckoo Sandbox vs. Process Monitor

| Dimension | Cuckoo / Catak Training Data | IsoLens Procmon Telemetry |
|---|---|---|
| **Monitoring Mechanism** | User-mode API hooking (`cuckoomon.dll`) | Kernel-mode mini-filter driver (`PROCMON24.SYS`) |
| **Observation Point** | Binary Entry Point (`main` / `WinMain`) | Process initialization (`NtCreateUserProcess`) |
| **Loader Boilerplate** | Largely omitted or abstracted | Completely logged (100–180 system events) |
| **Scope** | Monitored processes only | Every I/O request by Windows subsystem |

### 2.2 The Windows PE Loader Lifecycle

Before Windows transfers execution to a binary's entry point, the operating system executes extensive boilerplate:
1. **Console Allocation**: Spawning or attaching to `conhost.exe`.
2. **Shim Database Lookup**: Querying `C:\Windows\apppatch\sysmain.sdb`.
3. **Core DLL Mapping**: Mapping `ntdll.dll`, `kernel32.dll`, `KernelBase.dll`, `msvcrt.dll`, `rpcrt4.dll`, `sechost.dll`, `advapi32.dll`.
4. **Localization & NLS**: Reading `C:\Windows\System32\SortDefault.nls` and registry entries in `HKLM\Software\Microsoft\Windows NT\CurrentVersion\GRE_Initialize`.

### 2.3 Empirical Verification: Identical Initial Sequences

Extracting the first 30 calls from both CSV logs produced identical sequences:

```python
[
  'CreateProcessInternalW', 'CreateThread', 'LdrLoadDll', 'LdrLoadDll', 'NtCreateFile',
  'RegOpenKeyExW', 'RegOpenKeyExW', 'RegQueryValueExW', 'RegCloseKey', 'RegOpenKeyExW',
  'RegOpenKeyExW', 'RegOpenKeyExW', 'RegOpenKeyExW', 'RegQueryValueExW', 'RegCloseKey',
  'NtCreateFile', 'LdrLoadDll', 'LdrLoadDll', 'NtCreateFile', 'CreateFileMappingW',
  'CreateFileMappingW', 'RegOpenKeyExW', 'RegOpenKeyExW', 'RegQueryValueExW', 'RegCloseKey',
  'RegOpenKeyExW', 'RegOpenKeyExW', 'NtCreateFile', 'CloseHandle', 'NtCreateFile'
]
```

Because both executables were compiled with MinGW x86_64, their CRT startup routines are identical. The LSTM correctly recognized this sequence as standard, benign Windows OS behavior ($99.98\%$ Benign).

---

## 3. Quantitative Evidence Across Execution Windows

Evaluating sliding windows and the full sequence reveals the true behavioral difference:

| Sequence / Window Evaluated | `legit_sim.exe` $P(\text{Malware})$ | `malware_sim.exe` $P(\text{Malware})$ | Verdict Shift |
|---|---|---|---|
| **Window [0:100]** (Loader Startup) | $0.02\%$ | $0.02\%$ | Both Benign (Identical loader) |
| **Window [50:150]** (Late loader / transition) | $0.03\%$ | $0.03\%$ | Both Benign |
| **Window [100:200]** (`main()` execution) | $0.04\%$ | **$22.64\%$** | $566\times$ increase in risk |
| **Window [125:221]** (Malicious payload & Run key) | $0.18\%$ | **$20.97\%$** | Solid malware suspicion |
| **Full Process Sequence** (all 221 calls) | **$0.03\%$** | **$45.66\%$** | **$1,500\times$ risk divergence** |

### Actions Detected in `malware_sim.exe` Active Window:
- `CreateThread` (simulated shellcode execution)
- `RegSetValueExW` (`HKCU\Software\Microsoft\Windows\CurrentVersion\Run\IsoLensPersistenceSim`)
- `NtCreateFile` + `NtWriteFile` (`C:\IsoLens\samples\dropped_payload.tmp`)
- `CreateProcessInternalW` (`cmd.exe /c whoami`)

In contrast, `legit_sim.exe` contains **0 file writes**, **0 registry writes**, and **0 child process executions**.

---

## 4. Engineering Solutions

To resolve this issue and enable accurate end-to-end sandbox inference, three complementary enhancements are defined:

### 1. Intelligent PE Loader Noise Filtering
Filter out read/query operations directed at standard Windows OS system files during initial startup:
- Ignore `CreateFile` / `ReadFile` on `*.nls`, `*.sdb`, and system DLLs (`kernel32.dll`, `msvcrt.dll`, etc.).
- Retain all state-changing operations (`WriteFile`, `SetDisposition`, `RegSetValue`, `Process Create`, `Thread Create`) regardless of target path.

### 2. Multi-Window / Sliding-Window Inference
Instead of evaluating only a single static slice from index 0:
- Slide a window of length $W=100$ with stride $S=25$ across the entire extracted API sequence.
- Compute the maximum malware probability across all windows:
  $$\text{Risk}_{\text{sample}} = \max_{w \in \text{Windows}} P(\text{Malware} \mid w)$$
- Report the peak risk window along with the triggering API subsequence.

### 3. State-Changing Operation Prioritization
When generating a sequence from `procmon_summary.json` or raw CSV:
- Ensure notable operations (registry modifications, dropped files, child processes, remote threads) are prioritized in the chronological sequence, matching how the Cuckoo dynamic tracer captures malware behavior.

---

## 5. Next Steps
1. Update `core/modules/procmon_lstm_bridge.py` with:
   - `filter_loader_noise: bool = True` option in `extract_sequence_from_procmon_csv`.
   - Sliding-window inference support in `predict_procmon_sliding_window`.
2. Update unit test `tests/TEST_21_procmon_lstm_bridge.py` to assert loader filtering.
3. Update `ai-implementation/synthetic-augmentation/PLAN.md`.
