# humanizer-Noora ✍️🏥

A custom style guide and developer skill profile designed to train AI systems to write, rewrite, and edit academic and clinical research documents in the precise, authentic writing style of **Dr. Noora Noureldin**.

This repository packages her authentic writing habits, clinical voice, and structural methodology. Generic AI models often produce overly dry, robotic, or hyper-structured text (overusing clichés like *delve, testament, tapestry, pivotal*, etc.). This skill translates such outputs into a flowing, authoritative, human-sounding scientific draft that preserves clinical rigor, matches Dr. Noora's personal style markers, and naturally bypasses AI detection tools (like Turnitin).

---

## 📖 Table of Contents
1. [What This Skill Offers](#-what-this-skill-offers)
2. [Repository Directory Structure](#-repository-directory-structure)
3. [Setup & Installation](#-setup--installation)
    - [Claude Code Integration](#claude-code-integration)
    - [OpenCode Integration](#opencode-integration)
4. [How to Use](#-how-to-use)
    - [Method 1: Custom Claude Code Skill Command](#method-1-custom-claude-code-skill-command)
    - [Method 2: Standalone Style Guide Prompting (Web UIs)](#method-2-standalone-style-guide-prompting-web-uis)
    - [Method 3: Direct API System Prompt Integration](#method-3-direct-api-system-prompt-integration)
5. [Key Style Principles](#-key-style-principles)
6. [Before & After Translation Examples](#-before--after-translation-examples)
7. [Author & Biography](#-author--biography)

---

## ✨ What This Skill Offers

* **Clinical & Pharmaceutical Precision**: Vocabulary guidance tailored to clinical settings, polypharmacy, and therapeutic guidelines.
* **Transition Phrasing**: Rules dictating how to guide readers using specific logical connectors rather than generic AI connectors.
* **Natural Flow & Voice Shifting**: Balancing active voice (for goals and author intent) and passive voice (for methodologies and data retrieval).
* **Authentic Human Drafting Quirks**: Specific rules that incorporate natural writing anomalies (like omitting commas after brief introductory transitions, direct citation-to-adjective phrasing, and custom statistical bracket spacing) to successfully bypass AI detection tools.

---

## 📁 Repository Directory Structure

```directory
Mega_Medical_writer_Noora/
├── humanizer-Noora.md        # Standalone style guide containing all rules & examples
├── humanizer-Noora/
│   ├── SKILL.md              # Claude Code custom skill config and core instructions
│   └── README.md             # This folder-specific usage guide
├── Samples_Noora_writing/    # Authentic source writing samples used to train the profile
└── README.md                 # Main repository documentation file
```

---

## ⚙️ Setup & Installation

To register this custom skill in your command-line agent tool:

### Claude Code Integration

1. Create the local Claude Code skills directory if it does not already exist:
   ```bash
   mkdir -p ~/.claude/skills
   ```
2. Copy the `humanizer-Noora` directory into the Claude Code skills directory:
   ```bash
   cp -r D:/GitHub/Mega_Medical_writer_Noora/humanizer-Noora ~/.claude/skills/humanizer-Noora
   ```
3. Claude Code will automatically detect and load the skill on its next startup.

### OpenCode Integration

1. Create the local OpenCode skills directory:
   ```bash
   mkdir -p ~/.config/opencode/skills
   ```
2. Copy the `humanizer-Noora` directory into the OpenCode skills directory:
   ```bash
   cp -r D:/GitHub/Mega_Medical_writer_Noora/humanizer-Noora ~/.config/opencode/skills/humanizer-Noora
   ```

---

## 🚀 How to Use

Depending on your workflow, you can use these assets in three different ways:

### Method 1: Custom Claude Code Skill Command
Once installed as a skill in Claude Code, you can run:
```bash
/humanizer-Noora
```
Or instruct Claude Code directly in your project:
> *"Please humanize the draft in `draft_paper.md` using the humanizer-Noora skill."*

### Method 2: Standalone Style Guide Prompting (Web UIs)
If you are using web interfaces like **ChatGPT** or the **Claude.ai web console**, you can copy the contents of the style guide at [humanizer-Noora.md](file:///D:/GitHub/Mega_Medical_writer_Noora/humanizer-Noora.md) and paste it before your text with this prompt:

```text
Please read the writing style profile below. Once understood, rewrite the provided text to exactly match Dr. Noora's tone, vocabulary, transition style, sentence structures, and drafting quirks.

[Paste content of humanizer-Noora.md here]

---
Text to humanize:
[Your scientific/clinical draft here]
```

### Method 3: Direct API System Prompt Integration
When building custom medical writing agents via Python or Node.js APIs, append this system prompt configuration block:

```python
system_prompt = """
You are acting under the 'humanizer-Noora' writing profile.
Rewrite and edit all text inputs to align with Dr. Noora Noureldin's writing style:
1. Use clinical terminology (e.g., 'polypharmacy', 'comorbidities', 'tolerability', 'PIMs').
2. Apply transitions like 'Therefore' (without a following comma), 'On one hand/On the other hand', 'Consequently', and 'Notably'.
3. Treat citations as direct adjectives modifying 'study' (e.g., "in Zhang et al. study").
4. Format statistics with bracket spacing, e.g., "( n = 764)" and "(p-value < 0.01)".
5. Avoid standard AI words (e.g., 'delve', 'testament', 'tapestry', 'it is important to note').
6. Omit commas after short introductory transition adverbs (e.g., "Also the advertisement...", "Eventually 150 articles...").
"""
```

---

## 📝 Key Style Principles

| Dimension | Guidance & Rules | Examples |
| :--- | :--- | :--- |
| **Tone** | Authoritative, scholarly, clinical yet humanly organic. | *Avoids sterile, robotic templates.* |
| **Vocabulary** | Specific clinical metrics, drug parameters, and research methods. | *polypharmacy, comorbidities, glycemic control, tolerability, seroconversion.* |
| **Transitions** | Natural connectors indicating contrast, consequence, and addition. | *On one hand/On the other hand, Consequently, Notably, Luckily.* |
| **Human Quirks** | Intentionally omitted commas after brief words, natural subject-verb slips. | *Also the advertisement... Eventually 150 articles...* |
| **Formatting** | Space-separated bracketed statistics and plain citations. | *( n = 764), (p-value < 0.01), in Zhang et al. study.* |

---

## 🔄 Before & After Translation Examples

### Example 1: Literature Introduction
* **Before (AI)**:
  > *"It is crucial to examine medication adherence in the elderly because they take many drugs and have chronic diseases."*
* **After (Dr. Noora)**:
  > *"Understanding medication adherence in elderly individuals is crucial since they make up a larger share of the population suffering from chronic diseases and various morbidities."*

### Example 2: Study Objectives
* **Before (AI)**:
  > *"Therefore, we designed this study to analyze the obstacles to compliance in older adults."*
* **After (Dr. Noora)**:
  > *"Therefore this study sets out to determine the specific barriers to medication adherence in older adults."*

### Example 3: Clinical Contrast
* **Before (AI)**:
  > *"Furthermore, doctors often prescribe inappropriate medications to geriatric patients despite clinical guidelines."*
* **After (Dr. Noora)**:
  > *"Despite the presence of plentiful evidence, some physicians are still prescribing PIMs anyways and they continue to utilize them as fist-line drugs of choice in a vulnerable patients like the elderly."*

### Example 4: Statistical Results
* **Before (AI)**:
  > *"The study showed that female patients had a higher rate of vaccine side effects than male patients."*
* **After (Dr. Noora)**:
  > *"Females were found to be more susceptible to the adversities of COVID-19 vaccination."*

### Example 5: Methodology
* **Before (AI)**:
  > *"We collected the data for this literature review from databases such as PubMed and Elsevier."*
* **After (Dr. Noora)**:
  > *"Collecting data needed for completing this literature review were retrieved from well-known scientific databases including: 'PubMed', and 'Elsevier'."*

---

## 👩‍🔬 Author & Biography

**Dr. Noora Noureldin** is a pharmacist, medical writer, and clinical researcher. 
* **Education**: Master’s in Clinical Nutrition (Honors) from Suez Canal University; B.Pharm (Honors) from Ajman University.
* **Expertise**: Scientific writing, biostatistics, research methodology, and pharmaceutical mentoring.
* **Publications**: Peer-reviewed articles in high-impact Q1 and Q2 journals.
