"""Headless smoke tests for streamlit_app.py using Streamlit's AppTest.

Verifies the app boots cleanly and that run callbacks write results into
widget-bound session state (regression test for the stale-output bug where
`value=` + `key=` text areas ignored updated session state).
"""
import os
import sys

# Force rules-engine fallback: clear cloud keys BEFORE the app imports
# agent_wrapper (python-dotenv does not override existing env vars).
os.environ["GEMINI_API_KEY"] = ""
os.environ["GOOGLE_API_KEY"] = ""
os.environ["OPENROUTER_API_KEY"] = ""

from streamlit.testing.v1 import AppTest

APP_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "streamlit_app.py")


def _text_area_by_key(at, key):
    for ta in at.text_area:
        if ta.key == key:
            return ta
    raise AssertionError(f"text_area with key '{key}' not found")


def _click_button_by_label(at, label):
    for btn in at.button:
        if btn.label == label:
            btn.click()
            at.run()
            return
    raise AssertionError(f"button '{label}' not found")


def test_app_boots_without_exception():
    at = AppTest.from_file(APP_PATH, default_timeout=120)
    at.run()
    assert not at.exception


def test_paraphrase_populates_output_widget_state():
    at = AppTest.from_file(APP_PATH, default_timeout=120)
    at.run()
    assert not at.exception

    _text_area_by_key(at, "para_in").set_value("The study showed significant results.")
    at.run()
    _click_button_by_label(at, "Run Paraphrase")

    output = at.session_state["para_out"]
    assert isinstance(output, str)
    assert output.strip(), "para_out must be populated after Run Paraphrase"
    assert "Academic" in output or len(output) > 0


def test_humanize_populates_output_widget_state():
    at = AppTest.from_file(APP_PATH, default_timeout=120)
    at.run()
    assert not at.exception

    _text_area_by_key(at, "h_in").set_value(
        "Furthermore, this study delves into the intricate tapestry of clinical outcomes."
    )
    at.run()
    _click_button_by_label(at, "Humanize Text")

    output = at.session_state["h_out"]
    assert isinstance(output, str)
    assert output.strip(), "h_out must be populated after Humanize Text"


def test_vocab_analysis_populates_stats():
    at = AppTest.from_file(APP_PATH, default_timeout=120)
    at.run()
    assert not at.exception

    _text_area_by_key(at, "v_in").set_value(
        "The study demonstrated significant clinical outcomes using evidence-based methodology."
    )
    at.run()
    _click_button_by_label(at, "Analyze Vocabulary Density")

    stats = at.session_state["v_stats"]
    assert stats is not None
    assert stats["word_count"] > 0
    assert 0.0 <= stats["score"] <= 1.0
