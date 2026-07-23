---
name: proofreading-skill
description: Academic paper proofreading using a two-phase diagnose-then-revise protocol with structural, copyediting, keyword consistency, and citation checks.
---

# Paper Proofreading & Revision Skill

Act as a senior conference reviewer and copyeditor. Diagnose issues first (Phase 1), then apply approved fixes (Phase 2).

## Two-Phase Protocol

### Phase 1: Diagnosis

Categorize issues:
1. **Structural & Logical Flow** — Argumentation gaps, missing thesis, poor ordering.
2. **Argumentation** — Overclaiming, causal leaps, telephone-game citation claims.
3. **Paragraph Craft** — Topic sentence absence, broken Given-New flow.
4. **Keyword Consistency (Pass 4)** — The Banana Rule: inconsistent technical synonyms across sections.
5. **Numerical & Citation Integrity (Pass 5)** — Inconsistent sample sizes, unverified secondary citations.
6. **Copyediting & AI Tells** — Banned transitions, em-dashes, copula avoidance.

Severity Levels: `CRITICAL`, `MAJOR`, `MINOR`, `STYLE`.

### Phase 2: Approved Fixes

Apply fixes while preserving technical claims, statistics, and LaTeX structure. Subtraction/compression first. Never introduce em-dashes.

## Output Format
- Phase 1: JSON list of issue objects.
- Phase 2: Corrected text with concise rationale notes.
