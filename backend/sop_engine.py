"""
SOP Engine — Sentence-level transforms for academic paraphrasing and AI humanization.

Implements the user's Standard Operating Procedure (SOP) as rule-based transforms:
- Banned AI vocabulary replacement
- Anti-triplet guard
- Semicolon and em-dash elimination
- Active voice conversion
- Sentence burstiness mixing
- Intellectual hedging injection
- Logic reordering
- Micro-conclusion stripping
- Sentence opener diversification
"""

import re
import random


BANNED_WORDS_MAP = {
    "leverage": ["use", "build on", "take advantage of", "draw on"],
    "leveraged": ["used", "built on", "drew on"],
    "leveraging": ["using", "building on", "drawing on"],
    "leverages": ["uses", "builds on", "draws on"],
    "foster": ["support", "encourage", "promote", "help"],
    "fostered": ["supported", "encouraged", "promoted", "helped"],
    "fostering": ["supporting", "encouraging", "promoting", "helping"],
    "fosters": ["supports", "encourages", "promotes", "helps"],
    "utilize": ["use", "apply", "employ"],
    "utilized": ["used", "applied", "employed"],
    "utilizing": ["using", "applying", "employing"],
    "utilizes": ["uses", "applies", "employs"],
    "utilization": ["use", "application"],
    "robust": ["strong", "reliable", "solid", "well-tested"],
    "dynamic": ["active", "changing", "varied", "evolving"],
    "delve": ["explore", "examine", "look into", "investigate"],
    "delved": ["explored", "examined", "looked into"],
    "delving": ["exploring", "examining", "looking into"],
    "delves": ["explores", "examines", "looks into"],
    "intricate": ["complex", "detailed", "involved"],
    "paramount": ["critical", "key", "essential", "vital"],
    "tapestry": ["mix", "combination", "collection", "landscape"],
    "testament": ["proof", "evidence", "sign", "marker"],
    "multifaceted": ["complex", "varied", "diverse"],
    "comprehensive": ["thorough", "complete", "full", "broad"],
    "groundbreaking": ["new", "important", "significant", "original"],
    "cutting-edge": ["modern", "advanced", "recent", "new"],
    "pivotal": ["key", "central", "important", "major"],
    "crucial": ["key", "important", "essential", "necessary"],
    "furthermore": ["also", "in addition", "beyond that"],
    "moreover": ["also", "besides", "in addition"],
    "subsequently": ["then", "later", "after that", "next"],
    "henceforth": ["from now on", "going forward"],
    "notwithstanding": ["despite", "even so", "regardless"],
    "aforementioned": ["this", "the earlier", "the previous"],
    "endeavor": ["effort", "attempt", "work", "project"],
    "endeavors": ["efforts", "attempts", "projects"],
    "underscore": ["show", "highlight", "stress", "point out"],
    "underscores": ["shows", "highlights", "stresses"],
    "underscored": ["showed", "highlighted", "stressed"],
    "showcase": ["show", "present", "display", "demonstrate"],
    "showcases": ["shows", "presents", "displays"],
    "showcased": ["showed", "presented", "displayed"],
    "landscape": ["field", "area", "domain", "space"],
    "realm": ["area", "field", "domain"],
    "myriad": ["many", "numerous", "a range of"],
    "plethora": ["many", "a large number of", "plenty of"],
}

# Additional inflated phrases to replace
BANNED_PHRASES_MAP = {
    "a wide array of": ["many", "a range of", "various"],
    "a myriad of": ["many", "numerous"],
    "a plethora of": ["many", "plenty of", "a large number of"],
    "rich tapestry": ["mix", "combination", "collection"],
    "paradigm shift": ["change", "major change", "shift"],
    "game changer": ["breakthrough", "advance", "important step"],
    "game-changer": ["breakthrough", "advance", "important step"],
    "it is important to note that": ["notably", ""],
    "it should be noted that": ["notably", ""],
    "it is worth mentioning that": ["notably", ""],
    "in the realm of": ["in", "within"],
    "in the landscape of": ["in", "across"],
    "plays a crucial role in": ["contributes to", "helps with", "is central to"],
    "plays a pivotal role in": ["contributes to", "helps with", "is central to"],
    "plays a key role in": ["contributes to", "helps with", "is central to"],
    "plays a vital role in": ["contributes to", "helps with", "is central to"],
    "not only but also": ["and"],
    "first and foremost": ["first", "mainly"],
}


# Pre-compiled banned word/phrase patterns for fast replacement
_BANNED_WORDS_PATTERNS = [
    (re.compile(r'\b' + re.escape(w) + r'\b', re.IGNORECASE), replacements)
    for w, replacements in BANNED_WORDS_MAP.items()
]
_BANNED_PHRASES_PATTERNS = [
    (re.compile(re.escape(p), re.IGNORECASE), replacements)
    for p, replacements in BANNED_PHRASES_MAP.items()
]


_TRIPLET_PATTERN = re.compile(
    r'\b(\w+),\s+(\w+),\s+and\s+(\w+)\b',
    re.IGNORECASE
)


def _break_triplets(text):
    """Detect comma-separated triplets of adjectives/adverbs and break them."""
    def _replace_triplet(match):
        word_a = match.group(1)
        word_b = match.group(2)
        word_c = match.group(3)
        # Keep only 2 of the 3, chosen randomly
        pair = random.sample([word_a, word_b, word_c], 2)
        return f"{pair[0]} and {pair[1]}"

    return _TRIPLET_PATTERN.sub(_replace_triplet, text)


def _eliminate_semicolons(text):
    """Replace semicolons with periods or ', and' constructs."""
    parts = text.split(';')
    if len(parts) <= 1:
        return text

    result_parts = [parts[0].rstrip()]
    for part in parts[1:]:
        part = part.strip()
        if not part:
            continue
        # Randomly choose replacement
        if random.random() < 0.6:
            # Period + capitalize
            capitalized = part[0].upper() + part[1:] if part else part
            result_parts.append(capitalized)
        else:
            # Comma + conjunction
            conj = random.choice(["and", "but", "while"])
            lowered = part[0].lower() + part[1:] if part else part
            result_parts[-1] = result_parts[-1] + f", {conj} {lowered}"

    return '. '.join(result_parts)


def _eliminate_em_dashes(text):
    """Replace em-dashes and en-dashes with commas or parenthetical rewrites."""
    # Keep number ranges (e.g. 2019–2022)
    text = re.sub(r'(\d)\s*[—–]\s*(\d)', r'\1-\2', text)
    # Replace remaining em/en dashes with commas
    text = re.sub(r'\s*[—–]\s*', ', ', text)
    return text


_PASSIVE_PATTERN = re.compile(
    r'\b(was|were|is|are|been|being)\s+'
    r'(\w+ed|shown|seen|found|given|taken|made|done|known|written|built|held|run|set|put|cut|read)\b',
    re.IGNORECASE
)

_BY_PATTERN = re.compile(
    r'(\b\w[\w\s,]*?)\b(was|were|is|are)\s+(\w+(?:ed|en|wn|lt|nt|ven|ght))\s+by\s+([\w\s]+?)([.,;!?])',
    re.IGNORECASE
)


def _convert_passive_to_active(text):
    """Attempt simple passive-to-active conversions where feasible.

    Only handles straightforward 'was/were + past participle + by' patterns.
    Does not attempt complex restructuring to avoid meaning changes.
    """
    # Pattern: "X was done by Y" -> "Y did X"

    def _flip_by_passive(match):
        subject = match.group(1).strip()
        verb_past = match.group(3).strip()
        agent = match.group(4).strip()
        punct = match.group(5)
        # Simple flip
        return f"{agent} {verb_past} {subject}{punct}"

    # Only flip a subset (controlled probability to avoid garbling)
    result = text
    matches = list(_BY_PATTERN.finditer(result))
    if matches and random.random() < 0.5:
        match = random.choice(matches)
        result = result[:match.start()] + _flip_by_passive(match) + result[match.end():]

    return result


def _apply_burstiness(sentences):
    """Force variation in sentence lengths to match human burstiness patterns.

    Targets: mix of short (5-8 words) and long (20-50 words) sentences.
    Average aim: 10-25 words per sentence.
    """
    if len(sentences) < 3:
        return sentences

    result = list(sentences)
    lengths = [len(s.split()) for s in result]

    # Check if all sentences are roughly the same length (AI pattern)
    avg_len = sum(lengths) / len(lengths) if lengths else 0
    variance = sum((ln - avg_len) ** 2 for ln in lengths) / len(lengths) if lengths else 0

    # If variance is low (uniform lengths), inject burstiness
    if variance < 25 and len(result) >= 3:
        # Try to split a long sentence to create a short one
        for i in range(len(result)):
            words = result[i].split()
            if len(words) > 18:
                # Find a comma near the middle to split at
                mid = len(words) // 2
                for offset in range(min(5, mid)):
                    for check_pos in [mid + offset, mid - offset]:
                        if 0 < check_pos < len(words) - 3:
                            word = words[check_pos]
                            if word.endswith(','):
                                first_half = ' '.join(words[:check_pos + 1]).rstrip(',') + '.'
                                second_half = ' '.join(words[check_pos + 1:])
                                if second_half:
                                    second_half = second_half[0].upper() + second_half[1:]
                                result[i] = first_half
                                result.insert(i + 1, second_half)
                                break
                    else:
                        continue
                    break
                break

    return result


HEDGING_PHRASES = [
    "it appears that",
    "it seems that",
    "is believed to",
    "may suggest",
    "could indicate",
    "appears to",
    "one might argue that",
    "it is plausible that",
    "evidence points to",
]

_ABSOLUTE_PATTERNS = [
    (re.compile(r'\bThis proves that\b', re.IGNORECASE), ["This may suggest that", "This appears to show that", "Evidence from this points to"]),
    (re.compile(r'\bIt is clear that\b', re.IGNORECASE), ["It seems that", "It appears that", "One could argue that"]),
    (re.compile(r'\bIt is evident that\b', re.IGNORECASE), ["It seems that", "It appears that", "Evidence suggests that"]),
    (re.compile(r'\bIt is obvious that\b', re.IGNORECASE), ["It seems that", "It appears that"]),
    (re.compile(r'\bwithout doubt\b', re.IGNORECASE), ["likely", "plausibly", "with reasonable confidence"]),
    (re.compile(r'\bundoubtedly\b', re.IGNORECASE), ["likely", "arguably", "plausibly"]),
    (re.compile(r'\bunquestionably\b', re.IGNORECASE), ["arguably", "plausibly"]),
    (re.compile(r'\bclearly demonstrates\b', re.IGNORECASE), ["appears to show", "seems to demonstrate", "may demonstrate"]),
    (re.compile(r'\bclearly shows\b', re.IGNORECASE), ["appears to show", "seems to indicate", "may show"]),
    (re.compile(r'\bclearly indicates\b', re.IGNORECASE), ["appears to suggest", "seems to indicate"]),
    (re.compile(r'\bdefinitively\b', re.IGNORECASE), ["largely", "to a great extent", "with strong evidence"]),
    (re.compile(r'\balways results in\b', re.IGNORECASE), ["often results in", "tends to result in", "frequently leads to"]),
    (re.compile(r'\bnever fails to\b', re.IGNORECASE), ["rarely fails to", "tends to", "generally manages to"]),
]


def _inject_hedging(text, intensity=0.3):
    """Replace absolute statements with hedged academic language."""
    result = text
    for pattern, replacements in _ABSOLUTE_PATTERNS:
        if random.random() < intensity:
            result = pattern.sub(lambda m, r=replacements: random.choice(r), result)
    return result


_CAUSAL_PATTERN = re.compile(
    r'(\b\w[\w\s]*?)\b(causes?|leads?\s+to|results?\s+in)\s+([\w\s]+?),\s+'
    r'(leading\s+to|resulting\s+in|which\s+causes?)\s+([\w\s]+?)([.,])',
    re.IGNORECASE
)


def _reorder_causal_logic(text):
    """Flip 'A causes B, leading to C' to 'C often results from B, which stems from A'."""
    def _flip_chain(match):
        cause_a = match.group(1).strip()
        effect_b = match.group(3).strip()
        effect_c = match.group(5).strip()
        punct = match.group(6)

        templates = [
            f"{effect_c} often results from {effect_b}, which stems from {cause_a}{punct}",
            f"{effect_c} is frequently linked to {effect_b}, itself driven by {cause_a}{punct}",
            f"Starting from {effect_c}, one can trace this back to {effect_b} and ultimately {cause_a}{punct}",
        ]
        return random.choice(templates)

    if random.random() < 0.3:
        return _CAUSAL_PATTERN.sub(_flip_chain, text, count=1)
    return text


_MICRO_CONCLUSION_STARTERS = [
    re.compile(r'^Ultimately,?\s+', re.IGNORECASE),
    re.compile(r'^In conclusion,?\s+', re.IGNORECASE),
    re.compile(r'^This highlights\s+', re.IGNORECASE),
    re.compile(r'^This demonstrates\s+', re.IGNORECASE),
    re.compile(r'^This underscores\s+', re.IGNORECASE),
    re.compile(r'^This showcases\s+', re.IGNORECASE),
    re.compile(r'^Overall,?\s+this\s+', re.IGNORECASE),
    re.compile(r'^In summary,?\s+', re.IGNORECASE),
    re.compile(r'^To summarize,?\s+', re.IGNORECASE),
    re.compile(r'^All in all,?\s+', re.IGNORECASE),
    re.compile(r'^In essence,?\s+', re.IGNORECASE),
    re.compile(r'^Taken together,?\s+this\s+', re.IGNORECASE),
]


def _strip_micro_conclusions(sentences):
    """Remove trailing summary sentences from paragraph-level sentence lists."""
    if len(sentences) <= 2:
        return sentences

    last = sentences[-1].strip()
    for pattern in _MICRO_CONCLUSION_STARTERS:
        if pattern.match(last):
            return sentences[:-1]

    return sentences


_ALTERNATIVE_OPENERS = [
    "In this context,",
    "From this perspective,",
    "Building on this,",
    "Along these lines,",
    "To this end,",
    "With this in mind,",
    "In light of this,",
    "Given these considerations,",
    "Against this backdrop,",
    "From a practical standpoint,",
    "When viewed this way,",
    "Considering these factors,",
]


def _diversify_openers(sentences):
    """Ensure no two consecutive sentences start with the same word or phrase."""
    if len(sentences) < 2:
        return sentences

    result = list(sentences)
    for i in range(1, len(result)):
        prev_start = result[i - 1].split()[0].lower() if result[i - 1].split() else ""
        curr_start = result[i].split()[0].lower() if result[i].split() else ""

        if prev_start and curr_start and prev_start == curr_start:
            # Replace opening of current sentence
            opener = random.choice(_ALTERNATIVE_OPENERS)
            # Remove the repeated word and re-attach
            words = result[i].split()
            if len(words) > 1:
                rest = ' '.join(words[1:])
                # Lowercase first char of rest if it was capitalized
                if rest and rest[0].isupper():
                    rest = rest[0].lower() + rest[1:]
                result[i] = f"{opener} {rest}"

    return result


def _split_into_sentences(text):
    """Split text into sentences while preserving citation markers and abbreviations."""
    # Protect common abbreviations
    protected = text
    abbreviations = ['et al.', 'i.e.', 'e.g.', 'vs.', 'Dr.', 'Mr.', 'Mrs.', 'Ms.', 'Prof.', 'Fig.', 'Eq.', 'No.']
    placeholders = {}
    for idx, abbr in enumerate(abbreviations):
        placeholder = f"__ABBR{idx}__"
        placeholders[placeholder] = abbr
        protected = protected.replace(abbr, placeholder)

    # Split on sentence-ending punctuation
    raw_sentences = re.split(r'(?<=[.!?])\s+(?=[A-Z])', protected)

    # Restore abbreviations
    restored = []
    for sent in raw_sentences:
        for placeholder, abbr in placeholders.items():
            sent = sent.replace(placeholder, abbr)
        sent = sent.strip()
        if sent:
            restored.append(sent)

    return restored


def apply_sop_transforms(text, strength=3):
    """Apply the full SOP transformation pipeline to input text.

    Args:
        text: Input text to transform.
        strength: Intensity level 1-5 (1=light, 5=maximum).

    Returns:
        Transformed text with SOP rules applied.
    """
    if not text or not text.strip():
        return text

    strength = max(1, min(5, strength))
    intensity = {1: 0.2, 2: 0.35, 3: 0.5, 4: 0.7, 5: 0.85}.get(strength, 0.5)

    # Process paragraph by paragraph
    paragraphs = [p.strip() for p in re.split(r'\n\s*\n', text) if p.strip()]
    if not paragraphs:
        paragraphs = [text]

    transformed_paragraphs = []
    for para in paragraphs:
        result = para

        result = _replace_banned_words(result, intensity)

        result = _replace_banned_phrases(result, intensity)

        if strength >= 2:
            result = _break_triplets(result)

        result = _eliminate_semicolons(result)

        result = _eliminate_em_dashes(result)

        sentences = _split_into_sentences(result)

        if strength >= 2:
            converted = []
            for sent in sentences:
                if random.random() < intensity * 0.4:
                    converted.append(_convert_passive_to_active(sent))
                else:
                    converted.append(sent)
            sentences = converted

        if strength >= 2:
            hedged = []
            for sent in sentences:
                hedged.append(_inject_hedging(sent, intensity * 0.4))
            sentences = hedged

        if strength >= 3:
            reordered = []
            for sent in sentences:
                if random.random() < intensity * 0.3:
                    reordered.append(_reorder_causal_logic(sent))
                else:
                    reordered.append(sent)
            sentences = reordered

        if strength >= 2:
            sentences = _strip_micro_conclusions(sentences)

        if strength >= 2:
            sentences = _diversify_openers(sentences)

        if strength >= 3:
            sentences = _apply_burstiness(sentences)

        result = ' '.join(sentences)
        transformed_paragraphs.append(result)

    return '\n\n'.join(transformed_paragraphs)


def _replace_banned_words(text, intensity):
    """Replace banned AI vocabulary with concrete alternatives."""
    result = text
    for pattern, replacements in _BANNED_WORDS_PATTERNS:
        if random.random() < intensity:
            replacement = random.choice(replacements)
            def _case_match_replace(m, rep=replacement):
                original = m.group(0)
                if original[0].isupper():
                    return rep[0].upper() + rep[1:]
                return rep
            result = pattern.sub(_case_match_replace, result)
    return result


def _replace_banned_phrases(text, intensity):
    """Replace banned inflated phrases with simpler alternatives."""
    result = text
    for pattern, replacements in _BANNED_PHRASES_PATTERNS:
        if random.random() < intensity:
            replacement = random.choice(replacements)
            result = pattern.sub(replacement, result)
    return result
