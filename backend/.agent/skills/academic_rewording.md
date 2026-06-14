---
name: academic-rewording
description: A skill to paraphrase and rewrite text into Academic, Concise, and High-Impact variations with deep structural transformation.
---

# Academic Rewording Skill

Use this skill when you need to offer multiple stylistic choices for a selected sentence or paragraph. You must provide exactly three options: Academic/Formal, Concise/Direct, and High-Impact/Persuasive.

You MUST significantly restructure the text — do not merely swap synonyms or adjust tone. Every sentence should be structurally different from the original while preserving the core meaning.

## Core Transformation Rules (apply to ALL options)

1. **Restructure every sentence**: Reorder clauses, change sentence openings, use different grammatical structures (e.g., convert participle phrases to full clauses, use cleft sentences, invert subject-verb order where appropriate).
2. **Vary sentence boundaries**: Split long sentences into shorter ones; combine short sentences where it improves flow.
3. **Change voice deliberately**: Convert passive ↔ active voice based on the option's requirements.
4. **Replace low-information phrases**: Convert vague/generic phrasing into specific, substantive language.

## 1. Option Definitions

### Option A: Academic / Formal
* **Tone**: Authoritative, scholarly, objective, and precise.
* **Grammar**: Third-person perspective (or active researcher voice "we aimed to"), passive voice when explaining methodology, complex sentence structures showing logical progression.
* **Vocabulary**: High-tier academic words. Instead of "show", use "reflect", "indicate", "exhibit", "substantiate", "elucidate". Avoid casual verbs or colloquialisms.
* **Structure**: Ensure logical flow, clear causal relationships, and formal transitions (e.g., *consequently*, *furthermore*, *nevertheless*, *notably*).
* **Structural changes**: Open with contextualizing phrases, use nominalization, front subordinate clauses.

### Option B: Concise / Direct
* **Tone**: Direct, professional, and dense.
* **Rule**: Say the exact same thing in the fewest words possible.
* **Vocabulary**: Simple, clear nouns and verbs. Avoid qualifiers, fillers, or hedging (e.g. convert "it could be argued that" to direct assertions).
* **Fixes**: Remove phrases like "in order to" (use "to"), "due to the fact that" (use "because"), "at this point in time" (use "now").
* **Structural changes**: Eliminate redundant clauses, use appositives, compress multi-clause sentences into single assertive statements.

### Option C: High-Impact / Persuasive
* **Tone**: Active, engaging, strong, and highly readable.
* **Grammar**: Active voice is mandatory. Start sentences with the primary subject or a powerful verb.
* **Style**: Use vivid, direct, and convincing statements. Highlight the core result or meaning immediately. Avoid passive structures.
* **Structural changes**: Front-load key findings, use periodic sentences for emphasis, employ parallel structure for rhetorical effect.

## Transformation Intensity

The user may specify a strength level (1-5):

- **1-2 (Light)**: Moderate vocabulary upgrades and minor structural tweaks while keeping the original sentence flow mostly intact.
- **3 (Moderate)**: Clear restructuring of most sentences — change clause order, vary openings, split/combine judiciously.
- **4-5 (Aggressive)**: Complete transformation — every sentence must be rebuilt from the ground up. Change narrative flow, reorder information presentation, use entirely different grammatical scaffolding while preserving meaning.

---

## Output Format
When executing this skill, your response must be structured as a JSON block or a clean parsable structure containing:
1. **Academic**: The academically reworded text.
2. **Concise**: The concise text.
3. **High-Impact**: The high-impact text.
