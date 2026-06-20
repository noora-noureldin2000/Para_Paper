import os
import sys


def _get_base_dir():
    if getattr(sys, 'frozen', False):
        return sys._MEIPASS
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


ENGLISH_WORDS_PATH = os.path.join(_get_base_dir(), "english-words", "words_alpha.txt")

_word_set: set = None
_word_lower: set = None


def load_english_words() -> set:
    global _word_set, _word_lower
    if _word_set is not None:
        return _word_set
    _word_set = set()
    _word_lower = set()
    if not os.path.exists(ENGLISH_WORDS_PATH):
        print(f"[EnglishWords] Dictionary not found at {ENGLISH_WORDS_PATH}")
        return _word_set
    try:
        with open(ENGLISH_WORDS_PATH, "r", encoding="utf-8") as f:
            for line in f:
                w = line.strip()
                if w:
                    _word_set.add(w)
                    _word_lower.add(w.lower())
        print(f"[EnglishWords] Loaded {len(_word_set)} English words")
    except Exception as e:
        print(f"[EnglishWords] Error loading dictionary: {e}")
        _word_set = set()
        _word_lower = set()
    return _word_set


def get_english_lower() -> set:
    load_english_words()
    return _word_lower
