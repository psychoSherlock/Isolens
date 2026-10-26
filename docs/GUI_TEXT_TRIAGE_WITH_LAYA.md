# 🖥️ GUI Text Extraction & System 1 Triage with Laya

## 📌 Overview

This document outlines the design for **Visual & GUI Screen Text Triage** in IsoLens.

By capturing the graphical user interface (GUI) of the sandbox desktop, extracting displayed text, and passing it to **Laya** (a fast, non-generative System 1 model), IsoLens can instantly detect and classify user-facing threats such as:
* **Ransomware extortion notes** (e.g., WannaCry, LockBit payment demands and Bitcoin addresses)
* **Tech support / FakeAV scareware** (e.g., fake virus alerts demanding phone calls to toll-free numbers)
* **Fake UAC / Credential phishing prompts** (e.g., spoofed Windows authentication dialogs)
* **Social engineering / ClickFix lures** (e.g., instructions to execute malicious PowerShell commands via `Win+R`)

---

## 🔍 Why OCR vs. Alternative Text Extraction Methods?

Can we extract text from the screen without Optical Character Recognition (OCR)? **Yes.** Several native OS methods exist, each with distinct advantages and limitations.

### Alternative Extraction Methods:

### 1. Windows UI Automation (UIA) & Accessibility API
* **How it works**: Uses `UIAutomationClient` / `System.Windows.Automation` in Windows to traverse the desktop window tree and read text elements (`Name`, `ValuePattern`, `HelpText`) directly from window controls.
* **Pros**:
  * 100% digital accuracy (zero OCR spelling errors).
  * Extremely fast (<1 ms, no image processing).
  * Directly reads native Win32 message boxes (`MessageBoxW`), WPF dialogs, and standard Windows alert windows.
* **Cons**:
  * Malware frequently uses custom graphic toolkits (DirectX, raw GDI bitmaps, HTML/Canvas without accessibility hooks, or skinned dialogs) that expose zero UIAutomation text nodes.

### 2. Win32 Window Enumeration (`EnumWindows`, `GetWindowText`, `WM_GETTEXT`)
* **How it works**: Queries all open window titles, edit boxes, and static text controls on the interactive desktop.
* **Pros**:
  * Very lightweight PowerShell / Python one-liner in the guest agent.
  * Instant capture of window titles and Notepad content.
* **Cons**:
  * Only works for classic Win32 controls; modern custom GUIs don't respond to `WM_GETTEXT`.

### 3. Filesystem Ransom Note Interception (Procmon File Watcher)
* **How it works**: Most ransomware creates text/HTML ransom notes on disk (`README_DECRYPT.txt`, `HOW_TO_RESTORE_FILES.html`) and automatically launches them via `notepad.exe` or the default web browser.
* **Pros**:
  * We already monitor filesystem activity via Procmon!
  * 100% accurate file content read directly from disk with zero image processing.
* **Cons**:
  * Only catches malware that writes notes to disk; misses memory-only lockers, fake AV popups, and desktop wallpaper changers (`SystemParametersInfo(SPI_SETDESKWALLPAPER)`).

### 4. GDI / DirectWrite API Hooking
* **How it works**: Injects an API hook into `DrawTextW`, `ExtTextOutW`, or `MessageBoxW` to capture text as it is sent to the display driver.
* **Pros**: Captures text strings at render time.
* **Cons**: Heavy implementation complexity, easily detected/bypassed by anti-hooking malware, and completely blind to pre-rendered bitmap images.

---

## ⚖️ Extraction Methods Comparison Matrix

| Method | Extraction Mechanism | Speed / Overhead | Text Accuracy | Evasion Resistance | Best Use Case |
|---|---|---|---|---|---|
| **Filesystem Watcher** | Reading dropped `*.txt` / `*.html` | Instant (0 ms) | 100% Exact | Moderate | Classic ransomware notes |
| **UI Automation / Win32** | Querying OS window tree / `WM_GETTEXT` | Sub-millisecond (<5 ms) | 100% Exact | Low (bypassed by custom UI) | Standard dialogs, UAC prompts |
| **API Hooking** | Intercepting `DrawTextW` / `ExtTextOutW` | Fast | High | Very Low (evaded by hooks) | Standard GDI apps |
| **Optical Character Recognition (OCR)** | Computer vision on desktop screenshot | ~150–400 ms | High (~95%+) | **Highest (Universal)** | Image-only lockers, custom GUIs, wallpaper changers |

---

## 🏆 The Optimal Solution: Two-Tier Hybrid Pipeline

Instead of choosing between OCR and OS-level extraction, IsoLens uses a **two-tier hybrid strategy**:

```
                              [ Sandbox Screenshot / Execution ]
                                               │
                                               ▼
                      ┌──────────────────────────────────────────────────┐
                      │ Tier 1: Fast Native Extraction (Zero Overhead)   │
                      │ • Check dropped files: *.txt, *.html             │
                      │ • Query active window titles & edit text         │
                      └────────────────────────┬─────────────────────────┘
                                               │
                       Text Found? ────────────┼────────────► Text Empty / Custom UI?
                            │                                       │
                            ▼                                       ▼
                   [ Use Native Text ]                     ┌────────────────────────────────┐
                            │                              │ Tier 2: Visual OCR Fallback    │
                            │                              │ (Tesseract / Lightweight OCR)  │
                            │                              └────────────────┬───────────────┘
                            │                                               │
                            └───────────────────────┬───────────────────────┘
                                                    │
                                                    ▼
                                     ┌─────────────────────────────┐
                                     │ LAYA (System 1 Model)       │
                                     │ Typed Decision Evaluation   │
                                     └──────────────┬──────────────┘
                                                    │
                                                    ▼
                                    ┌───────────────────────────────┐
                                    │ Structured Verdict:           │
                                    │ • ransomware_extortion        │
                                    │ • tech_support_scam           │
                                    │ • credential_phish            │
                                    │ • benign_desktop              │
                                    └───────────────────────────────┘
```

1. **Tier 1 (Fast Native Path - Sub-millisecond)**:
   * Inspect any created files matching `*README*`, `*DECRYPT*`, `*RESTORE*`, `*.txt`, `*.html` on the Desktop.
   * Query active window titles using `GetWindowTextW`.
   * If substantive text is found, pass it directly to Laya without running OCR.
2. **Tier 2 (Visual OCR Fallback - Universal Safety Net)**:
   * If a fullscreen window, changed wallpaper, or unknown UI appears, run a lightweight OCR pass (e.g., `tesseract` or an edge OCR model) on the screenshot image.
   * Passes the extracted visual text to Laya.

---

## 🧠 Why Laya (System 1) Excels at this Task

Laya is a ModernBERT-large encoder with a **typed decision head**:
* **Language Match**: Ransom notes and scareware popups are written in English specifically to be understood by human victims. This aligns with ModernBERT's pretraining.
* **Noise Resilience**: Subword tokenization easily handles OCR noise or intentional l33tspeak (e.g., `B1tco1n`, `f1les encryp+ed`).
* **Typed Output without Hallucination**: Emits direct typed decisions (e.g. `choice: ["malicious", "benign"]`) in a single forward pass without token-by-token text generation.
* **Performance**: ~319 ms on CPU, 0 cloud token cost.

---

## 📊 Empirical Benchmark Results (56 Screen-Text Samples)

A rigorous benchmark was conducted using 56 OCR-style screen-text samples across 7 distinct classes (8 samples each):
* **Malicious Classes (32 samples)**: `ransomware_extortion`, `tech_support_scam`, `fake_antivirus`, `phishing_login`.
* **Benign Classes (24 samples)**: `benign_desktop`, `benign_app` (Chrome, Zoom, Spotify), `security_warning` (authentic Windows Defender / UAC).

### Results Matrix

| Checkpoint | Question Format | Accuracy | Precision | Recall | TP / FN / FP / TN | Latency (p50) |
|---|---|---|---|---|---|---|
| **English** | 7-way Choice | 32% | 67% | 88% | 28 / 4 / 14 / 10 | 612 ms |
| **English** | **Binary Choice** | **88%** | **84%** | **97%** | **31 / 1 / 6 / 18** | **319 ms** |
| **English** | Yes / No | 79% | 74% | 97% | 31 / 1 / 11 / 13 | 319 ms |
| **Typed-Decisions** | 7-way Choice | 52% | 86% | 56% | 18 / 14 / 3 / 21 | 613 ms |
| **Typed-Decisions** | **Binary Choice** | **88%** | **90%** | **88%** | **28 / 4 / 3 / 21** | **319 ms** |
| **Typed-Decisions** | Yes / No | 86% | 90% | 84% | 27 / 5 / 3 / 21 | 319 ms |

### Key Benchmark Takeaways & Architectural Decisions

1. **Binary Choice is the Production Standard**:
   * Attempting 7-way classification collapses accuracy (32%–52%) and doubles latency to ~612 ms because fine-grained distinctions between Tech Support vs FakeAV blur together.
   * **Binary Choice (`malicious` vs `benign`)** jumps to **88% Accuracy** with **97% Recall** on the `English` checkpoint (catching 31 out of 32 malicious samples with only 1 missed).
2. **Checkpoint Selection**:
   * In a malware sandbox, a missed infection (false negative) is far more critical than a false alarm. `English` binary caught 31 of 32 malicious samples (97% recall), whereas `Typed-Decisions` missed 4 (88% recall). Therefore, **`English` Binary Choice** is selected as the primary triage engine.
3. **Mitigating False Positives**:
   * English binary triggered 6 false alarms on benign application screens (Spotify, Zoom, Chrome onboarding).
   * **Mitigation**:
     * **Application Window Scoping**: Capture and OCR *only the uploaded executable's window*, not the entire desktop/taskbar.
     * **Word Count Filter**: Skip Laya if OCR extracts $<15$ characters.
     * **Keyword Pre-check**: Trigger Laya only when high-signal security/extortion terms appear (e.g., *pay, bitcoin, decrypt, encrypted, virus, toll-free, locked, security alert*).

---

## 🎯 Target Application Window Capture (No Fullscreen Desktop Noise)

To prevent OCR from ingesting desktop icons, the Windows taskbar, system clock, or background notifications, the capture pipeline specifically isolates the **target application window**:

1. **Guest-Side Window Tracking (`isolens_agent.py`)**:
   * Tracks processes matching the uploaded sample name (or spawned child processes).
   * Obtains `MainWindowHandle` and calls `GetWindowRect` via Win32.
   * Crops the bitmap to the exact client/window rectangle (`$w, $h` at `$rect.Left, $rect.Top`) instead of `PrimaryScreen.Bounds`.
2. **Host-Side Window Extraction Fallback (`gui_analyzer.py`)**:
   * If only full-display screenshots are available, the analyzer automatically detects and crops out taskbars and background wallpaper to isolate active application windows before passing text to Tesseract OCR.

3. **Phishing / Fake UAC**:
   > *"Windows Security: An application requires elevated privileges. Enter your administrator username and password to allow this program to make changes."*
   > **Expected Target:** `credential_phish`
4. **Benign Desktop / App**:
   > *"Welcome to Google Chrome. Sign in to sync your tabs and settings across devices. New Tab | Downloads | Bookmarks."*
   > **Expected Target:** `benign_ui`
