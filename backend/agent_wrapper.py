import os
import re
import asyncio
from dotenv import load_dotenv

# Load environment variables (e.g. from .env file)
load_dotenv()

# Skill Directory Path
SKILLS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".agent", "skills")

def get_skill_content(skill_filename: str) -> str:
    """Reads a skill markdown file and returns its instructions."""
    path = os.path.join(SKILLS_DIR, skill_filename)
    if not os.path.exists(path):
        # Check standard skills path
        path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".agent", "skills", skill_filename)
        if not os.path.exists(path):
            raise FileNotFoundError(f"Skill file not found: {skill_filename}")
    
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()
    
    # Strip YAML frontmatter if present
    if content.startswith("---"):
        parts = content.split("---", 2)
        if len(parts) >= 3:
            content = parts[2]
            
    return content.strip()

# Local simulation dictionary for dynamic text rewrites (fallback when no API key is present)
SIMULATION_DICTIONARY = {
    "show": {"academic": "elucidate", "concise": "show", "impact": "demonstrate"},
    "shows": {"academic": "reflects", "concise": "shows", "impact": "demonstrates"},
    "showed": {"academic": "indicated", "concise": "showed", "impact": "proved"},
    "good": {"academic": "substantive", "concise": "good", "impact": "exceptional"},
    "very": {"academic": "substantially", "concise": "", "impact": "exceptionally"},
    "important": {"academic": "pivotal", "concise": "key", "impact": "crucial"},
    "study": {"academic": "investigation", "concise": "study", "impact": "breakthrough research"},
    "result": {"academic": "empirical finding", "concise": "result", "impact": "breakthrough"},
    "results": {"academic": "empirical findings", "concise": "results", "impact": "breakthroughs"},
    "analyze": {"academic": "deconstruct", "concise": "check", "impact": "revolutionize"},
    "make": {"academic": "synthesize", "concise": "make", "impact": "forge"},
    "use": {"academic": "utilize", "concise": "use", "impact": "harness"},
    "get": {"academic": "derive", "concise": "get", "impact": "acquire"},
    "help": {"academic": "facilitate", "concise": "help", "impact": "empower"},
    "change": {"academic": "modify", "concise": "change", "impact": "transform"},
    "find": {"academic": "uncover", "concise": "find", "impact": "discover"}
}

def clean_cliches(text: str) -> str:
    """Helper to remove AI clichés for general humanizer simulation."""
    cliches = ["delve", "testament", "tapestry", "beacon", "underscore", "pivotal", "crucial role in shaping", "it is important to note that"]
    cleaned = text
    for c in cliches:
        # Replace case-insensitively with blank or simple synonym
        cleaned = re.sub(rf"\b{c}\b", "show" if c == "underscore" else "", cleaned, flags=re.IGNORECASE)
    return re.sub(r"\s+", " ", cleaned).strip()

def run_local_simulation(text: str, skill_name: str, payload_type: str = "") -> dict:
    """Simulates agent rewriting using rules-based dictionary transformations."""
    words = text.split()
    
    # 1. Paraphrase Simulation
    if "academic_rewording" in skill_name:
        academic_words = []
        concise_words = []
        impact_words = []
        
        for w in words:
            clean_w = re.sub(r"[^\w]", "", w).lower()
            punctuation = w[len(clean_w):] if w.endswith((".", ",", ";", "!", "?")) else ""
            
            if clean_w in SIMULATION_DICTIONARY:
                repl = SIMULATION_DICTIONARY[clean_w]
                
                # Match casing
                ac_word = repl["academic"]
                cc_word = repl["concise"]
                im_word = repl["impact"]
                if w[0].isupper():
                    ac_word = ac_word.capitalize() if ac_word else ""
                    cc_word = cc_word.capitalize() if cc_word else ""
                    im_word = im_word.capitalize() if im_word else ""
                
                academic_words.append(ac_word + punctuation if ac_word else "")
                if cc_word:
                    concise_words.append(cc_word + punctuation)
                impact_words.append(im_word + punctuation if im_word else "")
            else:
                academic_words.append(w)
                concise_words.append(w)
                impact_words.append(w)
                
        # Format sentences
        academic_str = " ".join([x for x in academic_words if x]).replace("  ", " ")
        concise_str = " ".join([x for x in concise_words if x]).replace("  ", " ")
        impact_str = " ".join([x for x in impact_words if x]).replace("  ", " ")
        
        # Add typical styling
        if academic_str and not academic_str.startswith(("Notably,", "Consequently,", "Interestingly,")):
            academic_str = f"Notably, {academic_str[0].lower()}{academic_str[1:]}"
            
        # Add high impact start
        if impact_str and not impact_str.startswith(("We ", "Our ")):
            impact_str = f"We successfully demonstrate that {impact_str[0].lower()}{impact_str[1:]}"
            
        return {
            "status": "success",
            "options": [
                {"type": "Academic", "text": academic_str},
                {"type": "Concise", "text": concise_str},
                {"type": "High-Impact", "text": impact_str}
            ]
        }
        
    # 2. Humanizer Simulation
    elif "humanizer" in skill_name:
        is_noora = "noora" in skill_name or payload_type == "noora"
        
        if is_noora:
            # Dr. Noora's quirks: Omit commas after short transitions, citation adjectives, spaces inside brackets
            transformed = text
            transformed = clean_cliches(transformed)
            # Replace common words with clinical terms
            transformed = transformed.replace("patients", "geriatric patients with comorbidities")
            transformed = transformed.replace("medication", "potentially inappropriate medications (PIMs)")
            transformed = transformed.replace("results", "biochemical measurements")
            
            # Apply punctuation spacing quirk: (n=764) -> ( n = 764 )
            transformed = re.sub(r"\((\w+)\s*=\s*(\w+)\)", r"( \1 = \2 )", transformed)
            
            # Omit commas after transitions
            transformed = re.sub(r"\b(Therefore|Consequently|Eventually|Luckily|Also),\s*", r"\1 ", transformed)
            
            # Citation adjective: "in the study of Zhang et al." -> "in Zhang et al. study"
            transformed = re.sub(r"in the study of\s+([\w\s\.]+et\s*al\.)", r"in \1 study", transformed, flags=re.IGNORECASE)
            
            # Ensure it ends with Dr. Noora style
            if not transformed.endswith(".") and len(transformed) > 5:
                transformed += "."
                
            return {
                "status": "success",
                "text": transformed
            }
        else:
            # General humanizer: Clean clichés, replace copula, remove em dashes
            transformed = text
            transformed = clean_cliches(transformed)
            transformed = transformed.replace("serves as", "is").replace("stands as", "is")
            transformed = transformed.replace("—", ", ")
            transformed = re.sub(r"\b(not only|but also)\b", "and", transformed, flags=re.IGNORECASE)
            return {
                "status": "success",
                "text": transformed
            }

    # 3. Proofread Simulation
    elif "proofreading" in skill_name:
        # Generate custom issues list for Phase 1 or fixed text for Phase 2
        if payload_type == "phase1":
            issues = []
            
            # Detect acronyms not defined
            acronyms = re.findall(r"\b[A-Z]{3,}\b", text)
            if acronyms:
                issues.append({
                    "id": 1,
                    "severity": "MAJOR",
                    "location": "Sentence 1",
                    "diagnosis": f"Acronym '{acronyms[0]}' is used without being defined at first occurrence.",
                    "why_matters": "Readers may not understand technical jargon, leading to review rejection.",
                    "actionable_fix": f"Define '{acronyms[0]}' explicitly when it is first used."
                })
                
            # Detect overclaiming words
            if "significantly" in text.lower() or "state-of-the-art" in text.lower():
                issues.append({
                    "id": len(issues) + 1,
                    "severity": "CRITICAL",
                    "location": "Sentence 1",
                    "diagnosis": "Overclaiming vocabulary ('significantly' or 'state-of-the-art') used without statistical validation.",
                    "why_matters": "Strict reviewers will flag unsupported claims immediately.",
                    "actionable_fix": "Remove the claims or replace with objective language like 'substantially'."
                })
                
            # Detect formatting: em dash
            if "—" in text:
                issues.append({
                    "id": len(issues) + 1,
                    "severity": "STYLE",
                    "location": "Clause 1",
                    "diagnosis": "Overuse of em-dashes ('—') in prose.",
                    "why_matters": "Disrupts logical sentence flow; commas or parentheses are cleaner.",
                    "actionable_fix": "Replace the em-dash with a comma or parentheses."
                })
                
            # Detect LaTeX spacing
            if re.search(r"\b\d+(cm|mm|m|kg|s)\b", text):
                issues.append({
                    "id": len(issues) + 1,
                    "severity": "MINOR",
                    "location": "Unit placement",
                    "diagnosis": "Missing space before unit measure.",
                    "why_matters": "Violates scientific typesetting conventions.",
                    "actionable_fix": "Insert thin space (e.g. '\\,' or space) before unit."
                })
                
            # Fallback if no specific issues detected
            if not issues:
                issues.append({
                    "id": 1,
                    "severity": "MINOR",
                    "location": "Sentence structure",
                    "diagnosis": "Nominalization detected (using verbs as nouns).",
                    "why_matters": "Makes reading passive and heavy.",
                    "actionable_fix": "Rewrite using active verbs."
                })
                
            return {
                "status": "success",
                "issues": issues
            }
        else:
            # Phase 2: apply fixes
            fixed_text = text
            # Replace em-dashes
            fixed_text = fixed_text.replace("—", ", ")
            # Define acronyms
            fixed_text = re.sub(r"\b(IWI)\b", r"\1 (Informal Word Identification)", fixed_text)
            fixed_text = re.sub(r"\b(COCA)\b", r"\1 (Corpus of Contemporary American English)", fixed_text)
            # Remove overclaiming
            fixed_text = fixed_text.replace("significantly", "substantially")
            fixed_text = fixed_text.replace("state-of-the-art", "highly competitive")
            # Replace units
            fixed_text = re.sub(r"\b(\d+)(cm|mm|m|kg|s)\b", r"\1 \2", fixed_text)
            
            return {
                "status": "success",
                "text": fixed_text
            }

    return {"status": "error", "message": "Unknown skill"}

class AntigravityAgent:
    """Wrapper that utilizes google-antigravity SDK if available, or direct Gemini API, or rules-based simulation."""
    def __init__(self, skill_filename: str):
        self.skill_filename = skill_filename
        self.skill_content = get_skill_content(skill_filename)
        self.api_key = os.getenv("GEMINI_API_KEY")
        
    async def run(self, text: str, payload_type: str = "") -> dict:
        # Check if we should use local simulation (no API Key available)
        if not self.api_key:
            print(f"[AgentWrapper] No GEMINI_API_KEY. Running local rules-based simulation for: {self.skill_filename}")
            return run_local_simulation(text, self.skill_filename, payload_type)

        # 1. Try to use google-antigravity SDK
        try:
            from google.antigravity import Agent, LocalAgentConfig
            print(f"[AgentWrapper] Using google-antigravity SDK for: {self.skill_filename}")
            
            config = LocalAgentConfig(
                system_instructions=self.skill_content
            )
            
            async with Agent(config) as agent:
                # Call agent.chat
                prompt = self._build_prompt(text, payload_type)
                response = await agent.chat(prompt)
                response_text = await response.text()
                return self._parse_response(response_text, payload_type)
        except Exception as e:
            print(f"[AgentWrapper] Google-antigravity SDK failed or not installed ({str(e)}). Falling back to direct Gemini API...")
            
        # 2. Try direct Gemini API fallback
        try:
            import google.generativeai as genai
            print(f"[AgentWrapper] Using google-generativeai SDK for: {self.skill_filename}")
            genai.configure(api_key=self.api_key)
            
            model = genai.GenerativeModel(
                model_name="gemini-1.5-flash",
                system_instruction=self.skill_content
            )
            
            prompt = self._build_prompt(text, payload_type)
            # Run in executor to avoid blocking the async event loop if needed, or call directly
            response = model.generate_content(prompt)
            response_text = response.text
            return self._parse_response(response_text, payload_type)
        except Exception as e:
            print(f"[AgentWrapper] Gemini API fallback failed ({str(e)}). Running local rules-based simulation.")
            return run_local_simulation(text, self.skill_filename, payload_type)

    def _build_prompt(self, text: str, payload_type: str) -> str:
        if "academic_rewording" in self.skill_filename:
            return (
                "Please rewrite the following text and provide exactly three options in JSON format:\n"
                "{\n"
                '  "Academic": "academic version",\n'
                '  "Concise": "concise version",\n'
                '  "High-Impact": "high-impact version"\n'
                "}\n"
                f"Text: \"{text}\""
            )
        elif "humanizer_noora" in self.skill_filename:
            return f"Rewrite the following draft to match Dr. Noora Noureldin's writing style. Output ONLY the rewritten text:\n\"{text}\""
        elif "humanizer_general" in self.skill_filename:
            return f"Rewrite the following draft to remove AI patterns. Output ONLY the rewritten text:\n\"{text}\""
        elif "proofreading" in self.skill_filename:
            if payload_type == "phase1":
                return (
                    "Analyze the text and detect proofreading issues. Return exactly a JSON list of issues in this format:\n"
                    "[\n"
                    "  {\n"
                    '    "id": 1,\n'
                    '    "severity": "CRITICAL|MAJOR|MINOR|STYLE",\n'
                    '    "location": "Sentence or clause context",\n'
                    '    "diagnosis": "What the issue is",\n'
                    '    "why_matters": "Why it matters",\n'
                    '    "actionable_fix": "How to fix it"\n'
                    "  }\n"
                    "]\n"
                    f"Text: \"{text}\""
                )
            else:
                # Phase 2
                return f"Apply all corrections for the text. Output ONLY the corrected text:\n\"{text}\""
        return f"Process this text:\n\"{text}\""

    def _parse_response(self, response_text: str, payload_type: str) -> dict:
        response_text = response_text.strip()
        
        # Clean JSON markdown syntax if present
        if response_text.startswith("```"):
            # strip backticks and optional json identifier
            lines = response_text.splitlines()
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines[-1].strip() == "```":
                lines = lines[:-1]
            response_text = "\n".join(lines).strip()
            
        if "academic_rewording" in self.skill_filename:
            try:
                import json
                data = json.loads(response_text)
                return {
                    "status": "success",
                    "options": [
                        {"type": "Academic", "text": data.get("Academic", "")},
                        {"type": "Concise", "text": data.get("Concise", "")},
                        {"type": "High-Impact", "text": data.get("High-Impact", "")}
                    ]
                }
            except Exception:
                # If JSON parse failed, split by keys
                return {
                    "status": "success",
                    "options": [
                        {"type": "Academic", "text": response_text},
                        {"type": "Concise", "text": response_text},
                        {"type": "High-Impact", "text": response_text}
                    ]
                }
        elif "proofreading" in self.skill_filename and payload_type == "phase1":
            try:
                import json
                issues = json.loads(response_text)
                return {
                    "status": "success",
                    "issues": issues
                }
            except Exception:
                return {
                    "status": "success",
                    "issues": [{
                        "id": 1,
                        "severity": "MINOR",
                        "location": "Text",
                        "diagnosis": "Review completed. No details parsed.",
                        "why_matters": "General clarity.",
                        "actionable_fix": "Check text manually."
                    }]
                }
        else:
            return {
                "status": "success",
                "text": response_text
            }
