import os
import sys
import io
import re
import asyncio
import streamlit as st

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

# Styling
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

# Session State Initialization
if "input_text" not in st.session_state:
    st.session_state.input_text = ""
if "output_text" not in st.session_state:
    st.session_state.output_text = ""

# Sidebar Configuration
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
    else: # Ollama
        model_id = st.text_input("Ollama Model", value="llama3.2")
        ollama_url = st.text_input("Ollama URL", value="http://localhost:11434")
        st.info("Ensure Ollama is running locally (`ollama pull llama3.2`)")
        
    st.divider()
    
    # Configure Backend Agent API
    prov_key = "gemini" if provider == "Gemini API" else ("openrouter" if provider == "OpenRouter" else "ollama")
    AntigravityAgent.set_api_config(provider=prov_key, api_key=api_key, model=model_id, base_url=ollama_url)
    
    st.subheader("📁 File Upload")
    uploaded_file = st.file_uploader("Upload .txt, .docx, or .pdf", type=["txt", "docx", "pdf"])
    if uploaded_file is not None:
        if st.button("Load File Content", use_container_width=True):
            content = ""
            ext = os.path.splitext(uploaded_file.name)[1].lower()
            bytes_data = uploaded_file.getvalue()
            
            if ext == ".txt":
                content = bytes_data.decode("utf-8", errors="replace")
            elif ext == ".docx":
                doc = Document(io.BytesIO(bytes_data))
                content = "\n\n".join(p.text for p in doc.paragraphs if p.text.strip())
            elif ext == ".pdf":
                from pypdf import PdfReader
                reader = PdfReader(io.BytesIO(bytes_data))
                content = "\n\n".join([page.extract_text() for page in reader.pages if page.extract_text()])
                
            st.session_state.input_text = content
            st.success(f"Loaded {len(content)} characters!")
            st.rerun()

# Hero Header
st.markdown("""
<div class="hero">
    <h1>Para Paper V2</h1>
    <p>Scientific Paraphrasing, Anti-AI Humanizing, Manuscript Review & Paper Generation Workspace</p>
</div>
""", unsafe_allow_html=True)

# Tabs
tabs = st.tabs([
    "✍️ Paraphrase",
    "🤖→🧑 Humanize",
    "🔍 Proofread",
    "📝 Manuscript Review",
    "📄 Write Paper",
    "📊 Vocab Analysis"
])

# Helper for async execution in Streamlit
def run_async(coro):
    return asyncio.run(coro)

# Helper for word count
def get_words(text):
    return len(re.findall(r"\b[\w'-]+\b", text or ""))

# ----------------------------
# TAB 1: PARAPHRASE
# ----------------------------
with tabs[0]:
    st.header("Academic & Clinical Paraphrasing")
    col_in, col_out = st.columns(2, gap="medium")
    
    with col_in:
        st.subheader("Original Text")
        input_text = st.text_area("Input", value=st.session_state.input_text, height=300, key="para_in")
        st.caption(f"Words: {get_words(input_text)} | Chars: {len(input_text)}")
        
    with col_out:
        st.subheader("Paraphrased Output")
        output_text = st.text_area("Output", value=st.session_state.output_text, height=300, key="para_out")
        st.caption(f"Words: {get_words(output_text)} | Delta: {get_words(output_text) - get_words(input_text)}")
        
    c1, c2, c3 = st.columns([2, 2, 1])
    with c1:
        mode = st.radio("Mode", ["General Academic", "Medical / Clinical preservation"], horizontal=True)
    with c2:
        strength = st.slider("Transformation Strength", 1, 5, 3)
    with c3:
        st.write("")
        st.write("")
        run_para = st.button("Run Paraphrase", type="primary", use_container_width=True)
        
    if run_para and input_text.strip():
        with st.spinner("Paraphrasing text..."):
            agent = AntigravityAgent("academic_rewording_medical.md" if "Medical" in mode else "academic_rewording.md")
            res = run_async(agent.run(input_text, strength=strength))
            if "options" in res:
                opt_texts = [f"### [{opt['type']}]\n{opt['text']}" for opt in res["options"]]
                st.session_state.output_text = "\n\n".join(opt_texts)
            else:
                st.session_state.output_text = res.get("text", "")
            st.rerun()

# ----------------------------
# TAB 2: HUMANIZE
# ----------------------------
with tabs[1]:
    st.header("Anti-AI Humanizing Engine")
    st.write("Removes robotic LLM signatures using Wikipedia's 29-pattern taxonomy & Dr. Noora style.")
    
    col1, col2 = st.columns(2)
    with col1:
        h_mode = st.selectbox("Style Profile", ["Dr. Noora Style", "General Anti-AI Cleanup"])
        h_input = st.text_area("AI Text", height=250, key="h_in")
    with col2:
        h_strength = st.slider("Humanize Strength", 1, 5, 3, key="h_str")
        if st.button("Humanize Text", type="primary", use_container_width=True):
            if h_input.strip():
                with st.spinner("Removing AI signatures..."):
                    agent_file = "humanizer_noora.md" if "Noora" in h_mode else "humanizer_general.md"
                    agent = AntigravityAgent(agent_file)
                    res = run_async(agent.run(h_input, strength=h_strength))
                    st.session_state.h_out = res.get("text", "")
        
        st.text_area("Humanized Output", value=st.session_state.get("h_out", ""), height=200, key="h_out_disp")

# ----------------------------
# TAB 3: PROOFREAD
# ----------------------------
with tabs[2]:
    st.header("2-Phase Manuscript Audit")
    p_input = st.text_area("Manuscript Segment", height=200, key="p_in")
    
    col_p1, col_p2 = st.columns(2)
    with col_p1:
        if st.button("Phase 1: Audit Text", type="primary", use_container_width=True):
            if p_input.strip():
                with st.spinner("Auditing manuscript..."):
                    agent = AntigravityAgent("proofreading.md")
                    res = run_async(agent.run(p_input, payload_type="phase1"))
                    st.session_state.p_issues = res.get("issues", [])
                    
    with col_p2:
        if st.button("Phase 2: Apply All Fixes", use_container_width=True):
            if p_input.strip():
                with st.spinner("Applying corrections..."):
                    agent = AntigravityAgent("proofreading.md")
                    res = run_async(agent.run(p_input, payload_type="phase2"))
                    st.session_state.p_fixed = res.get("text", "")
                    
    if "p_issues" in st.session_state:
        st.subheader("Audit Issues")
        st.json(st.session_state.p_issues)
        
    if "p_fixed" in st.session_state:
        st.subheader("Proofread Output")
        st.text_area("Fixed Output", value=st.session_state.p_fixed, height=200)

# ----------------------------
# TAB 4: MANUSCRIPT REVIEW (5-PASS)
# ----------------------------
with tabs[3]:
    st.header("5-Pass Writing Quality Review")
    st.markdown("Applies Dr. Sainani's methodology: Clutter, Voice, Architecture, Terminology, Citation Integrity.")
    
    rev_mode = st.selectbox("Review Mode", ["full-review", "section-review", "targeted", "interactive"])
    rev_input = st.text_area("Manuscript Text", height=220, key="rev_in")
    
    if st.button("Run 5-Pass Review", type="primary"):
        if rev_input.strip():
            with st.spinner("Performing 5-pass audit..."):
                agent = AntigravityAgent("manuscript_review.md")
                res = run_async(agent.run(f"Mode: {rev_mode}\n\n{rev_input}"))
                st.session_state.rev_out = res.get("text", "")
                
    if "rev_out" in st.session_state:
        st.markdown(st.session_state.rev_out)

# ----------------------------
# TAB 5: WRITE PAPER
# ----------------------------
with tabs[4]:
    st.header("Paper Generation Assistant")
    doc_type = st.selectbox("Document Type", ["Research Paper", "Literature Review", "Case Report", "Grant Proposal"])
    topic = st.text_input("Topic / Title")
    outline = st.text_area("Outline / Key Findings (Optional)", height=150)
    
    if st.button("Generate Paper Draft & Peer Review", type="primary"):
        if topic.strip():
            with st.spinner("Drafting paper & conducting peer review..."):
                pw = PaperWriterAgent()
                res = run_async(pw.generate_draft(topic=topic, doc_type=doc_type, outline=outline))
                st.session_state.pw_res = res
                
    if "pw_res" in st.session_state:
        res = st.session_state.pw_res
        st.subheader("Generated Draft")
        st.markdown(res.get("draft", ""))
        st.divider()
        st.subheader("Peer Review Feedback")
        st.markdown(res.get("review", ""))
        
        docx_data = make_docx(res.get("draft", ""), title=f"{doc_type}: {topic}")
        st.download_button("Download Word Document (.docx)", data=docx_data, file_name="para_paper_v2_draft.docx")

# ----------------------------
# TAB 6: VOCAB ANALYSIS
# ----------------------------
with tabs[5]:
    st.header("Academic & Medical Vocabulary Analysis")
    v_input = st.text_area("Text to Analyze", height=200, key="v_in")
    
    if st.button("Analyze Vocabulary Density", type="primary"):
        if v_input.strip():
            score = get_academic_score(v_input)
            st.metric("Academic Vocabulary List (AVL) Score", f"{score * 100:.1f}%")
            st.info("Measures percentage of formal academic terms matched against the COCA Academic Vocabulary List.")

# Download section for main outputs
if st.session_state.output_text.strip():
    st.divider()
    st.subheader("Export Results")
    d_docx = make_docx(st.session_state.output_text, title="Para Paper V2 Export")
    st.download_button("Download (.docx)", data=d_docx, file_name="para_paper_v2_output.docx", mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document")
