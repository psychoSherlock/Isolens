# 📊 Example Analysis Summary — IsoLens

> **Note:** This document is a human-readable rendering of real analysis output produced by IsoLens after executing a sample inside the sandbox VM. It serves as a reference for understanding what IsoLens captures and how the data is structured.

---

## 🧪 Analysis Metadata

| Field                 | Value                                                            |
| --------------------- | ---------------------------------------------------------------- |
| **Sample**            | `malware_emulator.exe`                                           |
| **Analysis ID**       | `20260228_160948_5c7a739f`                                       |
| **Timestamp**         | 2026-02-28T16:11:19 UTC                                          |
| **Execution Timeout** | 60 seconds                                                       |
| **Agent Version**     | 1.2.0                                                            |
| **VM**                | Windows 10 Home Build 19045 (AtlasOS), hostname `WindowsSandbox` |

### Collectors Status

| Collector        | Status     | Output                 |
| ---------------- | ---------- | ---------------------- |
| Sysmon           | ✅ ok      | `sysmon_summary.json`  |
| Procmon          | ✅ ok      | `procmon_summary.json` |
| Network (tshark) | ✅ ok      | `network_summary.json` |
| FakeNet          | ✅ ok      | `fakenet_capture.pcap` |
| Handle           | ✅ ok      | `handle_snapshot.txt`  |
| Tcpvcon          | ✅ ok      | `tcpvcon_snapshot.csv` |
| Screenshots      | ⚠️ no_data | —                      |

---

## 🔬 Sysmon — Process & Event Summary

**Total Sysmon events logged:** 106  
**Events related to sample:** 2  
**Sample PIDs:** 2996, 1772

### Process Tree

```
cmd.exe (PID 5596)
 └─ malware_emulator.exe (PID 2996)  [WINDOWSSANDBOX\admin]
     └─ conhost.exe (PID 1772)
```

### Process Creation Events

| Time (UTC)   | Image                                     | PID  | Parent                 | User                   |
| ------------ | ----------------------------------------- | ---- | ---------------------- | ---------------------- |
| 16:09:58.867 | `C:\IsoLens\samples\malware_emulator.exe` | 2996 | `cmd.exe`              | `WINDOWSSANDBOX\admin` |
| 16:09:58.925 | `C:\Windows\System32\conhost.exe`         | 1772 | `malware_emulator.exe` | `WINDOWSSANDBOX\admin` |

### Network / DNS / File / Registry via Sysmon

Sysmon recorded **no network connections, DNS queries, file creations, or registry modifications** for the sample PIDs directly. This is typical for .NET executables that perform these actions through higher-level APIs which Procmon captures more effectively.

---

## 📋 Procmon — Detailed Behavioral Activity

**Total Procmon rows captured:** 317,671  
**Rows attributed to `malware_emulator.exe`:** 3,946

### File Activity (Notable Operations)

#### Files Written

| Path                                                  | Significance                                         |
| ----------------------------------------------------- | ---------------------------------------------------- |
| `%TEMP%\isolens_emulator\emulator_log.txt`            | Execution log created by sample                      |
| `%TEMP%\isolens_emulator\dropped_payload.bin`         | ⚠️ **Dropped payload** — binary written to disk      |
| `%TEMP%\isolens_emulator\update_service.bat`          | ⚠️ **Batch script** — possible persistence mechanism |
| `%TEMP%\isolens_emulator\staging\exfil\chunk_000.enc` | ⚠️ **Encrypted chunk** — staged for exfiltration     |
| `%TEMP%\isolens_emulator\staging\exfil\chunk_001.enc` | ⚠️ Encrypted chunk                                   |
| `%TEMP%\isolens_emulator\staging\exfil\chunk_002.enc` | ⚠️ Encrypted chunk                                   |
| `%TEMP%\isolens_emulator\staging\exfil\chunk_003.enc` | ⚠️ Encrypted chunk                                   |
| `%TEMP%\isolens_emulator\staging\exfil\chunk_004.enc` | ⚠️ Encrypted chunk                                   |

#### Files Created / Accessed (Selected Highlights)

| Path                                                   | Observation                                               |
| ------------------------------------------------------ | --------------------------------------------------------- |
| `C:\IsoLens\samples\malware_emulator.exe`              | Sample loaded from sandbox share                          |
| `C:\IsoLens\samples\malware_emulator.exe.config`       | .NET config probe                                         |
| `C:\IsoLens\samples\malware_emulator.INI`              | INI config probe                                          |
| `C:\Windows\Prefetch\MALWARE_EMULATOR.EXE-517502C9.pf` | Prefetch file created (execution evidence)                |
| `%TEMP%\isolens_emulator\svchost_update.exe`           | ⚠️ **Masqueraded executable** — named to mimic svchost    |
| `%TEMP%\isolens_emulator\.hidden_c2_config.dat`        | ⚠️ **Hidden C2 config** — command & control configuration |

#### Directories Probed

| Path                                                      | Significance                   |
| --------------------------------------------------------- | ------------------------------ |
| `C:\Users\admin\Desktop`                                  | User desktop enumeration       |
| `C:\Users\admin\Documents`                                | User documents enumeration     |
| `C:\Users\admin\AppData\Roaming\Microsoft\Windows\Recent` | Recent files enumeration       |
| `C:\Users\admin\AppData\Roaming\Microsoft\Credentials`    | ⚠️ **Credential store access** |
| `C:\Windows\System32\config`                              | System configuration access    |

#### .NET Runtime Loading

The sample loaded the .NET Framework v4.0.30319 runtime, including:

- `mscoree.dll` → `mscoreei.dll` → `clr.dll` → `clrjit.dll`
- Native images: `mscorlib.ni.dll`, `System.ni.dll`, `System.Core.ni.dll`, `System.Configuration.ni.dll`, `System.Xml.ni.dll`

This confirms the sample is a **.NET Framework 4.x executable**.

### Registry Activity

#### Registry Values Set

| Key                                                                      | Significance                                                  |
| ------------------------------------------------------------------------ | ------------------------------------------------------------- |
| `HKCU\SOFTWARE\Microsoft\Windows\CurrentVersion\Run\IsoLensEmulatorTest` | ⚠️ **Persistence** — Run key created for auto-start           |
| `HKLM\...\Services\bam\...\conhost.exe`                                  | Background Activity Moderator tracking (system-level, normal) |

#### Registry Values Deleted

| Key                                                                      | Significance                                |
| ------------------------------------------------------------------------ | ------------------------------------------- |
| `HKCU\SOFTWARE\Microsoft\Windows\CurrentVersion\Run\IsoLensEmulatorTest` | Cleanup — persistence key removed after use |

#### Registry Keys Created

| Key                                                       | Observation                              |
| --------------------------------------------------------- | ---------------------------------------- |
| `HKLM\System\CurrentControlSet\Services\Tcpip\Parameters` | Network configuration access             |
| `HKLM\Software\Microsoft\Tracing`                         | Tracing infrastructure (used by WinHTTP) |
| `HKCU\...\Internet Settings\Connections`                  | Internet connection settings probed      |

#### Registry Operation Counts

| Operation                | Count |
| ------------------------ | ----- |
| RegOpenKey               | 80    |
| RegQueryValue            | 80    |
| RegQueryKey              | 29    |
| RegSetInfoKey            | 9     |
| RegEnumKey               | 2     |
| RegEnumValue             | 2     |
| RegSetValue              | 2     |
| RegQueryMultipleValueKey | 1     |

### Network Activity (via Procmon)

The sample made **multiple TCP connections** to `192.0.2.123:80` (HTTP):

| Operation          | Endpoint                                  | Result  |
| ------------------ | ----------------------------------------- | ------- |
| TCP Reconnect (×3) | `WindowsSandbox:65283 → 192.0.2.123:http` | SUCCESS |
| TCP Disconnect     | `WindowsSandbox:65283 → 192.0.2.123:http` | SUCCESS |
| TCP Reconnect (×3) | `WindowsSandbox:65284 → 192.0.2.123:http` | SUCCESS |
| TCP Disconnect     | `WindowsSandbox:65284 → 192.0.2.123:http` | SUCCESS |
| TCP Reconnect (×4) | `WindowsSandbox:65285 → 192.0.2.123:http` | SUCCESS |

> **Note:** `192.0.2.123` is a TEST-NET-1 address (RFC 5737), confirming this is emulated C2 traffic. In a real malware scenario, this would be an actual C2 server IP.

### Process Activity

| Operation         | Detail                                                                                                                                                                                                     |
| ----------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Process Start** | `C:\IsoLens\samples\malware_emulator.exe` — Parent PID 5596 (`cmd.exe`)                                                                                                                                    |
| **Child Process** | `conhost.exe` spawned for console I/O                                                                                                                                                                      |
| **DLLs Loaded**   | 49 DLLs loaded including .NET CLR, crypto (`cryptsp.dll`, `rsaenh.dll`, `cryptbase.dll`), networking (`ws2_32.dll`, `mswsock.dll`, `dnsapi.dll`, `IPHLPAPI.DLL`, `winhttp.dll`), and shell (`shell32.dll`) |

### File Operation Summary

| Operation                       | Count |
| ------------------------------- | ----- |
| CreateFile                      | 80    |
| CloseFile                       | 80    |
| RegCloseKey                     | 80    |
| QueryBasicInformationFile       | 46    |
| CreateFileMapping               | 42    |
| QueryDirectory                  | 26    |
| QueryStandardInformationFile    | 16    |
| QueryNetworkOpenInformationFile | 12    |
| ReadFile                        | 10    |
| WriteFile                       | 8     |
| Others                          | 17    |

---

## 🌐 Network — tshark Packet Capture

### TCP Conversations

| Source               | Destination           | Frames | Bytes | Duration |
| -------------------- | --------------------- | ------ | ----- | -------- |
| `192.168.56.1:37248` | `192.168.56.105:9090` | 8      | 592 B | 11.23s   |
| `192.168.56.1:50676` | `192.168.56.105:9090` | 8      | 592 B | 11.38s   |
| `192.168.56.1:50222` | `192.168.56.105:9090` | 5      | 370 B | 8.29s    |

> **Note:** These conversations are between the **host orchestrator** and the **agent** (port 9090). The sample's outbound C2 traffic to `192.0.2.123` was intercepted by FakeNet before reaching the network interface, so tshark only captured agent management traffic. This is expected behavior — FakeNet operates at a higher level than the packet capture.

### DNS Queries

None captured. FakeNet intercepted DNS resolution before it reached the wire.

---

## 🔒 Handle Snapshot

Open handles held by `malware_emulator.exe` (PID 2996) at time of capture:

| Handle | Type    | Access | Path                                              |
| ------ | ------- | ------ | ------------------------------------------------- |
| `4C`   | File    | RW-    | `C:\Windows\System32`                             |
| `15C`  | Section | —      | `\BaseNamedObjects\Cor_Private_IPCBlock_v4_2996`  |
| `160`  | Section | —      | `\...\Cor_SxSPublic_IPCBlock`                     |
| `2C8`  | File    | R--    | `%TEMP%\isolens_emulator\emulator_log.txt`        |
| `2F0`  | Section | —      | `\BaseNamedObjects\NLS_CodePage_437_3_2_0_0`      |
| `378`  | Section | —      | `\BaseNamedObjects\windows_shell_global_counters` |
| `41C`  | File    | R-D    | `C:\Windows\System32\en-US\KernelBase.dll.mui`    |
| `528`  | Section | —      | `\BaseNamedObjects\NLS_CodePage_1252_3_2_0_0`     |

**Observations:**

- `.NET IPC blocks` (`Cor_Private_IPCBlock_v4_2996`) confirm .NET CLR hosting
- Open file handle to `emulator_log.txt` shows the sample was actively writing logs
- Code page sections (437 = OEM US, 1252 = Windows Latin-1) indicate console + text operations

---

## 🧠 Behavioral Summary

### Indicators of Compromise (IOCs)

| Type              | Value                              | Context                                         |
| ----------------- | ---------------------------------- | ----------------------------------------------- |
| **IP Address**    | `192.0.2.123`                      | Outbound C2 communication (TCP port 80)         |
| **File Drop**     | `dropped_payload.bin`              | Binary payload written to `%TEMP%`              |
| **File Drop**     | `svchost_update.exe`               | Masqueraded executable mimicking system process |
| **File Drop**     | `.hidden_c2_config.dat`            | Command & control configuration file            |
| **File Drop**     | `update_service.bat`               | Batch script (possible persistence/execution)   |
| **Exfil Staging** | `chunk_000.enc` – `chunk_004.enc`  | Encrypted data staged for exfiltration          |
| **Registry**      | `HKCU\...\Run\IsoLensEmulatorTest` | Auto-start persistence (created then deleted)   |

### MITRE ATT&CK Mapping (Observed Behaviors)

| Technique ID | Technique                                                | Evidence                                       |
| ------------ | -------------------------------------------------------- | ---------------------------------------------- |
| T1059.003    | Command and Scripting Interpreter: Windows Command Shell | `cmd.exe` parent, `update_service.bat` dropped |
| T1547.001    | Boot or Logon Autostart: Registry Run Keys               | `HKCU\...\Run` key created                     |
| T1005        | Data from Local System                                   | Desktop, Documents, Recent files probed        |
| T1555        | Credentials from Password Stores                         | `Microsoft\Credentials` directory accessed     |
| T1071.001    | Application Layer Protocol: Web Protocols                | HTTP connections to `192.0.2.123:80`           |
| T1041        | Exfiltration Over C2 Channel                             | Encrypted chunks staged in `staging\exfil\`    |
| T1036.005    | Masquerading: Match Legitimate Name                      | `svchost_update.exe` mimics system process     |
| T1027        | Obfuscated Files or Information                          | `.enc` files suggest encrypted payloads        |
| T1074.001    | Data Staged: Local Data Staging                          | `staging\exfil\` directory with chunked data   |

### Risk Assessment

| Category              | Level       | Rationale                                                                                                 |
| --------------------- | ----------- | --------------------------------------------------------------------------------------------------------- |
| **File System**       | 🔴 High     | Multiple payloads dropped, exfil staging directory created                                                |
| **Persistence**       | 🟡 Medium   | Registry Run key created (and cleaned up)                                                                 |
| **Network**           | 🟡 Medium   | Outbound C2 communication on port 80                                                                      |
| **Credential Access** | 🟡 Medium   | Credentials directory probed                                                                              |
| **Discovery**         | 🟡 Medium   | User directories enumerated                                                                               |
| **Overall**           | 🔴 **High** | Multi-stage behavior: drops payloads, establishes persistence, stages encrypted exfiltration, contacts C2 |

---

## 📁 Output Files

All artifacts for this analysis are stored under:

```
core/storage/reports/20260228_160948_5c7a739f/
├── artifacts/
│   ├── analysis_summary.json      ← Aggregated machine-readable summary
│   ├── metadata.json              ← Collector status and file listing
│   ├── sysmon/
│   │   └── sysmon_summary.json    ← Filtered Sysmon events
│   ├── procmon/
│   │   └── procmon_summary.json   ← Filtered Procmon events
│   ├── network/
│   │   └── network_summary.json   ← tshark conversations & DNS
│   └── handle/
│       └── handle_snapshot.txt    ← Process handle dump
└── (original zip from agent)
```

> **Data Reduction:** The raw Procmon capture was 317,671 rows. After filtering to the sample process and extracting only notable operations, the final output is a compact JSON summary. Combined with all other collectors, the total artifact size was reduced from ~295 MB (raw) to ~88 KB (filtered summaries only).

---

_Generated by IsoLens v1.2.0 — Academic Malware Sandbox_
