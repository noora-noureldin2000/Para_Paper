---
name: medical-rewording
description: A skill to paraphrase clinical, pharmaceutical, and biomedical text into Academic, Concise, and High-Impact variations with medical terminology preservation.
---

# Medical Academic Rewording Skill

Use this skill when you need to paraphrase medical, clinical, or pharmaceutical text. You must provide exactly three options: Academic/Formal, Concise/Direct, and High-Impact/Persuasive.

You MUST significantly restructure the text while preserving clinical accuracy and medical terminology. Never change drug names, dosages, anatomical terms, or quantitative clinical data.

## Core Medical Transformation Rules

1. **Preserve clinical meaning**: Do not alter numerical values, drug names, dosages, routes of administration, or statistical results.
2. **Maintain medical terminology**: Keep specialized clinical vocabulary (e.g., polypharmacy, comorbidities, glycemic control, pharmacokinetics).
3. **Citation integrity**: Preserve all citations, references, and clinical trial identifiers.
4. **Restructure with medical context**: Reorder clauses and vary sentence openings while keeping medical logic intact.

## 1. Option Definitions

### Option A: Academic / Formal (Medical)
* **Tone**: Authoritative, evidence-based, scholarly, and clinically precise.
* **Grammar**: Third-person, passive voice for methods ("patients were enrolled"), active for conclusions ("these data suggest").
* **Vocabulary**: Tier-1 clinical terminology. Use "demonstrate" over "show", "manifest" over "appear", "ameliorate" over "improve". Use formal medical descriptors.
* **Transitions**: "Consequently", "Furthermore", "Notably", "Clinically", "In this cohort", "Of particular significance".
* **Structural changes**: Front-load clinical context, nominalize where appropriate ("the administration of" vs "giving").

### Option B: Concise / Direct (Medical)
* **Tone**: Direct, professional, dense clinical writing.
* **Rule**: Convey the same clinical information in the fewest words possible without sacrificing precision.
* **Vocabulary**: Standard medical abbreviations after definition (RCT, ICU, PIMs) are acceptable. Remove hedging ("it may be possible that" -> "the treatment may").
* **Fixes**: "in order to assess" -> "to assess", "due to the fact that" -> "because", "a majority of" -> "most".
* **Structural changes**: Eliminate redundant clinical descriptors, use tabular thinking in prose.

### Option C: High-Impact / Persuasive (Medical)
* **Tone**: Active, compelling, clinically urgent.
* **Grammar**: Active voice preferred. Start with the clinical finding or implication.
* **Vocabulary**: Strong claims when supported by data. "We demonstrate", "Our findings reveal", "This trial establishes".
* **Structural changes**: Front-load the key clinical outcome, use parallel structure for comparative results, end with clinical implication.

## Transformation Intensity

The user may specify a strength level (1-5):

- **1-2 (Light)**: Moderate vocabulary upgrades, minor structural changes. Keep clinical flow intact.
- **3 (Moderate)**: Clear restructuring of sentences while preserving medical logic and terminology.
- **4-5 (Aggressive)**: Complete transformation. Rebuild every sentence with entirely different grammatical structure while preserving all clinical data points and meaning.

---

## Output Format
Your response must be structured as a JSON block or clean parsable structure containing:
1. **Academic**: The medically-academic reworded text.
2. **Concise**: The concise clinical text.
3. **High-Impact**: The high-impact clinical text.
