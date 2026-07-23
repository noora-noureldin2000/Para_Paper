# Para Paper V2

An AI-powered scientific writing assistant built with Streamlit providing **Paraphrasing**, **Anti-AI Humanizing**, **Two-Phase Proofreading**, **5-Pass Manuscript Review**, **Autonomous Paper Generation**, and **Academic Vocabulary Analysis**.

## Features

- **Paraphrase** — Rewrites text into Academic, Concise, or High-Impact styles with clinical term preservation options
- **Humanize** — Removes AI writing patterns (Dr. Noora clinical style or General anti-AI cleanup using Wikipedia's 29-pattern taxonomy)
- **Proofread** — 2-phase audit: Phase 1 detects issues; Phase 2 applies approved fixes
- **Manuscript Review** — 5-pass audit (Clutter, Active Voice, Sentence Architecture, Terminology, Citation Integrity)
- **Write Paper** — Autonomous draft generation & peer-review scoring
- **Vocabulary Analysis** — Evaluates vocabulary density against the COCA Academic Vocabulary List (AVL) and Medical Academic Word List (MAWL)

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Run Application

```bash
streamlit run streamlit_app.py
```

Open **http://localhost:8501** in your browser.

## API Key & Model Configuration

1. In the sidebar, select your provider: **Gemini API** or **OpenRouter**.
2. Paste your API Key (stored session-only, never saved to disk).
3. If using OpenRouter, specify any model ID (defaults to `openrouter/auto`).

### Optional Local Ollama Setup (Llama 3.2)

1. Download and install [Ollama](https://ollama.com/).
2. Pull the Llama 3.2 model:
   ```bash
   ollama pull llama3.2
   ```
3. In the sidebar, select **Ollama (Local)** as the provider.

## Deployment to Streamlit Cloud

1. Push this repository to GitHub.
2. Sign in to [Streamlit Community Cloud](https://share.streamlit.io/).
3. Click **Create app**, select your repository, and set the main file path to:
   ```text
   streamlit_app.py
   ```
4. Click **Deploy**!
