# AI Writing Assistant

An AI-powered writing tool for **paraphrasing**, **humanizing** (anti-AI detection cleanup), and **proofreading** academic and clinical manuscripts. Runs locally on your machine — no internet required after setup.

## Features

| Feature | Description |
|---|---|
| **Paraphrase** | Rewrites text in Academic, Concise, or High-Impact styles |
| **Humanize** | Removes AI-detection patterns (Dr. Noora clinical style or General anti-AI cleanup) |
| **Proofread** | Two-phase audit: detects issues, then applies fixes |

## Quick Start (Windows)

### 1. Install Python

Make sure you have **Python 3.10 or later** installed.
Check by opening a terminal (Command Prompt or PowerShell) and running:

```
python --version
```

If not installed, download from [python.org](https://www.python.org/downloads/) and check **"Add Python to PATH"** during installation.

### 2. Run the setup script

Open PowerShell or Command Prompt and run:

```powershell
cd D:\GitHub\Para_Paper\backend
python main.py
```

The first time you run it, you may need to install dependencies. If you see import errors, run:

```powershell
pip install -r requirements.txt
```

Then try `python main.py` again.

### 3. Open in your browser

Once you see:

```
=======================================================
  AI Writing Assistant Backend
=======================================================
  Server:  http://localhost:8765
  Open in your browser to start
=======================================================
```

Open **http://localhost:8765** in your browser (Chrome, Edge, or Firefox).

### 4. Use the tool

1. **Paste or type** your text in the text box at the top
2. Click a tab: **Paraphrase**, **Humanize**, or **Proofread**
3. Click the action button (e.g. "Paraphrase Text")
4. Click **"Copy to Clipboard"** on any result to copy it

---

## How each feature works

### Paraphrase
Paste text and click "Paraphrase Text". You get three versions:
- **Academic / Formal** — scholarly vocabulary, passive constructions
- **Concise / Direct** — short, to-the-point
- **High-Impact / Active** — bold claims, active voice

### Humanize
Two modes:
- **Dr. Noora Style** — clinical vocabulary, bracket spacing quirks, citation patterns
- **General Anti-AI Cleanup** — removes cliches like "delve", "testament", "tapestry"

### Proofread
Two phases:
- **Phase 1 (Detection)** — scans for undefined acronyms, overclaiming words, formatting issues
- **Phase 2 (Fix)** — applies fixes to the approved issues you selected

---

## Troubleshooting

| Problem | Solution |
|---|---|
| `port 8000` error / port already in use | Another program is using the port. The server uses port **8765** by default. |
| "Cannot reach server" error in the UI | Make sure the terminal from Step 2 is still running. Don't close it. |
| "Opened directly from file system" | You opened the HTML file directly. Access via **http://localhost:8765** instead. |
| `pip install` fails | Make sure Python is installed and added to PATH. Restart your terminal after installing Python. |
| Blank results or simulation mode | The tool works even without an API key using a built-in rules engine. Results are still useful for basic rewrites. |

## Project structure

```
Para_Paper/
├── backend/           # Python FastAPI server (run this)
│   ├── main.py        # Server entry point
│   ├── agent_wrapper.py   # AI agent + fallback rules
│   ├── .agent/skills/ # Skill prompt files
│   ├── .env           # API key (optional)
│   └── requirements.txt
├── frontend/          # Web interface
│   ├── index.html     # Main page
│   ├── taskpane.js    # Frontend logic
│   └── taskpane.css   # Styling
├── humanizer-main/    # Humanizer skill reference
├── humanizer-Noora/   # Dr. Noora style reference
├── proof-reading-skill/   # Proofreading skill reference
└── par4Acad-master/   # Academic NLP resources
```
