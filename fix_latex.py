import re

with open("Miniproject_Report/main_codex.tex", "r") as f:
    content = f.read()

# 1. Add List of Tables
content = content.replace(
    "\\addcontentsline{toc}{section}{\\uppercase\\textbf{List of Figures}}\n\n\\newpage",
    "\\addcontentsline{toc}{section}{\\uppercase\\textbf{List of Figures}}\n\n\\newpage\n\\listoftables\n\\addcontentsline{toc}{section}{\\uppercase\\textbf{List of Tables}}\n\n\\newpage"
)

# 2. Fix Place/Date explicit breaks
content = content.replace("\\vspace{2cm}\n{\\noindent Place: ERNAKULAM", "\\vfill\n{\\noindent Place: ERNAKULAM")
content = content.replace("\\vspace{3cm}\n{\\noindent Place: ERNAKULAM", "\\vfill\n{\\noindent Place: ERNAKULAM")

# 3. Add references to Figures & Tables in the text and exact labels
reps = {
    # Figure Labels
    "\\caption{IsoLens high-level dashboard and interface direction}\n\\end{figure}": "\\caption{IsoLens high-level dashboard and interface direction}\n\\label{fig:ui_direction}\n\\end{figure}",
    "\\caption{Overall architecture diagram showing UI, gateway, controller, VM agent, collectors, storage, and AI threat intelligence flow}\n\\end{figure}": "\\caption{Overall architecture diagram showing UI, gateway, controller, VM agent, collectors, storage, and AI threat intelligence flow}\n\\label{fig:overall_arch}\n\\end{figure}",
    "\\caption{DFD Level 0: User submits sample to IsoLens and receives generated analysis report}\n\\end{figure}": "\\caption{DFD Level 0: User submits sample to IsoLens and receives generated analysis report}\n\\label{fig:dfd0}\n\\end{figure}",
    "\\caption{DFD Level 1: Interface, Gateway, Controller, VM Agent, Storage, and AI Analysis interactions}\n\\end{figure}": "\\caption{DFD Level 1: Interface, Gateway, Controller, VM Agent, Storage, and AI Analysis interactions}\n\\label{fig:dfd1}\n\\end{figure}",
    "\\caption{DFD Level 2: Detailed analysis pipeline including sample transfer, execution, collectors, screenshots, and final report generation}\n\\end{figure}": "\\caption{DFD Level 2: Detailed analysis pipeline including sample transfer, execution, collectors, screenshots, and final report generation}\n\\label{fig:dfd2}\n\\end{figure}",
    "\\caption{Scan page showing sample upload and submission workflow.}\n\\end{figure}": "\\caption{Scan page showing sample upload and submission workflow.}\n\\label{fig:scan_page}\n\\end{figure}",
    "\\caption{Reports page showing generated analysis output.}\n\\end{figure}": "\\caption{Reports page showing generated analysis output.}\n\\label{fig:reports_page}\n\\end{figure}",
    "\\caption{Settings page for configuring sandbox and analysis preferences.}\n\\end{figure}": "\\caption{Settings page for configuring sandbox and analysis preferences.}\n\\label{fig:settings_page}\n\\end{figure}",
    "\\caption{AI summary view showing consolidated intelligence findings and report output.}\n\\end{figure}": "\\caption{AI summary view showing consolidated intelligence findings and report output.}\n\\label{fig:ai_summary}\n\\end{figure}",
    "\\caption{Illustrative evaluation chart based on documented project results}\n\\end{figure}": "\\caption{Illustrative evaluation chart based on documented project results}\n\\label{fig:eval_chart}\n\\end{figure}",
    "\\caption{Comparative detection performance presented for report visualization}\n\\end{figure}": "\\caption{Comparative detection performance presented for report visualization}\n\\label{fig:comp_detect}\n\\end{figure}",
    "\\caption{Sandbox execution status and settings view.}\n\\end{figure}": "\\caption{Sandbox execution status and settings view.}\n\\label{fig:appendix_sandbox}\n\\end{figure}",
    
    # Table Labels
    "\\caption{Current file-based storage design}\n\\begin{tabularx}": "\\caption{Current file-based storage design}\n\\label{tab:storage_design}\n\\begin{tabularx}",
    "\\caption{Planned logical database entities}\n\\begin{tabularx}": "\\caption{Planned logical database entities}\n\\label{tab:db_schema}\n\\begin{tabularx}",
    "\\caption{Technology stack used in IsoLens}\n\\begin{tabularx}": "\\caption{Technology stack used in IsoLens}\n\\label{tab:tech_stack}\n\\begin{tabularx}",
    "\\caption{Indicative system requirements}\n\\begin{tabularx}": "\\caption{Indicative system requirements}\n\\label{tab:sys_req}\n\\begin{tabularx}",
    "\\caption{Key reported evaluation metrics}\n\\begin{tabularx}": "\\caption{Key reported evaluation metrics}\n\\label{tab:eval_metrics}\n\\begin{tabularx}",
    
    # Textual references
    "architecture follows a left-to-right data path.": "architecture (Figure \\ref{fig:overall_arch}) follows a left-to-right data path.",
    "browser interface by selecting": "browser interface (Figure \\ref{fig:ui_direction}) by selecting",
    "Level 0 DFD is useful": "Level 0 DFD (Figure \\ref{fig:dfd0}) is useful",
    "Level 1 DFD shows how": "Level 1 DFD (Figure \\ref{fig:dfd1}) shows how",
    "Level 2 DFD provides the": "Level 2 DFD (Figure \\ref{fig:dfd2}) provides the",
    "primarily uses a file-based storage model.": "primarily uses a file-based storage model (Table \\ref{tab:storage_design}).",
    "The following table presents a": "The following table (Table \\ref{tab:db_schema}) presents a",
    "The scan page allows file": "The scan page (Figure \\ref{fig:scan_page}) allows file",
    "The reports page presents": "The reports page (Figure \\ref{fig:reports_page}) presents",
    "The scan history page is intended for browsing past analyses. Settings and help pages support configuration and guidance.": "Settings and help pages (Figure \\ref{fig:settings_page}) support configuration and guidance.",
    "grouped findings make the": "grouped findings (Figure \\ref{fig:ai_summary}) make the",
    "\\section{TECHNOLOGY STACK}\n\\begin{table}": "\\section{TECHNOLOGY STACK}\nThe architecture relies on the underlying technologies layered as detailed in Table \\ref{tab:tech_stack}.\n\n\\begin{table}",
    "\\section{SYSTEM REQUIREMENTS}\n\\begin{table}": "\\section{SYSTEM REQUIREMENTS}\nTable \\ref{tab:sys_req} specifies the indicative system requirements for host and guest environments.\n\n\\begin{table}",
    "indicators for the final mini-project report.": "indicators for the final mini-project report (Figure \\ref{fig:eval_chart}).",
    "within the scope of the project. The detection rate suggests": "within the scope of the project. Comparative analysis (Figure \\ref{fig:comp_detect}) further confirms the advantages of this dynamic approach over traditional static methods. The detection rate suggests",
    "The reported values show that IsoLens": "The reported values (Table \\ref{tab:eval_metrics}) show that IsoLens"
}

for k, v in reps.items():
    content = content.replace(k, v)

with open("Miniproject_Report/main_codex.tex", "w") as f:
    f.write(content)

print("Done replacing.")
