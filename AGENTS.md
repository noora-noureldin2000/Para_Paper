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

- Python 3.10+ with FastAPI + uvicorn
- Backend lives in `backend/`; frontend (static HTML/JS/CSS) in `frontend/`
- All lexical resources are preloaded at module import time in `agent_wrapper.py`
- The rules-based simulation engine (`run_local_simulation()`) is the primary execution path — Gemini API is optional fallback
- Never bundle data files inside `backend/data/` without updating `.gitignore`
- No hardcoded paths — use `os.path.join(os.path.dirname(os.path.abspath(__file__)), ...)`
