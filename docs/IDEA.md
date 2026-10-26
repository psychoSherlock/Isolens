### 💡 Additional Specialized Proposals & Modules:
- **[GUI Screen Text Triage with Laya (System 1 Model)](GUI_TEXT_TRIAGE_WITH_LAYA.md)**: Two-tier extraction (OS Win32/Filesystem + Visual OCR Fallback) paired with Laya for sub-second detection of ransomware extortion notes, fake AV scareware, and credential phishing prompts.

## The Idea & The Solution:
Ok so Here is the idea: To Create a locally running version of Any.run
Like mobsf for android.

To host a container like environment or a virtual environment.
The target project is made for a windows machine
For first the client UI will be a website.
For initial phase, users can upload a file.
The program will then upload it to our VM/container 
VM/Container have monitoring tools installed. VM/Container will execute the program while also doign a sreenrecord/multiple screenshots
VM/Container will analyze Network Traffic, Process & Sub Process, FileSystem monitoring, UI Interaction etc stuff like that.
All these are outputted and then the data is send to either a locally running AI or a remote AI. 
AI generated a report, IOC, summary, risk score and YARA rule to detect such a malware if existed.




### Problem Description and Solution I gave in the PPT:

With the rapid increase in unknown and untrusted software distributed through the
internet, the availability of reliable and automated mechanisms to safely analyze suspicious
files has become essential for modern cybersecurity. This work presents an open-source,
cross-platform malware sandboxing system that automatically analyzes newly downloaded
files by executing them inside fully isolated Windows or Linux environments selected based
on the file type. The system leverages containerization and virtualization technologies
such as Docker, Kubernetes, and Vagrant to dynamically provision secure analysis
environments, while continuously observing runtime behavior through file system
monitoring, process activity tracking, network traffic inspection, user interface
interaction analysis, and other behavioral indicators. Security-focused tools and
frameworks such as YARA and runtime detection engines are used to identify known
malicious patterns and anomalies during execution. The collected behavioral data is then
processed using a locally hosted large language model to generate an intelligent summary,
compute a risk score indicating the likelihood of malicious intent, and produce a
comprehensive analysis report enriched with execution screenshots, indicators of
compromise, and detection artifacts. By combining modern infrastructure technologies with
intelligent analysis in a fully open and extensible platform, this system highlights the
importance of accessible malware analysis solutions in strengthening early threat detection
and reducing dependence on manual investigation.



#### CHATGPT:
##### Workflow:

Create Windows 10 VM (2GB RAM)
Install:

- Sysmon
- Procmon
- Wireshark
- TCPView
- Process Explorer
- https://github.com/mandiant/flare-fakenet-ng
- procmon_lite
- Sysmon
- Wireshark/tshar
- watchdog
- mss / ffmpeg
 Process Monitoring

Use:

- **Sysmon**
- **Process Explorer**
- Windows Event Logs

Network:
- Install Wireshark OR    
- Use tshark (CLI version)
- Or use Fakenet-NG (simulate internet safely)

## Screenshot / Screen Recording

Inside VM:

Option 1:

- Use ffmpeg screen capture
    

Option 2:

- Take periodic screenshots via PowerShell:
    

Add-Type -AssemblyName System.Windows.Forms  
Add-Type -AssemblyName System.Drawing

Every 5 seconds → Save screenshot.

---
Setup:
- Install guest additions
- Take clean snapshotRevert snapshot
- Start VM
- Upload sample via shared folder
- Execute sample
- Start monitoring
- After timeout → Collect logs
- Shutdown VM
- Revert snapshot


