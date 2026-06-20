import os
import sys
import json


def _get_base_dir():
    if getattr(sys, 'frozen', False):
        return os.path.join(sys._MEIPASS, 'backend')
    return os.path.dirname(os.path.abspath(__file__))


AVL_PATH = os.path.join(_get_base_dir(), "data", "AVL.json")
MAWL_PATH = os.path.join(_get_base_dir(), "data", "MAWL.json")

_avl_set: set = None
_mawl_set: set = None
_avl_data: dict = None


def load_avl() -> dict:
    global _avl_data, _avl_set
    if _avl_data is not None:
        return _avl_data
    _avl_data = {}
    _avl_set = set()
    if not os.path.exists(AVL_PATH):
        print(f"[AcademicVocab] AVL not found at {AVL_PATH}")
        return _avl_data
    try:
        with open(AVL_PATH, "r", encoding="utf-8") as f:
            raw = json.load(f)
        for band, words in raw.items():
            for word, info in words.items():
                _avl_data[word.lower()] = info
                _avl_set.add(word.lower())
        print(f"[AcademicVocab] Loaded {len(_avl_set)} academic vocabulary terms (AVL)")
    except Exception as e:
        print(f"[AcademicVocab] Error loading AVL: {e}")
    return _avl_data


def load_mawl() -> set:
    global _mawl_set
    if _mawl_set is not None:
        return _mawl_set
    _mawl_set = set()
    if not os.path.exists(MAWL_PATH):
        print(f"[AcademicVocab] MAWL not found at {MAWL_PATH}")
        return _mawl_set
    try:
        with open(MAWL_PATH, "r", encoding="utf-8") as f:
            raw = json.load(f)
        for word in raw:
            _mawl_set.add(word.lower())
        print(f"[AcademicVocab] Loaded {len(_mawl_set)} medical academic vocabulary terms (MAWL)")
    except Exception as e:
        print(f"[AcademicVocab] Error loading MAWL: {e}")
    return _mawl_set


def get_academic_score(text: str) -> float:
    words = [w.strip(".,;:!?()[]{}'\"") for w in text.split() if len(w.strip(".,;:!?()[]{}'\"")) > 2]
    if not words:
        return 0.0
    load_avl()
    match_count = sum(1 for w in words if w.lower() in _avl_set)
    return match_count / len(words)
