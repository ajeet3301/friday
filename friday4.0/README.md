# FRIDAY AI Dashboard v3.0

## Quick Start

```bash
# 1. Clone / copy files
cd friday_dashboard

# 2. Install dependencies
pip install -r requirements.txt --break-system-packages

# 3. Set up environment
cp .env.example .env
# Edit .env — add your GROQ_API_KEY at minimum

# 4. Run
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Open browser → http://localhost:8000
# Admin panel  → http://localhost:8000/admin
```

---

## File Structure

```
friday_dashboard/
├── main.py               ← FastAPI backend (ALL logic here)
├── requirements.txt
├── .env.example          ← Copy to .env and fill keys
├── static/
│   ├── index.html        ← Main dashboard UI
│   └── admin.html        ← Admin panel
├── uploads/              ← PDF uploads land here (auto-created)
└── knowledge_base/       ← FAISS index + metadata (auto-created)
```

---

## Where to Plug In Your Code

### 1. Object Detection (Camera)
In `main.py`, find `VisionStream._process_frame()`:
```python
def _process_frame(self, frame: np.ndarray) -> np.ndarray:
    # ← PASTE your YOLO / MediaPipe / plant detection here
    # Set state["detected_object"] = "plant"  ← updates the UI badge
    return frame
```

### 2. AI Response Logic
In `main.py`, find `Brain.ask_ai()`:
```python
def ask_ai(self, query: str, kb_context: str = "") -> str:
    # ← PASTE your Groq / LangChain / custom LLM call here
    # kb_context is auto-injected from RAG when KB has docs
    ...
```

### 3. Adding New API Routes
Just add `@app.get("/api/your-endpoint")` anywhere in `main.py`.

---

## Features

| Feature | Where |
|---|---|
| Live webcam feed | Dashboard left column |
| Object detection label | Overlaid on camera + status card |
| Chat (text + voice) | Dashboard right column |
| Voice input | Browser Web Speech API (mic button) |
| PDF knowledge upload | Admin → Knowledge Base |
| RAG context injection | Automatic on every chat message |
| Theme editor | Admin → Theme |
| System prompt editor | Admin → System Prompt |
| Status badges | Header (Brain / Cam / KB) |

---

## Environment Variables

| Key | Required | Description |
|---|---|---|
| `GROQ_API_KEY` | ✅ | Your Groq API key |
| `GROQ_MODEL` | optional | Default: `llama-3.3-70b-versatile` |
| `CAMERA_INDEX` | optional | Default: `0` (first webcam) |
