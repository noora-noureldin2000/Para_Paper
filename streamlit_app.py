import os
import sys
import io
import re
import asyncio
import streamlit as st
from docx import Document

# Add backend directory to sys.path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.join(BASE_DIR, "backend")
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from agent_wrapper import AntigravityAgent
from academic_vocab import get_academic_score, load_avl, load_mawl
from medical_vocab import load_medical_terms
from paper_writer import PaperWriterAgent, make_docx

# Preload vocabulary
load_avl()
load_mawl()
load_medical_terms()

st.set_page_config(
    page_title="Para Paper V2",
    page_icon="📝",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    .stApp { background-color: #0e1117; color: #e0e0e0; }
    .hero {
        background: linear-gradient(115deg, #123f47, #315f67 58%, #217f74);
        padding: 24px 30px;
        border-radius: 16px;
        color: white;
        margin-bottom: 20px;
        box-shadow: 0 8px 24px rgba(0,0,0,0.3);
    }
    .hero h1 { margin: 0; font-size: 2.2rem; font-weight: 700; color: #ffffff; }
    .hero p { margin: 6px 0 0 0; color: #dfefef; font-size: 1.05rem; }
    .stButton>button { border-radius: 8px; font-weight: 600; }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Session State — initialize every widget-bound key ONCE, before widgets exist.
# Widgets are bound to these keys (no `value=` param), so the keys are the
# single source of truth and callbacks can update them safely.
# ---------------------------------------------------------------------------
_WIDGET_KEYS = ["para_in", "para_out", "h_in", "h_out", "p_in", "p_fixed", "rev_in", "v_in"]
for _key in _WIDGET_KEYS:
    if _key not in st.session_state:
        st.session_state[_key] = ""

# Non-widget result keys
for _key in ["p_issues", "rev_out", "pw_res", "v_stats"]:
    if _key not in st.session_state:
        st.session_state[_key] = None


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def run_async(coro):
    return asyncio.run(coro)


def get_words(text):
    return len(re.findall(r"\b[\w'-]+\b", text or ""))


# ---------------------------------------------------------------------------
# Sidebar: provider config + file upload
# ---------------------------------------------------------------------------
with st.sidebar:
    st.title("⚙️ Config & Setup")

    provider = st.radio("LLM Provider", ["Gemini API", "OpenRouter", "Ollama (Local)"])

    api_key = ""
    model_id = ""
    ollama_url = "http://localhost:11434"

    if provider == "Gemini API":
        api_key = st.text_input("Gemini API Key", type="password", help="Session-only key")
    elif provider == "OpenRouter":
        api_key = st.text_input("OpenRouter API Key", type="password", help="Session-only key")
        model_id = st.text_input("Model ID", value="openrouter/auto", help="e.g. google/gemini-2.0-flash-001 or anthropic/claude-3.5-sonnet")
    else:  # Ollama
        model_id = st.text_input("Ollama Model", value="llama3.2")
        ollama_url = st.text_input("Ollama URL", value="http://localhost:11434")
        st.info("Ensure Ollama is running locally (`ollama pull llama3.2`)")

    prov_key = "gemini" if provider == "Gemini API" else ("openrouter" if provider == "OpenRouter" else "ollama")
    AntigravityAgent.set_api_config(provider=prov_key, api_key=api_key, model=model_id, base_url=ollama_url)

    st.divider()
    st.subheader("📁 File Upload")
    uploaded_file = st.file_uploader("Upload .txt, .docx, or .pdf", type=["txt", "docx", "pdf"])

    def _load_file_into_input():
        """Callback: extract file text into the paraphrase input widget state.

        Runs before the script rerun, so writing to the widget key is legal.
        """
        if uploaded_file is None:
            return
        ext = os.path.splitext(uploaded_file.name)[1].lower()
        bytes_data = uploaded_file.getvalue()
        content = ""

        if ext == ".txt":
            content = bytes_data.decode("utf-8", errors="replace")
        elif ext == ".docx":
            doc = Document(io.BytesIO(bytes_data))
            content = "\n\n".join(p.text for p in doc.paragraphs if p.text.strip())
        elif ext == ".pdf":
            from pypdf import PdfReader
            reader = PdfReader(io.BytesIO(bytes_data))
            content = "\n\n".join(
                page.extract_text() for page in reader.pages if page.extract_text()
            )

        if content.strip():
            st.session_state["para_in"] = content
            st.session_state["h_in"] = content
            st.session_state["p_in"] = content
            st.session_state["rev_in"] = content
            st.session_state["v_in"] = content

    st.button("Load File Content", use_container_width=True, on_click=_load_file_into_input)


# ---------------------------------------------------------------------------
# Hero header
# ---------------------------------------------------------------------------
st.markdown("""
<div class="hero">
    <h1>Para Paper V2</h1>
    <p>Scientific Paraphrasing, Anti-AI Humanizing, Manuscript Review & Paper Generation Workspace</p>
</div>
""", unsafe_allow_html=True)

tabs = st.tabs([
    "✍️ Paraphrase",
    "🤖→🧑 Humanize",
    "🔍 Proofread",
    "📝 Manuscript Review",
    "📄 Write Paper",
    "📊 Vocab Analysis"
])

# ---------------------------------------------------------------------------
# TAB 1: PARAPHRASE
# ---------------------------------------------------------------------------
with tabs[0]:
    st.header("Academic & Clinical Paraphrasing")

    def _run_paraphrase():
        text = st.session_state["para_in"].strip()
        if not text:
            return
        mode_label = st.session_state.get("para_mode", "General Academic")
        strength = st.session_state.get("para_strength", 3)
        skill = "academic_rewording_medical.md" if "Medical" in mode_label else "academic_rewording.md"
        with st.spinner("Paraphrasing text..."):
            agent = AntigravityAgent(skill)
            res = run_async(agent.run(text, strength=strength))
        if "options" in res:
            st.session_state["para_out"] = "\n\n".join(
                f"### [{opt['type']}]\n{opt['text']}" for opt in res["options"]
            )
        else:
            st.session_state["para_out"] = res.get("text", "")

    col_in, col_out = st.columns(2, gap="medium")
    with col_in:
        st.subheader("Original Text")
        st.text_area("Input", height=300, key="para_in", label_visibility="collapsed")
        st.caption(f"Words: {get_words(st.session_state['para_in'])} | Chars: {len(st.session_state['para_in'])}")
    with col_out:
        st.subheader("Paraphrased Output")
        st.text_area("Output", height=300, key="para_out", label_visibility="collapsed")
        st.caption(f"Words: {get_words(st.session_state['para_out'])} | Delta: {get_words(st.session_state['para_out']) - get_words(st.session_state['para_in'])}")

    c1, c2, c3 = st.columns([2, 2, 1])
    with c1:
        st.radio("Mode", ["General Academic", "Medical / Clinical preservation"], horizontal=True, key="para_mode")
    with c2:
        st.slider("Transformation Strength", 1, 5, 3, key="para_strength")
    with c3:
        st.write("")
        st.write("")
        st.button("Run Paraphrase", type="primary", use_container_width=True, on_click=_run_paraphrase)

# ---------------------------------------------------------------------------
# TAB 2: HUMANIZE
# ---------------------------------------------------------------------------
with tabs[1]:
    st.header("Anti-AI Humanizing Engine")
    st.write("Removes robotic LLM signatures via style-profile transforms.")

    def _run_humanize():
        text = st.session_state["h_in"].strip()
        if not text:
            return
        mode = st.session_state.get("h_mode", "Dr. Noora Style")
        strength = st.session_state.get("h_strength", 3)
        skill = "humanizer_noora.md" if "Noora" in mode else "humanizer_general.md"
        with st.spinner("Removing AI signatures..."):
            agent = AntigravityAgent(skill)
            res = run_async(agent.run(text, strength=strength))
        st.session_state["h_out"] = res.get("text", "")

    col1, col2 = st.columns(2)
    with col1:
        st.selectbox("Style Profile", ["Dr. Noora Style", "General Anti-AI Cleanup"], key="h_mode")
        st.text_area("AI Text", height=250, key="h_in")
    with col2:
        st.slider("Humanize Strength", 1, 5, 3, key="h_strength")
        st.button("Humanize Text", type="primary", use_container_width=True, on_click=_run_humanize)
        st.text_area("Humanized Output", height=200, key="h_out")

# ---------------------------------------------------------------------------
# TAB 3: PROOFREAD
# ---------------------------------------------------------------------------
with tabs[2]:
    st.header("2-Phase Manuscript Audit")

    def _run_audit():
        text = st.session_state["p_in"].strip()
        if not text:
            return
        with st.spinner("Auditing manuscript..."):
            agent = AntigravityAgent("proofreading.md")
            res = run_async(agent.run(text, payload_type="phase1"))
        st.session_state["p_issues"] = res.get("issues", [])

    def _run_fixes():
        text = st.session_state["p_in"].strip()
        if not text:
            return
        with st.spinner("Applying corrections..."):
            agent = AntigravityAgent("proofreading.md")
            res = run_async(agent.run(text, payload_type="phase2"))
        st.session_state["p_fixed"] = res.get("text", "")

    st.text_area("Manuscript Segment", height=200, key="p_in")

    col_p1, col_p2 = st.columns(2)
    with col_p1:
        st.button("Phase 1: Audit Text", type="primary", use_container_width=True, on_click=_run_audit)
    with col_p2:
        st.button("Phase 2: Apply All Fixes", use_container_width=True, on_click=_run_fixes)

    if st.session_state["p_issues"]:
        st.subheader("Audit Issues")
        st.json(st.session_state["p_issues"])

    st.text_area("Fixed Output", height=200, key="p_fixed")

# ---------------------------------------------------------------------------
# TAB 4: MANUSCRIPT REVIEW
# ---------------------------------------------------------------------------
with tabs[3]:
    st.header("5-Pass Writing Quality Review")
    st.markdown("Applies a structured methodology: Clutter, Voice, Architecture, Terminology, Citation Integrity.")

    def _run_review():
        text = st.session_state["rev_in"].strip()
        if not text:
            return
        mode = st.session_state.get("rev_mode", "full-review")
        with st.spinner("Performing 5-pass audit..."):
            agent = AntigravityAgent("manuscript_review.md")
            res = run_async(agent.run(f"Mode: {mode}\n\n{text}"))

        if res.get("status") == "error" or not res.get("text", "").strip():
            # Rules-engine fallback: proofread audit + vocabulary score
            proof_agent = AntigravityAgent("proofreading.md")
            proof_res = run_async(proof_agent.run(text, payload_type="phase1"))
            issues = proof_res.get("issues", [])
            score = get_academic_score(text)
            lines = [
                "### Rules-Engine Review Report",
                f"- **Academic vocabulary density:** {score * 100:.1f}%",
                f"- **Issues detected:** {len(issues)}",
                "",
            ]
            for issue in issues:
                lines.append(
                    f"- **[{issue.get('severity', 'MINOR')}]** {issue.get('diagnosis', '')} "
                    f"→ *Fix:* {issue.get('actionable_fix', '')}"
                )
            if not issues:
                lines.append("No structural issues detected by the rules engine.")
            st.session_state["rev_out"] = "\n".join(lines)
        else:
            st.session_state["rev_out"] = res.get("text", "")

    st.selectbox("Review Mode", ["full-review", "section-review", "targeted", "interactive"], key="rev_mode")
    st.text_area("Manuscript Text", height=220, key="rev_in")
    st.button("Run 5-Pass Review", type="primary", on_click=_run_review)

    if st.session_state["rev_out"]:
        st.markdown(st.session_state["rev_out"])

# ---------------------------------------------------------------------------
# TAB 5: WRITE PAPER
# ---------------------------------------------------------------------------
with tabs[4]:
    st.header("Paper Generation Assistant")

    def _run_write_paper():
        topic = st.session_state.get("pw_topic", "").strip()
        if not topic:
            return
        doc_type = st.session_state.get("pw_doctype", "Research Paper")
        outline = st.session_state.get("pw_outline", "")
        with st.spinner("Drafting paper & conducting peer review..."):
            pw = PaperWriterAgent()
            st.session_state["pw_res"] = run_async(
                pw.generate_draft(topic=topic, doc_type=doc_type, outline=outline)
            )

    st.selectbox("Document Type", ["Research Paper", "Literature Review", "Case Report", "Grant Proposal"], key="pw_doctype")
    st.text_input("Topic / Title", key="pw_topic")
    st.text_area("Outline / Key Findings (Optional)", height=150, key="pw_outline")
    st.button("Generate Paper Draft & Peer Review", type="primary", on_click=_run_write_paper)

    if st.session_state["pw_res"]:
        res = st.session_state["pw_res"]
        st.subheader("Generated Draft")
        st.markdown(res.get("draft", ""))
        st.divider()
        st.subheader("Peer Review Feedback")
        st.markdown(res.get("review", ""))
        docx_data = make_docx(res.get("draft", ""), title=f"{st.session_state.get('pw_doctype', 'Paper')}: {st.session_state.get('pw_topic', '')}")
        st.download_button("Download Word Document (.docx)", data=docx_data, file_name="para_paper_v2_draft.docx")

# ---------------------------------------------------------------------------
# TAB 6: VOCAB ANALYSIS
# ---------------------------------------------------------------------------
with tabs[5]:
    st.header("Academic & Medical Vocabulary Analysis")

    def _run_vocab():
        text = st.session_state["v_in"].strip()
        if not text:
            return
        score = get_academic_score(text)
        words = re.findall(r"\b[\w'-]+\b", text)
        sentences = [s for s in re.split(r"[.!?]+", text) if s.strip()]
        st.session_state["v_stats"] = {
            "score": score,
            "word_count": len(words),
            "unique_words": len(set(w.lower() for w in words)),
            "sentence_count": len(sentences),
        }

    st.text_area("Text to Analyze", height=200, key="v_in")
    st.button("Analyze Vocabulary Density", type="primary", on_click=_run_vocab)

    if st.session_state["v_stats"]:
        stats = st.session_state["v_stats"]
        st.metric("Academic Vocabulary List (AVL) Score", f"{stats['score'] * 100:.1f}%")
        c1, c2, c3 = st.columns(3)
        c1.metric("Words", stats["word_count"])
        c2.metric("Unique Words", stats["unique_words"])
        c3.metric("Sentences", stats["sentence_count"])
        st.info("Measures percentage of formal academic terms matched against the COCA Academic Vocabulary List.")

# ---------------------------------------------------------------------------
# Export section — paraphrase output
# ---------------------------------------------------------------------------
if st.session_state["para_out"].strip():
    st.divider()
    st.subheader("Export Results")
    d_docx = make_docx(st.session_state["para_out"], title="Para Paper V2 Export")
    st.download_button(
        "Download (.docx)",
        data=d_docx,
        file_name="para_paper_v2_output.docx",
        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    )
