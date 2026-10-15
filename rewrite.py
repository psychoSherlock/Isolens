import re

with open("Miniproject_Report/main_codex.tex", "r") as f:
    text = f.read()

# Make backup
with open("Miniproject_Report/main_codex.tex.bak", "w") as f:
    f.write(text)

# 1. Add List of Abbreviations
abbreviations = r"""\newpage
\chapter*{\uppercase{List of Abbreviations}}
\addcontentsline{toc}{section}{LIST OF ABBREVIATIONS}
\begin{table}[H]
\renewcommand{\arraystretch}{1.5}
\begin{tabularx}{\textwidth}{>{\bfseries}l X}
API & Application Programming Interface \\
DFD & Data Flow Diagram \\
GUI & Graphical User Interface \\
IOC & Indicator of Compromise \\
LLM & Large Language Model \\
VM & Virtual Machine \\
OS & Operating System \\
\end{tabularx}
\end{table}

\newpage
"""
text = text.replace(r"\addcontentsline{toc}{section}{LIST OF TABLES}", r"\addcontentsline{toc}{section}{LIST OF TABLES}" + "\n\n" + abbreviations)


# 2. Extract sections for reshuffling
def get_block(start_marker, end_marker):
    pattern = re.compile(re.escape(start_marker) + r"(.*?)(?=" + re.escape(end_marker) + ")", re.DOTALL)
    m = pattern.search(text)
    return m.group(1).strip() if m else ""

# The document is currently ordered:
# \chapter{INTRODUCTION} -> \section{INTRODUCTION} -> \section{SCOPE AND MOTIVATION} -> 
# \chapter{PROPOSED WORK} -> \section{OBJECTIVES} -> \section{PROBLEM STATEMENT} -> \section{LITERATURE SURVEY} [papers] -> \section{EXISTING SYSTEM AND PROPOSED SOLUTION}
# \chapter{PROJECT DESIGN} -> \section{SYSTEM ARCHITECTURE} -> \section{MODULES} -> \section{DATA FLOW DIAGRAM} -> \section{DATABASE TABLE DESIGN} -> \section{GUI DESIGN} -> \section{TECHNOLOGY STACK} -> \section{SYSTEM REQUIREMENTS}
# \section{RESULTS AND DISCUSSION} ...

ch1_intro = get_block(r"\chapter{INTRODUCTION}", r"\section{SCOPE AND MOTIVATION}")
ch1_motivation = get_block(r"\section{SCOPE AND MOTIVATION}", r"\chapter{PROPOSED WORK}")
ch1_problem = get_block(r"\section{PROBLEM STATEMENT}", r"\section{LITERATURE SURVEY}")

# Literature Survey papers (currently under \subsection)
# We will just replace \section{LITERATURE SURVEY} with \chapter{LITERATURE REVIEW}
# And for each paper, change \subsection{...} to \section{... [Title], [Author], [Year]} 
# and split the paragraph into \subsection{Summary} and \subsection{Methodology}.

lit_review = get_block(r"\section{LITERATURE SURVEY}", r"\section{EXISTING SYSTEM AND PROPOSED SOLUTION}")

papers_map = {
    "Improving the Efficiency of Dynamic Malware Analysis": "Ulrich Bayer et al., 2010",
    "A Survey on Automated Dynamic Malware-Analysis Techniques and Tools": "Manuel Egele et al., 2012",
    "A Survey On Automated Dynamic Malware Analysis Evasion and Counter-Evasion: PC, Mobile, and Web": "Alexei Bulazel et al., 2017",
    "Dynamic Malware Analysis in the Modern Era---A State of the Art Survey": "Ori Or-Meir et al., 2019",
    "An Inside Look into the Practice of Malware Analysis": "Miuyin Yong Wong et al., 2021",
    "A Dynamic Analysis-Powered Explanation Framework for Malware Detection": "Huijuan Zhu et al., 2024"
}

for title, author_year in papers_map.items():
    # Find the subsection block
    old_header = r"\subsection{" + title + r"}"
    new_header = r"\section{" + title + r", " + author_year + r"}"
    # The text is just one big paragraph. We'll find the first period halfway and split it.
    
    parts = lit_review.split(old_header)
    if len(parts) > 1:
        # get the text until the next \subsection or end
        following = parts[1]
        next_sub = following.find(r"\subsection{")
        if next_sub == -1: next_sub = len(following)
        
        paper_text = following[:next_sub].strip()
        
        # Split paper_text roughly in half at a sentence boundary
        sentences = paper_text.split(". ")
        mid = len(sentences) // 2
        summary_text = ". ".join(sentences[:mid]) + "."
        methodology_text = ". ".join(sentences[mid:])
        
        new_block = new_header + "\n\n\\subsection{Summary}\n" + summary_text + "\n\n\\subsection{Methodology}\n" + methodology_text + "\n\n"
        lit_review = lit_review.replace(old_header + following[:next_sub], new_block)

ch3_objectives = get_block(r"\section{OBJECTIVES}", r"\section{PROBLEM STATEMENT}")
ch3_proposed = get_block(r"\section{EXISTING SYSTEM AND PROPOSED SOLUTION}", r"\chapter{PROJECT DESIGN}")

sys_req_old = get_block(r"\section{SYSTEM REQUIREMENTS}", r"\section{RESULTS AND DISCUSSION}")

sys_req_new = r"""\section{System Requirements}
\subsection{Hardware}
\begin{itemize}
\item System capable of running VirtualBox and Python-based backend services.
\item Multi-core CPU suitable for running host services and a guest VM.
\item 8 GB RAM or higher recommended.
\item 50 GB or higher storage for VM images, reports, and artifacts.
\end{itemize}

\subsection{Software}
\begin{itemize}
\item Windows 10/11 sandbox VM natively configured with standard monitoring utilities.
\item Oracle VirtualBox with guest additions.
\item Python, FastAPI, Next.js, and VirtualBox tooling on the host.
\end{itemize}
"""

ch4_prefix = get_block(r"\chapter{PROJECT DESIGN}", r"\section{SYSTEM REQUIREMENTS}")

ch5_schedule = r"""\chapter{PROJECT SCHEDULE}
The following section outlines the timeline and milestones for the development, testing, and documentation of the IsoLens sandbox project over the academic year.

\begin{figure}[H]
\centering
\includegraphics[width=0.85\textwidth]{figure/project_schedule.png}
\caption{Project schedule and Gantt chart timeline.}
\label{fig:project_schedule}
\end{figure}
"""


# Assemble the new document body
new_body = ""
new_body += "\\chapter{INTRODUCTION}\n" + ch1_intro.replace("\\chapter{INTRODUCTION}", "").strip() + "\n\n"
new_body += "\\section{Motivation}\n" + ch1_motivation + "\n\n"
new_body += "\\section{Problem Statement}\n" + ch1_problem + "\n\n"

new_body += "\\chapter{LITERATURE REVIEW}\n" + lit_review + "\n\n"

new_body += "\\chapter{PROPOSED PROJECT}\n"
new_body += "\\section{Objectives}\n" + ch3_objectives + "\n\n"
new_body += "\\section{Proposed Solution}\n" + ch3_proposed + "\n\n"

new_body += "\\chapter{PROJECT DESIGN}\n"
# Capitalize section headers to match the formatting request, but we can leave existing LaTeX headers alone.
# The prefix already has System Architecture, Modules, DFD, DB, GUI, Tech Stack.
new_body += ch4_prefix.replace("\\chapter{PROJECT DESIGN}", "").strip() + "\n\n"
new_body += sys_req_new + "\n\n"

new_body += ch5_schedule + "\n\n"

# Append the rest (Results and Conclusion)
rest_of_doc = text[text.find(r"\section{RESULTS AND DISCUSSION}"):]
# We should probably upgrade \section{RESULTS AND DISCUSSION} to \chapter{RESULTS AND DISCUSSION} to maintain chapter flow
rest_of_doc = rest_of_doc.replace(r"\section{RESULTS AND DISCUSSION}", r"\chapter{RESULTS AND DISCUSSION}")

new_body += rest_of_doc

# Replace the body in the original text
start_idx = text.find(r"\chapter{INTRODUCTION}")
final_text = text[:start_idx] + new_body

# A small fix: change some remaining ALL CAPS \section commands to Title Case to match the user's example style if desired,
# but usually standard LaTeX handles that via \sectionfont. Leaving them as they were mapped.

with open("Miniproject_Report/main_codex.tex", "w") as f:
    f.write(final_text)

print("Rewriting complete. Compiling to check...")
