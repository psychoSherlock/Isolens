import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import os

# Create figures directory if it doesn't exist
fig_dir = "Miniproject_Report/figure"
os.makedirs(fig_dir, exist_ok=True)

def save_fig(name):
    plt.savefig(os.path.join(fig_dir, name + ".png"), dpi=300, bbox_inches='tight')
    plt.close()

def setup_plot():
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.set_axis_off()
    return fig, ax

def draw_box(ax, x, y, w, h, text, shape='rect'):
    if shape == 'rect':
        rect = patches.Rectangle((x, y), w, h, linewidth=1.5, edgecolor='black', facecolor='white')
        ax.add_patch(rect)
    elif shape == 'cylinder':
        # Simple cylinder representation using two ellipses and lines
        top = patches.Ellipse((x + w/2, y + h), w, h*0.2, linewidth=1.5, edgecolor='black', facecolor='white')
        bottom = patches.Ellipse((x + w/2, y), w, h*0.2, linewidth=1.5, edgecolor='black', facecolor='white')
        ax.add_patch(bottom)
        ax.add_patch(patches.Rectangle((x, y), w, h, linewidth=0, facecolor='white'))
        ax.plot([x, x], [y, y + h], 'k-', lw=1.5)
        ax.plot([x + w, x + w], [y, y + h], 'k-', lw=1.5)
        ax.add_patch(top)
    elif shape == 'process':
        # DFD process (circle)
        circle = patches.Circle((x + w/2, y + h/2), min(w, h)/2, linewidth=1.5, edgecolor='black', facecolor='white')
        ax.add_patch(circle)
    elif shape == 'store':
        # DFD data store (open rectangle)
        ax.plot([x, x+w], [y, y], 'k-', lw=1.5)
        ax.plot([x, x+w], [y+h, y+h], 'k-', lw=1.5)
        ax.plot([x, x], [y, y+h], 'k-', lw=1.5)
    
    ax.text(x + w/2, y + h/2, text, ha='center', va='center', fontsize=10, fontweight='bold', wrap=True)

def draw_arrow(ax, x1, y1, x2, y2, text=""):
    ax.annotate(text, xy=(x2, y2), xytext=(x1, y1),
                arrowprops=dict(arrowstyle='->', lw=1.2, color='black'),
                ha='center', va='bottom', fontsize=8)

# 1. Overall System Architecture
fig, ax = setup_plot()
# Layers
draw_box(ax, 0.1, 0.8, 0.8, 0.1, "INTERFACE (Next.js)")
draw_box(ax, 0.1, 0.65, 0.8, 0.1, "GATEWAY (FastAPI API)")
draw_box(ax, 0.1, 0.5, 0.8, 0.1, "CONTROLLER (Orchestration)")
draw_box(ax, 0.1, 0.35, 0.35, 0.1, "MODULES (Parsing)")
draw_box(ax, 0.55, 0.35, 0.35, 0.1, "STORAGE (Reports/Logs)")
draw_box(ax, 0.1, 0.15, 0.35, 0.1, "VM SANDBOX (VirtualBox)")
draw_box(ax, 0.55, 0.15, 0.35, 0.1, "THREAT INTEL (AI Analysis)")

# Connections
draw_arrow(ax, 0.5, 0.8, 0.5, 0.75)
draw_arrow(ax, 0.5, 0.65, 0.5, 0.6)
draw_arrow(ax, 0.5, 0.5, 0.3, 0.45) # to modules
draw_arrow(ax, 0.5, 0.5, 0.7, 0.45) # to storage
draw_arrow(ax, 0.3, 0.35, 0.3, 0.25) # modules to vm
draw_arrow(ax, 0.7, 0.35, 0.7, 0.25) # storage to intel
save_fig("overall_architecture")

# 2. DFD Level 0
fig, ax = setup_plot()
draw_box(ax, 0.1, 0.4, 0.2, 0.2, "USER")
draw_box(ax, 0.4, 0.35, 0.3, 0.3, "ISOLENS SYSTEM", shape='process')
draw_box(ax, 0.8, 0.4, 0.2, 0.2, "STORAGE /\nVM", shape='store')
draw_arrow(ax, 0.3, 0.55, 0.4, 0.55, "Upload Sample")
draw_arrow(ax, 0.4, 0.45, 0.3, 0.45, "Analysis Report")
draw_arrow(ax, 0.7, 0.55, 0.8, 0.55, "Data/Execution")
draw_arrow(ax, 0.8, 0.45, 0.7, 0.45, "Artifacts")
save_fig("dfd_level_0")

# 3. DFD Level 1
fig, ax = setup_plot()
draw_box(ax, 0.05, 0.7, 0.2, 0.15, "INTERFACE", shape='process')
draw_box(ax, 0.35, 0.7, 0.2, 0.15, "GATEWAY", shape='process')
draw_box(ax, 0.65, 0.7, 0.2, 0.15, "CONTROLLER", shape='process')
draw_box(ax, 0.65, 0.4, 0.2, 0.15, "AGENT / VM", shape='process')
draw_box(ax, 0.35, 0.4, 0.2, 0.15, "STORAGE", shape='store')
draw_box(ax, 0.05, 0.4, 0.2, 0.15, "AI ANALYSIS", shape='process')

draw_arrow(ax, 0.25, 0.775, 0.35, 0.775, "Upload")
draw_arrow(ax, 0.55, 0.775, 0.65, 0.775, "Submit")
draw_arrow(ax, 0.75, 0.7, 0.75, 0.55, "Execute")
draw_arrow(ax, 0.65, 0.475, 0.55, 0.475, "Artifacts")
draw_arrow(ax, 0.35, 0.475, 0.25, 0.475, "Data")
draw_arrow(ax, 0.15, 0.55, 0.15, 0.7, "Report")
save_fig("dfd_level_1")

# 4. DFD Level 2 (Detailed Pipeline)
fig, ax = setup_plot()
draw_box(ax, 0.1, 0.85, 0.8, 0.1, "SAMPLE ARCHIVAL (Host)")
draw_box(ax, 0.1, 0.7, 0.8, 0.1, "SHARED FOLDER TRANSFER (SandboxShare)")
draw_box(ax, 0.1, 0.55, 0.8, 0.1, "IN-VM AGENT EXECUTION")
draw_box(ax, 0.1, 0.4, 0.8, 0.1, "COLLECTOR RUNS (Sysmon, Procmon, etc.)")
draw_box(ax, 0.1, 0.25, 0.8, 0.1, "RETRIEVAL & UNPACKING (Host)")
draw_box(ax, 0.1, 0.1, 0.8, 0.1, "AI ENRICHMENT & REPORTING")

for y in [0.85, 0.7, 0.55, 0.4, 0.25]:
    draw_arrow(ax, 0.5, y, 0.5, y - 0.05)
save_fig("dfd_level_2")

# 5. UI Wireframe: Scan Page
fig, ax = setup_plot()
# Browser frame
rect = patches.Rectangle((0.1, 0.1), 0.8, 0.8, linewidth=1, edgecolor='black', facecolor='white')
ax.add_patch(rect)
ax.plot([0.1, 0.9], [0.8, 0.8], 'k-', lw=1) # URL bar area
ax.text(0.5, 0.85, "IsoLens - Scan Submission", ha='center', va='center')
# Sidebar
ax.plot([0.3, 0.3], [0.1, 0.8], 'k-', lw=1)
# Content
draw_box(ax, 0.4, 0.5, 0.4, 0.2, "Drag & Drop Sample\n(or Click to Upload)")
draw_box(ax, 0.4, 0.3, 0.2, 0.1, "TIMEOUT (60s)")
draw_box(ax, 0.65, 0.3, 0.15, 0.1, "START SCAN")
save_fig("ui_scan_page")

# 6. UI Wireframe: Reports Page
fig, ax = setup_plot()
rect = patches.Rectangle((0.1, 0.1), 0.8, 0.8, linewidth=1, edgecolor='black', facecolor='white')
ax.add_patch(rect)
ax.plot([0.1, 0.9], [0.8, 0.8], 'k-', lw=1)
ax.plot([0.3, 0.3], [0.1, 0.8], 'k-', lw=1)
# Summary card
draw_box(ax, 0.35, 0.6, 0.5, 0.15, "THREAT SUMMARY\nRisk: 85/100 (HIGH)")
# Tabs
draw_box(ax, 0.35, 0.5, 0.15, 0.05, "Sysmon")
draw_box(ax, 0.52, 0.5, 0.15, 0.05, "Network")
draw_box(ax, 0.7, 0.5, 0.15, 0.05, "AI Report")
# Details
draw_box(ax, 0.35, 0.15, 0.5, 0.3, "Detailed Artifact List / AI Conclusions")
save_fig("ui_reports_page")

# 7. UI Wireframe: Scan History / Settings
fig, ax = setup_plot()
rect = patches.Rectangle((0.1, 0.1), 0.8, 0.8, linewidth=1, edgecolor='black', facecolor='white')
ax.add_patch(rect)
ax.plot([0.1, 0.9], [0.8, 0.8], 'k-', lw=1)
ax.plot([0.3, 0.3], [0.1, 0.8], 'k-', lw=1)
draw_box(ax, 0.35, 0.55, 0.5, 0.2, "SCAN HISTORY\n(List of recent analysis results)")
draw_box(ax, 0.35, 0.3, 0.5, 0.2, "VM SETTINGS\n(IP: 192.168.56.105, Port: 9090)")
save_fig("ui_history_settings")

# 8. Runtime Screenshots Mockup
fig, ax = setup_plot()
# Multiple windows
draw_box(ax, 0.1, 0.5, 0.4, 0.35, "SANDBOX VM\n(Sample Execution)")
draw_box(ax, 0.55, 0.5, 0.4, 0.35, "HOST CONTROLLER\n(Polling Status)")
draw_box(ax, 0.1, 0.1, 0.4, 0.35, "ARTIFACT PACKAGE\n(Extracted Files)")
draw_box(ax, 0.55, 0.1, 0.4, 0.35, "AI ANALYSIS PIPELINE\n(Agent Coordination)")
save_fig("runtime_screenshots")
