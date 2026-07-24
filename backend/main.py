import os
import sys
import re
from typing import List, Optional
from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from agent_wrapper import AntigravityAgent, run_local_simulation
from academic_vocab import get_academic_score

app = FastAPI(
    title="Antigravity AI Writing Backend",
    description="FastAPI service for real-time paraphrasing, humanizing, proofreading, manuscript review, paper writing, and vocab analysis",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class TextPayload(BaseModel):
    text: str
    strength: int = 3

class HumanizePayload(BaseModel):
    text: str
    mode: str = "noora"
    strength: int = 3

class ProofreadPayload(BaseModel):
    text: str
    phase: str = "detection"
    approved_ids: Optional[List[int]] = None

class MedicalParaphrasePayload(BaseModel):
    text: str
    strength: int = 3

class ApiConfigPayload(BaseModel):
    provider: str = "gemini"
    api_key: str = ""
    model: str = ""
    base_url: str = ""

class PaperOutlinePayload(BaseModel):
    topic: str
    sections: Optional[List[str]] = None
    style: str = "academic"

paraphrase_agent = AntigravityAgent("academic_rewording.md")
paraphrase_medical_agent = AntigravityAgent("academic_rewording_medical.md")
humanizer_noora_agent = AntigravityAgent("humanizer_noora.md")
humanizer_general_agent = AntigravityAgent("humanizer_general.md")
proofread_agent = AntigravityAgent("proofreading.md")


@app.post("/api/configure")
async def configure_api(payload: ApiConfigPayload):
    """Set API provider and key at runtime (Link/Sync button)."""
    AntigravityAgent.set_api_config(
        provider=payload.provider,
        api_key=payload.api_key,
        model=payload.model,
        base_url=payload.base_url
    )
    print(f"[API] Provider configured: {payload.provider}")
    return {"status": "ok", "provider": payload.provider}


@app.post("/api/paraphrase")
async def paraphrase_text(payload: TextPayload):
    try:
        if not payload.text.strip():
            raise HTTPException(status_code=400, detail="Empty text selection")
        print(f"[API] Paraphrase request received. Text length: {len(payload.text)}, strength: {payload.strength}")
        result = await paraphrase_agent.run(payload.text, strength=payload.strength)
        return result
    except Exception as e:
        print(f"[API] Paraphrase error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/paraphrase/medical")
async def paraphrase_medical(payload: MedicalParaphrasePayload):
    try:
        if not payload.text.strip():
            raise HTTPException(status_code=400, detail="Empty text selection")
        print(f"[API] Medical Paraphrase request received. Text length: {len(payload.text)}, strength: {payload.strength}")
        result = await paraphrase_medical_agent.run(payload.text, strength=payload.strength)
        return result
    except Exception as e:
        print(f"[API] Medical Paraphrase error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/humanize")
async def humanize_text(payload: HumanizePayload):
    try:
        if not payload.text.strip():
            raise HTTPException(status_code=400, detail="Empty text selection")
        print(f"[API] Humanize request received (mode: {payload.mode}, strength: {payload.strength}). Text length: {len(payload.text)}")
        if payload.mode == "noora":
            result = await humanizer_noora_agent.run(payload.text, payload_type="noora", strength=payload.strength)
        else:
            result = await humanizer_general_agent.run(payload.text, payload_type="general", strength=payload.strength)
        return result
    except Exception as e:
        print(f"[API] Humanize error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/proofread")
async def proofread_text(payload: ProofreadPayload):
    try:
        if not payload.text.strip():
            raise HTTPException(status_code=400, detail="Empty text selection")
        print(f"[API] Proofread request received (phase: {payload.phase}). Text length: {len(payload.text)}")
        if payload.phase == "detection":
            result = await proofread_agent.run(payload.text, payload_type="phase1")
            return result
        else:
            result = await proofread_agent.run(payload.text, payload_type="phase2")
            return result
    except Exception as e:
        print(f"[API] Proofread error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/manuscript-review")
async def manuscript_review(payload: TextPayload):
    """Full manuscript review: proofread + academic scoring + style analysis."""
    try:
        if not payload.text.strip():
            raise HTTPException(status_code=400, detail="Empty text selection")
        print(f"[API] Manuscript Review request received. Text length: {len(payload.text)}")

        proofread_result = await proofread_agent.run(payload.text, payload_type="phase1")
        issues = proofread_result.get("issues", []) if proofread_result.get("status") == "success" else []

        score = get_academic_score(payload.text)
        sentences = [s.strip() for s in re.split(r'[.!?]+', payload.text) if s.strip()]
        words = payload.text.split()
        avg_sentence_length = round(len(words) / max(len(sentences), 1), 1)

        return {
            "status": "success",
            "issues": issues,
            "academic_score": round(score, 2),
            "stats": {
                "word_count": len(words),
                "sentence_count": len(sentences),
                "avg_sentence_length": avg_sentence_length,
                "char_count": len(payload.text)
            }
        }
    except Exception as e:
        print(f"[API] Manuscript Review error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/write-paper")
async def write_paper(payload: PaperOutlinePayload):
    """Generate academic paper content from topic/outline."""
    try:
        if not payload.topic.strip():
            raise HTTPException(status_code=400, detail="Empty topic")
        print(f"[API] Write Paper request received. Topic: {payload.topic[:50]}...")

        text = f"Topic: {payload.topic}"
        if payload.sections:
            text += "\nSections: " + ", ".join(payload.sections)

        result = await paraphrase_agent.run(text, strength=3)
        return result
    except Exception as e:
        print(f"[API] Write Paper error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/vocab-analysis")
async def vocab_analysis(payload: TextPayload):
    """Analyze text for academic vocabulary density and readability."""
    try:
        if not payload.text.strip():
            raise HTTPException(status_code=400, detail="Empty text")
        print(f"[API] Vocab Analysis request received. Text length: {len(payload.text)}")

        score = get_academic_score(payload.text)
        words = payload.text.split()
        word_count = len(words)
        unique_words = len(set(w.lower().strip(".,!?;:\"'()[]") for w in words))
        sentences = [s.strip() for s in re.split(r'[.!?]+', payload.text) if s.strip()]
        sentence_count = len(sentences)
        avg_word_length = round(sum(len(w.strip(".,!?;:\"'()[]")) for w in words) / max(word_count, 1), 2)
        long_words = sum(1 for w in words if len(w.strip(".,!?;:\"'()[]")) > 6)

        return {
            "status": "success",
            "academic_score": round(score, 2),
            "stats": {
                "word_count": word_count,
                "unique_words": unique_words,
                "sentence_count": sentence_count,
                "avg_word_length": avg_word_length,
                "long_words": long_words,
                "lexical_diversity": round(unique_words / max(word_count, 1) * 100, 1)
            }
        }
    except Exception as e:
        print(f"[API] Vocab Analysis error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/health")
async def health_check():
    return {"status": "ok", "message": "Antigravity AI Backend is running securely"}


@app.post("/api/upload")
async def upload_file(file: UploadFile = File(...)):
    """Extract text from uploaded .docx, .pdf, or .txt files."""
    try:
        filename = file.filename or ""
        ext = os.path.splitext(filename)[1].lower()
        content = await file.read()

        if ext == ".txt":
            text = content.decode("utf-8", errors="replace")

        elif ext == ".docx":
            import io
            from docx import Document
            doc = Document(io.BytesIO(content))
            paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
            text = "\n\n".join(paragraphs)

        elif ext == ".pdf":
            import io
            from pypdf import PdfReader
            reader = PdfReader(io.BytesIO(content))
            pages = []
            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    pages.append(page_text)
            text = "\n\n".join(pages)

        else:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported file type: {ext}. Use .docx, .pdf, or .txt"
            )

        if not text.strip():
            raise HTTPException(
                status_code=400,
                detail="No text could be extracted from the file."
            )

        print(f"[API] File upload: {filename} ({ext}), extracted {len(text)} chars")
        return {"text": text, "filename": filename}

    except HTTPException:
        raise
    except Exception as e:
        print(f"[API] File upload error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to process file: {str(e)}")


@app.get("/api/ollama-status")
async def check_ollama_status():
    """Check if Ollama is running and the configured model is available."""
    model = os.getenv("OLLAMA_MODEL", "llama3.2").strip()
    base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434").rstrip("/")

    if not model:
        return {"available": False, "model": "", "reason": "No model configured"}

    try:
        import httpx
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(f"{base_url}/api/tags")
            if resp.status_code != 200:
                return {"available": False, "model": model, "reason": "Ollama not responding"}
            models = resp.json().get("models", [])
            found = any(model in m.get("name", "") for m in models)
            if found:
                return {"available": True, "model": model}
            return {
                "available": False,
                "model": model,
                "reason": f"Model '{model}' not found. Run: ollama pull {model}"
            }
    except Exception:
        return {"available": False, "model": model, "reason": "Ollama not running"}


# Serve static frontend files (index.html, taskpane.css, taskpane.js)
def _get_project_base_dir():
    if getattr(sys, 'frozen', False):
        return sys._MEIPASS
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

frontend_dir = os.path.join(_get_project_base_dir(), "frontend")
if os.path.exists(frontend_dir):
    print(f"[API] Serving frontend from: {frontend_dir}")
    app.mount("/", StaticFiles(directory=frontend_dir, html=True), name="frontend")
else:
    print(f"[WARNING] Frontend directory not found at: {frontend_dir}")

if __name__ == "__main__":
    import uvicorn
    import socket
    
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    port = 8765
    result = sock.connect_ex(('127.0.0.1', port))
    sock.close()
    
    if result == 0:
        print(f"[WARNING] Port {port} is already in use by another program.")
        print(f"[WARNING] Close that program or change the port in main.py.")
        print()
    
    print(f"Starting server at http://localhost:{port}")
    uvicorn.run("main:app", host="127.0.0.1", port=port, reload=False)
