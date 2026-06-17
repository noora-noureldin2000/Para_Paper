# AI Writing Assistant

An AI-powered writing assistant that provides **paraphrasing**, **humanizing** (anti-AI detection cleanup), and **proofreading** of academic and clinical manuscripts. Runs fully offline using a local rules-based engine — no API key required.

## Features

- **Paraphrase** — Rewrites text in Academic, Concise, or High-Impact styles with adjustable strength (1–5)
- **Medical Paraphrase** — Clinically-aware rewrites that preserve drug names, dosages, citations, and numerical accuracy
- **Humanize** — Removes AI writing patterns (Dr. Noora clinical style or General anti-AI cleanup)
- **Proofread** — Two-phase audit: Phase 1 detects issues (6 categories); Phase 2 applies fixes
- **Academic Vocabulary Scoring** — Measures vocabulary density against the COCA Academic Vocabulary List (3,000 lemmas)

## Quick Start

## Prerequisites
- Python 3.10+
- Windows, macOS, or Linux
- (Optional) [Ollama](https://ollama.com/) + a pulled model (e.g. `ollama pull llama3.2`) for local LLM-powered rewrites — see [Configuration](#configuration)

### Setup
```bash
# Clone with submodules
git clone --recurse-submodules https://github.com/YOUR_USER/Para_Paper.git
cd Para_Paper

# Install Python dependencies
cd backend
pip install -r requirements.txt
```

### Run
```bash
cd backend
python main.py
```

Open **http://localhost:8765** in your browser.

## Lexical Resources

The tool bundles four lexical datasets for high-quality academic and medical text processing:

| Resource | Source | Entries | Used By |
|---|---|---|---|
| **Medical Terms** | [wordlist-medicalterms-en](https://github.com/glutanimate/wordlist-medicalterms-en) | 98,119 | Medical term detection, clinical paraphrasing |
| **English Dictionary** | [english-words](https://github.com/dwyl/english-words) | 479,000 | Lexical validation in rewrites |
| **Academic Vocabulary (AVL)** | [COCA Academic Vocabulary List](https://www.academicvocabulary.info/) | 3,000 lemmas | Academic density scoring, style analysis |
| **Medical Academic Wordlist (MAWL)** | [machine_readable_wordlists](https://github.com/lpmi-13/machine_readable_wordlists) | 623 words | Medical-academic vocabulary detection |

Medical content is auto-detected when ≥10% of text vocabulary matches the medical term list (excluding common English words). When detected, the system routes through the clinical paraphrasing pipeline automatically.

## Project Structure

```
Para_Paper/
├── backend/                    # Python FastAPI server
│   ├── main.py                 # Server entry point (port 8765)
│   ├── agent_wrapper.py        # Agent orchestration + rules engine
│   ├── medical_vocab.py        # Medical term loader + synonym maps
│   ├── academic_vocab.py       # AVL/MAWL academic vocabulary loader
│   ├── english_words_loader.py # English dictionary loader
│   ├── data/                   # Bundled lexical datasets
│   │   ├── AVL.json            # Academic Vocabulary List (3K lemmas)
│   │   └── MAWL.json           # Medical Academic Word List (623 words)
│   ├── .agent/skills/          # Agent skill prompt files
│   │   ├── academic_rewording.md
│   │   ├── academic_rewording_medical.md
│   │   ├── humanizer_noora.md
│   │   ├── humanizer_general.md
│   │   └── proofreading.md
│   ├── .agent/proofreading_references/  # Reference guides
│   ├── .env                    # API key (optional — works without)
│   └── requirements.txt
├── frontend/                   # Web UI (served by backend)
│   ├── index.html
│   ├── taskpane.js
│   └── taskpane.css
├── wordlist-medicalterms-en/   # Medical word list (98K terms)
├── english-words/              # English dictionary (479K words)
├── guard-skills/               # Code-quality agent skills
├── LICENSE
└── README.md
```

## How It Works

### Paraphrase
Select a style: **Academic**, **Concise**, or **High-Impact**, and a strength (1–5). The engine applies dictionary-based synonym replacement, sentence restructuring, and style-specific transformations. For medical text, select "Medical / Clinical" mode to preserve clinical terminology.

### Humanize
- **Dr. Noora Style** — Clinical vocabulary, bracket-spacing quirks, citation patterns
- **General Anti-AI Cleanup** — Removes clichés (delve, testament, tapestry), em-dashes, formulaic transitions

### Proofread
- **Phase 1 (Diagnose)** — Scans for: undefined acronyms, overclaiming, banned transitions, promotional adjectives, importance-signaling verbs, inflated noun phrases, template shapes, tense inconsistency, low academic density
- **Phase 2 (Fix)** — Applies corrections for all detected patterns

## Configuration

The backend tries backends in this order:

1. **Ollama** (local) — if `OLLAMA_MODEL` is set and Ollama is running
2. **Gemini API** — if `GEMINI_API_KEY` is set
3. **Rules-based simulation** — always works, no dependencies

### Option 1: Ollama (local, recommended for best quality)

Pull a local model and set the environment variable:

```bash
# Install Ollama from https://ollama.com/
ollama pull llama3.2        # ~2 GB — good for paraphrasing & humanizing
# or try smaller models:
ollama pull llama3.2:1b     # ~0.7 GB — faster but lower quality
```

Then create `backend/.env`:

```
OLLAMA_MODEL=llama3.2
# Optional — defaults to http://localhost:11434
# OLLAMA_BASE_URL=http://localhost:11434
```

The Ollama model provides LLM-quality rewrites for paraphrasing, humanizing, and proofreading — running 100% locally on your machine.

### Option 2: Gemini API (cloud)

Set a `GEMINI_API_KEY` in `backend/.env`:

```
GEMINI_API_KEY=your_key_here
```

### No configuration

Without either option, all features work locally using the rules-based simulation engine.

## License

MIT

## Acknowledgments

- [glutanimate/wordlist-medicalterms-en](https://github.com/glutanimate/wordlist-medicalterms-en) — Medical vocabulary
- [dwyl/english-words](https://github.com/dwyl/english-words) — English dictionary
- [Gardner & Davies (COCA) AVL](https://www.academicvocabulary.info/) — Academic vocabulary
- [lpmi-13/machine_readable_wordlists](https://github.com/lpmi-13/machine_readable_wordlists) — Machine-readable academic wordlists
- [paper-revision-editor](https://github.com/anomalyco/paper-revision-editor) — Proofreading patterns and editing principles
