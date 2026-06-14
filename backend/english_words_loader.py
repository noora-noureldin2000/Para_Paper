import os
import json

ENGLISH_WORDS_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "english-words", "words_dictionary.json")

_word_dict: dict = None
_word_set: set = None


def load_english_words() -> dict:
    global _word_dict, _word_set
    if _word_dict is not None:
        return _word_dict
    _word_dict = {}
    if not os.path.exists(ENGLISH_WORDS_PATH):
        print(f"[EnglishWords] Dictionary not found at {ENGLISH_WORDS_PATH}")
        return _word_dict
    try:
        with open(ENGLISH_WORDS_PATH, "r", encoding="utf-8") as f:
            _word_dict = json.load(f)
        _word_set = set(_word_dict.keys())
        print(f"[EnglishWords] Loaded {len(_word_dict)} English words")
    except Exception as e:
        print(f"[EnglishWords] Error loading dictionary: {e}")
        _word_dict = {}
        _word_set = set()
    return _word_dict


def is_english_word(word: str) -> bool:
    load_english_words()
    return word.lower() in _word_set


def get_word_variations(word: str) -> list:
    load_english_words()
    base = word.lower()
    variations = []
    if base in _word_set:
        variations.append(base)
    suffixes = ["s", "ed", "ing", "er", "est", "ly", "ness", "tion", "ment", "able", "al", "ful", "less", "ous", "ive"]
    for suffix in suffixes:
        if base + suffix in _word_set:
            variations.append(base + suffix)
    prefixes = ["un", "re", "in", "im", "dis", "pre", "mis", "non", "anti", "over", "under", "out"]
    for prefix in prefixes:
        if prefix + base in _word_set:
            variations.append(prefix + base)
    return variations
