# 📄 AI Resume Editor: Precision Zero-Reflow PDF Editing Agent

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://pdf-editor-agent.streamlit.app/)
[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-blue.svg)](https://www.python.org/downloads/)
[![Groq LPU](https://img.shields.io/badge/Inference-Groq%20LPU-orange.svg)](https://console.groq.com)
[![PyMuPDF](https://img.shields.io/badge/PDF%20Engine-PyMuPDF-green.svg)](https://pymupdf.readthedocs.io/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

An agentic, prompt-driven resume editor that performs **zero-reflow in-place text and link modifications** on PDF resumes without breaking ATS formatting, grid alignment, or typographic style.

🔗 **Live Demo:** [https://pdf-editor-agent.streamlit.app/](https://pdf-editor-agent.streamlit.app/)

---

## 🎯 The Problem

Modifying a finalized PDF resume before an application deadline is notoriously difficult:
- **Layout Collapses:** Traditional editors or AI converters rewrite the layout entirely, shifting bullet points, dates, and column margins.
- **ATS Incompatibility:** Broken baseline grids and shifted bounding boxes can degrade text parsing across Applicant Tracking Systems.
- **Dead Hyperlinks:** Editing the visible anchor text (e.g., updating a GitHub or LinkedIn handle) routinely severs or ignores the underlying clickable URI annotation layer.

---

## 💡 The Solution

This system separates **reasoning** from **rendering**:

1. **LLM Orchestration (Groq LPU):** Natural language prompts are interpreted by high-speed LLMs to extract editing intent and generate deterministic tool parameters.
2. **Deterministic PDF Physics (PyMuPDF):** Rather than letting the model approximate layout coordinates, the engine queries the exact millimeter/point span boundaries, line pitch, font metrics, and sRGB color matrices directly from the PDF dictionary.
3. **Precision Redaction & Re-stamping:** Cleans only the target span bounding box and re-stamps replacement text using the matched font family, weight, calculated point size, and letter tracking to eliminate horizontal overflow.
4. **Dual-Layer URI Rebinding:** Intercepts PDF `/Link` annotations and remaps them so updated URLs remain interactive.

---


## 🏗️ Architecture
User Prompt: "Update my GPA to 3.9 and point my GitHub link to github.com/newdev"
                          │
                          ▼
               [ Groq Orchestration Agent ]
                 (Fast LPU Tool-Calling Loop)
                          │
 ┌────────────────────────┴────────────────────────┐
 ▼                                                 ▼
[ inspect_resume_text ]                          [ inspect_resume_links ]
• Resolves coordinates [x0, y0, x1, y1]          • Locates active /Link URIs
• Extracts font, size, weight & sRGB             • Extracts clickable bounds
│                                                 │
└────────────────────────┬────────────────────────┘
                         │
                         ▼
            [ Python Engine (PyMuPDF) ]
           • In-place visual redaction
           • Matched typography re-stamping
           • Interactive URI annotation rebinding
                        │
                        ▼
           Pixel-Perfect ATS Resume Output


---

## 🚀 Features

- **🎯 Exact Font & Style Matching:** Automatically resolves serif, sans-serif, monospaced, bold, and italic weights from embedded PostScript names.
- **📐 Grid & Baseline Locking:** Updates numbers, dates, titles, and text strings without causing cascading line reflows.
- **🔗 Dual-Layer Link Synchronization:** Modifies visible link labels while synchronizing the underlying clickable destination URI.
- **↩ Multi-Step Undo:** In-memory byte-level history stack enables immediate restoration of earlier states.
- **⚡ Sub-Second Inference:** Powered by Groq LPU tool-calling endpoints for responsive interaction.

---

## 📂 Project Structure

```text
pdf-editor-agent/
│
├── .env                          # Local environment variables & API keys
├── requirements.txt              # Core dependencies
├── app.py                        # Streamlit UI & main application entrypoint
│
├── core/                         # Deterministic PDF Manipulation Engine
│   ├── inspector.py              # Span geometry, font metadata & URI scanner
│   ├── typography.py             # Font resolution, style mapping & color normalization
│   └── mutator.py                # In-place redaction, re-stamping & link binding
│
├── agent/                        # AI Orchestration & Tool Calling
│   ├── prompts.py                # Resume-specific system instructions & guardrails
│   ├── tools.py                  # JSON schemas & execution wrappers
│   └── orchestrator.py           # Multi-turn Groq tool execution loop
│
└── ui/                           # Streamlit Layout & State Management
    ├── state.py                  # In-memory document byte states & undo history
    └── components.py             # Side-by-side comparison & export controls
