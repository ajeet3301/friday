"""
╔══════════════════════════════════════════════════════════════╗
║           FRIDAY DASHBOARD  —  FastAPI Backend               ║
╚══════════════════════════════════════════════════════════════╝

Run:  uvicorn main:app --reload --host 0.0.0.0 --port 8000
"""

import os, json, time, base64, threading, asyncio, shutil
from datetime import datetime
from pathlib import Path
from typing import Optional

import cv2
import numpy as np
from fastapi import FastAPI, UploadFile, File, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

# ── Optional AI / RAG imports ──────────────────────────────────────────────
try:
    from groq import Groq
    GROQ_AVAILABLE = True
except ImportError:
    GROQ_AVAILABLE = False
    print("⚠️  groq not installed")

try:
    from langchain_community.document_loaders import PyPDFLoader
    from langchain.text_splitter import RecursiveCharacterTextSplitter
    from langchain_community.vectorstores import FAISS
    from langchain_community.embeddings import HuggingFaceEmbeddings
    RAG_AVAILABLE = True
except ImportError:
    RAG_AVAILABLE = False
    print("⚠️  langchain / FAISS not installed — RAG disabled")

load_dotenv()

# ═══════════════════════════════════════════════════════════════════════════
# CONFIG
# ═══════════════════════════════════════════════════════════════════════════

UPLOAD_DIR       = Path("uploads")
KB_DIR           = Path("knowledge_base")
STATIC_DIR       = Path("static")
GROQ_API_KEY     = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL       = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
GROQ_WHISPER     = os.getenv("GROQ_WHISPER_MODEL", "whisper-large-v3-turbo")
CAMERA_INDEX     = int(os.getenv("CAMERA_INDEX", "0"))

for d in [UPLOAD_DIR, KB_DIR, STATIC_DIR]:
    d.mkdir(exist_ok=True)

# ═══════════════════════════════════════════════════════════════════════════
# STATE  (in-memory, replace with DB for production)
# ═══════════════════════════════════════════════════════════════════════════

state = {
    "wake_active":    False,
    "camera_active":  False,
    "detected_object": "—",
    "kb_docs":        [],           # list of {name, pages, added}
    "chat_history":   [],           # list of {role, content, time}
    "theme": {
        "accent":     "#00e5ff",
        "bg":         "#0a0f1a",
        "surface":    "#111827",
        "text":       "#e2e8f0",
        "font":       "Space Mono",
    }
}

# ═══════════════════════════════════════════════════════════════════════════
# RAG MANAGER
# ═══════════════════════════════════════════════════════════════════════════

class RAGManager:
    """Handles PDF ingestion + vector search."""

    def __init__(self):
        self.vectorstore = None
        self.embeddings  = None
        self._init_embeddings()
        self._load_existing()

    def _init_embeddings(self):
        if not RAG_AVAILABLE:
            return
        try:
            self.embeddings = HuggingFaceEmbeddings(
                model_name="sentence-transformers/all-MiniLM-L6-v2"
            )
            print("✅ RAG embeddings ready")
        except Exception as e:
            print(f"⚠️  Embeddings error: {e}")

    def _load_existing(self):
        """Load previously saved FAISS index."""
        idx_path = KB_DIR / "faiss_index"
        if idx_path.exists() and RAG_AVAILABLE and self.embeddings:
            try:
                self.vectorstore = FAISS.load_local(
                    str(idx_path), self.embeddings,
                    allow_dangerous_deserialization=True
                )
                print(f"✅ RAG index loaded ({str(idx_path)})")
            except Exception as e:
                print(f"⚠️  RAG index load failed: {e}")

        # Load metadata
        meta_path = KB_DIR / "meta.json"
        if meta_path.exists():
            with open(meta_path) as f:
                state["kb_docs"] = json.load(f)

    def ingest(self, pdf_path: str, filename: str) -> dict:
        """Load PDF → split → embed → save index."""
        if not RAG_AVAILABLE:
            return {"error": "RAG libraries not installed"}
        if not self.embeddings:
            return {"error": "Embeddings not initialized"}
        try:
            loader   = PyPDFLoader(pdf_path)
            pages    = loader.load()
            splitter = RecursiveCharacterTextSplitter(chunk_size=800, chunk_overlap=100)
            docs     = splitter.split_documents(pages)

            if self.vectorstore is None:
                self.vectorstore = FAISS.from_documents(docs, self.embeddings)
            else:
                self.vectorstore.add_documents(docs)

            self.vectorstore.save_local(str(KB_DIR / "faiss_index"))

            meta = {"name": filename, "pages": len(pages), "added": datetime.now().isoformat()}
            state["kb_docs"].append(meta)
            with open(KB_DIR / "meta.json", "w") as f:
                json.dump(state["kb_docs"], f)

            return {"pages": len(pages), "chunks": len(docs)}
        except Exception as e:
            return {"error": str(e)}

    def query(self, question: str, k: int = 3) -> str:
        """Return relevant context chunks for a question."""
        if not self.vectorstore:
            return ""
        try:
            docs = self.vectorstore.similarity_search(question, k=k)
            return "\n\n".join(d.page_content for d in docs)
        except:
            return ""

    def delete_doc(self, name: str):
        """Remove from metadata (full re-index needed for real deletion)."""
        state["kb_docs"] = [d for d in state["kb_docs"] if d["name"] != name]
        with open(KB_DIR / "meta.json", "w") as f:
            json.dump(state["kb_docs"], f)


rag = RAGManager()

# ═══════════════════════════════════════════════════════════════════════════
# AI BRAIN
# ═══════════════════════════════════════════════════════════════════════════

class Brain:
    """Friday's LLM brain — swap provider here."""

    SYSTEM_PROMPT = """You are Friday, an advanced AI assistant.
Be concise, helpful, and occasionally call the user "Boss".
Keep answers under 4 sentences unless detailed explanation is needed.
If knowledge base context is provided, use it to answer accurately.
Current time: {time}"""

    def __init__(self):
        self.client = None
        if GROQ_AVAILABLE and GROQ_API_KEY:
            self.client = Groq(api_key=GROQ_API_KEY)
            print(f"✅ Brain: Groq ({GROQ_MODEL})")
        else:
            print("⚠️  Brain: Echo mode (no Groq API key)")

    # ── PASTE YOUR OWN ask_ai LOGIC HERE ──────────────────────────────────
    def ask_ai(self, query: str, kb_context: str = "") -> str:
        """
        Main entrypoint — replace this body with your own logic if needed.
        kb_context: retrieved RAG text (auto-injected when KB has docs)
        """
        if not self.client:
            return f"[Echo] You said: {query}. Add GROQ_API_KEY to .env for real responses."

        system = self.SYSTEM_PROMPT.format(time=datetime.now().strftime("%I:%M %p, %A %d %B %Y"))
        if kb_context:
            system += f"\n\n--- Knowledge Base Context ---\n{kb_context}\n--- End Context ---"

        history = [{"role": m["role"], "content": m["content"]}
                   for m in state["chat_history"][-8:]]

        msgs = [{"role": "system", "content": system}] + history + \
               [{"role": "user", "content": query}]

        try:
            r = self.client.chat.completions.create(
                model=GROQ_MODEL, messages=msgs, max_tokens=500, temperature=0.7
            )
            return r.choices[0].message.content.strip()
        except Exception as e:
            return f"Brain error: {e}"


brain = Brain()

# ═══════════════════════════════════════════════════════════════════════════
# VISION
# ═══════════════════════════════════════════════════════════════════════════

class VisionStream:
    """Webcam grab + optional object detection placeholder."""

    def __init__(self):
        self.cap     = None
        self.running = False
        self.frame   = None

    def start(self):
        if self.running:
            return
        self.cap = cv2.VideoCapture(CAMERA_INDEX)
        if self.cap.isOpened():
            self.running = True
            state["camera_active"] = True
            t = threading.Thread(target=self._loop, daemon=True)
            t.start()
            print("✅ Camera started")
        else:
            print("⚠️  Camera not found")

    def stop(self):
        self.running = False
        state["camera_active"] = False
        if self.cap:
            self.cap.release()
            self.cap = None

    def _loop(self):
        while self.running and self.cap and self.cap.isOpened():
            ok, frame = self.cap.read()
            if ok:
                frame = self._process_frame(frame)
                self.frame = frame
            time.sleep(0.033)

    # ── PASTE YOUR DETECTION LOGIC HERE ───────────────────────────────────
    def _process_frame(self, frame: np.ndarray) -> np.ndarray:
        """
        Drop in your cv2 processing here.
        e.g. YOLO, MediaPipe, plant detection, etc.
        Update state["detected_object"] with what you find.
        """
        # Example: flip + overlay
        frame = cv2.flip(frame, 1)
        # state["detected_object"] = "plant"  ← set from your detector
        return frame

    def get_jpeg(self) -> bytes | None:
        if self.frame is None:
            return None
        _, buf = cv2.imencode(".jpg", self.frame, [cv2.IMWRITE_JPEG_QUALITY, 75])
        return buf.tobytes()


vision = VisionStream()

# ═══════════════════════════════════════════════════════════════════════════
# FASTAPI APP
# ═══════════════════════════════════════════════════════════════════════════

app = FastAPI(title="Friday Dashboard", version="3.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
app.mount("/static", StaticFiles(directory="static"), name="static")

# ── Pydantic models ────────────────────────────────────────────────────────

class ChatMsg(BaseModel):
    message: str

class ThemeUpdate(BaseModel):
    accent: Optional[str] = None
    bg:     Optional[str] = None
    surface:Optional[str] = None
    text:   Optional[str] = None
    font:   Optional[str] = None

class WakeState(BaseModel):
    active: bool

# ═══════════════════════════════════════════════════════════════════════════
# ROUTES
# ═══════════════════════════════════════════════════════════════════════════

@app.get("/", response_class=HTMLResponse)
async def index():
    with open("static/index.html") as f:
        return f.read()

@app.get("/admin", response_class=HTMLResponse)
async def admin():
    with open("static/admin.html") as f:
        return f.read()

# ── Status ────────────────────────────────────────────────────────────────

@app.get("/api/status")
def get_status():
    return {
        "wake_active":     state["wake_active"],
        "camera_active":   state["camera_active"],
        "detected_object": state["detected_object"],
        "kb_count":        len(state["kb_docs"]),
        "rag_available":   RAG_AVAILABLE,
        "groq_available":  GROQ_AVAILABLE and bool(GROQ_API_KEY),
        "time":            datetime.now().strftime("%I:%M %p"),
        "date":            datetime.now().strftime("%A, %d %B %Y"),
    }

# ── Wake Word Toggle ──────────────────────────────────────────────────────

@app.post("/api/wake")
def set_wake(body: WakeState):
    state["wake_active"] = body.active
    return {"wake_active": state["wake_active"]}

# ── Chat ──────────────────────────────────────────────────────────────────

@app.post("/api/chat")
def chat(body: ChatMsg):
    q = body.message.strip()
    if not q:
        raise HTTPException(400, "Empty message")

    kb_ctx = rag.query(q)
    answer = brain.ask_ai(q, kb_ctx)

    now = datetime.now().strftime("%I:%M %p")
    state["chat_history"].append({"role": "user",      "content": q,      "time": now})
    state["chat_history"].append({"role": "assistant",  "content": answer, "time": now})

    if len(state["chat_history"]) > 60:
        state["chat_history"] = state["chat_history"][-60:]

    return {"response": answer, "used_kb": bool(kb_ctx)}

@app.get("/api/chat/history")
def chat_history():
    return {"history": state["chat_history"]}

@app.delete("/api/chat/history")
def clear_history():
    state["chat_history"] = []
    return {"ok": True}

# ── Camera ────────────────────────────────────────────────────────────────

@app.post("/api/camera/start")
def camera_start():
    vision.start()
    return {"camera_active": state["camera_active"]}

@app.post("/api/camera/stop")
def camera_stop():
    vision.stop()
    return {"camera_active": False}

@app.get("/api/camera/frame")
def camera_frame():
    jpg = vision.get_jpeg()
    if jpg is None:
        raise HTTPException(404, "No frame")
    b64 = base64.b64encode(jpg).decode()
    return {"frame": b64, "detected": state["detected_object"]}

# ── WebSocket for live camera ─────────────────────────────────────────────

@app.websocket("/ws/camera")
async def ws_camera(ws: WebSocket):
    await ws.accept()
    try:
        while True:
            jpg = vision.get_jpeg()
            if jpg:
                b64 = base64.b64encode(jpg).decode()
                await ws.send_json({"frame": b64, "detected": state["detected_object"]})
            await asyncio.sleep(0.1)
    except WebSocketDisconnect:
        pass

# ── Knowledge Base ────────────────────────────────────────────────────────

@app.post("/api/kb/upload")
async def kb_upload(file: UploadFile = File(...)):
    if not file.filename.endswith(".pdf"):
        raise HTTPException(400, "Only PDF files accepted")

    save_path = UPLOAD_DIR / file.filename
    with open(save_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    result = rag.ingest(str(save_path), file.filename)
    if "error" in result:
        raise HTTPException(500, result["error"])

    return {"filename": file.filename, **result}

@app.get("/api/kb/docs")
def kb_docs():
    return {"docs": state["kb_docs"]}

@app.delete("/api/kb/docs/{name}")
def kb_delete(name: str):
    rag.delete_doc(name)
    return {"ok": True}

# ── Theme ────────────────────────────────────────────────────────────────

@app.get("/api/theme")
def get_theme():
    return state["theme"]

@app.post("/api/theme")
def update_theme(body: ThemeUpdate):
    for k, v in body.dict(exclude_none=True).items():
        state["theme"][k] = v
    return state["theme"]

@app.post("/api/theme/reset")
def reset_theme():
    state["theme"] = {
        "accent": "#00e5ff", "bg": "#0a0f1a", "surface": "#111827",
        "text": "#e2e8f0", "font": "Space Mono"
    }
    return state["theme"]

# ═══════════════════════════════════════════════════════════════════════════
# STARTUP / SHUTDOWN
# ═══════════════════════════════════════════════════════════════════════════

@app.on_event("startup")
def startup():
    print("🚀 Friday Dashboard starting...")

@app.on_event("shutdown")
def shutdown():
    vision.stop()
    print("✅ Friday Dashboard stopped.")
