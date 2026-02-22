"""
FRIDAY AI — Gemini-style clean UI
Run: streamlit run main.py
"""

import os, base64, time
from datetime import datetime
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv

load_dotenv()

# ── Optional imports ──────────────────────────────────────────────────────
try:
    from groq import Groq
    GROQ_OK = True
except ImportError:
    GROQ_OK = False

try:
    from langchain_huggingface import HuggingFaceEmbeddings
    from langchain_community.document_loaders import PyPDFLoader
    from langchain.text_splitter import RecursiveCharacterTextSplitter
    from langchain_community.vectorstores import FAISS
    RAG_OK = True
except ImportError:
    RAG_OK = False

try:
    import cv2, numpy as np
    CAM_OK = True
except ImportError:
    CAM_OK = False

# ─────────────────────────────────────────────────────────────────────────
# DIRS
# ─────────────────────────────────────────────────────────────────────────
Path("uploads").mkdir(exist_ok=True)
Path("knowledge_base").mkdir(exist_ok=True)

# ─────────────────────────────────────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Friday",
    page_icon="✦",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ─────────────────────────────────────────────────────────────────────────
# CSS  — Gemini-inspired: white/soft bg, minimal, large camera, bottom bar
# ─────────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Google+Sans:wght@400;500;700&family=Google+Sans+Mono&display=swap');
/* fallback if Google Sans not available */
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;600&family=DM+Mono&display=swap');

:root {
  --bg:       #0f0f0f;
  --surface:  #1c1c1c;
  --surface2: #242424;
  --border:   rgba(255,255,255,.08);
  --text:     #e8eaed;
  --muted:    #9aa0a6;
  --accent:   #8ab4f8;
  --red:      #f28b82;
  --green:    #81c995;
  --sans:     'DM Sans', 'Google Sans', sans-serif;
  --mono:     'DM Mono', 'Google Sans Mono', monospace;
}

html, body, [class*="css"] {
  font-family: var(--sans) !important;
  background: var(--bg) !important;
  color: var(--text) !important;
}

/* Hide streamlit chrome */
#MainMenu, footer, header { visibility: hidden; }
.block-container { padding: 0 !important; max-width: 100% !important; }
section[data-testid="stSidebar"] { display: none !important; }

/* ── TOP NAV ── */
.top-nav {
  display: flex; align-items: center; justify-content: space-between;
  padding: 14px 24px;
  border-bottom: 1px solid var(--border);
  background: var(--bg);
  position: sticky; top: 0; z-index: 100;
}
.nav-logo {
  font-size: 1.1rem; font-weight: 600; color: var(--text);
  display: flex; align-items: center; gap: 8px; letter-spacing: -.01em;
}
.nav-logo span { color: var(--accent); }
.nav-pills { display: flex; gap: 6px; }
.nav-pill {
  padding: 6px 14px; border-radius: 20px; font-size: .8rem;
  border: 1px solid var(--border); color: var(--muted);
  cursor: pointer; transition: .15s; background: transparent;
  font-family: var(--sans);
}
.nav-pill:hover, .nav-pill.active {
  background: var(--surface2); color: var(--text);
  border-color: rgba(255,255,255,.15);
}
.nav-right { display: flex; align-items: center; gap: 10px; }
.status-dot {
  width: 8px; height: 8px; border-radius: 50%;
  display: inline-block; margin-right: 4px;
}
.dot-green { background: var(--green); box-shadow: 0 0 6px var(--green); }
.dot-grey  { background: #5f6368; }
.dot-blue  { background: var(--accent); box-shadow: 0 0 6px var(--accent); animation: pulse 2s infinite; }
@keyframes pulse { 0%,100%{opacity:1} 50%{opacity:.4} }

/* ── MAIN BODY ── */
.main-body {
  display: flex;
  height: calc(100vh - 57px);
  overflow: hidden;
}

/* ── LEFT PANEL: CAMERA ── */
.cam-panel {
  width: 55%;
  display: flex;
  flex-direction: column;
  border-right: 1px solid var(--border);
  background: #000;
  position: relative;
}
.cam-feed {
  flex: 1;
  display: flex; align-items: center; justify-content: center;
  overflow: hidden;
  position: relative;
}
.cam-feed img { width: 100%; height: 100%; object-fit: cover; }
.cam-offline {
  display: flex; flex-direction: column; align-items: center; gap: 12px;
  color: #5f6368; font-size: .85rem;
}
.cam-offline-icon { font-size: 3rem; opacity: .3; }

/* Detection overlay */
.detect-overlay {
  position: absolute; bottom: 16px; left: 16px;
  background: rgba(0,0,0,.7); backdrop-filter: blur(8px);
  border: 1px solid rgba(255,255,255,.12);
  border-radius: 8px; padding: 8px 14px;
  font-size: .78rem; color: var(--text);
  font-family: var(--mono);
}
.detect-label { color: var(--accent); font-size: .7rem; margin-bottom: 2px; }

/* Cam controls bar */
.cam-bar {
  padding: 12px 16px;
  display: flex; align-items: center; gap: 10px;
  border-top: 1px solid var(--border);
  background: rgba(0,0,0,.4);
}
.cam-btn {
  padding: 8px 18px; border-radius: 20px; font-size: .78rem;
  border: 1px solid var(--border); color: var(--muted);
  background: var(--surface); cursor: pointer;
  font-family: var(--sans); transition: .15s; white-space: nowrap;
}
.cam-btn:hover { background: var(--surface2); color: var(--text); }
.cam-btn.primary {
  background: var(--accent); color: #000;
  border-color: transparent; font-weight: 500;
}
.cam-btn.primary:hover { opacity: .9; }

/* ── RIGHT PANEL: CHAT ── */
.chat-panel {
  flex: 1;
  display: flex;
  flex-direction: column;
  background: var(--bg);
  overflow: hidden;
}
.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: 20px 24px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}
.chat-messages::-webkit-scrollbar { width: 4px; }
.chat-messages::-webkit-scrollbar-thumb { background: var(--border); border-radius: 2px; }

/* Welcome state */
.welcome {
  display: flex; flex-direction: column; align-items: center;
  justify-content: center; flex: 1; gap: 8px; padding: 40px;
  text-align: center;
}
.welcome-title { font-size: 1.6rem; font-weight: 300; color: var(--text); }
.welcome-title b { color: var(--accent); font-weight: 600; }
.welcome-sub { font-size: .85rem; color: var(--muted); max-width: 300px; line-height: 1.6; }
.suggestion-chips { display: flex; flex-wrap: wrap; gap: 8px; justify-content: center; margin-top: 16px; }
.chip {
  padding: 8px 16px; border-radius: 20px; font-size: .8rem;
  border: 1px solid var(--border); color: var(--muted);
  cursor: pointer; transition: .15s;
}
.chip:hover { background: var(--surface2); color: var(--text); border-color: rgba(255,255,255,.2); }

/* Messages */
.msg-row { display: flex; gap: 10px; align-items: flex-start; }
.msg-row.user { flex-direction: row-reverse; }
.avatar {
  width: 28px; height: 28px; border-radius: 50%;
  display: flex; align-items: center; justify-content: center;
  font-size: .75rem; flex-shrink: 0; margin-top: 2px;
}
.avatar-ai  { background: var(--surface2); color: var(--accent); border: 1px solid var(--border); }
.avatar-usr { background: #444; color: var(--text); }
.bubble {
  max-width: 78%;
  padding: 10px 14px;
  border-radius: 18px;
  font-size: .85rem;
  line-height: 1.6;
}
.bubble-ai  { background: var(--surface); border-radius: 4px 18px 18px 18px; }
.bubble-usr { background: var(--surface2); border-radius: 18px 4px 18px 18px; }
.bubble-meta { font-size: .62rem; color: #5f6368; margin-top: 4px; }
.kb-chip {
  display: inline-block; font-size: .62rem; padding: 1px 6px;
  background: rgba(138,180,248,.1); border: 1px solid rgba(138,180,248,.25);
  border-radius: 8px; color: var(--accent); margin-left: 6px; vertical-align: middle;
}
.typing { display: flex; gap: 5px; padding: 12px 16px; }
.typing span {
  width: 6px; height: 6px; border-radius: 50%; background: var(--muted);
  animation: bounce .9s infinite;
}
.typing span:nth-child(2){ animation-delay:.15s; }
.typing span:nth-child(3){ animation-delay:.3s; }
@keyframes bounce { 0%,100%{transform:translateY(0);opacity:.4} 50%{transform:translateY(-5px);opacity:1} }

/* ── BOTTOM INPUT BAR ── */
.input-area {
  padding: 14px 20px 18px;
  border-top: 1px solid var(--border);
  background: var(--bg);
}
.input-wrap {
  display: flex; align-items: flex-end; gap: 10px;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 24px;
  padding: 8px 8px 8px 16px;
  transition: .2s;
}
.input-wrap:focus-within {
  border-color: rgba(138,180,248,.4);
  box-shadow: 0 0 0 3px rgba(138,180,248,.07);
}

/* Streamlit overrides for inputs */
.stTextInput > div > div > input {
  background: transparent !important;
  border: none !important;
  box-shadow: none !important;
  color: var(--text) !important;
  font-family: var(--sans) !important;
  font-size: .9rem !important;
  padding: 4px 0 !important;
}
.stButton > button {
  background: var(--accent) !important;
  color: #000 !important;
  border: none !important;
  border-radius: 20px !important;
  font-family: var(--sans) !important;
  font-weight: 500 !important;
  padding: 8px 20px !important;
  font-size: .8rem !important;
  transition: .15s !important;
}
.stButton > button:hover { opacity: .9 !important; }

/* ── SLIDE-IN PANEL (PDF upload) ── */
.slide-panel {
  position: fixed; right: 0; top: 57px; bottom: 0;
  width: 320px;
  background: var(--surface);
  border-left: 1px solid var(--border);
  padding: 20px;
  z-index: 200;
  transform: translateX(100%);
  transition: transform .25s cubic-bezier(.4,0,.2,1);
  overflow-y: auto;
}
.slide-panel.open { transform: translateX(0); }
.panel-header {
  font-size: .95rem; font-weight: 600; margin-bottom: 16px;
  display: flex; align-items: center; justify-content: space-between;
}
.panel-close {
  width: 28px; height: 28px; border-radius: 50%;
  background: var(--surface2); border: none;
  color: var(--muted); cursor: pointer; font-size: .9rem;
  display: flex; align-items: center; justify-content: center;
}
.doc-item {
  display: flex; align-items: center; justify-content: space-between;
  padding: 10px 12px; border-radius: 10px;
  background: var(--surface2); margin-bottom: 8px;
  border: 1px solid var(--border);
}
.doc-name { font-size: .8rem; color: var(--text); }
.doc-meta { font-size: .68rem; color: var(--muted); margin-top: 2px; }
.doc-del  { background: none; border: none; color: var(--muted); cursor: pointer; font-size: .85rem; }
.doc-del:hover { color: var(--red); }
.stFileUploader > div {
  background: var(--surface2) !important;
  border: 2px dashed rgba(138,180,248,.25) !important;
  border-radius: 12px !important;
}
.section-label {
  font-size: .7rem; color: var(--muted); letter-spacing: .06em;
  text-transform: uppercase; margin-bottom: 8px; margin-top: 16px;
}
.api-input > div > div > input {
  background: var(--surface2) !important;
  border: 1px solid var(--border) !important;
  border-radius: 8px !important;
  color: var(--text) !important;
  font-family: var(--mono) !important;
  font-size: .78rem !important;
}
.stTextArea > div > div > textarea {
  background: var(--surface2) !important;
  border: 1px solid var(--border) !important;
  border-radius: 10px !important;
  color: var(--text) !important;
  font-family: var(--sans) !important;
  font-size: .82rem !important;
}
.save-btn > button {
  background: var(--green) !important;
  color: #000 !important;
  width: 100% !important;
}
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────
# SESSION STATE
# ─────────────────────────────────────────────────────────────────────────
def _init():
    d = {
        "messages":      [],
        "vectorstore":   None,
        "kb_docs":       [],
        "panel_open":    False,
        "detected":      "Nothing",
        "cam_frame":     None,
        "groq_key":      os.getenv("GROQ_API_KEY", ""),
        "groq_model":    os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile"),
        "sys_prompt":    "You are Friday, a smart AI assistant. Be concise and helpful. Call the user Boss sometimes.",
        "wake_on":       True,
    }
    for k, v in d.items():
        if k not in st.session_state:
            st.session_state[k] = v
_init()

# ─────────────────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────────────────
@st.cache_resource
def load_embeddings():
    if not RAG_OK: return None
    try:
        return HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
    except:
        return None

def get_client():
    key = st.session_state.groq_key
    if GROQ_OK and key:
        return Groq(api_key=key)
    return None

def rag_query(q):
    vs = st.session_state.vectorstore
    if not vs: return ""
    try:
        docs = vs.similarity_search(q, k=3)
        return "\n\n".join(d.page_content for d in docs)
    except: return ""

# ─────────────────────────────────────────────────────────────────────────
# AI  — paste your logic inside ask_ai()
# ─────────────────────────────────────────────────────────────────────────
def ask_ai(query: str, kb_ctx: str = "", cam_desc: str = "") -> str:
    client = get_client()
    if not client:
        return "Please add your Groq API key in the panel on the right → click ☰"

    sys = st.session_state.sys_prompt + \
          f"\nTime: {datetime.now().strftime('%I:%M %p, %A %d %B %Y')}"
    if kb_ctx:
        sys += f"\n\n[Knowledge Base]\n{kb_ctx}"
    if cam_desc:
        sys += f"\n\n[Camera currently sees: {cam_desc}]"

    history = [{"role": m["role"], "content": m["content"]}
               for m in st.session_state.messages[-10:]]
    try:
        r = client.chat.completions.create(
            model=st.session_state.groq_model,
            messages=[{"role":"system","content":sys}] + history +
                     [{"role":"user","content":query}],
            max_tokens=500, temperature=0.7
        )
        return r.choices[0].message.content.strip()
    except Exception as e:
        return f"Error: {e}"

# ─────────────────────────────────────────────────────────────────────────
# CAMERA  — paste your detection logic inside process_frame()
# ─────────────────────────────────────────────────────────────────────────
def process_frame(frame):
    """
    ── DROP YOUR DETECTION CODE HERE ──
    e.g. YOLO, MediaPipe plant detection, etc.
    Set st.session_state.detected = "plant leaf"
    """
    frame = cv2.flip(frame, 1)
    # Example: edge detection overlay
    # gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    # st.session_state.detected = "Person"
    return frame

def grab_frame():
    if not CAM_OK: return None
    try:
        cap = cv2.VideoCapture(0)
        ok, frame = cap.read()
        cap.release()
        if ok:
            frame = process_frame(frame)
            _, buf = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
            return buf.tobytes()
    except: pass
    return None

def ingest_pdf(f) -> dict:
    if not RAG_OK: return {"error":"Install: langchain-huggingface faiss-cpu pypdf"}
    path = Path("uploads") / f.name
    path.write_bytes(f.getbuffer())
    try:
        pages = PyPDFLoader(str(path)).load()
        docs  = RecursiveCharacterTextSplitter(chunk_size=800,chunk_overlap=100).split_documents(pages)
        emb   = load_embeddings()
        if not emb: return {"error":"Embeddings failed"}
        if st.session_state.vectorstore is None:
            st.session_state.vectorstore = FAISS.from_documents(docs, emb)
        else:
            st.session_state.vectorstore.add_documents(docs)
        return {"pages": len(pages), "chunks": len(docs)}
    except Exception as e:
        return {"error": str(e)}

def ingest_text(name: str, text: str) -> dict:
    if not RAG_OK: return {"error":"RAG not available"}
    try:
        from langchain.schema import Document
        docs = RecursiveCharacterTextSplitter(chunk_size=800,chunk_overlap=100)\
               .split_documents([Document(page_content=text, metadata={"source":name})])
        emb = load_embeddings()
        if not emb: return {"error":"Embeddings failed"}
        if st.session_state.vectorstore is None:
            st.session_state.vectorstore = FAISS.from_documents(docs, emb)
        else:
            st.session_state.vectorstore.add_documents(docs)
        return {"chunks": len(docs)}
    except Exception as e:
        return {"error": str(e)}

# ─────────────────────────────────────────────────────────────────────────
# ── TOP NAV
# ─────────────────────────────────────────────────────────────────────────
key_ok    = bool(st.session_state.groq_key)
kb_count  = len(st.session_state.kb_docs)
dot_brain = "dot-green" if key_ok  else "dot-grey"
dot_kb    = "dot-blue"  if kb_count else "dot-grey"

st.markdown(f"""
<div class="top-nav">
  <div class="nav-logo">✦ <span>Friday</span></div>
  <div class="nav-right">
    <span style="font-size:.75rem;color:#9aa0a6;display:flex;align-items:center;gap:5px;">
      <span class="status-dot {dot_brain}"></span>
      {'Groq connected' if key_ok else 'No API key'}
    </span>
    <span style="font-size:.75rem;color:#9aa0a6;display:flex;align-items:center;gap:5px;margin-left:8px;">
      <span class="status-dot {dot_kb}"></span>
      KB: {kb_count} doc{'s' if kb_count!=1 else ''}
    </span>
  </div>
</div>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────
# ── MAIN LAYOUT:  camera | chat
# ─────────────────────────────────────────────────────────────────────────
col_cam, col_chat = st.columns([11, 9], gap="small")

# ══════════════════════════════════════════
#  CAMERA COLUMN
# ══════════════════════════════════════════
with col_cam:
    cam_slot = st.empty()
    det_slot = st.empty()

    # Controls
    cc1, cc2, cc3, _ = st.columns([2, 2, 2, 4])
    with cc1:
        snap   = st.button("📸 Capture")
    with cc2:
        live   = st.toggle("🔴 Live", value=False)
    with cc3:
        ask_cam = st.button("💬 Ask about this")

    if snap or live:
        fb = grab_frame()
        if fb:
            cam_slot.image(fb, use_container_width=True)
            det_slot.markdown(
                f'<div style="font-size:.75rem;color:#9aa0a6;padding:4px 0;">'
                f'Detected: <span style="color:#8ab4f8;">{st.session_state.detected}</span></div>',
                unsafe_allow_html=True
            )
            st.session_state.cam_frame = True
        else:
            cam_slot.markdown("""
            <div style="background:#111;border-radius:12px;aspect-ratio:16/9;
                        display:flex;flex-direction:column;align-items:center;
                        justify-content:center;gap:10px;color:#444;">
              <div style="font-size:3rem;">📷</div>
              <div style="font-size:.8rem;">Camera offline — works locally</div>
              <div style="font-size:.7rem;color:#333;">Streamlit Cloud has no camera access</div>
            </div>""", unsafe_allow_html=True)
    else:
        cam_slot.markdown("""
        <div style="background:#111;border-radius:12px;aspect-ratio:16/9;
                    display:flex;flex-direction:column;align-items:center;
                    justify-content:center;gap:10px;color:#3c3c3c;">
          <div style="font-size:3rem;">📷</div>
          <div style="font-size:.8rem;">Press Capture or enable Live</div>
        </div>""", unsafe_allow_html=True)

    if live and CAM_OK:
        live_slot = st.empty()
        for _ in range(50):
            fb = grab_frame()
            if fb:
                live_slot.image(fb, use_container_width=True)
            time.sleep(0.12)

    if ask_cam:
        cam_q = f"What do you see? Camera detected: {st.session_state.detected}. Describe it and give insights."
        ctx   = rag_query(cam_q)
        reply = ask_ai(cam_q, ctx, st.session_state.detected)
        t = datetime.now().strftime("%I:%M %p")
        st.session_state.messages.append({"role":"user",     "content":cam_q, "time":t})
        st.session_state.messages.append({"role":"assistant","content":reply, "time":t, "used_kb":bool(ctx)})
        st.rerun()

# ══════════════════════════════════════════
#  CHAT COLUMN
# ══════════════════════════════════════════
with col_chat:

    # ── Panel toggle button (top right)
    pcol1, pcol2 = st.columns([8,2])
    with pcol2:
        panel_btn = st.button("☰ Setup", key="panel_open_btn")
    if panel_btn:
        st.session_state.panel_open = not st.session_state.panel_open

    # ── Messages
    if not st.session_state.messages:
        st.markdown("""
        <div style="display:flex;flex-direction:column;align-items:center;
                    justify-content:center;padding:40px 20px;text-align:center;gap:10px;">
          <div style="font-size:2rem;font-weight:300;color:#e8eaed;">
            Hello, <span style="color:#8ab4f8;font-weight:600;">Boss</span>
          </div>
          <div style="font-size:.88rem;color:#9aa0a6;max-width:280px;line-height:1.7;">
            Ask me anything. I can see your camera, read your documents, and answer questions.
          </div>
        </div>
        """, unsafe_allow_html=True)
        # Suggestion chips
        sc1,sc2,sc3 = st.columns(3)
        suggestions = [
            (sc1, "What time is it?"),
            (sc2, "Tell me a joke"),
            (sc3, "What can you do?"),
        ]
        for col, sug in suggestions:
            with col:
                if st.button(sug, key=f"sug_{sug}", use_container_width=True):
                    ctx   = rag_query(sug)
                    reply = ask_ai(sug, ctx)
                    t     = datetime.now().strftime("%I:%M %p")
                    st.session_state.messages.append({"role":"user",     "content":sug,  "time":t})
                    st.session_state.messages.append({"role":"assistant","content":reply,"time":t,"used_kb":bool(ctx)})
                    st.rerun()
    else:
        chat_box = st.container(height=440)
        with chat_box:
            for m in st.session_state.messages:
                if m["role"] == "user":
                    st.markdown(f"""
                    <div style="display:flex;justify-content:flex-end;margin:6px 0;">
                      <div style="max-width:78%;background:#2d2d2d;border-radius:18px 4px 18px 18px;
                                  padding:10px 14px;font-size:.85rem;line-height:1.6;">
                        {m['content']}
                        <div style="font-size:.6rem;color:#5f6368;margin-top:4px;text-align:right;">{m.get('time','')}</div>
                      </div>
                    </div>""", unsafe_allow_html=True)
                else:
                    kb = '<span style="font-size:.6rem;padding:1px 6px;background:rgba(138,180,248,.1);border:1px solid rgba(138,180,248,.2);border-radius:8px;color:#8ab4f8;margin-left:6px;">KB</span>' if m.get("used_kb") else ""
                    st.markdown(f"""
                    <div style="display:flex;gap:10px;margin:6px 0;align-items:flex-start;">
                      <div style="width:28px;height:28px;border-radius:50%;background:#1c1c1c;
                                  border:1px solid #333;display:flex;align-items:center;
                                  justify-content:center;font-size:.7rem;color:#8ab4f8;flex-shrink:0;">✦</div>
                      <div style="max-width:78%;background:#1c1c1c;border-radius:4px 18px 18px 18px;
                                  padding:10px 14px;font-size:.85rem;line-height:1.6;">
                        {m['content']}{kb}
                        <div style="font-size:.6rem;color:#5f6368;margin-top:4px;">{m.get('time','')}</div>
                      </div>
                    </div>""", unsafe_allow_html=True)

    # ── Input
    with st.form("chat_form", clear_on_submit=True):
        ic1, ic2 = st.columns([9,2])
        with ic1:
            user_msg = st.text_input("msg", placeholder="Ask Friday…",
                                      label_visibility="collapsed")
        with ic2:
            send = st.form_submit_button("Send", use_container_width=True)

    if send and user_msg.strip():
        q   = user_msg.strip()
        ctx = rag_query(q)
        with st.spinner(""):
            reply = ask_ai(q, ctx, st.session_state.detected)
        t = datetime.now().strftime("%I:%M %p")
        st.session_state.messages.append({"role":"user",     "content":q,    "time":t})
        st.session_state.messages.append({"role":"assistant","content":reply,"time":t,"used_kb":bool(ctx)})
        st.rerun()

    if st.button("🗑 Clear chat", key="clr"):
        st.session_state.messages = []
        st.rerun()

# ─────────────────────────────────────────────────────────────────────────
# ── SETUP PANEL (slides in when ☰ Setup clicked)
# ─────────────────────────────────────────────────────────────────────────
if st.session_state.panel_open:
    with st.sidebar:
        st.markdown("### ⚙️ Setup")

        # ── API KEY ───────────────────────────────────────────────────────
        st.markdown("**Groq API Key**")
        new_key = st.text_input(
            "key", value=st.session_state.groq_key,
            placeholder="gsk_...",
            type="password",
            label_visibility="collapsed"
        )
        if new_key != st.session_state.groq_key:
            st.session_state.groq_key = new_key
            st.success("Key saved!")

        st.caption("Get your key free at [console.groq.com](https://console.groq.com)")

        st.divider()

        # ── MODEL ─────────────────────────────────────────────────────────
        st.markdown("**Model**")
        model = st.selectbox("model", [
            "llama-3.3-70b-versatile",
            "llama-3.1-8b-instant",
            "mixtral-8x7b-32768",
            "gemma2-9b-it",
        ], index=0, label_visibility="collapsed")
        st.session_state.groq_model = model

        st.divider()

        # ── UPLOAD PDF ────────────────────────────────────────────────────
        st.markdown("**Upload PDF**")
        pdf_file = st.file_uploader("pdf", type=["pdf"], label_visibility="collapsed")
        if pdf_file:
            if not any(d["name"]==pdf_file.name for d in st.session_state.kb_docs):
                with st.spinner("Processing…"):
                    result = ingest_pdf(pdf_file)
                if "error" in result:
                    st.error(result["error"])
                else:
                    st.session_state.kb_docs.append({
                        "name": pdf_file.name,
                        "type": "pdf",
                        "pages": result["pages"],
                    })
                    st.success(f"✓ {result['pages']} pages added")

        # ── PASTE TEXT ────────────────────────────────────────────────────
        st.markdown("**Or paste text / notes**")
        txt_title = st.text_input("Title", placeholder="My Notes", key="txt_title")
        txt_body  = st.text_area("Content", placeholder="Paste any text here…",
                                  height=120, key="txt_body")
        if st.button("Add to Knowledge Base", use_container_width=True):
            if txt_body.strip():
                with st.spinner("Adding…"):
                    r = ingest_text(txt_title or "Pasted Text", txt_body)
                if "error" in r:
                    st.error(r["error"])
                else:
                    st.session_state.kb_docs.append({
                        "name": txt_title or "Pasted Text",
                        "type": "text",
                        "chunks": r["chunks"],
                    })
                    st.success(f"✓ Added ({r['chunks']} chunks)")

        # ── DOC LIST ──────────────────────────────────────────────────────
        if st.session_state.kb_docs:
            st.divider()
            st.markdown(f"**Knowledge Base** ({len(st.session_state.kb_docs)} docs)")
            for i, d in enumerate(st.session_state.kb_docs):
                c1, c2 = st.columns([5,1])
                with c1:
                    icon = "📄" if d["type"]=="pdf" else "📝"
                    info = f"{d.get('pages','?')}p" if d["type"]=="pdf" else f"{d.get('chunks','?')} chunks"
                    st.markdown(f"<small>{icon} **{d['name']}** · {info}</small>",
                                unsafe_allow_html=True)
                with c2:
                    if st.button("✕", key=f"rm_{i}"):
                        st.session_state.kb_docs.pop(i)
                        st.rerun()

        st.divider()

        # ── SYSTEM PROMPT ────────────────────────────────────────────────
        with st.expander("✏️ Edit Friday's personality"):
            new_prompt = st.text_area("Prompt", value=st.session_state.sys_prompt,
                                       height=120, label_visibility="collapsed")
            if st.button("Save", key="save_prompt"):
                st.session_state.sys_prompt = new_prompt
                st.success("Saved!")

        st.divider()
        st.caption("friday3.streamlit.app")
