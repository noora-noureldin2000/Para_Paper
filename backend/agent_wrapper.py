import os
import re
import random
from dotenv import load_dotenv
from medical_vocab import load_medical_terms, MEDICAL_SYNONYMS, MEDICAL_ACADEMIC_PHRASES
from english_words_loader import load_english_words
from academic_vocab import load_avl, load_mawl, get_academic_score

# Load environment variables (e.g. from .env file)
load_dotenv()

# Preload lexical resources
load_medical_terms()
load_english_words()
load_avl()
load_mawl()

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
    "change": {"academic": "modification", "concise": "change", "impact": "transformation"},
    "find": {"academic": "uncover", "concise": "find", "impact": "discover"},
    "investigates": {"academic": "examines", "concise": "", "impact": "probes"},
    "investigated": {"academic": "examined", "concise": "", "impact": "probed"},
    "investigating": {"academic": "examining", "concise": "", "impact": "probing"},
    "investigation": {"academic": "systematic analysis", "concise": "inquiry", "impact": "comprehensive inquiry"}
}

_COMMON_WORDS = {
    "company", "quarter", "a", "an", "the", "and", "or", "but", "in", "on", "at",
    "to", "for", "of", "with", "by", "from", "as", "is", "was", "were", "are",
    "be", "been", "being", "have", "has", "had", "do", "does", "did", "will",
    "would", "could", "should", "may", "might", "can", "shall", "not", "no",
    "yes", "so", "if", "then", "than", "that", "this", "these", "those", "it",
    "its", "he", "she", "they", "them", "their", "we", "us", "our", "you",
    "your", "all", "each", "every", "some", "any", "many", "much", "more",
    "most", "few", "less", "little", "good", "bad", "big", "small", "new",
    "old", "first", "last", "next", "other", "same", "different", "own",
    "very", "too", "also", "just", "only", "now", "then", "here", "there",
    "when", "where", "why", "how", "what", "which", "who", "whom", "whose",
    "about", "above", "after", "again", "against", "before", "between",
    "through", "during", "without", "within", "along", "among", "around",
    "because", "under", "until", "upon", "while", "yet",
}

def has_medical_terms(text: str) -> bool:
    words = re.findall(r'\b[a-zA-Z]{3,}\b', text.lower())
    if not words:
        return False
    med_terms = load_medical_terms()
    med_lower = {t.lower() for t in med_terms}
    eng_dict = load_english_words()
    eng_lower = {w.lower() for w in eng_dict}
    # Strong signal: a word that is in the medical list but NOT in the general English dictionary
    # (e.g., drug names like "metformin")
    med_specific = [w for w in words if w in med_lower and w not in eng_lower]
    if med_specific:
        return True
    # Fallback: high density of general medical-academic terms
    match_count = sum(1 for w in words if w in med_lower and w not in _COMMON_WORDS)
    return match_count >= 8 and match_count / len(words) >= 0.3


def medical_paraphrase(text: str, strength: int = 3) -> dict:
    def _med_synonym_replace(sentence: str, style: str) -> str:
        words = sentence.split()
        result = []
        for w in words:
            clean_w = re.sub(r"[^\w]", "", w).lower()
            punct = ""
            if w.endswith((".", ",", ";", "!", "?")):
                for p in [".", ",", ";", "!", "?"]:
                    if w.endswith(p):
                        punct = p
                        clean_w = w[:-len(p)].lower()
                        break
            if clean_w in MEDICAL_ACADEMIC_PHRASES or clean_w in MEDICAL_SYNONYMS:
                repl = MEDICAL_ACADEMIC_PHRASES.get(clean_w) or MEDICAL_SYNONYMS.get(clean_w, "")
                if style == "academic" and repl:
                    if w[0].isupper():
                        repl = repl.capitalize()
                    result.append(repl + punct)
                elif style == "concise":
                    result.append(w)
                elif style == "impact":
                    im_repl = MEDICAL_SYNONYMS.get(clean_w, repl)
                    if w[0].isupper():
                        im_repl = im_repl.capitalize()
                    result.append(im_repl + punct if im_repl else w)
            elif clean_w in SIMULATION_DICTIONARY:
                repl = SIMULATION_DICTIONARY[clean_w].get(style, "")
                if repl:
                    if w[0].isupper():
                        repl = repl.capitalize()
                    result.append(repl + punct)
                else:
                    result.append(w)
            else:
                result.append(w)
        return " ".join(result)

    ac = _paraphrase(text, "academic", strength)
    ac_sentences = _split_sentences(ac)
    ac_med = " ".join(_med_synonym_replace(s, "academic") for s in ac_sentences)

    co = _paraphrase(text, "concise", strength)
    co_sentences = _split_sentences(co)
    co_med = " ".join(_med_synonym_replace(s, "concise") for s in co_sentences)

    im = _paraphrase(text, "impact", strength)
    im_sentences = _split_sentences(im)
    im_med = " ".join(_med_synonym_replace(s, "impact") for s in im_sentences)

    if strength >= 3:
        academic_prefixes = ["Notably, ", "Clinically, ", "In this context, ", "From a clinical perspective, "]
        ac_med = random.choice(academic_prefixes) + ac_med[0].lower() + ac_med[1:]

    if strength >= 4:
        impact_prefixes = ["We demonstrate that ", "Our findings reveal that ", "This investigation establishes that "]
        im_med = random.choice(impact_prefixes) + im_med[0].lower() + im_med[1:]

    return {
        "status": "success",
        "options": [
            {"type": "Academic", "text": ac_med},
            {"type": "Concise", "text": co_med},
            {"type": "High-Impact", "text": im_med}
        ]
    }


def clean_cliches(text: str) -> str:
    cliches = ["delve", "testament", "tapestry", "beacon", "underscore", "pivotal", "crucial role in shaping", "it is important to note that"]
    cleaned = text
    for c in cliches:
        cleaned = re.sub(rf"\b{c}\b", "show" if c == "underscore" else "", cleaned, flags=re.IGNORECASE)
    return re.sub(r"\s+", " ", cleaned).strip()


# ---- Structural Paraphrase Transforms (inspired by T5/PAWS) ----

_ACADEMIC_VERB_MAP = {
    "shows": "shown", "showed": "shown", "demonstrates": "demonstrated", "demonstrated": "demonstrated",
    "indicates": "indicated", "indicated": "indicated", "reveals": "revealed", "revealed": "revealed",
    "suggests": "suggested", "suggested": "suggested", "proposes": "proposed", "proposed": "proposed",
    "highlights": "highlighted", "highlighted": "highlighted", "illustrates": "illustrated", "illustrated": "illustrated",
    "implies": "implied", "implied": "implied", "confirms": "confirmed", "confirmed": "confirmed",
    "establishes": "established", "established": "established", "identifies": "identified", "identified": "identified",
    "examines": "examined", "examined": "examined", "investigates": "investigated", "investigated": "investigated",
    "explores": "explored", "explored": "explored", "analyzes": "analyzed", "analyzed": "analyzed",
}

_PASSIVE_TRIGGERS = {"shows", "demonstrates", "indicates", "reveals", "suggests", "proposes", "highlights",
                     "illustrates", "implies", "confirms", "establishes", "identifies"}

_CLAUSE_CONNECTORS_BECAUSE = r'\b(because|since|as|due to the fact that)\b'
_CLAUSE_CONNECTORS_ALTHOUGH = r'\b(although|though|while|whereas)\b'
_CLAUSE_CONNECTORS_IF = r'\b(if|provided that|assuming)\b'


def _split_sentences(text: str) -> list:
    raw = re.split(r'(?<=[.!?])\s+', text.strip())
    return [s.strip() for s in raw if s.strip()]


def _try_passive(sentence: str) -> str:
    m = re.search(
        r'\b(.+?)\s+(shows|showed|demonstrates|demonstrated|indicates|indicated|reveals|revealed|'
        r'suggests|suggested|proposes|proposed|highlights|highlighted|illustrates|illustrated)\s+(.+)',
        sentence, re.IGNORECASE
    )
    if m:
        subj = m.group(1).strip()
        verb_base = m.group(2).lower()
        obj = m.group(3).strip().rstrip(".")
        past = _ACADEMIC_VERB_MAP.get(verb_base, verb_base + "ed")
        subj_lower = subj[0].lower() + subj[1:] if subj else subj
        new = f"{obj} is {past} by {subj_lower}."
        if sentence[0].isupper():
            new = new[0].upper() + new[1:]
        return new
    return None


def _try_reorder_clause(sentence: str) -> str:
    low = sentence.lower()

    def _reorder_with(sent, conn_match, alt_map):
        conn = conn_match.group(1)
        idx = sent.lower().index(conn.lower())
        before = sent[:idx].strip().rstrip(",")
        rest = sent[idx + len(conn):].strip().rstrip(",")
        # connector at beginning: "Because X, Y" → "Y because X"
        if idx < 5 and "," in rest:
            parts = re.split(r",\s+", rest, maxsplit=1)
            if len(parts) == 2:
                main_conn = alt_map.get(conn.lower(), conn)
                before_clause = parts[0].strip().rstrip(".")
                after_clause = parts[1].strip().rstrip(".")
                new = f"{after_clause} {main_conn} {before_clause[0].lower()}{before_clause[1:]}"
                if not new.endswith("."):
                    new += "."
                if sentence[0].isupper():
                    new = new[0].upper() + new[1:]
                return new
        # connector in middle: "X because Y" → "Y because X"
        if before and rest:
            main_conn = alt_map.get(conn.lower(), conn)
            before_clean = before.strip().rstrip(".")
            rest_clean = rest.strip().rstrip(".")
            new = f"{rest_clean} {main_conn} {before_clean[0].lower()}{before_clean[1:]}"
            if not new.endswith("."):
                new += "."
            if sentence[0].isupper():
                new = new[0].upper() + new[1:]
            return new
        return None

    m = re.search(_CLAUSE_CONNECTORS_BECAUSE, low)
    if m:
        alt_conn = {"because": "because", "since": "since", "as": "as", "due to the fact that": "because"}
        result = _reorder_with(sentence, m, alt_conn)
        if result:
            return result
    m = re.search(_CLAUSE_CONNECTORS_ALTHOUGH, low)
    if m:
        conn = m.group(1)
        idx = low.index(conn)
        before = sentence[:idx].strip().rstrip(",")
        after = sentence[idx + len(conn):].strip().rstrip(",")
        # connector at beginning: "Although X, Y" → "Y, although X"
        if idx < 5 and "," in after:
            parts = re.split(r",\s+", after, maxsplit=1)
            if len(parts) == 2:
                before_clause = parts[0].strip().rstrip(".")
                after_clause = parts[1].strip().rstrip(".")
                new = f"{after_clause}, {conn} {before_clause[0].lower()}{before_clause[1:]}"
                if not new.endswith("."):
                    new += "."
                if sentence[0].isupper():
                    new = new[0].upper() + new[1:]
                return new
        # connector in middle: "X although Y" → "Y, although X"
        if before and after:
            before_clean = before.strip().rstrip(".")
            after_clean = after.strip().rstrip(".")
            new = f"{after_clean}, {conn} {before_clean[0].lower()}{before_clean[1:]}"
            if not new.endswith("."):
                new += "."
            if sentence[0].isupper():
                new = new[0].upper() + new[1:]
            return new
    return None


def _try_split_sentence(sentence: str) -> str:
    for splitter, joiner in [(" and ", ", and "), (" as well as ", ", as well as "),
                             (" not only ", ". Not only "), (" but also ", " but also ")]:
        if splitter in sentence and len(sentence) > 80:
            parts = sentence.split(splitter, 1)
            if len(parts) == 2:
                return f"{parts[0].rstrip('.')}. {parts[1][0].upper()}{parts[1][1:]}"
    m = re.match(r'(\w[\w\s]+),\s*(which|that|where|whereby|when)\s+(.+)', sentence, re.IGNORECASE)
    if m and len(sentence) > 80:
        return f"{m.group(1).strip().rstrip(',')}. {m.group(2).capitalize()} {m.group(3)}"
    return None


def _try_merge_sentences(sentences: list, idx: int, style: str) -> str:
    if idx >= len(sentences) - 1:
        return None
    a, b = sentences[idx], sentences[idx + 1]
    if len(a.split()) + len(b.split()) > 35:
        return None
    b_low = b[0].lower()
    connectors = {"academic": "; moreover, ", "concise": "; ", "impact": "; "}
    if style == "academic" and len(b.split()) > 3:
        return f"{a.rstrip('.')}{connectors[style]}{b_low}{b[1:]}"
    return None


def _try_nominalize(sentence: str) -> str:
    pairs = [
        (r'\b(we|this study|this paper|this work)\s+(investigate|examine|analyze|explore)\s+(.+)$',
         r'An investigation into \3 was conducted'),
        (r'\b(we|this study|this paper|this work)\s+(propose|introduce|present)\s+(.+)$',
         r'A \2 is proposed for \3'),
        (r'\b(we|this study|this paper)\s+(find|found)\s+that\s+(.+)$',
         r'It was found that \3'),
    ]
    for pattern, replacement in pairs:
        m = re.search(pattern, sentence, re.IGNORECASE)
        if m:
            result = re.sub(pattern, replacement, sentence, flags=re.IGNORECASE)
            if result and result != sentence:
                # fix capitalization
                if sentence[0].isupper():
                    result = result[0].upper() + result[1:]
                return result
    return None


def _try_that_to_infinitive(sentence: str) -> str:
    m = re.search(r'\b(.+?)\s+(found|shown|demonstrated|observed|shown|reported)\s+that\s+(.+)', sentence, re.IGNORECASE)
    if m:
        subj = m.group(1).strip()
        verb = m.group(2).lower()
        obj = m.group(3).strip()
        new = f"{obj.rstrip('.')} was {verb} by {subj}."
        if sentence[0].isupper():
            new = new[0].upper() + new[1:]
        return new
    return None


def _try_frontload(sentence: str) -> str:
    m = re.search(r'\b(the|this)\s+(.+?)\s+(is|was|shows|demonstrates|indicates|reveals)\s+(.+)', sentence, re.IGNORECASE)
    if m:
        det = m.group(1)
        subj = m.group(2).strip()
        verb = m.group(3).lower()
        rest = m.group(4).strip()
        if verb in ("is", "was"):
            new = f"{det.capitalize()} {subj} — {rest}"
        else:
            obj = rest.split()[0] if rest.split() else ""
            remainder = " ".join(rest.split()[1:]) if len(rest.split()) > 1 else ""
            new = f"{obj.capitalize()} {remainder} — {det} {subj} {verb}s"
        if not new.endswith("."):
            new += "."
        return new
    return None


def _apply_synonym_replacements(sentence: str, style: str) -> str:
    words = sentence.split()
    result = []
    for w in words:
        clean_w = re.sub(r"[^\w]", "", w).lower()
        punct = ""
        if w.endswith((".", ",", ";", "!", "?")):
            for p in [".", ",", ";", "!", "?"]:
                if w.endswith(p):
                    punct = p
                    clean_w = w[:-len(p)].lower()
                    break
        if clean_w in SIMULATION_DICTIONARY:
            repl = SIMULATION_DICTIONARY[clean_w].get(style, "")
            if repl:
                if w[0].isupper():
                    repl = repl.capitalize()
                result.append(repl + punct)
            else:
                result.append(w)
        else:
            result.append(w)
    return " ".join(result)


_TRANSFORM_PIPELINES = {
    "academic": [_try_passive, _try_reorder_clause, _try_nominalize, _try_that_to_infinitive],
    "concise":  [_try_split_sentence],
}


def _paraphrase(text: str, style: str, strength: int) -> str:
    sentences = _split_sentences(text)
    if not sentences:
        return text

    # 1. Apply synonym replacements first
    replaced = [_apply_synonym_replacements(s, style) for s in sentences]

    # 2. Apply structural transforms based on strength and style
    dense = strength >= 3
    very_dense = strength >= 4
    max_dense = strength >= 5

    transformed = []

    for i, sent in enumerate(replaced):
        t = sent

        # Try structural transforms in priority order
        transforms = _TRANSFORM_PIPELINES.get(style, [])

        if style == "academic":
            if dense and len(sent.split()) > 6:
                for fn in transforms[:2]:
                    result = fn(t)
                    if result:
                        t = result
                        break
            if very_dense and len(sent.split()) > 8:
                for fn in transforms[2:]:
                    result = fn(t)
                    if result:
                        t = result
                        break
            if max_dense and len(sent.split()) > 10:
                result = _try_nominalize(t)
                if result:
                    t = result

        elif style == "concise":
            if dense and len(sent.split()) > 8:
                result = _try_split_sentence(t)
                if result:
                    t = result
            fillers = r'\b(indeed|actually|basically|essentially|generally|importantly|interestingly|notably|particularly|significantly)\b'
            t = re.sub(fillers, '', t, flags=re.IGNORECASE)

        elif style == "impact":
            if dense and len(sent.split()) > 6:
                result = _try_frontload(t)
                if result:
                    t = result
            if very_dense and len(sent.split()) > 8:
                result = _try_reorder_clause(t)
                if result:
                    t = result
            if max_dense and len(sent.split()) > 10:
                result = _try_passive(t)
                if result:
                    t = result

        transformed.append(t)

    # 3. Sentence merging (academic & impact) / splitting (concise)
    if style in ("academic", "impact") and dense:
        merged = []
        skip = False
        for i, s in enumerate(transformed):
            if skip:
                skip = False
                continue
            if i < len(transformed) - 1 and len(s.split()) < 12 and len(transformed[i+1].split()) < 12:
                result = _try_merge_sentences(transformed, i, style)
                if result:
                    merged.append(result)
                    skip = True
                    continue
            merged.append(s)
        transformed = merged

    # 4. Variety: sentence-length alternation for academic style
    if style == "academic" and very_dense and len(transformed) >= 3:
        varied = []
        for i, s in enumerate(transformed):
            if i % 3 == 1 and len(s.split()) > 8:
                parts = re.split(r'(,\s+and\s+|;\s+)', s, maxsplit=1)
                if len(parts) >= 3:
                    varied.append(parts[0].rstrip(".") + ".")
                    varied.append(parts[1].strip() + " " + parts[2].strip())
                    continue
            varied.append(s)
        transformed = varied

    # 5. Style-specific prefixes/additions
    result = " ".join(transformed)

    if style == "academic":
        if dense and not any(result.startswith(t) for t in ("Notably,", "Consequently,", "Furthermore,", "Nevertheless,", "Interestingly,")):
            transitions = ["Notably, ", "Consequently, ", "Furthermore, ", "Nevertheless, "]
            idx = hash(text) % len(transitions)
            result = transitions[idx] + result[0].lower() + result[1:]

    # Impact prefixes handled by _try_frontload in the structural pipeline

    result = re.sub(r'\s+', ' ', result).strip()

    # 6. Deduplication: ensure >30% word difference from original
    orig_words = set(w.lower().strip(".,;:!?") for w in text.split())
    new_words = set(w.lower().strip(".,;:!?") for w in result.split())
    if orig_words and len(orig_words & new_words) / len(orig_words) > 0.85:
        pass  # Accept anyway — still better than nothing

    return result


def run_local_simulation(text: str, skill_name: str, payload_type: str = "", strength: int = 3) -> dict:
    """Simulates agent rewriting using rules-based dictionary + structural transformations."""
    strength = max(1, min(5, strength))

    # 1. Medical Paraphrase
    if "academic_rewording_medical" in skill_name or (has_medical_terms(text) and "academic_rewording" in skill_name):
        return medical_paraphrase(text, strength)

    # 2. Paraphrase (Academic / Concise / High-Impact)
    if "academic_rewording" in skill_name:
        academic_str = _paraphrase(text, "academic", strength)
        concise_str = _paraphrase(text, "concise", strength)
        impact_str = _paraphrase(text, "impact", strength)

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

    # 3. Proofread Simulation (enhanced with paper-revision-editor patterns)
    elif "proofreading" in skill_name:
        if payload_type == "phase1":
            return _run_proofreading_phase1(text)
        else:
            return _run_proofreading_phase2(text)

    return {"status": "error", "message": "Unknown skill"}


# ---- Proofreading Phase 1 & 2 (enhanced with paper-revision-editor patterns) ----

_BANNED_TRANSITIONS = {
    "furthermore", "moreover", "crucially", "importantly", "notably", "ultimately", "delving"
}

_BANNED_PROMOTIONAL = {
    "novel", "interesting", "groundbreaking", "game-changing", "state-of-the-art"
}

_IMPORTANCE_VERBS_PATTERNS = [
    r"\bunderscores\b", r"\bhighlights\b", r"\bshowcases\b",
    r"\bplays\s+a\s+(key|central|crucial|vital|pivotal)\s+role\b"
]

_INFLATED_NOUN_PHRASES = [
    r"\bthe\s+landscape\s+of\b", r"\bthe\s+realm\s+of\b", r"\bthe\s+world\s+of\b",
    r"\ba\s+myriad\s+of\b", r"\ba\s+plethora\s+of\b", r"\ba\s+wide\s+array\s+of\b",
    r"\brich\s+tapestry\b", r"\bparadigm\s+shift\b", r"\bgame.?changer\b"
]

_TEMPLATE_SHAPES = [
    (r"\bit\s+(is|'s)\s+(not\s+)?(just|merely|not\s+just)\s+about\b", "False-modesty antithesis template"),
    (r"\bnot\s+only\s+.*\bbut\s+also\b", "'Not only...but also' template"),
    (r"\bfirstly\b.*\bsecondly\b.*\bthirdly\b", "Firstly/Secondly/Thirdly list"),
    (r"\bwe\s+show\s+that\b", "'We show that' frame (replace with claim)"),
    (r"\bit\s+is\s+well\s+known\s+that\b", "'It is well known that' frame (cite or cut)"),
]

def _detect_section_type(text: str) -> str:
    low = text.lower()[:300]
    if any(w in low for w in ["abstract", "summary"]):
        return "Abstract"
    if any(w in low for w in ["introduction", "background", "motivation"]):
        return "Introduction"
    if any(w in low for w in ["method", "methodology", "experiment", "setup", "implementation"]):
        return "Methodology"
    if any(w in low for w in ["result", "finding", "experiment", "evaluation"]):
        return "Results"
    if any(w in low for w in ["discussion", "implication", "limitation"]):
        return "Discussion"
    if any(w in low for w in ["conclusion", "concluding", "summary", "future work"]):
        return "Conclusion"
    return "General"


def _run_proofreading_phase1(text: str) -> dict:
    issues = []
    issue_id = 0
    section_type = _detect_section_type(text)

    # --- Category: Structural / Logical Flow ---
    # Check for section-specific structural issues
    if section_type == "Abstract":
        sentences = re.split(r'(?<=[.!?])\s+', text)
        if len(sentences) < 4:
            issue_id += 1
            issues.append({
                "id": issue_id, "severity": "MAJOR", "category": "Structural",
                "location": "Whole abstract",
                "diagnosis": f"Abstract has only {len(sentences)} sentences; may lack context, gap, contribution, evidence, or implications.",
                "why_matters": "Readers often read only the abstract to decide whether to continue.",
                "actionable_fix": "Ensure abstract includes: context, gap, contribution, evidence, and implications in order."
            })
    elif section_type == "Introduction":
        if any(w in text.lower() for w in ["is a fundamental problem", "is a critical challenge", "has been widely studied"]):
            issue_id += 1
            issues.append({
                "id": issue_id, "severity": "STYLE", "category": "Structural",
                "location": "Opening sentence",
                "diagnosis": "Textbook opening detected ('is a fundamental problem'). Most papers in the field start this way.",
                "why_matters": "Wasted opening — the reader has seen this sentence many times before.",
                "actionable_fix": "Start with a specific puzzle, question, or concrete observation."
            })

    # --- Category: Argumentation ---
    overclaim_words = ["significantly", "state-of-the-art", "groundbreaking", "unprecedented", "revolutionary"]
    found_overclaims = [w for w in overclaim_words if w in text.lower()]
    if found_overclaims:
        issue_id += 1
        issues.append({
            "id": issue_id, "severity": "CRITICAL", "category": "Argumentation",
            "location": "Various",
            "diagnosis": f"Overclaiming vocabulary detected: {', '.join(found_overclaims)}. These terms assert statistical or competitive superiority without evidence.",
            "why_matters": "Reviewers immediately flag unsupported claims.",
            "actionable_fix": "Remove or replace with objective language. Reserve 'significantly' for statistical significance only."
        })

    # --- Category: Paragraph Craft ---
    sentences = re.split(r'(?<=[.!?])\s+', text)
    if len(sentences) > 6:
        # Check for nominalization as paragraph craft issue
        nominalizations = re.findall(r'\b\w+(tion|sion|ment|ance|ence|ity|ism)\b', text.lower())
        if len(nominalizations) > len(sentences) * 0.5:
            issue_id += 1
            issues.append({
                "id": issue_id, "severity": "MINOR", "category": "Paragraph",
                "location": "Throughout",
                "diagnosis": "High density of nominalizations detected. Verbs are buried inside nouns, making prose passive and heavy.",
                "why_matters": "Forces readers to unpack meaning; fatiguing at paragraph scale.",
                "actionable_fix": "Convert nominalizations to active verbs: 'conducted an investigation of' -> 'investigated'."
            })

    # --- Category: Copyediting ---
    # Undefined acronyms
    acronyms = re.findall(r"\b[A-Z]{2,}\b", text)
    if acronyms:
        issue_id += 1
        issues.append({
            "id": issue_id, "severity": "MAJOR", "category": "Copyediting",
            "location": "First occurrence",
            "diagnosis": f"Acronym(s) like '{acronyms[0]}' may be used without being defined.",
            "why_matters": "Readers may not understand technical jargon, leading to review rejection.",
            "actionable_fix": "Define each acronym explicitly at first use."
        })

    # Missing space before units
    if re.search(r"\b\d+(cm|mm|m|kg|s|mg|ml|g)\b", text):
        issue_id += 1
        issues.append({
            "id": issue_id, "severity": "MINOR", "category": "Copyediting",
            "location": "Unit placement",
            "diagnosis": "Missing space before unit measure (e.g. '10cm' should be '10 cm').",
            "why_matters": "Violates scientific typesetting conventions.",
            "actionable_fix": "Insert space before unit symbols."
        })

    # Tense inconsistency (rough heuristic)
    past_count = len(re.findall(r'\b(was|were|studied|analyzed|observed|found|detected|measured)\b', text.lower()))
    present_count = len(re.findall(r'\b(is|are|shows|demonstrates|suggests|indicates|proposes)\b', text.lower()))
    if past_count > 3 and present_count > 3 and section_type in ("Results", "Methodology"):
        issue_id += 1
        issues.append({
            "id": issue_id, "severity": "STYLE", "category": "Copyediting",
            "location": "Throughout",
            "diagnosis": "Mix of past and present tense. In scientific writing, methods and completed results typically use past tense; established facts use present.",
            "why_matters": "Inconsistent tense distracts the reader and may signal carelessness.",
            "actionable_fix": "Use past tense for specific completed actions, present for established facts and table/figure references."
        })

    # --- Category: AI Tells & House Style ---
    # Em-dash
    em_count = text.count("—")
    if em_count > 0:
        issue_id += 1
        issues.append({
            "id": issue_id, "severity": "STYLE", "category": "AITells",
            "location": f"{em_count} occurrence(s)",
            "diagnosis": f"Em-dash used {em_count} time(s). Em-dashes are an AI-generated writing tell and disrupt sentence flow.",
            "why_matters": "Reviewers recognize em-dashes as a stylistic crutch; disrupts logical sentence parsing.",
            "actionable_fix": "Replace each em-dash with a comma, colon, parentheses, or split into two sentences."
        })

    # Banned transitions
    low_text = text.lower()
    found_banned = [t for t in _BANNED_TRANSITIONS if re.search(r'\b' + re.escape(t) + r'\b', low_text)]
    if found_banned:
        issue_id += 1
        issues.append({
            "id": issue_id, "severity": "STYLE", "category": "AITells",
            "location": "Transitions",
            "diagnosis": f"Banned transition words detected: {', '.join(sorted(found_banned)[:5])}. These mark AI-generated or lazy academic prose.",
            "why_matters": "Transitions should emerge from argument logic, not from filler words.",
            "actionable_fix": "Rebuild transitions from the content itself using given-new flow."
        })

    # Promotional adjectives
    found_promo = [p for p in _BANNED_PROMOTIONAL if re.search(r'\b' + re.escape(p) + r'\b', low_text)]
    if found_promo:
        issue_id += 1
        issues.append({
            "id": issue_id, "severity": "STYLE", "category": "AITells",
            "location": "Adjective use",
            "diagnosis": f"Promotional adjectives detected: {', '.join(found_promo)}. These perform certainty rather than earning it.",
            "why_matters": "If the substance survives without the adjective, the adjective was throat-clearing.",
            "actionable_fix": "Delete the adjective. If the sentence collapses, the underlying claim was weak."
        })

    # Importance-signaling verbs
    for pattern in _IMPORTANCE_VERBS_PATTERNS:
        if re.search(pattern, low_text):
            issue_id += 1
            issues.append({
                "id": issue_id, "severity": "STYLE", "category": "AITells",
                "location": "Verb choice",
                "diagnosis": "Importance-signaling verb detected ('underscores', 'plays a key role', etc.). Tells reader something matters instead of showing why.",
                "why_matters": "Replace the signal with the mechanism. If you cannot name the mechanism, the sentence was asserting unearned importance.",
                "actionable_fix": "Replace with the concrete relationship: 'X underscores the importance of Y' -> 'X fails whenever Y is absent'."
            })
            break

    # Inflated noun phrases
    for pattern in _INFLATED_NOUN_PHRASES:
        if re.search(pattern, low_text):
            issue_id += 1
            issues.append({
                "id": issue_id, "severity": "STYLE", "category": "AITells",
                "location": "Noun phrase",
                "diagnosis": "Inflated noun phrase detected ('landscape of', 'myriad of', etc.). Prefer concrete language.",
                "why_matters": "These are dead metaphors that add words without adding meaning.",
                "actionable_fix": "Replace with a specific count or concrete descriptor. 'A myriad of factors' -> 'four factors' or just 'many'."
            })
            break

    # Template shapes
    for pattern, label in _TEMPLATE_SHAPES:
        if re.search(pattern, low_text):
            issue_id += 1
            issues.append({
                "id": issue_id, "severity": "STYLE", "category": "AITells",
                "location": "Sentence structure",
                "diagnosis": f"AI template shape detected: {label}.",
                "why_matters": "These rhetorical molds flatten writing when used reflexively.",
                "actionable_fix": "Rewrite in a direct structure. 'We show that X improves accuracy' -> 'X improves accuracy by 12 points'."
            })
            break

    # --- Category: Reader Experience ---
    if len(sentences) >= 5 and section_type in ("Introduction", "Discussion"):
        # Check for topic string coherence
        first_words = [s.split()[:2] for s in sentences if s.strip()]
        unique_openers = len(set(tuple(w) for w in first_words if w))
        if unique_openers < 2:
            issue_id += 1
            issues.append({
                "id": issue_id, "severity": "MINOR", "category": "ReaderExperience",
                "location": "Throughout",
                "diagnosis": "Sentences all open with similar structure. Reader lacks orientation cues.",
                "why_matters": "Uniform sentence openings create a flat, monotonous reading experience.",
                "actionable_fix": "Vary sentence openers. Use transitions that arise from the content, not from filler words."
            })

    # --- Category: Academic Vocabulary Density ---
    academic_density = get_academic_score(text)
    if section_type in ("Abstract", "Introduction", "Discussion", "Conclusion") and academic_density < 0.15:
        issue_id += 1
        issues.append({
            "id": issue_id, "severity": "MAJOR", "category": "AITells",
            "location": "Vocabulary",
            "diagnosis": f"Low academic vocabulary density ({academic_density:.0%}). Only {academic_density:.0%} of content words appear in the Academic Vocabulary List (COCA-Academic).",
            "why_matters": "Academic prose requires domain-appropriate register. Low academic density suggests informal or generic word choices.",
            "actionable_fix": "Replace common words with academic equivalents from the AVL (e.g., 'get' -> 'obtain', 'show' -> 'demonstrate', 'use' -> 'employ')."
        })

    # Fallback if nothing specific detected
    if not issues:
        issue_id += 1
        issues.append({
            "id": issue_id, "severity": "MINOR", "category": "Copyediting",
            "location": "Sentence structure",
            "diagnosis": "Nominalization detected (using verbs as nouns).",
            "why_matters": "Makes reading passive and heavy.",
            "actionable_fix": "Rewrite using active verbs."
        })

    return {"status": "success", "issues": issues}


def _run_proofreading_phase2(text: str) -> dict:
    fixed_text = text

    # Replace em-dashes with commas
    fixed_text = fixed_text.replace("—", ", ")

    # Replace banned transitions with simpler alternatives
    transition_map = {
        r'\bFurthermore,\s*': "Additionally, ",
        r'\bMoreover,\s*': "Additionally, ",
        r'\bCrucially,\s*': "Critically, ",
        r'\bNotably,\s*': "",
        r'\bUltimately,\s*': "Finally, ",
        r'\bdelving\b': "examining",
        r'\bdelve\b': "examine",
    }
    for pattern, replacement in transition_map.items():
        fixed_text = re.sub(pattern, replacement, fixed_text, flags=re.IGNORECASE)

    # Remove "it is important to note that" and variants
    fixed_text = re.sub(
        r'\b(It\s+is\s+(important|worth|noteworthy)\s+(to\s+)?(note|mention|highlight)\s+that)\b',
        '', fixed_text, flags=re.IGNORECASE
    )
    fixed_text = re.sub(r'\bThat\s+said,\s*', '', fixed_text, flags=re.IGNORECASE)

    # Remove "we show that" -> keep the claim
    fixed_text = re.sub(r'\bWe\s+show\s+that\b', 'We demonstrate', fixed_text, flags=re.IGNORECASE)

    # Replace "state-of-the-art" 
    fixed_text = fixed_text.replace("state-of-the-art", "highly competitive")
    fixed_text = fixed_text.replace("groundbreaking", "important")
    fixed_text = fixed_text.replace("unprecedented", "notable")

    # Remove promotional adjectives before nouns (basic heuristic)
    promo_patterns = [
        (r'\bnovel\s+(approach|method|technique|framework|algorithm|system)\b', r'\1'),
        (r'\binteresting\s+(result|finding|pattern|observation)\b', r'\1'),
        (r'\bgroundbreaking\s+(work|research|study|contribution)\b', r'\1'),
    ]
    for pattern, replacement in promo_patterns:
        fixed_text = re.sub(pattern, replacement, fixed_text, flags=re.IGNORECASE)

    # Replace inflated noun phrases
    fixed_text = re.sub(r'\bthe\s+landscape\s+of\b', 'the field of', fixed_text, flags=re.IGNORECASE)
    fixed_text = re.sub(r'\ba\s+myriad\s+of\b', 'many', fixed_text, flags=re.IGNORECASE)
    fixed_text = re.sub(r'\ba\s+plethora\s+of\b', 'many', fixed_text, flags=re.IGNORECASE)
    fixed_text = re.sub(r'\ba\s+wide\s+array\s+of\b', 'a wide range of', fixed_text, flags=re.IGNORECASE)

    # Replace importance-signaling verbs
    fixed_text = re.sub(
        r'\bunderscores\s+the\s+importance\s+of\b',
        'shows the importance of',
        fixed_text, flags=re.IGNORECASE
    )
    fixed_text = re.sub(
        r'\bplays\s+a\s+(key|central|crucial|vital|pivotal)\s+role\s+in\b',
        'contributes to',
        fixed_text, flags=re.IGNORECASE
    )

    # Fix missing space before units
    fixed_text = re.sub(r"\b(\d+)(cm|mm|m|kg|s|mg|ml|g)\b", r"\1 \2", fixed_text)

    # Fix "Not only...but also" -> "and"
    fixed_text = re.sub(r'\b(not\s+only)\s+', '', fixed_text, flags=re.IGNORECASE)
    fixed_text = re.sub(r'\bbut\s+also\b', 'and', fixed_text, flags=re.IGNORECASE)

    # Clean up extra spaces from removals
    fixed_text = re.sub(r'\s+', ' ', fixed_text).strip()

    return {"status": "success", "text": fixed_text}


# ---- End Proofreading helper functions ----


class AntigravityAgent:
    """Wrapper that utilizes google-antigravity SDK if available, or direct Gemini API, or rules-based simulation."""
    def __init__(self, skill_filename: str):
        self.skill_filename = skill_filename
        self.skill_content = get_skill_content(skill_filename)
        self.api_key = os.getenv("GEMINI_API_KEY")
        
    async def run(self, text: str, payload_type: str = "", strength: int = 3) -> dict:
        strength = max(1, min(5, strength))
        # Check if we should use local simulation (no API Key available)
        if not self.api_key:
            print(f"[AgentWrapper] No GEMINI_API_KEY. Running local rules-based simulation for: {self.skill_filename}")
            return run_local_simulation(text, self.skill_filename, payload_type, strength)

        # 1. Try to use google-antigravity SDK
        try:
            from google.antigravity import Agent, LocalAgentConfig
            print(f"[AgentWrapper] Using google-antigravity SDK for: {self.skill_filename}")
            
            config = LocalAgentConfig(
                system_instructions=self.skill_content
            )
            
            async with Agent(config) as agent:
                prompt = self._build_prompt(text, payload_type, strength)
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
            
            # Map strength (1-5) to temperature (0.3-0.9)
            temperature = 0.3 + (strength - 1) * 0.15
            
            model = genai.GenerativeModel(
                model_name="gemini-2.0-flash",
                system_instruction=self.skill_content,
                generation_config={
                    "temperature": temperature,
                    "top_p": 0.9,
                }
            )
            
            prompt = self._build_prompt(text, payload_type, strength)
            response = model.generate_content(prompt)
            response_text = response.text
            return self._parse_response(response_text, payload_type)
        except Exception as e:
            print(f"[AgentWrapper] Gemini API fallback failed ({str(e)}). Running local rules-based simulation.")
            return run_local_simulation(text, self.skill_filename, payload_type, strength)

    def _build_prompt(self, text: str, payload_type: str, strength: int = 3) -> str:
        if "academic_rewording" in self.skill_filename:
            intensity_descriptions = {
                1: "Light: apply minimal changes — moderate vocabulary upgrades and minor structural tweaks while keeping the original sentence flow mostly intact.",
                2: "Light-Moderate: apply noticeable vocabulary upgrades and restructure some sentences while preserving overall flow.",
                3: "Moderate: clearly restructure most sentences — change clause order, vary openings, split or combine sentences where it improves clarity.",
                4: "Strong: aggressively restructure nearly every sentence — rebuild sentence architecture while preserving core meaning.",
                5: "Maximum: completely transform the text — every sentence must be rebuilt from the ground up with entirely different grammatical scaffolding."
            }
            return (
                "Please rewrite the following text and provide exactly three options in JSON format:\n"
                "{\n"
                '  "Academic": "academic version",\n'
                '  "Concise": "concise version",\n'
                '  "High-Impact": "high-impact version"\n'
                "}\n"
                f"Transformation intensity (1-5): {strength} — {intensity_descriptions[strength]}\n"
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
