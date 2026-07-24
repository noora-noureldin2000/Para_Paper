# Agent Instructions for Para_Paper

## Guard Skills

This project includes guard skills under `guard-skills/` that AI coding agents should apply after writing or editing code:

| Skill | When to Use |
|---|---|
| `guard-skills/clean-code-guard/SKILL.md` | After any code edit — review for naming, structure, SOLID, DRY, AI failure modes |
| `guard-skills/docs-guard/SKILL.md` | After editing documentation or README files |
| `guard-skills/test-guard/SKILL.md` | After adding or modifying Python source files — ensure tests exist |

### Workflow

1. **Before writing**: Read `AGENTS.md` (this file), one neighbor of the file to edit, and match existing conventions
2. **After writing**: Apply `clean-code-guard` on the diff — fix violations (unused imports, generic names, broad error handling, hardcoded returns)
3. **If docs changed**: Apply `docs-guard`
4. **If source code changed**: Apply `test-guard`

## Project Conventions

- Python 3.10+ with Streamlit
- Primary application entry point: `streamlit_app.py` (`streamlit run streamlit_app.py`)
- All backend logic lives in `backend/`
- All lexical resources are preloaded at module import time in `agent_wrapper.py`
- Backend priority: **User Provider (Gemini / OpenRouter API)** → **Ollama (Optional Local)** → **Rules-based simulation (Fallback)**
- API keys are session-only in Streamlit, never hardcoded or saved to disk
- No `.exe` builds — deliver as web app only

### Streamlit UI rules

- Widgets bind to `st.session_state` keys — never combine `value=` with `key=` on the same widget (keyed widgets ignore `value=` after first render → stale output bug)
- Mutate widget-keyed state only inside `on_click` callbacks (callbacks run before the rerun, where such writes are legal)
- Non-widget results live in plain session keys and render via `st.markdown` / `st.json` / `st.metric`
