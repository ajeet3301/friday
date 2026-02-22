"""
╔══════════════════════════════════════════════════════════════╗
║  FRIDAY AI  —  v5.0  FINAL                                   ║
║  streamlit run main.py                                       ║
╚══════════════════════════════════════════════════════════════╝

EASY CUSTOMIZATION GUIDE  (search the tag to jump there)
  #CONFIG      → API keys, models, default settings
  #THEMES      → Color themes
  #PROMPTS     → Friday's personality / system prompt
  #VISION      → What happens when camera captures a frame
  #AI          → Core LLM call (swap provider here)
  #RAG         → PDF / text knowledge ingestion
  #UI_MAIN     → Main page layout
  #UI_SIDEBAR  → Settings panel
"""

import os, base64, io, json, time
from datetime import datetime
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv

load_dotenv()

# ════════════════════════════════════════════════════════════════
#CONFIG  ← change defaults here
# ════════════════════════════════════════════════════════════════
class CFG:
    # ── API (override with .env or Streamlit secrets) ──────────
    GROQ_API_KEY   = os.getenv("GROQ_API_KEY", "")
    GROQ_CHAT      = os.getenv("GROQ_MODEL",   "llama-3.3-70b-versatile")
    GROQ_VISION    = "meta-llama/llama-4-scout-17b-16e-instruct"  # vision model
    GROQ_WHISPER   = "whisper-large-v3-turbo"

    # ── Available models (shown in settings) ───────────────────
    CHAT_MODELS = [
        "llama-3.3-70b-versatile",
        "llama-3.1-8b-instant",
        "mixtral-8x7b-32768",
        "gemma2-9b-it",
    ]
    VISION_MODELS = [
        "meta-llama/llama-4-scout-17b-16e-instruct",
        "llama-3.2-11b-vision-preview",
        "llama-3.2-90b-vision-preview",
    ]

    # ── Dirs ───────────────────────────────────────────────────
    UPLOAD_DIR = Path("uploads")
    KB_DIR     = Path("knowledge_base")

    # ── RAG chunk settings ────────────────────────────────────
    CHUNK_SIZE    = 800
    CHUNK_OVERLAP = 100
    RAG_TOP_K     = 3

# ════════════════════════════════════════════════════════════════
#THEMES  ← add / edit themes here
# ════════════════════════════════════════════════════════════════
THEMES = {
    "Dark": {
        "bg":      "#0f0f0f",
        "surface": "#1a1a1a",
        "s2":      "#242424",
        "border":  "rgba(255,255,255,.07)",
        "text":    "#e8eaed",
        "muted":   "#9aa0a6",
        "accent":  "#8ab4f8",
        "accent2": "#a8d8a8",
        "danger":  "#f28b82",
    },
    "Midnight": {
        "bg":      "#050810",
        "surface": "#0d1117",
        "s2":      "#161b22",
        "border":  "rgba(48,54,61,.8)",
        "text":    "#c9d1d9",
        "muted":   "#8b949e",
        "accent":  "#58a6ff",
        "accent2": "#3fb950",
        "danger":  "#f85149",
    },
    "Slate": {
        "bg":      "#0f172a",
        "surface": "#1e293b",
        "s2":      "#334155",
        "border":  "rgba(148,163,184,.1)",
        "text":    "#e2e8f0",
        "muted":   "#94a3b8",
        "accent":  "#818cf8",
        "accent2": "#34d399",
        "danger":  "#f87171",
    },
    "Amoled": {
        "bg":      "#000000",
        "surface": "#0a0a0a",
        "s2":      "#111111",
        "border":  "rgba(255,255,255,.05)",
        "text":    "#ffffff",
        "muted":   "#666666",
        "accent":  "#00d4ff",
        "accent2": "#00ff88",
        "danger":  "#ff4444",
    },
    "Forest": {
        "bg":      "#0a0f0a",
        "surface": "#111811",
        "s2":      "#1a2a1a",
        "border":  "rgba(74,222,128,.08)",
        "text":    "#dcfce7",
        "muted":   "#86efac",
        "accent":  "#4ade80",
        "accent2": "#a3e635",
        "danger":  "#f87171",
    },
}

# ════════════════════════════════════════════════════════════════
#PROMPTS  ← edit Friday's personality here
# ════════════════════════════════════════════════════════════════
DEFAULT_SYSTEM_PROMPT = """You are Friday, an advanced AI assistant like JARVIS from Iron Man.
You can see through the camera and analyse images in real time.
Be concise, helpful, and occasionally call the user "Boss".
When analysing camera images: identify objects, plants, problems, and give practical solutions.
For plant issues: identify the plant, diagnose problems (disease, pests, watering), give solutions.
Keep answers short and actionable unless the user asks for detail.
Current time: {time}"""

VISION_PROMPT = """Analyse this image carefully. Identify:
1. Main objects / subjects
2. Any problems, issues, or anomalies (plant disease, damage, etc.)
3. Practical solutions or recommendations
Be specific and helpful. If it's a plant: name it, diagnose issues, suggest fixes."""

# ════════════════════════════════════════════════════════════════
# DIRS + PAGE CONFIG
# ════════════════════════════════════════════════════════════════
CFG.UPLOAD_DIR.mkdir(exist_ok=True)
CFG.KB_DIR.mkdir(exist_ok=True)

st.set_page_config(
    page_title="Friday",
    page_icon="✦",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ════════════════════════════════════════════════════════════════
# OPTIONAL IMPORTS
# ════════════════════════════════════════════════════════════════
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
    from langchain.schema import Document
    RAG_OK = True
except ImportError:
    RAG_OK = False

# ════════════════════════════════════════════════════════════════
# SESSION STATE INIT
# ════════════════════════════════════════════════════════════════
def _init():
    defaults = {
        "messages":     [],
        "vectorstore":  None,
        "kb_docs":      [],
        "groq_key":     CFG.GROQ_API_KEY,
        "chat_model":   CFG.GROQ_CHAT,
        "vision_model": CFG.GROQ_VISION,
        "sys_prompt":   DEFAULT_SYSTEM_PROMPT,
        "theme_name":   "Dark",
        "detected":     "",
        "last_snap_b64": None,
        "cam_analysis": "",
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

_init()

# ════════════════════════════════════════════════════════════════
# THEME HELPER
# ════════════════════════════════════════════════════════════════
def T(key):
    return THEMES[st.session_state.theme_name][key]

# ════════════════════════════════════════════════════════════════
# CSS — injected dynamically so theme changes apply live
# ════════════════════════════════════════════════════════════════
def inject_css():
    t = THEMES[st.session_state.theme_name]
    st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:ital,wght@0,300;0,400;0,500;0,600;1,400&family=DM+Mono:wght@400;500&display=swap');

:root {{
  --bg:      {t['bg']};
  --sf:      {t['surface']};
  --sf2:     {t['s2']};
  --bd:      {t['border']};
  --tx:      {t['text']};
  --mu:      {t['muted']};
  --ac:      {t['accent']};
  --ac2:     {t['accent2']};
  --dg:      {t['danger']};
  --sans:    'DM Sans', sans-serif;
  --mono:    'DM Mono', monospace;
  --rad:     12px;
  --rad-sm:  8px;
  --rad-pill:24px;
}}

/* ── RESET ── */
html,body,[class*="css"]{{
  font-family:var(--sans)!important;
  background:var(--bg)!important;
  color:var(--tx)!important;
  line-height:1.5;
}}
*{{box-sizing:border-box;}}
#MainMenu,footer,header{{visibility:hidden;}}
.block-container{{padding:0!important;max-width:100%!important;}}

/* ── SCROLLBAR ── */
::-webkit-scrollbar{{width:3px;height:3px;}}
::-webkit-scrollbar-track{{background:transparent;}}
::-webkit-scrollbar-thumb{{background:var(--bd);border-radius:2px;}}

/* ── TOPBAR ── */
.topbar{{
  display:flex;align-items:center;justify-content:space-between;
  padding:12px 20px;
  background:var(--bg);
  border-bottom:1px solid var(--bd);
  position:sticky;top:0;z-index:200;
  backdrop-filter:blur(20px);
}}
.logo{{
  font-size:1.05rem;font-weight:600;color:var(--tx);
  display:flex;align-items:center;gap:8px;letter-spacing:-.02em;
}}
.logo-star{{color:var(--ac);font-size:1.1rem;}}
.topbar-right{{display:flex;align-items:center;gap:8px;}}

/* ── STATUS PILL ── */
.status-pill{{
  display:inline-flex;align-items:center;gap:6px;
  padding:5px 12px;border-radius:var(--rad-pill);
  border:1px solid var(--bd);
  font-size:.72rem;color:var(--mu);background:var(--sf);
  cursor:default;
}}
.sdot{{width:6px;height:6px;border-radius:50%;flex-shrink:0;}}
.sdot-green{{background:var(--ac2);box-shadow:0 0 6px var(--ac2);animation:sdpulse 2s infinite;}}
.sdot-grey {{background:#444;}}
.sdot-blue {{background:var(--ac);box-shadow:0 0 6px var(--ac);animation:sdpulse 2s infinite;}}
@keyframes sdpulse{{0%,100%{{opacity:1}}50%{{opacity:.4}}}}

/* ── ICON BTN ── */
.icon-btn{{
  width:36px;height:36px;border-radius:50%;
  background:var(--sf);border:1px solid var(--bd);
  display:flex;align-items:center;justify-content:center;
  cursor:pointer;transition:.15s;color:var(--mu);font-size:.9rem;
}}
.icon-btn:hover{{background:var(--sf2);color:var(--tx);border-color:rgba(255,255,255,.15);}}

/* ── MAIN GRID ── */
.main-grid{{
  display:grid;
  grid-template-columns:1fr 1fr;
  height:calc(100vh - 57px);
  overflow:hidden;
}}

/* ── CAM PANEL ── */
.cam-panel{{
  background:#000;
  border-right:1px solid var(--bd);
  display:flex;flex-direction:column;
  overflow:hidden;position:relative;
}}

/* ── CHAT PANEL ── */
.chat-panel{{
  display:flex;flex-direction:column;
  background:var(--bg);
  overflow:hidden;
}}

/* ── CHAT MESSAGES ── */
.chat-scroll{{
  flex:1;overflow-y:auto;
  padding:16px 20px;
  display:flex;flex-direction:column;gap:12px;
}}

/* Welcome screen */
.welcome-wrap{{
  display:flex;flex-direction:column;align-items:center;justify-content:center;
  flex:1;padding:32px 24px;text-align:center;gap:12px;
}}
.welcome-title{{font-size:1.75rem;font-weight:300;letter-spacing:-.03em;}}
.welcome-title b{{color:var(--ac);font-weight:600;}}
.welcome-sub{{font-size:.85rem;color:var(--mu);max-width:280px;line-height:1.7;}}
.chips{{display:flex;flex-wrap:wrap;gap:8px;justify-content:center;margin-top:8px;}}
.chip{{
  padding:8px 16px;border-radius:var(--rad-pill);
  border:1px solid var(--bd);font-size:.8rem;color:var(--mu);
  cursor:pointer;transition:.15s;background:var(--sf);
}}
.chip:hover{{background:var(--sf2);color:var(--tx);border-color:rgba(255,255,255,.15);}}

/* Messages */
.msg-user{{
  display:flex;justify-content:flex-end;
}}
.msg-ai{{
  display:flex;gap:10px;align-items:flex-start;
}}
.av{{
  width:26px;height:26px;border-radius:50%;flex-shrink:0;
  display:flex;align-items:center;justify-content:center;
  font-size:.7rem;margin-top:2px;
  background:var(--sf2);border:1px solid var(--bd);color:var(--ac);
}}
.bub{{
  max-width:82%;padding:10px 14px;font-size:.84rem;line-height:1.65;
  border-radius:18px;
}}
.bub-user{{background:var(--sf2);border-radius:18px 4px 18px 18px;}}
.bub-ai{{background:var(--sf);border-radius:4px 18px 18px 18px;}}
.bub-meta{{font-size:.6rem;color:var(--mu);margin-top:4px;}}
.kb-badge{{
  display:inline-block;font-size:.58rem;padding:1px 6px;
  background:rgba(138,180,248,.1);border:1px solid rgba(138,180,248,.2);
  border-radius:6px;color:var(--ac);margin-left:5px;vertical-align:middle;
}}
.cam-badge{{
  display:inline-block;font-size:.58rem;padding:1px 6px;
  background:rgba(74,222,128,.1);border:1px solid rgba(74,222,128,.2);
  border-radius:6px;color:var(--ac2);margin-left:5px;vertical-align:middle;
}}

/* Typing indicator */
.typing{{display:flex;gap:5px;padding:10px 14px;background:var(--sf);
  border-radius:4px 18px 18px 18px;width:fit-content;}}
.typing span{{width:5px;height:5px;border-radius:50%;background:var(--mu);
  animation:bounce .9s infinite;}}
.typing span:nth-child(2){{animation-delay:.15s;}}
.typing span:nth-child(3){{animation-delay:.3s;}}
@keyframes bounce{{0%,100%{{transform:translateY(0);opacity:.4}}50%{{transform:translateY(-4px);opacity:1}}}}

/* ── BOTTOM INPUT ── */
.input-wrap{{
  padding:12px 16px 16px;
  border-top:1px solid var(--bd);
  background:var(--bg);
}}
.input-row{{
  display:flex;align-items:center;gap:8px;
  background:var(--sf);border:1px solid var(--bd);
  border-radius:var(--rad-pill);padding:6px 6px 6px 16px;
  transition:.2s;
}}
.input-row:focus-within{{
  border-color:color-mix(in srgb,var(--ac) 50%,transparent);
  box-shadow:0 0 0 3px color-mix(in srgb,var(--ac) 8%,transparent);
}}

/* ── SETTINGS SIDEBAR ── */
.settings-panel{{
  position:fixed;right:0;top:0;bottom:0;width:300px;
  background:var(--sf);border-left:1px solid var(--bd);
  z-index:999;overflow-y:auto;
  transform:translateX(100%);
  transition:transform .25s cubic-bezier(.4,0,.2,1);
  padding:20px;
}}
.settings-panel.open{{transform:translateX(0);}}
.settings-title{{
  font-size:.95rem;font-weight:600;margin-bottom:16px;
  display:flex;align-items:center;justify-content:space-between;
}}
.settings-section{{
  font-size:.68rem;color:var(--mu);letter-spacing:.08em;
  text-transform:uppercase;margin:16px 0 8px;
}}
.theme-grid{{display:grid;grid-template-columns:repeat(5,1fr);gap:6px;}}
.theme-swatch{{
  aspect-ratio:1;border-radius:8px;cursor:pointer;
  border:2px solid transparent;transition:.15s;
  display:flex;align-items:center;justify-content:center;
  font-size:.6rem;color:rgba(255,255,255,.7);
}}
.theme-swatch:hover{{transform:scale(1.08);}}
.theme-swatch.active{{border-color:var(--ac);}}

/* ── OVERLAY (dim behind settings panel) ── */
.overlay{{
  display:none;position:fixed;inset:0;background:rgba(0,0,0,.5);z-index:998;
}}
.overlay.show{{display:block;}}

/* ── STREAMLIT OVERRIDES ── */
.stTextInput>div>div>input{{
  background:transparent!important;border:none!important;
  box-shadow:none!important;color:var(--tx)!important;
  font-family:var(--sans)!important;font-size:.9rem!important;
  padding:4px 0!important;
}}
.stTextInput>label{{display:none!important;}}
.stButton>button{{
  background:var(--ac)!important;color:#000!important;
  border:none!important;border-radius:var(--rad-pill)!important;
  font-family:var(--sans)!important;font-weight:500!important;
  padding:8px 20px!important;font-size:.8rem!important;
  transition:.15s!important;white-space:nowrap!important;
}}
.stButton>button:hover{{opacity:.88!important;transform:scale(1.01)!important;}}

/* ghost button variant */
button.ghost{{
  background:transparent!important;border:1px solid var(--bd)!important;
  color:var(--mu)!important;
}}
button.ghost:hover{{background:var(--sf2)!important;color:var(--tx)!important;}}

.stSelectbox>div>div{{
  background:var(--sf2)!important;border:1px solid var(--bd)!important;
  border-radius:var(--rad-sm)!important;color:var(--tx)!important;
}}
.stTextArea>div>div>textarea{{
  background:var(--sf2)!important;border:1px solid var(--bd)!important;
  border-radius:var(--rad-sm)!important;color:var(--tx)!important;
  font-family:var(--sans)!important;
}}
.stFileUploader>div{{
  background:var(--sf2)!important;
  border:2px dashed color-mix(in srgb,var(--ac) 30%,transparent)!important;
  border-radius:var(--rad)!important;
}}
.stFileUploader label{{color:var(--mu)!important;}}
div[data-testid="stSidebar"]{{
  background:var(--sf)!important;
  border-right:1px solid var(--bd)!important;
  min-width:300px!important;max-width:300px!important;
}}
div[data-testid="stSidebar"] .stMarkdown p,
div[data-testid="stSidebar"] label,
div[data-testid="stSidebar"] .stSelectbox label{{color:var(--tx)!important;}}
.stExpander summary{{color:var(--mu)!important;font-size:.82rem!important;}}
.stExpander[data-expanded="true"] summary{{color:var(--tx)!important;}}
.stDivider{{border-color:var(--bd)!important;}}
.stAlert{{background:var(--sf2)!important;border-color:var(--bd)!important;}}
.element-container{{animation:fadeUp .2s ease;}}
@keyframes fadeUp{{from{{opacity:0;transform:translateY(4px)}}to{{opacity:1;transform:none}}}}
</style>
""", unsafe_allow_html=True)

inject_css()

# ════════════════════════════════════════════════════════════════
# WEBCAM HTML — always-on, browser-native
# ════════════════════════════════════════════════════════════════
CAM_HTML = f"""
<!DOCTYPE html>
<html>
<head>
<style>
*{{margin:0;padding:0;box-sizing:border-box;}}
body{{background:#000;font-family:'DM Sans',sans-serif;overflow:hidden;}}

#wrap{{position:relative;width:100%;height:480px;background:#000;}}
video{{width:100%;height:100%;object-fit:cover;display:block;}}

/* Overlay HUD */
#hud{{
  position:absolute;inset:0;pointer-events:none;
}}

/* Top-left: logo */
#hud-logo{{
  position:absolute;top:14px;left:14px;
  color:rgba(255,255,255,.7);font-size:.75rem;
  display:flex;align-items:center;gap:6px;
}}
#live-dot{{
  width:7px;height:7px;border-radius:50%;
  background:#4ade80;box-shadow:0 0 6px #4ade80;
  animation:pulse 2s infinite;
}}
@keyframes pulse{{0%,100%{{opacity:1}}50%{{opacity:.3}}}}

/* Bottom: detected label */
#detect-box{{
  position:absolute;bottom:56px;left:14px;
  background:rgba(0,0,0,.65);backdrop-filter:blur(8px);
  border:1px solid rgba(255,255,255,.12);border-radius:8px;
  padding:6px 12px;display:none;
}}
#detect-text{{
  font-size:.72rem;color:#8ab4f8;font-family:'DM Mono',monospace;
}}
#detect-sub{{font-size:.62rem;color:rgba(255,255,255,.4);margin-top:2px;}}

/* Corner brackets */
.corner{{position:absolute;width:18px;height:18px;opacity:.4;}}
.corner.tl{{top:10px;left:10px;border-top:2px solid #8ab4f8;border-left:2px solid #8ab4f8;}}
.corner.tr{{top:10px;right:10px;border-top:2px solid #8ab4f8;border-right:2px solid #8ab4f8;}}
.corner.bl{{bottom:50px;left:10px;border-bottom:2px solid #8ab4f8;border-left:2px solid #8ab4f8;}}
.corner.br{{bottom:50px;right:10px;border-bottom:2px solid #8ab4f8;border-right:2px solid #8ab4f8;}}

/* Offline state */
#offline{{
  position:absolute;inset:0;display:flex;flex-direction:column;
  align-items:center;justify-content:center;gap:12px;color:#444;
}}
#offline-icon{{font-size:3rem;opacity:.3;}}
#offline-text{{font-size:.82rem;}}
#offline-sub{{font-size:.7rem;color:#333;}}

/* Bottom controls bar */
#controls{{
  position:absolute;bottom:0;left:0;right:0;
  padding:10px 14px;
  background:linear-gradient(transparent,rgba(0,0,0,.8));
  display:flex;align-items:center;gap:10px;pointer-events:all;
}}
.ctrl-btn{{
  padding:7px 16px;border-radius:20px;font-size:.75rem;
  border:1px solid rgba(255,255,255,.18);
  background:rgba(0,0,0,.5);color:rgba(255,255,255,.8);
  cursor:pointer;backdrop-filter:blur(8px);
  font-family:'DM Sans',sans-serif;transition:.15s;
  white-space:nowrap;
}}
.ctrl-btn:hover{{background:rgba(255,255,255,.1);color:#fff;}}
.ctrl-btn.primary{{
  background:{T('accent')};color:#000;border:none;font-weight:600;
}}
.ctrl-btn.primary:hover{{opacity:.85;}}
#snap-flash{{
  position:absolute;inset:0;background:#fff;opacity:0;pointer-events:none;
  transition:opacity .1s;
}}
</style>
</head>
<body>
<div id="wrap">
  <video id="vid" autoplay playsinline muted></video>

  <!-- Scan corners -->
  <div class="corner tl"></div>
  <div class="corner tr"></div>
  <div class="corner bl"></div>
  <div class="corner br"></div>

  <!-- HUD -->
  <div id="hud">
    <div id="hud-logo">
      <div id="live-dot" style="display:none;"></div>
      <span id="hud-status">OFFLINE</span>
    </div>
    <div id="detect-box">
      <div id="detect-text">Scanning…</div>
      <div id="detect-sub">tap Analyse to identify</div>
    </div>
  </div>

  <!-- Offline placeholder -->
  <div id="offline">
    <div id="offline-icon">📷</div>
    <div id="offline-text">Camera ready</div>
    <div id="offline-sub">Press Start to activate</div>
  </div>

  <!-- Snap flash -->
  <div id="snap-flash"></div>

  <!-- Controls -->
  <div id="controls">
    <button class="ctrl-btn primary" id="btn-start" onclick="startCam()">▶ Start Camera</button>
    <button class="ctrl-btn" id="btn-snap" onclick="snapPhoto()" style="display:none;">📸 Capture</button>
    <button class="ctrl-btn" id="btn-stop" onclick="stopCam()" style="display:none;">■ Stop</button>
    <button class="ctrl-btn" id="btn-front" onclick="toggleFacing()" style="display:none;">🔄 Flip</button>
  </div>
</div>

<!-- hidden output -->
<input type="hidden" id="snap-out" value="">

<script>
let stream = null;
let facing = 'environment'; // rear cam default

async function startCam() {{
  try {{
    stream = await navigator.mediaDevices.getUserMedia({{
      video: {{ facingMode: facing, width:{{ideal:1280}}, height:{{ideal:720}} }},
      audio: false
    }});
    document.getElementById('vid').srcObject = stream;
    document.getElementById('offline').style.display = 'none';
    document.getElementById('live-dot').style.display = 'block';
    document.getElementById('hud-status').textContent = 'LIVE';
    document.getElementById('detect-box').style.display = 'block';
    document.getElementById('btn-start').style.display = 'none';
    document.getElementById('btn-snap').style.display  = 'block';
    document.getElementById('btn-stop').style.display  = 'block';
    document.getElementById('btn-front').style.display = 'block';
  }} catch(e) {{
    document.getElementById('offline-text').textContent = 'Camera permission denied';
    document.getElementById('offline-sub').textContent  = 'Allow camera in browser settings';
  }}
}}

async function toggleFacing() {{
  facing = facing === 'environment' ? 'user' : 'environment';
  if (stream) {{ stream.getTracks().forEach(t => t.stop()); }}
  await startCam();
}}

function stopCam() {{
  if (stream) {{ stream.getTracks().forEach(t => t.stop()); stream = null; }}
  document.getElementById('vid').srcObject = null;
  document.getElementById('offline').style.display = 'flex';
  document.getElementById('live-dot').style.display = 'none';
  document.getElementById('hud-status').textContent = 'OFFLINE';
  document.getElementById('detect-box').style.display = 'none';
  document.getElementById('btn-start').style.display = 'block';
  document.getElementById('btn-snap').style.display  = 'none';
  document.getElementById('btn-stop').style.display  = 'none';
  document.getElementById('btn-front').style.display = 'none';
}}

function snapPhoto() {{
  const vid = document.getElementById('vid');
  const cnv = document.createElement('canvas');
  cnv.width  = vid.videoWidth  || 640;
  cnv.height = vid.videoHeight || 480;
  cnv.getContext('2d').drawImage(vid, 0, 0);

  // Flash effect
  const fl = document.getElementById('snap-flash');
  fl.style.opacity = '0.7';
  setTimeout(() => fl.style.opacity = '0', 120);

  const b64 = cnv.toDataURL('image/jpeg', 0.85);
  document.getElementById('snap-out').value = b64;

  // Post to Streamlit via URL param trick
  const url = new URL(window.location.href);
  url.searchParams.set('snap', Date.now().toString());
  window.history.replaceState({{}}, '', url);

  // Store in parent
  try {{
    window.parent.postMessage({{ type:'friday_snap', data: b64 }}, '*');
  }} catch(e) {{}}
}}
</script>
</body>
</html>
"""

# ════════════════════════════════════════════════════════════════
#VISION  ← paste your detection/analysis logic here
# ════════════════════════════════════════════════════════════════
def analyse_image(image_b64: str, question: str = "") -> str:
    """
    Send image to Groq vision model.
    image_b64: base64 string (with or without data: prefix)
    question:  optional custom question, defaults to VISION_PROMPT
    """
    key = st.session_state.groq_key
    if not key:
        return "Add your Groq API key in ⚙ Settings to analyse images."
    if not GROQ_OK:
        return "Install groq: pip install groq"

    # Strip data URL prefix
    if "," in image_b64:
        image_b64 = image_b64.split(",", 1)[1]

    prompt = question if question.strip() else VISION_PROMPT

    try:
        client = Groq(api_key=key)
        r = client.chat.completions.create(
            model=st.session_state.vision_model,
            messages=[{
                "role": "user",
                "content": [
                    {"type": "image_url",
                     "image_url": {"url": f"data:image/jpeg;base64,{image_b64}"}},
                    {"type": "text", "text": prompt}
                ]
            }],
            max_tokens=400
        )
        result = r.choices[0].message.content.strip()
        # Extract first line as detected label
        first_line = result.split("\n")[0][:60]
        st.session_state.detected = first_line
        return result
    except Exception as e:
        return f"Vision error: {e}"

# ════════════════════════════════════════════════════════════════
#AI  ← swap LLM provider here
# ════════════════════════════════════════════════════════════════
def ask_ai(query: str, kb_ctx: str = "", cam_ctx: str = "") -> str:
    """
    Core LLM call. Swap provider by changing this function.
    kb_ctx:  text from RAG knowledge base
    cam_ctx: recent camera analysis
    """
    key = st.session_state.groq_key
    if not key:
        return "Add your Groq API key in ⚙ Settings (top-right gear icon)."
    if not GROQ_OK:
        return "Install groq: pip install groq"

    sys = st.session_state.sys_prompt.format(
        time=datetime.now().strftime("%I:%M %p, %A %d %B %Y")
    )
    if kb_ctx:
        sys += f"\n\n[Knowledge Base]\n{kb_ctx}"
    if cam_ctx:
        sys += f"\n\n[Camera just saw: {cam_ctx[:300]}]"

    history = [{"role": m["role"], "content": m["content"]}
               for m in st.session_state.messages[-12:]]

    try:
        client = Groq(api_key=key)
        r = client.chat.completions.create(
            model=st.session_state.chat_model,
            messages=[{"role": "system", "content": sys}] + history +
                     [{"role": "user", "content": query}],
            max_tokens=500, temperature=0.7
        )
        return r.choices[0].message.content.strip()
    except Exception as e:
        return f"Error: {e}"

# ════════════════════════════════════════════════════════════════
#RAG  ← knowledge ingestion
# ════════════════════════════════════════════════════════════════
@st.cache_resource(show_spinner=False)
def load_embeddings():
    if not RAG_OK:
        return None
    try:
        return HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2"
        )
    except:
        return None

def rag_query(q: str) -> str:
    vs = st.session_state.vectorstore
    if not vs:
        return ""
    try:
        docs = vs.similarity_search(q, k=CFG.RAG_TOP_K)
        return "\n\n".join(d.page_content for d in docs)
    except:
        return ""

def ingest_pdf(f) -> dict:
    if not RAG_OK:
        return {"error": "Install: langchain-huggingface faiss-cpu pypdf"}
    path = CFG.UPLOAD_DIR / f.name
    path.write_bytes(f.getbuffer())
    try:
        pages = PyPDFLoader(str(path)).load()
        docs  = RecursiveCharacterTextSplitter(
            chunk_size=CFG.CHUNK_SIZE, chunk_overlap=CFG.CHUNK_OVERLAP
        ).split_documents(pages)
        emb = load_embeddings()
        if not emb:
            return {"error": "Embeddings failed — check sentence-transformers install"}
        if st.session_state.vectorstore is None:
            st.session_state.vectorstore = FAISS.from_documents(docs, emb)
        else:
            st.session_state.vectorstore.add_documents(docs)
        return {"pages": len(pages), "chunks": len(docs)}
    except Exception as e:
        return {"error": str(e)}

def ingest_text(name: str, text: str) -> dict:
    if not RAG_OK:
        return {"error": "RAG not available"}
    try:
        docs = RecursiveCharacterTextSplitter(
            chunk_size=CFG.CHUNK_SIZE, chunk_overlap=CFG.CHUNK_OVERLAP
        ).split_documents([Document(page_content=text, metadata={"source": name})])
        emb = load_embeddings()
        if not emb:
            return {"error": "Embeddings failed"}
        if st.session_state.vectorstore is None:
            st.session_state.vectorstore = FAISS.from_documents(docs, emb)
        else:
            st.session_state.vectorstore.add_documents(docs)
        return {"chunks": len(docs)}
    except Exception as e:
        return {"error": str(e)}

def _add_msg(role, content, used_kb=False, used_cam=False):
    st.session_state.messages.append({
        "role": role, "content": content,
        "time": datetime.now().strftime("%I:%M %p"),
        "used_kb": used_kb, "used_cam": used_cam,
    })

# ════════════════════════════════════════════════════════════════
#UI_MAIN  ← layout starts here
# ════════════════════════════════════════════════════════════════

# ── TOP BAR ──────────────────────────────────────────────────────────────
key_ok   = bool(st.session_state.groq_key)
kb_count = len(st.session_state.kb_docs)

top_l, top_r = st.columns([8, 2])
with top_l:
    st.markdown(f"""
    <div class="topbar" style="border-bottom:none;padding:10px 0 6px;">
      <div class="logo">
        <span class="logo-star">✦</span> Friday
      </div>
      <div class="topbar-right">
        <div class="status-pill">
          <div class="sdot {'sdot-green' if key_ok else 'sdot-grey'}"></div>
          {'AI ready' if key_ok else 'No API key'}
        </div>
        {"" if not kb_count else f'<div class="status-pill"><div class="sdot sdot-blue"></div>{kb_count} doc{"s" if kb_count!=1 else ""}</div>'}
      </div>
    </div>
    """, unsafe_allow_html=True)

with top_r:
    st.markdown("<div style='height:4px'></div>", unsafe_allow_html=True)
    settings_btn = st.button("⚙ Settings", key="open_settings")
    if settings_btn:
        st.session_state["settings_open"] = not st.session_state.get("settings_open", False)

st.markdown("<hr style='margin:0;border-color:var(--bd);'>", unsafe_allow_html=True)

# ── TWO COLUMN LAYOUT ─────────────────────────────────────────────────────
col_cam, col_chat = st.columns([11, 10], gap="small")

# ══════════════════════════════════════════
#  LEFT: CAMERA (always on, browser-native)
# ══════════════════════════════════════════
with col_cam:
    # Render the always-on browser webcam
    st.components.v1.html(CAM_HTML, height=490, scrolling=False)

    # ── Upload photo (cloud fallback + extra use case) ───────────────────
    with st.expander("📁 Upload photo to analyse"):
        uf = st.file_uploader("img", type=["jpg","jpeg","png","webp"],
                               label_visibility="collapsed", key="up_img")
        uq = st.text_input("Question", placeholder="What's wrong with this plant?",
                            key="up_q", label_visibility="visible")
        if uf:
            st.image(uf, use_container_width=True)
            if st.button("✦ Analyse", key="do_analyse"):
                b64 = base64.b64encode(uf.read()).decode()
                with st.spinner("Analysing…"):
                    result = analyse_image(b64, uq)
                st.session_state.cam_analysis = result
                _add_msg("user",      f"[Image] {uq or 'What do you see?'}", used_cam=False)
                _add_msg("assistant", result, used_cam=True)
                st.rerun()

# ══════════════════════════════════════════
#  RIGHT: CHAT
# ══════════════════════════════════════════
with col_chat:

    # ── Messages area ────────────────────────────────────────────────────
    if not st.session_state.messages:
        st.markdown(f"""
        <div style="padding:32px 16px 16px;text-align:center;">
          <div style="font-size:1.6rem;font-weight:300;letter-spacing:-.02em;margin-bottom:8px;">
            Hello, <b style="color:{T('accent')};font-weight:600;">Boss</b>
          </div>
          <div style="font-size:.84rem;color:{T('muted')};line-height:1.7;max-width:260px;margin:0 auto 16px;">
            Start camera → capture → I'll identify objects, plants, problems and give solutions.
          </div>
        </div>
        """, unsafe_allow_html=True)

        # Suggestion chips as real buttons
        c1, c2, c3 = st.columns(3)
        suggestions = [
            (c1, "🌿 Identify plant", "Identify this plant and tell me how to care for it."),
            (c2, "🔍 What is this?",  "What object is this? Explain what it's used for."),
            (c3, "⚠️ Any problems?",  "Do you see any problems, damage or issues? How to fix?"),
        ]
        for col, label, prompt in suggestions:
            with col:
                if st.button(label, key=f"sug_{label}", use_container_width=True):
                    kb_ctx = rag_query(prompt)
                    cam_ctx = st.session_state.cam_analysis
                    with st.spinner(""):
                        reply = ask_ai(prompt, kb_ctx, cam_ctx)
                    _add_msg("user",      prompt)
                    _add_msg("assistant", reply, used_kb=bool(kb_ctx), used_cam=bool(cam_ctx))
                    st.rerun()
    else:
        # Message list
        chat_c = st.container(height=380)
        with chat_c:
            for m in st.session_state.messages:
                kb_b  = f'<span class="kb-badge">KB</span>'  if m.get("used_kb")  else ""
                cam_b = f'<span class="cam-badge">CAM</span>' if m.get("used_cam") else ""
                t_str = m.get("time","")

                if m["role"] == "user":
                    st.markdown(f"""
                    <div class="msg-user" style="margin:4px 0;">
                      <div class="bub bub-user">{m['content']}
                        <div class="bub-meta">{t_str}</div>
                      </div>
                    </div>""", unsafe_allow_html=True)
                else:
                    st.markdown(f"""
                    <div class="msg-ai" style="margin:4px 0;">
                      <div class="av">✦</div>
                      <div class="bub bub-ai">{m['content']}{kb_b}{cam_b}
                        <div class="bub-meta">{t_str}</div>
                      </div>
                    </div>""", unsafe_allow_html=True)

    # ── Input bar ─────────────────────────────────────────────────────────
    st.markdown(f"""
    <div style="height:1px;background:var(--bd);margin:4px 0;"></div>
    """, unsafe_allow_html=True)

    with st.form("chat_form", clear_on_submit=True):
        fc1, fc2 = st.columns([10, 2])
        with fc1:
            user_msg = st.text_input("m", placeholder="Ask Friday anything…",
                                      label_visibility="collapsed")
        with fc2:
            sent = st.form_submit_button("Send", use_container_width=True)

    if sent and user_msg.strip():
        q      = user_msg.strip()
        kb_ctx = rag_query(q)
        cam_ctx = st.session_state.cam_analysis
        with st.spinner(""):
            reply = ask_ai(q, kb_ctx, cam_ctx)
        _add_msg("user",      q)
        _add_msg("assistant", reply, used_kb=bool(kb_ctx), used_cam=bool(cam_ctx))
        st.rerun()

    # Quick action row
    qa1, qa2, qa3, qa4 = st.columns(4)
    quick = [
        (qa1, "🕐 Time",    "What time and date is it?"),
        (qa2, "🌤 Weather", "What's the weather like today?"),
        (qa3, "💡 Tip",     "Give me one useful daily life tip."),
        (qa4, "🗑 Clear",   None),
    ]
    for col, label, prompt in quick:
        with col:
            if st.button(label, key=f"q_{label}", use_container_width=True):
                if prompt is None:
                    st.session_state.messages = []
                    st.session_state.cam_analysis = ""
                    st.rerun()
                else:
                    kb_ctx = rag_query(prompt)
                    reply  = ask_ai(prompt, kb_ctx)
                    _add_msg("user", prompt)
                    _add_msg("assistant", reply, used_kb=bool(kb_ctx))
                    st.rerun()

# ════════════════════════════════════════════════════════════════
#UI_SIDEBAR  ← Settings panel
# ════════════════════════════════════════════════════════════════
if st.session_state.get("settings_open"):
    with st.sidebar:
        st.markdown(f"### ⚙️ Settings")
        st.markdown("---")

        # ── THEME ─────────────────────────────────────────────────────────
        st.markdown("**Theme**")
        theme_cols = st.columns(len(THEMES))
        for i, (tname, tdata) in enumerate(THEMES.items()):
            with theme_cols[i]:
                is_active = st.session_state.theme_name == tname
                border = f"2px solid {tdata['accent']}" if is_active else "2px solid transparent"
                st.markdown(f"""
                <div style="width:100%;aspect-ratio:1;border-radius:8px;
                  background:linear-gradient(135deg,{tdata['bg']},{tdata['surface']});
                  border:{border};cursor:pointer;position:relative;
                  display:flex;align-items:center;justify-content:center;">
                  <div style="width:8px;height:8px;border-radius:50%;
                    background:{tdata['accent']};"></div>
                </div>
                <div style="font-size:.6rem;color:{'#fff' if is_active else '#666'};
                  text-align:center;margin-top:3px;">{tname}</div>
                """, unsafe_allow_html=True)
                if st.button("  ", key=f"th_{tname}", use_container_width=True,
                             help=tname):
                    st.session_state.theme_name = tname
                    st.rerun()

        st.markdown("---")

        # ── API KEY ───────────────────────────────────────────────────────
        st.markdown("**Groq API Key**")
        new_key = st.text_input("key", value=st.session_state.groq_key,
                                 placeholder="gsk_…", type="password",
                                 label_visibility="collapsed")
        if new_key != st.session_state.groq_key:
            st.session_state.groq_key = new_key
            st.success("✓ Key saved")
        st.caption("[Get free key → console.groq.com](https://console.groq.com)")

        st.markdown("---")

        # ── MODELS ────────────────────────────────────────────────────────
        st.markdown("**Chat Model**")
        cm_idx = CFG.CHAT_MODELS.index(st.session_state.chat_model) \
                 if st.session_state.chat_model in CFG.CHAT_MODELS else 0
        st.session_state.chat_model = st.selectbox(
            "cm", CFG.CHAT_MODELS, index=cm_idx, label_visibility="collapsed"
        )

        st.markdown("**Vision Model**")
        vm_idx = CFG.VISION_MODELS.index(st.session_state.vision_model) \
                 if st.session_state.vision_model in CFG.VISION_MODELS else 0
        st.session_state.vision_model = st.selectbox(
            "vm", CFG.VISION_MODELS, index=vm_idx, label_visibility="collapsed"
        )

        st.markdown("---")

        # ── KNOWLEDGE BASE ────────────────────────────────────────────────
        st.markdown("**Knowledge Base**")

        uploaded_pdf = st.file_uploader("Upload PDF", type=["pdf"],
                                         label_visibility="collapsed")
        if uploaded_pdf:
            if not any(d["name"] == uploaded_pdf.name for d in st.session_state.kb_docs):
                with st.spinner("Processing PDF…"):
                    result = ingest_pdf(uploaded_pdf)
                if "error" in result:
                    st.error(result["error"])
                else:
                    st.session_state.kb_docs.append({
                        "name": uploaded_pdf.name,
                        "type": "pdf",
                        "pages": result["pages"],
                    })
                    st.success(f"✓ {result['pages']} pages · {result['chunks']} chunks")

        with st.expander("📝 Add text / notes"):
            txt_title = st.text_input("Title", placeholder="My notes", key="txt_t")
            txt_body  = st.text_area("Content", placeholder="Paste text here…",
                                      height=100, key="txt_b")
            if st.button("Add to KB", use_container_width=True, key="add_txt"):
                if txt_body.strip():
                    with st.spinner("Adding…"):
                        r = ingest_text(txt_title or "Notes", txt_body)
                    if "error" in r:
                        st.error(r["error"])
                    else:
                        st.session_state.kb_docs.append({
                            "name": txt_title or "Notes",
                            "type": "text",
                            "chunks": r["chunks"],
                        })
                        st.success(f"✓ {r['chunks']} chunks added")

        # Doc list
        if st.session_state.kb_docs:
            st.markdown(f"**{len(st.session_state.kb_docs)} documents**")
            for i, d in enumerate(st.session_state.kb_docs):
                dc1, dc2 = st.columns([5, 1])
                with dc1:
                    icon = "📄" if d["type"] == "pdf" else "📝"
                    info = f"{d.get('pages','?')}p" if d["type"]=="pdf" else f"{d.get('chunks','?')} chunks"
                    st.markdown(
                        f"<div style='font-size:.76rem;color:var(--tx);'>{icon} {d['name']}</div>"
                        f"<div style='font-size:.62rem;color:var(--mu);'>{info}</div>",
                        unsafe_allow_html=True
                    )
                with dc2:
                    if st.button("✕", key=f"rm_{i}", help="Remove"):
                        st.session_state.kb_docs.pop(i)
                        st.rerun()
            if st.button("🗑 Clear all KB", use_container_width=True, key="clr_kb"):
                st.session_state.kb_docs = []
                st.session_state.vectorstore = None
                st.rerun()

        st.markdown("---")

        # ── SYSTEM PROMPT ─────────────────────────────────────────────────
        with st.expander("✏️ Friday's personality"):
            new_p = st.text_area("Prompt", value=st.session_state.sys_prompt,
                                  height=140, label_visibility="collapsed")
            if st.button("Save", key="save_p", use_container_width=True):
                st.session_state.sys_prompt = new_p
                st.success("Saved!")

        st.markdown("---")

        # ── DANGER ZONE ───────────────────────────────────────────────────
        with st.expander("🗑 Reset"):
            if st.button("Clear Chat", use_container_width=True, key="clr_chat"):
                st.session_state.messages = []
                st.rerun()
            if st.button("Reset Everything", use_container_width=True, key="rst_all"):
                for k in ["messages","kb_docs","vectorstore","cam_analysis","detected"]:
                    st.session_state[k] = [] if k in ["messages","kb_docs"] else None \
                        if k == "vectorstore" else ""
                st.rerun()

        st.markdown(
            f"<div style='font-size:.6rem;color:var(--mu);text-align:center;margin-top:12px;'>"
            f"Friday v5.0 · Theme: {st.session_state.theme_name}</div>",
            unsafe_allow_html=True
        )
