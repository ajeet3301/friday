"""
Friday AI Assistant — Hackathon Dashboard
Run: streamlit run app.py
"""

import streamlit as st
import cv2
import numpy as np
import time
import os
import threading
import tempfile
from datetime import datetime

# ── Page config ──────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Friday AI",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Inject custom CSS ─────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&family=IBM+Plex+Mono:wght@300;400;500&display=swap');

/* ── Base ── */
html, body, [class*="css"] {
    background-color: #050a0f;
    color: #c8d8e8;
    font-family: 'IBM Plex Mono', monospace;
}

/* ── Scrollbar ── */
::-webkit-scrollbar { width: 4px; }
::-webkit-scrollbar-track { background: #050a0f; }
::-webkit-scrollbar-thumb { background: #00d4ff44; border-radius: 2px; }

/* ── Sidebar ── */
[data-testid="stSidebar"] {
    background: #080e15;
    border-right: 1px solid #00d4ff18;
}

/* ── Header ── */
.friday-header {
    font-family: 'Orbitron', monospace;
    font-size: 2.4rem;
    font-weight: 900;
    letter-spacing: 0.18em;
    color: #00d4ff;
    text-shadow: 0 0 30px #00d4ff88, 0 0 60px #00d4ff33;
    margin: 0;
    line-height: 1;
}
.friday-sub {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.72rem;
    letter-spacing: 0.3em;
    color: #00d4ff55;
    margin-top: 4px;
}

/* ── Status badges ── */
.status-row {
    display: flex;
    gap: 12px;
    margin: 12px 0 18px 0;
    flex-wrap: wrap;
}
.badge {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 5px 12px;
    border-radius: 2px;
    font-size: 0.68rem;
    letter-spacing: 0.15em;
    font-family: 'IBM Plex Mono', monospace;
    font-weight: 500;
    border: 1px solid;
}
.badge-on  { color: #00ffaa; border-color: #00ffaa33; background: #00ffaa0a; }
.badge-off { color: #ff4466; border-color: #ff446633; background: #ff44660a; }
.badge-warn{ color: #ffaa00; border-color: #ffaa0033; background: #ffaa000a; }
.dot { width: 6px; height: 6px; border-radius: 50%; }
.dot-on   { background: #00ffaa; box-shadow: 0 0 6px #00ffaa; }
.dot-off  { background: #ff4466; box-shadow: 0 0 6px #ff4466; }
.dot-warn { background: #ffaa00; box-shadow: 0 0 6px #ffaa00; }

/* ── Panel cards ── */
.panel {
    background: #080e15;
    border: 1px solid #00d4ff18;
    border-radius: 4px;
    padding: 16px;
    margin-bottom: 12px;
    position: relative;
}
.panel::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 1px;
    background: linear-gradient(90deg, transparent, #00d4ff44, transparent);
}
.panel-label {
    font-family: 'Orbitron', monospace;
    font-size: 0.6rem;
    letter-spacing: 0.3em;
    color: #00d4ff66;
    margin-bottom: 12px;
    text-transform: uppercase;
}

/* ── Camera feed ── */
.cam-wrapper {
    background: #000;
    border: 1px solid #00d4ff22;
    border-radius: 2px;
    overflow: hidden;
    aspect-ratio: 16/9;
    display: flex;
    align-items: center;
    justify-content: center;
}
.cam-offline {
    color: #00d4ff22;
    font-family: 'Orbitron', monospace;
    font-size: 0.8rem;
    letter-spacing: 0.2em;
    text-align: center;
}

/* ── Detected object pill ── */
.detect-pill {
    display: inline-block;
    padding: 6px 16px;
    background: #00d4ff11;
    border: 1px solid #00d4ff33;
    border-radius: 2px;
    font-size: 0.75rem;
    letter-spacing: 0.12em;
    color: #00d4ff;
    margin-top: 8px;
}

/* ── Chat ── */
.chat-box {
    height: 360px;
    overflow-y: auto;
    padding: 12px;
    display: flex;
    flex-direction: column;
    gap: 10px;
    background: #050a0f;
    border: 1px solid #00d4ff12;
    border-radius: 2px;
}
.msg-user {
    align-self: flex-end;
    background: #00d4ff14;
    border: 1px solid #00d4ff33;
    border-radius: 2px 2px 0 2px;
    padding: 8px 14px;
    max-width: 75%;
    font-size: 0.8rem;
    color: #c8d8e8;
}
.msg-ai {
    align-self: flex-start;
    background: #0a1520;
    border: 1px solid #00ffaa22;
    border-radius: 2px 2px 2px 0;
    padding: 8px 14px;
    max-width: 75%;
    font-size: 0.8rem;
    color: #00ffaa;
}
.msg-label {
    font-size: 0.58rem;
    letter-spacing: 0.2em;
    opacity: 0.45;
    margin-bottom: 3px;
}

/* ── Inputs ── */
.stTextInput input, .stTextArea textarea {
    background: #080e15 !important;
    border: 1px solid #00d4ff22 !important;
    border-radius: 2px !important;
    color: #c8d8e8 !important;
    font-family: 'IBM Plex Mono', monospace !important;
    font-size: 0.8rem !important;
}
.stTextInput input:focus, .stTextArea textarea:focus {
    border-color: #00d4ff55 !important;
    box-shadow: 0 0 0 1px #00d4ff22 !important;
}

/* ── Buttons ── */
.stButton button {
    background: transparent !important;
    border: 1px solid #00d4ff44 !important;
    color: #00d4ff !important;
    font-family: 'IBM Plex Mono', monospace !important;
    font-size: 0.72rem !important;
    letter-spacing: 0.15em !important;
    border-radius: 2px !important;
    padding: 6px 20px !important;
    transition: all 0.2s !important;
}
.stButton button:hover {
    background: #00d4ff11 !important;
    border-color: #00d4ff88 !important;
    box-shadow: 0 0 12px #00d4ff22 !important;
}

/* ── File uploader ── */
[data-testid="stFileUploader"] {
    border: 1px dashed #00d4ff22 !important;
    border-radius: 4px !important;
    background: #050a0f !important;
}

/* ── Sidebar labels ── */
.sidebar-section {
    font-family: 'Orbitron', monospace;
    font-size: 0.58rem;
    letter-spacing: 0.3em;
    color: #00d4ff44;
    text-transform: uppercase;
    margin: 20px 0 8px 0;
    padding-bottom: 6px;
    border-bottom: 1px solid #00d4ff12;
}

/* ── Scanline overlay ── */
.scanline {
    pointer-events: none;
    position: fixed;
    top: 0; left: 0; right: 0; bottom: 0;
    background: repeating-linear-gradient(
        0deg,
        transparent,
        transparent 2px,
        #00000008 2px,
        #00000008 4px
    );
    z-index: 999;
}

/* ── Divider ── */
hr { border-color: #00d4ff12 !important; margin: 8px 0 !important; }

/* ── RAG doc list ── */
.doc-item {
    font-size: 0.7rem;
    color: #00ffaa88;
    padding: 5px 0;
    border-bottom: 1px solid #00d4ff08;
    display: flex;
    align-items: center;
    gap: 6px;
}
.doc-icon { color: #00d4ff44; }

/* ── Metric number ── */
.metric-num {
    font-family: 'Orbitron', monospace;
    font-size: 1.6rem;
    font-weight: 700;
    color: #00d4ff;
}
.metric-label {
    font-size: 0.6rem;
    letter-spacing: 0.2em;
    color: #00d4ff44;
}

/* ── Spinner override ── */
.stSpinner > div { border-top-color: #00d4ff !important; }
</style>
<div class="scanline"></div>
""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════
# ░░ STATE INIT ░░
# ══════════════════════════════════════════════════════════════════════════

def init_state():
    defaults = {
        "chat_history": [],
        "uploaded_docs": [],
        "rag_ready": False,
        "wake_active": False,
        "detected_object": "SCANNING...",
        "cam_running": False,
        "db_status": "OFFLINE",
        "frame_placeholder": None,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

init_state()


# ══════════════════════════════════════════════════════════════════════════
# ░░ PLACEHOLDER INTEGRATION FUNCTIONS — PASTE YOUR LOGIC HERE ░░
# ══════════════════════════════════════════════════════════════════════════

def process_frame(frame: np.ndarray) -> tuple[np.ndarray, str]:
    """
    🔌 PLUG IN YOUR CV2 / DETECTION LOGIC HERE.
    Args:
        frame: BGR numpy array from webcam
    Returns:
        (annotated_frame, detected_label)
    """
    # ── Example: draw a corner bracket overlay ──────────────────────────
    h, w = frame.shape[:2]
    color = (0, 212, 255)
    t = 2
    s = 30
    # corners
    for x, y in [(0,0),(w-s,0),(0,h-s),(w-s,h-s)]:
        cv2.line(frame, (x,y), (x+s,y), color, t)
        cv2.line(frame, (x,y), (x,y+s), color, t)
    # center crosshair
    cx, cy = w//2, h//2
    cv2.line(frame, (cx-15,cy), (cx+15,cy), color, 1)
    cv2.line(frame, (cx,cy-15), (cx,cy+15), color, 1)
    cv2.circle(frame, (cx,cy), 4, color, 1)
    # timestamp
    ts = datetime.now().strftime("%H:%M:%S")
    cv2.putText(frame, ts, (10, h-10),
                cv2.FONT_HERSHEY_MONO, 0.45, color, 1)
    return frame, "AWAITING DETECTION"


def build_rag(doc_paths: list[str]) -> bool:
    """
    🔌 PLUG IN YOUR LANGCHAIN / RAG SETUP HERE.
    Args:
        doc_paths: list of local file paths to uploaded PDFs
    Returns:
        True if RAG built successfully
    """
    # ── Example stub ────────────────────────────────────────────────────
    # from langchain.document_loaders import PyPDFLoader
    # from langchain.text_splitter import RecursiveCharacterTextSplitter
    # from langchain.vectorstores import FAISS
    # from langchain.embeddings import HuggingFaceEmbeddings
    # loader = PyPDFLoader(path); docs = loader.load()
    # splitter = RecursiveCharacterTextSplitter(chunk_size=500)
    # chunks = splitter.split_documents(docs)
    # embeddings = HuggingFaceEmbeddings()
    # vectorstore = FAISS.from_documents(chunks, embeddings)
    # st.session_state["vectorstore"] = vectorstore
    time.sleep(0.8)   # simulate processing
    return True


def ask_ai(query: str, use_rag: bool = False) -> str:
    """
    🔌 PLUG IN YOUR GROQ / LLM LOGIC HERE.
    Args:
        query:   user question
        use_rag: whether to inject RAG context
    Returns:
        AI response string
    """
    # ── Example stub ────────────────────────────────────────────────────
    # from groq import Groq
    # client = Groq(api_key=os.getenv("GROQ_API_KEY"))
    # context = ""
    # if use_rag and st.session_state.get("vectorstore"):
    #     docs = st.session_state["vectorstore"].similarity_search(query, k=3)
    #     context = "\n".join(d.page_content for d in docs)
    # messages = [{"role":"system","content":"You are Friday, an advanced AI."}]
    # if context:
    #     messages.append({"role":"system","content":f"Knowledge base:\n{context}"})
    # messages.append({"role":"user","content":query})
    # r = client.chat.completions.create(model="llama-3.3-70b-versatile", messages=messages)
    # return r.choices[0].message.content
    rag_note = " [RAG active]" if use_rag else ""
    return f"Friday response to: '{query}'{rag_note} — connect your Groq API key to activate."


# ══════════════════════════════════════════════════════════════════════════
# ░░ SIDEBAR ░░
# ══════════════════════════════════════════════════════════════════════════

with st.sidebar:
    st.markdown('<div class="friday-header" style="font-size:1.3rem">⚡ FRIDAY</div>', unsafe_allow_html=True)
    st.markdown('<div class="friday-sub">SYSTEM PANEL</div>', unsafe_allow_html=True)
    st.markdown("---")

    # ── Wake word toggle ─────────────────────────────────────────────────
    st.markdown('<div class="sidebar-section">Wake Word</div>', unsafe_allow_html=True)
    wake_toggle = st.toggle("Activate 'Friday'", value=st.session_state.wake_active)
    st.session_state.wake_active = wake_toggle

    # ── Camera toggle ────────────────────────────────────────────────────
    st.markdown('<div class="sidebar-section">Camera</div>', unsafe_allow_html=True)
    cam_toggle = st.toggle("Live Feed", value=st.session_state.cam_running)
    if cam_toggle != st.session_state.cam_running:
        st.session_state.cam_running = cam_toggle
        st.rerun()

    cam_index = st.number_input("Device index", min_value=0, max_value=4, value=0, step=1)

    # ── RAG Knowledge Base ───────────────────────────────────────────────
    st.markdown('<div class="sidebar-section">Knowledge Base</div>', unsafe_allow_html=True)

    uploaded_files = st.file_uploader(
        "Drop PDFs here",
        type=["pdf", "txt", "docx"],
        accept_multiple_files=True,
        label_visibility="collapsed",
    )

    if uploaded_files:
        paths = []
        for uf in uploaded_files:
            name = uf.name
            if name not in st.session_state.uploaded_docs:
                st.session_state.uploaded_docs.append(name)
                # save to temp
                with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(name)[1]) as tmp:
                    tmp.write(uf.read())
                    paths.append(tmp.name)

        if paths:
            with st.spinner("Indexing..."):
                ok = build_rag(paths)
            if ok:
                st.session_state.rag_ready = True
                st.session_state.db_status = "ONLINE"

    # Doc list
    if st.session_state.uploaded_docs:
        for doc in st.session_state.uploaded_docs[-5:]:
            st.markdown(f'<div class="doc-item"><span class="doc-icon">▸</span>{doc}</div>',
                        unsafe_allow_html=True)

    if st.session_state.uploaded_docs:
        if st.button("CLEAR KNOWLEDGE BASE"):
            st.session_state.uploaded_docs = []
            st.session_state.rag_ready = False
            st.session_state.db_status = "OFFLINE"
            st.rerun()

    # ── System metrics ───────────────────────────────────────────────────
    st.markdown('<div class="sidebar-section">System</div>', unsafe_allow_html=True)
    try:
        import psutil
        cpu = psutil.cpu_percent(interval=0.1)
        ram = psutil.virtual_memory().percent
        c1, c2 = st.columns(2)
        with c1:
            st.markdown(f'<div class="metric-num">{cpu:.0f}<span style="font-size:0.7rem">%</span></div><div class="metric-label">CPU</div>', unsafe_allow_html=True)
        with c2:
            st.markdown(f'<div class="metric-num">{ram:.0f}<span style="font-size:0.7rem">%</span></div><div class="metric-label">RAM</div>', unsafe_allow_html=True)
    except:
        st.markdown('<div style="font-size:0.7rem;color:#00d4ff33">psutil not installed</div>', unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════
# ░░ MAIN LAYOUT ░░
# ══════════════════════════════════════════════════════════════════════════

# ── Header ───────────────────────────────────────────────────────────────
st.markdown('<div class="friday-header">FRIDAY</div>', unsafe_allow_html=True)
st.markdown('<div class="friday-sub">ADVANCED AI ASSISTANT  •  v3.0</div>', unsafe_allow_html=True)

# ── Status bar ───────────────────────────────────────────────────────────
wake_cls  = "badge-on"  if st.session_state.wake_active  else "badge-off"
wake_dot  = "dot-on"    if st.session_state.wake_active  else "dot-off"
wake_txt  = "WAKE ACTIVE" if st.session_state.wake_active else "WAKE INACTIVE"

cam_cls   = "badge-on"  if st.session_state.cam_running  else "badge-off"
cam_dot   = "dot-on"    if st.session_state.cam_running  else "dot-off"
cam_txt   = "CAMERA ON" if st.session_state.cam_running  else "CAMERA OFF"

rag_cls   = "badge-on"  if st.session_state.rag_ready    else "badge-warn"
rag_dot   = "dot-on"    if st.session_state.rag_ready    else "dot-warn"
rag_txt   = "RAG READY" if st.session_state.rag_ready    else "NO DOCS"

db_cls    = "badge-on"  if st.session_state.db_status == "ONLINE" else "badge-off"
db_dot    = "dot-on"    if st.session_state.db_status == "ONLINE" else "dot-off"

st.markdown(f"""
<div class="status-row">
  <span class="badge {wake_cls}"><span class="dot {wake_dot}"></span>{wake_txt}</span>
  <span class="badge {cam_cls}"><span class="dot {cam_dot}"></span>{cam_txt}</span>
  <span class="badge {rag_cls}"><span class="dot {rag_dot}"></span>{rag_txt}</span>
  <span class="badge {db_cls}"><span class="dot {db_dot}"></span>DB {st.session_state.db_status}</span>
  <span class="badge badge-warn"><span class="dot dot-warn"></span>{st.session_state.detected_object}</span>
</div>
""", unsafe_allow_html=True)

st.markdown("---")

# ── Two-column layout ─────────────────────────────────────────────────────
col_cam, col_chat = st.columns([1.1, 1], gap="medium")

# ════════════════════════════════════════
# LEFT: CAMERA FEED
# ════════════════════════════════════════
with col_cam:
    st.markdown('<div class="panel-label">▸ VISION FEED</div>', unsafe_allow_html=True)

    frame_slot = st.empty()

    if st.session_state.cam_running:
        cap = cv2.VideoCapture(int(cam_index))
        if not cap.isOpened():
            frame_slot.error("Camera not accessible.")
        else:
            # Show up to 200 frames per run (refresh stops naturally; user re-toggles)
            for _ in range(200):
                ret, frame = cap.read()
                if not ret:
                    break
                annotated, label = process_frame(frame)
                st.session_state.detected_object = label
                rgb = cv2.cvtColor(annotated, cv2.COLOR_BGR2RGB)
                frame_slot.image(rgb, use_container_width=True)
                time.sleep(0.03)
            cap.release()
    else:
        frame_slot.markdown("""
        <div style="aspect-ratio:16/9;background:#050a0f;border:1px solid #00d4ff12;
                    border-radius:2px;display:flex;align-items:center;justify-content:center;flex-direction:column;gap:8px">
            <div style="font-family:'Orbitron',monospace;font-size:0.7rem;letter-spacing:0.25em;color:#00d4ff22">NO SIGNAL</div>
            <div style="font-size:0.6rem;color:#00d4ff11;letter-spacing:0.15em">ENABLE CAMERA IN SIDEBAR</div>
        </div>
        """, unsafe_allow_html=True)

    # Detected object display
    st.markdown(f'<div class="detect-pill">DETECTED &nbsp;▸&nbsp; {st.session_state.detected_object}</div>',
                unsafe_allow_html=True)

    # ── Manual snapshot ──────────────────────────────────────────────────
    if st.button("⬡  CAPTURE FRAME"):
        cap2 = cv2.VideoCapture(int(cam_index))
        ret, snap = cap2.read()
        cap2.release()
        if ret:
            ann, lbl = process_frame(snap)
            fname = f"snap_{datetime.now().strftime('%H%M%S')}.png"
            cv2.imwrite(fname, ann)
            st.success(f"Saved → {fname}")


# ════════════════════════════════════════
# RIGHT: CHAT INTERFACE
# ════════════════════════════════════════
with col_chat:
    st.markdown('<div class="panel-label">▸ CHAT INTERFACE</div>', unsafe_allow_html=True)

    # ── Chat history ─────────────────────────────────────────────────────
    chat_html = '<div class="chat-box" id="chatbox">'
    if not st.session_state.chat_history:
        chat_html += '<div style="margin:auto;text-align:center;color:#00d4ff18;font-size:0.7rem;letter-spacing:0.2em">AWAITING INPUT</div>'
    for msg in st.session_state.chat_history:
        if msg["role"] == "user":
            chat_html += f'<div class="msg-user"><div class="msg-label">YOU</div>{msg["content"]}</div>'
        else:
            chat_html += f'<div class="msg-ai"><div class="msg-label">FRIDAY</div>{msg["content"]}</div>'
    chat_html += '</div>'
    st.markdown(chat_html, unsafe_allow_html=True)

    # ── Input row ────────────────────────────────────────────────────────
    inp_col, btn_col = st.columns([5, 1])
    with inp_col:
        user_input = st.text_input(
            "Query",
            placeholder="Ask Friday anything...",
            label_visibility="collapsed",
            key="chat_input",
        )
    with btn_col:
        send = st.button("SEND")

    # ── Quick commands ───────────────────────────────────────────────────
    st.markdown('<div style="font-size:0.6rem;letter-spacing:0.15em;color:#00d4ff33;margin:8px 0 4px 0">QUICK</div>', unsafe_allow_html=True)
    q1, q2, q3, q4 = st.columns(4)
    quick = None
    with q1:
        if st.button("Weather"):   quick = "What's the weather today?"
    with q2:
        if st.button("Summary"):   quick = "Summarize the uploaded document."
    with q3:
        if st.button("Status"):    quick = "What do you see in the camera?"
    with q4:
        if st.button("Help"):      quick = "What can you do?"

    # ── Process query ─────────────────────────────────────────────────────
    query = quick or (user_input if send else None)

    if query:
        st.session_state.chat_history.append({"role": "user", "content": query})
        with st.spinner(""):
            response = ask_ai(query, use_rag=st.session_state.rag_ready)
        st.session_state.chat_history.append({"role": "assistant", "content": response})
        st.rerun()

    # ── Clear chat ────────────────────────────────────────────────────────
    if st.session_state.chat_history:
        if st.button("CLEAR CHAT"):
            st.session_state.chat_history = []
            st.rerun()

    # ── RAG status panel ─────────────────────────────────────────────────
    st.markdown("---")
    st.markdown('<div class="panel-label">▸ KNOWLEDGE BASE</div>', unsafe_allow_html=True)

    if st.session_state.rag_ready:
        doc_count = len(st.session_state.uploaded_docs)
        st.markdown(f"""
        <div style="display:flex;gap:20px;align-items:center;margin:8px 0">
            <div><div class="metric-num">{doc_count}</div><div class="metric-label">DOCS INDEXED</div></div>
            <div style="flex:1;padding:10px 14px;background:#00ffaa08;border:1px solid #00ffaa22;border-radius:2px;font-size:0.72rem;color:#00ffaa88">
                RAG pipeline active — answers grounded in your documents.
            </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div style="padding:12px 14px;background:#080e15;border:1px dashed #00d4ff18;
                    border-radius:2px;font-size:0.72rem;color:#00d4ff33;letter-spacing:0.1em">
            Upload PDFs in the sidebar to activate document-grounded answers.
        </div>
        """, unsafe_allow_html=True)
