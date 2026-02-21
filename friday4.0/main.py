"""
╔══════════════════════════════════════════════════════════════╗
║        FRIDAY AI DASHBOARD — Streamlit Edition               ║
║  Run: streamlit run main.py                                  ║
╚══════════════════════════════════════════════════════════════╝
"""

import os, time, json, shutil
from datetime import datetime
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv

load_dotenv()

# ── Optional imports (graceful fallback) ──────────────────────────────────
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
    import cv2
    import numpy as np
    CAM_OK = True
except ImportError:
    CAM_OK = False

# ═══════════════════════════════════════════════════════════════════════════
# CONFIG
# ═══════════════════════════════════════════════════════════════════════════

GROQ_API_KEY  = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL    = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
KB_DIR        = Path("knowledge_base")
UPLOAD_DIR    = Path("uploads")
KB_DIR.mkdir(exist_ok=True)
UPLOAD_DIR.mkdir(exist_ok=True)

SYSTEM_PROMPT = """You are Friday, an advanced AI assistant inspired by Iron Man's JARVIS.
Be helpful, witty, and concise. Keep responses under 3 sentences unless detail is needed.
Address the user as "Boss" occasionally. Never say you can't do things.
Current time: {time}"""

# ═══════════════════════════════════════════════════════════════════════════
# PAGE CONFIG & THEME
# ═══════════════════════════════════════════════════════════════════════════

st.set_page_config(
    page_title="FRIDAY AI",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ─────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Mono:wght@400;700&family=Syne:wght@700;800&display=swap');

/* Global */
html, body, [class*="css"] { font-family: 'Space Mono', monospace; }
.stApp { background: #0a0f1a; }

/* Hide default Streamlit chrome */
#MainMenu, footer, header { visibility: hidden; }
.block-container { padding-top: 1rem; padding-bottom: 1rem; }

/* ── TOP BANNER ── */
.friday-header {
    background: linear-gradient(135deg, #0f1729 0%, #111827 100%);
    border: 1px solid rgba(0,229,255,.15);
    border-radius: 10px;
    padding: 1rem 1.5rem;
    margin-bottom: 1rem;
    display: flex;
    align-items: center;
    justify-content: space-between;
}
.friday-title {
    font-family: 'Syne', sans-serif;
    font-size: 1.6rem;
    font-weight: 800;
    color: #00e5ff;
    letter-spacing: .2em;
    margin: 0;
}
.friday-sub { color: #64748b; font-size: .7rem; letter-spacing: .1em; margin-top:.2rem; }

/* ── STATUS BADGES ── */
.badge-row { display:flex; gap:.6rem; flex-wrap:wrap; margin-bottom:.75rem; }
.badge {
    font-size: .65rem; padding: .28rem .7rem; border-radius: 20px;
    border: 1px solid; letter-spacing: .08em; display: inline-flex;
    align-items: center; gap: .35rem;
}
.badge-on  { color:#22c55e; border-color:rgba(34,197,94,.35); background:rgba(34,197,94,.08); }
.badge-off { color:#64748b; border-color:rgba(100,116,139,.2); background:rgba(100,116,139,.05); }
.badge-warn{ color:#f59e0b; border-color:rgba(245,158,11,.3); background:rgba(245,158,11,.06); }
.dot { width:6px;height:6px;border-radius:50%;display:inline-block; }
.dot-on   { background:#22c55e; box-shadow:0 0 5px #22c55e; }
.dot-off  { background:#64748b; }
.dot-warn { background:#f59e0b; box-shadow:0 0 5px #f59e0b; }

/* ── PANELS ── */
.panel {
    background: #111827;
    border: 1px solid rgba(0,229,255,.12);
    border-radius: 10px;
    padding: 1rem;
    margin-bottom: .75rem;
    position: relative;
}
.panel-title {
    font-size: .7rem; color: #64748b;
    letter-spacing: .12em; margin-bottom: .75rem;
    border-bottom: 1px solid rgba(255,255,255,.05);
    padding-bottom: .5rem;
}

/* ── CHAT BUBBLES ── */
.msg-user {
    background: rgba(124,58,237,.2);
    border: 1px solid rgba(124,58,237,.3);
    border-radius: 10px 10px 2px 10px;
    padding: .6rem .9rem;
    margin: .35rem 0;
    text-align: right;
    color: #e2e8f0;
    font-size: .82rem;
}
.msg-ai {
    background: rgba(0,229,255,.07);
    border: 1px solid rgba(0,229,255,.15);
    border-radius: 10px 10px 10px 2px;
    padding: .6rem .9rem;
    margin: .35rem 0;
    color: #e2e8f0;
    font-size: .82rem;
}
.msg-meta { font-size: .6rem; color: #475569; margin-top:.25rem; }
.kb-used { font-size:.6rem; color:#a78bfa;
    background:rgba(124,58,237,.15); border:1px solid rgba(124,58,237,.25);
    border-radius:8px; padding:.1rem .4rem; margin-left:.4rem; }

/* ── STAT CARDS ── */
.stat-grid { display:grid; grid-template-columns:1fr 1fr; gap:.6rem; }
.stat-card {
    background: rgba(255,255,255,.03);
    border: 1px solid rgba(0,229,255,.1);
    border-radius: 8px; padding: .7rem;
}
.stat-label { font-size:.58rem; color:#64748b; letter-spacing:.1em; margin-bottom:.3rem; }
.stat-val { font-size:1rem; font-weight:700; color:#00e5ff; }
.stat-val-muted { font-size:.8rem; font-weight:600; color:#94a3b8; }

/* ── SIDEBAR ── */
section[data-testid="stSidebar"] {
    background: #0d1420 !important;
    border-right: 1px solid rgba(0,229,255,.1);
}
section[data-testid="stSidebar"] .stMarkdown p { color:#94a3b8; font-size:.8rem; }

/* ── INPUTS ── */
.stTextInput>div>div>input, .stTextArea>div>div>textarea {
    background: rgba(255,255,255,.04) !important;
    border: 1px solid rgba(0,229,255,.2) !important;
    border-radius: 8px !important;
    color: #e2e8f0 !important;
    font-family: 'Space Mono', monospace !important;
}
.stTextInput>div>div>input:focus, .stTextArea>div>div>textarea:focus {
    border-color: rgba(0,229,255,.5) !important;
    box-shadow: 0 0 0 2px rgba(0,229,255,.1) !important;
}

/* ── BUTTONS ── */
.stButton>button {
    background: rgba(0,229,255,.1) !important;
    border: 1px solid rgba(0,229,255,.3) !important;
    color: #00e5ff !important;
    border-radius: 7px !important;
    font-family: 'Space Mono', monospace !important;
    font-size: .72rem !important;
    letter-spacing: .06em !important;
    transition: .2s !important;
}
.stButton>button:hover {
    background: rgba(0,229,255,.2) !important;
    border-color: rgba(0,229,255,.5) !important;
}

/* ── FILE UPLOADER ── */
.stFileUploader>div { border-radius:8px; background:rgba(0,229,255,.04); }

/* ── SELECTBOX ── */
.stSelectbox>div>div {
    background: rgba(255,255,255,.04) !important;
    border: 1px solid rgba(0,229,255,.2) !important;
    border-radius: 8px !important;
    color: #e2e8f0 !important;
}

/* ── EXPANDER ── */
.streamlit-expanderHeader {
    background: rgba(255,255,255,.03) !important;
    border: 1px solid rgba(0,229,255,.1) !important;
    border-radius: 8px !important;
    color: #94a3b8 !important;
    font-size: .75rem !important;
}

/* ── COLOR PICKERS ── */
.stColorPicker>div { border-radius:8px; }

/* Scrollbar */
::-webkit-scrollbar { width:4px; }
::-webkit-scrollbar-track { background:transparent; }
::-webkit-scrollbar-thumb { background:rgba(0,229,255,.2); border-radius:2px; }
</style>
""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════
# SESSION STATE INIT
# ═══════════════════════════════════════════════════════════════════════════

def init_state():
    defaults = {
        "chat_history":   [],
        "vectorstore":    None,
        "kb_docs":        [],
        "wake_active":    False,
        "detected_obj":   "—",
        "groq_client":    None,
        "theme_accent":   "#00e5ff",
        "theme_bg":       "#0a0f1a",
        "embeddings":     None,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

init_state()

# ═══════════════════════════════════════════════════════════════════════════
# HELPERS
# ═══════════════════════════════════════════════════════════════════════════

@st.cache_resource
def get_groq_client():
    if GROQ_OK and GROQ_API_KEY:
        return Groq(api_key=GROQ_API_KEY)
    return None

@st.cache_resource
def get_embeddings():
    if not RAG_OK:
        return None
    try:
        return HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
    except Exception as e:
        st.warning(f"Embeddings error: {e}")
        return None

def badge(label, state="off", dot=True):
    cls = {"on":"badge-on","off":"badge-off","warn":"badge-warn"}[state]
    dcls= {"on":"dot-on","off":"dot-off","warn":"dot-warn"}[state]
    d   = f'<span class="dot {dcls}"></span>' if dot else ""
    return f'<span class="badge {cls}">{d}{label}</span>'

def now_str():
    return datetime.now().strftime("%I:%M %p")

# ═══════════════════════════════════════════════════════════════════════════
# AI BRAIN
# ═══════════════════════════════════════════════════════════════════════════

def ask_ai(query: str, kb_context: str = "") -> str:
    """
    ── PLUG YOUR LLM LOGIC HERE ──
    kb_context is auto-injected from RAG when KB has documents.
    """
    client = get_groq_client()
    if not client:
        return f"[Echo] {query} — Add GROQ_API_KEY to secrets for real responses."

    system = SYSTEM_PROMPT.format(time=datetime.now().strftime("%I:%M %p, %A %d %B %Y"))
    if kb_context:
        system += f"\n\n--- Knowledge Base ---\n{kb_context}\n--- End ---"

    history = [{"role": m["role"], "content": m["content"]}
               for m in st.session_state.chat_history[-8:]]

    msgs = [{"role": "system", "content": system}] + history + \
           [{"role": "user", "content": query}]
    try:
        r = client.chat.completions.create(
            model=GROQ_MODEL, messages=msgs, max_tokens=500, temperature=0.7
        )
        return r.choices[0].message.content.strip()
    except Exception as e:
        return f"Error: {e}"

# ═══════════════════════════════════════════════════════════════════════════
# RAG
# ═══════════════════════════════════════════════════════════════════════════

def ingest_pdf(uploaded_file) -> dict:
    """Save PDF → split → embed → store in session."""
    if not RAG_OK:
        return {"error": "Install langchain-huggingface faiss-cpu pypdf"}

    save_path = UPLOAD_DIR / uploaded_file.name
    with open(save_path, "wb") as f:
        f.write(uploaded_file.getbuffer())

    try:
        loader   = PyPDFLoader(str(save_path))
        pages    = loader.load()
        splitter = RecursiveCharacterTextSplitter(chunk_size=800, chunk_overlap=100)
        docs     = splitter.split_documents(pages)

        emb = get_embeddings()
        if emb is None:
            return {"error": "Embeddings not available"}

        if st.session_state.vectorstore is None:
            st.session_state.vectorstore = FAISS.from_documents(docs, emb)
        else:
            st.session_state.vectorstore.add_documents(docs)

        meta = {"name": uploaded_file.name, "pages": len(pages),
                "chunks": len(docs), "added": datetime.now().strftime("%d %b %Y")}
        st.session_state.kb_docs.append(meta)
        return meta
    except Exception as e:
        return {"error": str(e)}

def rag_query(question: str) -> str:
    if st.session_state.vectorstore is None:
        return ""
    try:
        docs = st.session_state.vectorstore.similarity_search(question, k=3)
        return "\n\n".join(d.page_content for d in docs)
    except:
        return ""

# ═══════════════════════════════════════════════════════════════════════════
# CAMERA (only works locally, not on Streamlit Cloud)
# ═══════════════════════════════════════════════════════════════════════════

def capture_frame():
    """
    ── PLUG YOUR DETECTION LOGIC HERE ──
    Replace body with your YOLO / MediaPipe / plant detection.
    Set st.session_state.detected_obj = "plant" etc.
    """
    if not CAM_OK:
        return None
    try:
        cap = cv2.VideoCapture(0)
        ok, frame = cap.read()
        cap.release()
        if ok:
            frame = cv2.flip(frame, 1)
            # ↓ your detection here → st.session_state.detected_obj = "..."
            _, buf = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
            return buf.tobytes()
    except:
        pass
    return None

# ═══════════════════════════════════════════════════════════════════════════
# SIDEBAR  (Admin / Settings)
# ═══════════════════════════════════════════════════════════════════════════

with st.sidebar:
    st.markdown("""
    <div style="text-align:center;padding:1rem 0 .5rem;">
      <div style="font-family:'Syne',sans-serif;font-size:1.3rem;font-weight:800;
                  color:#00e5ff;letter-spacing:.2em;">FRIDAY</div>
      <div style="font-size:.6rem;color:#475569;letter-spacing:.15em;margin-top:.2rem;">ADMIN PANEL</div>
    </div>
    """, unsafe_allow_html=True)

    st.divider()

    # ── KNOWLEDGE BASE ────────────────────────────────────────────────────
    st.markdown('<div class="panel-title">📚 KNOWLEDGE BASE</div>', unsafe_allow_html=True)

    uploaded = st.file_uploader(
        "Upload PDF", type=["pdf"], label_visibility="collapsed",
        help="Upload manuals, docs, or any PDF for Friday to reference"
    )

    if uploaded:
        if not any(d["name"] == uploaded.name for d in st.session_state.kb_docs):
            with st.spinner(f"Processing {uploaded.name}…"):
                result = ingest_pdf(uploaded)
            if "error" in result:
                st.error(result["error"])
            else:
                st.success(f"✓ {result['pages']} pages · {result['chunks']} chunks")

    # Doc list
    if st.session_state.kb_docs:
        st.markdown('<div style="margin-top:.5rem"></div>', unsafe_allow_html=True)
        for i, doc in enumerate(st.session_state.kb_docs):
            col1, col2 = st.columns([5, 1])
            with col1:
                st.markdown(
                    f'<div style="font-size:.7rem;color:#94a3b8;">📄 {doc["name"]}<br>'
                    f'<span style="color:#475569;font-size:.6rem;">{doc["pages"]}p · {doc.get("added","")}</span></div>',
                    unsafe_allow_html=True
                )
            with col2:
                if st.button("🗑", key=f"del_{i}", help="Remove"):
                    st.session_state.kb_docs.pop(i)
                    st.rerun()
    else:
        st.markdown('<div style="font-size:.7rem;color:#475569;padding:.3rem 0;">No documents yet.</div>',
                    unsafe_allow_html=True)

    st.divider()

    # ── WAKE WORD ─────────────────────────────────────────────────────────
    st.markdown('<div class="panel-title">⚡ WAKE WORD</div>', unsafe_allow_html=True)
    wake = st.toggle("Enable 'Friday' wake word", value=st.session_state.wake_active)
    st.session_state.wake_active = wake
    if wake:
        st.markdown('<div style="font-size:.68rem;color:#22c55e;">● Active — say "Friday" to wake</div>',
                    unsafe_allow_html=True)

    st.divider()

    # ── THEME ─────────────────────────────────────────────────────────────
    st.markdown('<div class="panel-title">🎨 THEME</div>', unsafe_allow_html=True)
    with st.expander("Color Settings"):
        accent  = st.color_picker("Accent",     st.session_state.theme_accent)
        bg_col  = st.color_picker("Background", st.session_state.theme_bg)
        if accent != st.session_state.theme_accent or bg_col != st.session_state.theme_bg:
            st.session_state.theme_accent = accent
            st.session_state.theme_bg     = bg_col
            st.markdown(f"""<style>
                :root {{ --accent:{accent}; --bg:{bg_col}; }}
                .stApp {{ background:{bg_col}; }}
            </style>""", unsafe_allow_html=True)

    st.divider()

    # ── SYSTEM PROMPT ─────────────────────────────────────────────────────
    st.markdown('<div class="panel-title">🧠 SYSTEM PROMPT</div>', unsafe_allow_html=True)
    with st.expander("Edit Prompt"):
        new_prompt = st.text_area("", value=SYSTEM_PROMPT, height=140, label_visibility="collapsed")
        if st.button("Save Prompt"):
            # Update global (session-scoped)
            SYSTEM_PROMPT = new_prompt
            st.success("Saved!")

    st.divider()

    # ── CLEAR CHAT ────────────────────────────────────────────────────────
    if st.button("🗑 Clear Chat History", use_container_width=True):
        st.session_state.chat_history = []
        st.rerun()

    # ── FOOTER ────────────────────────────────────────────────────────────
    st.markdown(
        '<div style="font-size:.6rem;color:#334155;text-align:center;margin-top:1rem;">'
        'FRIDAY v4.0 · Built with ❤</div>',
        unsafe_allow_html=True
    )

# ═══════════════════════════════════════════════════════════════════════════
# MAIN CONTENT
# ═══════════════════════════════════════════════════════════════════════════

# ── HEADER BAR ─────────────────────────────────────────────────────────────
groq_state = "on"  if (GROQ_OK and GROQ_API_KEY) else "warn"
rag_state  = "on"  if RAG_OK else "off"
kb_state   = "on"  if st.session_state.kb_docs else "off"
cam_state  = "on"  if CAM_OK else "off"
wake_state = "on"  if st.session_state.wake_active else "off"
kb_label   = f"KB {len(st.session_state.kb_docs)}"

st.markdown(f"""
<div class="friday-header">
  <div>
    <div class="friday-title">⚡ FRIDAY</div>
    <div class="friday-sub">{datetime.now().strftime("%A, %d %B %Y  ·  %I:%M %p")}</div>
  </div>
  <div class="badge-row">
    {badge("BRAIN", groq_state)}
    {badge("RAG", rag_state)}
    {badge(kb_label, kb_state)}
    {badge("CAM", cam_state)}
    {badge("WAKE", wake_state)}
  </div>
</div>
""", unsafe_allow_html=True)

# ── TWO-COLUMN LAYOUT ──────────────────────────────────────────────────────
col_left, col_right = st.columns([1, 1], gap="medium")

# ════════════════════════════════════════════════════════════════════════════
# LEFT COLUMN — Camera + Status
# ════════════════════════════════════════════════════════════════════════════

with col_left:

    # ── CAMERA ────────────────────────────────────────────────────────────
    st.markdown('<div class="panel-title">📷 LIVE VISION</div>', unsafe_allow_html=True)

    cam_placeholder = st.empty()
    detected_placeholder = st.empty()

    c1, c2, c3 = st.columns(3)
    with c1:
        snap = st.button("📸 Capture", use_container_width=True)
    with c2:
        cam_refresh = st.button("🔄 Refresh", use_container_width=True)
    with c3:
        cam_stream = st.toggle("Live", value=False)

    if snap or cam_refresh:
        frame_bytes = capture_frame()
        if frame_bytes:
            cam_placeholder.image(frame_bytes, channels="BGR", use_container_width=True)
            detected_placeholder.markdown(
                f'<div style="font-size:.72rem;color:#00e5ff;font-family:\'Space Mono\',monospace;'
                f'margin-top:.3rem;">Detected: {st.session_state.detected_obj}</div>',
                unsafe_allow_html=True
            )
        else:
            cam_placeholder.markdown(
                '<div style="background:#0d1420;border:1px solid rgba(0,229,255,.1);border-radius:8px;'
                'padding:3rem;text-align:center;color:#334155;font-size:.8rem;">'
                '📷 Camera not available<br>'
                '<span style="font-size:.65rem;color:#1e293b;">Camera works locally only on Streamlit Cloud</span>'
                '</div>', unsafe_allow_html=True
            )

    if cam_stream and CAM_OK:
        stream_slot = st.empty()
        for _ in range(30):   # 30 frames then stop (prevents infinite loop)
            fb = capture_frame()
            if fb:
                stream_slot.image(fb, channels="BGR", use_container_width=True)
            time.sleep(0.15)

    st.divider()

    # ── STATUS CARDS ──────────────────────────────────────────────────────
    st.markdown('<div class="panel-title">📊 STATUS</div>', unsafe_allow_html=True)

    st.markdown(f"""
    <div class="stat-grid">
      <div class="stat-card">
        <div class="stat-label">DETECTED</div>
        <div class="stat-val">{st.session_state.detected_obj}</div>
      </div>
      <div class="stat-card">
        <div class="stat-label">KNOWLEDGE BASE</div>
        <div class="stat-val">{len(st.session_state.kb_docs)} docs</div>
      </div>
      <div class="stat-card">
        <div class="stat-label">AI BRAIN</div>
        <div class="stat-val-muted">{'Groq ✓' if GROQ_OK and GROQ_API_KEY else 'Echo mode'}</div>
      </div>
      <div class="stat-card">
        <div class="stat-label">RAG</div>
        <div class="stat-val-muted">{'Ready ✓' if RAG_OK else 'Not installed'}</div>
      </div>
    </div>
    """, unsafe_allow_html=True)

# ════════════════════════════════════════════════════════════════════════════
# RIGHT COLUMN — Chat
# ════════════════════════════════════════════════════════════════════════════

with col_right:
    st.markdown('<div class="panel-title">💬 FRIDAY CHAT</div>', unsafe_allow_html=True)

    # ── Chat history display ───────────────────────────────────────────────
    chat_container = st.container(height=420)

    with chat_container:
        if not st.session_state.chat_history:
            st.markdown(
                '<div class="msg-ai">Hello Boss! Friday online and ready. '
                'Ask me anything or upload a PDF to the knowledge base.'
                '<div class="msg-meta">System</div></div>',
                unsafe_allow_html=True
            )

        for msg in st.session_state.chat_history:
            kb_tag = '<span class="kb-used">KB</span>' if msg.get("used_kb") else ""
            if msg["role"] == "user":
                st.markdown(
                    f'<div class="msg-user">{msg["content"]}'
                    f'<div class="msg-meta">{msg.get("time","")}</div></div>',
                    unsafe_allow_html=True
                )
            else:
                st.markdown(
                    f'<div class="msg-ai">{msg["content"]}{kb_tag}'
                    f'<div class="msg-meta">{msg.get("time","")}</div></div>',
                    unsafe_allow_html=True
                )

    # ── Input row ─────────────────────────────────────────────────────────
    with st.form(key="chat_form", clear_on_submit=True):
        inp_col, btn_col = st.columns([5, 1])
        with inp_col:
            user_input = st.text_input(
                "Message", placeholder="Ask Friday anything…",
                label_visibility="collapsed"
            )
        with btn_col:
            submitted = st.form_submit_button("SEND", use_container_width=True)

    # ── Process message ────────────────────────────────────────────────────
    if submitted and user_input.strip():
        q = user_input.strip()

        # RAG context
        kb_ctx = rag_query(q)

        # Get AI response
        with st.spinner("Friday is thinking…"):
            answer = ask_ai(q, kb_ctx)

        t = now_str()
        st.session_state.chat_history.append(
            {"role": "user",      "content": q,      "time": t, "used_kb": False}
        )
        st.session_state.chat_history.append(
            {"role": "assistant", "content": answer,  "time": t, "used_kb": bool(kb_ctx)}
        )
        st.rerun()

    # ── Quick commands ─────────────────────────────────────────────────────
    st.markdown('<div style="margin-top:.4rem;font-size:.62rem;color:#334155;">Quick:</div>',
                unsafe_allow_html=True)
    qc1, qc2, qc3, qc4 = st.columns(4)
    quick_cmds = [
        (qc1, "🕐 Time",   "What time is it?"),
        (qc2, "🌤 Weather","What's the weather in Delhi?"),
        (qc3, "😄 Joke",   "Tell me a joke"),
        (qc4, "📋 Notes",  "Read my recent notes"),
    ]
    for col, label, cmd in quick_cmds:
        with col:
            if st.button(label, use_container_width=True, key=f"qc_{label}"):
                kb_ctx = rag_query(cmd)
                answer = ask_ai(cmd, kb_ctx)
                t = now_str()
                st.session_state.chat_history.append({"role":"user",     "content":cmd,    "time":t})
                st.session_state.chat_history.append({"role":"assistant","content":answer, "time":t,"used_kb":bool(kb_ctx)})
                st.rerun()
