import os
from typing import List, Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from agent_wrapper import AntigravityAgent

app = FastAPI(
    title="Antigravity AI Writing Backend",
    description="FastAPI service for real-time paraphrasing, humanizing, and proofreading via google-antigravity",
    version="1.0.0"
)

# CORS Configuration
# Allows secure requests from MS Word WebView2 contexts
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all for local development and sideloading
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request Models
class TextPayload(BaseModel):
    text: str
    strength: int = 3

class HumanizePayload(BaseModel):
    text: str
    mode: str = "noora"  # "noora" or "general"
    strength: int = 3

class ProofreadPayload(BaseModel):
    text: str
    phase: str = "detection"  # "detection" or "fix"
    approved_ids: Optional[List[int]] = None

class MedicalParaphrasePayload(BaseModel):
    text: str
    strength: int = 3

# Initialize Agents
paraphrase_agent = AntigravityAgent("academic_rewording.md")
paraphrase_medical_agent = AntigravityAgent("academic_rewording_medical.md")
humanizer_noora_agent = AntigravityAgent("humanizer_noora.md")
humanizer_general_agent = AntigravityAgent("humanizer_general.md")
proofread_agent = AntigravityAgent("proofreading.md")

# API Endpoints
@app.post("/api/paraphrase")
async def handle_paraphrase(payload: TextPayload):
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
async def handle_medical_paraphrase(payload: MedicalParaphrasePayload):
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
async def handle_humanize(payload: HumanizePayload):
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
async def handle_proofread(payload: ProofreadPayload):
    try:
        if not payload.text.strip():
            raise HTTPException(status_code=400, detail="Empty text selection")
            
        print(f"[API] Proofread request received (phase: {payload.phase}). Text length: {len(payload.text)}")
        
        if payload.phase == "detection":
            # Phase 1: Detection
            result = await proofread_agent.run(payload.text, payload_type="phase1")
            return result
        else:
            # Phase 2: Fix
            result = await proofread_agent.run(payload.text, payload_type="phase2")
            return result
    except Exception as e:
        print(f"[API] Proofread error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Health check endpoint
@app.get("/api/health")
async def health_check():
    return {"status": "ok", "message": "Antigravity AI Backend is running securely"}

# Serve static frontend files (index.html, taskpane.css, taskpane.js)
frontend_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "frontend")
if os.path.exists(frontend_dir):
    print(f"[API] Serving frontend from: {frontend_dir}")
    app.mount("/", StaticFiles(directory=frontend_dir, html=True), name="frontend")
else:
    print(f"[WARNING] Frontend directory not found at: {frontend_dir}")

if __name__ == "__main__":
    import uvicorn
    import socket
    
    # Check if port is available
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    port = 8765
    result = sock.connect_ex(('127.0.0.1', port))
    sock.close()
    
    if result == 0:
        print(f"[WARNING] Port {port} is already in use by another program.")
        print(f"[WARNING] Close that program or change the port in main.py.")
        print()
    
    print("=" * 55)
    print("  AI Writing Assistant Backend")
    print("=" * 55)
    print(f"  Server:  http://localhost:{port}")
    print(f"  Open in your browser to start")
    print("=" * 55)
    uvicorn.run("main:app", host="127.0.0.1", port=port, reload=False)
