"""
FRIDAY v12.0 - Enhanced Edition
- Auto-start on load (no click required)
- Text chat input with send button
- File upload as RAG (txt, md, pdf client-side)
- Quick prompt chips
- Copy last response
- Improved UX polish
"""

import os
import streamlit as st
import json
from dotenv import load_dotenv
load_dotenv()

def load_config(file, default):
    if os.path.exists(file):
        with open(file, 'r') as f:
            return json.load(f)
    return default

CONFIG = load_config("friday_config.json", {
    "groq_api_key": os.getenv("GROQ_API_KEY", ""),
    "chat_model": "llama-3.3-70b-versatile",
    "vision_model": "meta-llama/llama-4-scout-17b-16e-instruct",
    "system_prompt": "You are Friday, a real-time AI voice assistant. You understand both English and Hindi (written in Roman script/Hinglish). Be concise and helpful.",
    "tts_voice": "en-IN-NeerjaNeural",
    "enable_rag": True,
    "max_tokens": 250,
    "temperature": 0.75
})

st.set_page_config(
    page_title="Friday AI",
    page_icon="✦",
    layout="wide",
    initial_sidebar_state="collapsed"
)

st.markdown("""
<style>
* { margin:0; padding:0; }
html,body,[class*="css"] { background:#000!important; overflow:hidden; }
#MainMenu,footer,header { visibility:hidden; }
.block-container { padding:0!important; max-width:100%!important; }
iframe { border:none!important; }
</style>
""", unsafe_allow_html=True)

if not CONFIG['groq_api_key']:
    st.error("❌ GROQ_API_KEY not set. Add it to .env or friday_config.json")
    st.stop()

KNOWLEDGE_CONTEXT = ""
if CONFIG['enable_rag'] and os.path.exists("friday_knowledge/"):
    files = [f for f in os.listdir("friday_knowledge/") if f.endswith(('.txt', '.md'))]
    for file in files[:5]:
        try:
            with open(os.path.join("friday_knowledge/", file), 'r', encoding='utf-8') as f:
                KNOWLEDGE_CONTEXT += f"\n\n[Knowledge: {file}]:\n{f.read()[:3000]}"
        except:
            pass

safe_knowledge = KNOWLEDGE_CONTEXT.replace('`', "'").replace('\\', '\\\\').replace('\n', '\\n')[:3000]
safe_prompt = CONFIG['system_prompt'].replace('`', "'").replace('\\', '\\\\').replace('\n', '\\n')

HTML = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Friday AI</title>
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@200;300;400;500&family=DM+Mono:wght@300;400&display=swap');

:root {{
  --blue: #4facfe;
  --purple: #764ba2;
  --pink: #f093fb;
  --glass: rgba(255,255,255,.06);
  --glass-border: rgba(255,255,255,.1);
  --radius: 16px;
}}

* {{ margin:0; padding:0; box-sizing:border-box; }}
html,body {{
  width:100vw; height:100vh; overflow:hidden;
  background:#000; font-family:'DM Sans', sans-serif; color:#fff; user-select:none;
}}

/* ── CAMERA ── */
#vid {{
  position:fixed; inset:0; width:100%; height:100%; object-fit:cover;
  opacity:0; transition:opacity 1.4s; filter:brightness(.6) saturate(1.1);
}}
#vid.on {{ opacity:1; }}
#vid.analyzing {{ filter:brightness(.55) saturate(1.6) hue-rotate(12deg); transition:filter .4s; }}

/* ── OVERLAYS ── */
.vignette {{
  position:fixed; inset:0; z-index:1; pointer-events:none;
  background:radial-gradient(ellipse at center, transparent 30%, rgba(0,0,0,.8) 100%);
}}
.scan-line {{
  position:fixed; inset:0; z-index:1; pointer-events:none; opacity:0; transition:opacity .3s;
  background:repeating-linear-gradient(0deg, transparent, transparent 2px, rgba(0,255,200,.015) 2px, rgba(0,255,200,.015) 4px);
}}
.scan-line.active {{ opacity:1; }}
.grad-overlay {{
  position:fixed; inset:0; z-index:1; pointer-events:none;
  background:linear-gradient(to bottom, rgba(0,0,0,.55) 0%, transparent 20%, transparent 65%, rgba(0,0,0,.9) 100%);
}}

/* ══ ORB — Bottom Right ══ */
#orb-wrap {{
  position:fixed; z-index:20; bottom:32px; right:32px;
  width:96px; height:96px;
  opacity:0; transition:opacity .8s, transform .25s;
  cursor:pointer;
}}
#orb-wrap.on {{ opacity:1; }}
#orb-wrap:hover {{ transform:scale(1.06); }}
#orb-glow {{
  position:absolute; inset:-28px; border-radius:50%;
  background:radial-gradient(circle, rgba(79,172,254,.22) 0%, transparent 70%);
  opacity:0; transition:opacity .5s;
  animation:glowPulse 3s ease-in-out infinite;
}}
#orb-wrap.listening #orb-glow,
#orb-wrap.speaking #orb-glow {{ opacity:1; }}
@keyframes glowPulse {{ 0%,100% {{ transform:scale(1); }} 50% {{ transform:scale(1.18); }} }}

#orb {{
  position:absolute; inset:0; border-radius:50%;
  background:radial-gradient(circle at 32% 28%,
    rgba(220,240,255,.95) 0%, #4facfe 18%, #00c9ff 33%,
    #667eea 52%, #764ba2 70%, #f093fb 86%, #ff6fd8 100%);
  box-shadow:0 0 36px rgba(79,172,254,.5), 0 0 72px rgba(102,126,234,.2),
    inset 0 0 28px rgba(255,255,255,.08);
  transition:box-shadow .4s;
}}
#orb-wrap.listening #orb {{ animation:orbPulse 1.1s ease-in-out infinite; }}
#orb-wrap.thinking #orb {{ animation:orbSpin 2.5s linear infinite; filter:blur(1px) brightness(1.15); }}
#orb-wrap.speaking #orb {{ animation:orbWave .85s ease-in-out infinite; }}
#orb-wrap.analyzing #orb {{ animation:orbScan 1.8s ease-in-out infinite; }}
#orb-wrap.sleeping #orb {{ opacity:.35; filter:brightness(.55); }}
@keyframes orbPulse {{ 0%,100% {{ transform:scale(1); box-shadow:0 0 36px rgba(79,172,254,.5); }} 50% {{ transform:scale(1.13); box-shadow:0 0 65px rgba(79,172,254,.8); }} }}
@keyframes orbSpin {{ from {{ transform:rotate(0deg) scale(1.05); }} to {{ transform:rotate(360deg) scale(1.05); }} }}
@keyframes orbWave {{ 0%,100% {{ border-radius:50%; transform:scale(1); }} 25% {{ border-radius:48% 52%; transform:scale(1.05); }} 50% {{ transform:scale(1.09); }} 75% {{ border-radius:52% 48%; transform:scale(1.05); }} }}
@keyframes orbScan {{ 0%,100% {{ transform:scale(1); box-shadow:0 0 36px rgba(0,200,255,.6); }} 50% {{ transform:scale(1.09); box-shadow:0 0 75px rgba(0,200,255,1); }} }}
#orb-label {{
  position:absolute; bottom:-26px; left:50%; transform:translateX(-50%);
  font-size:.58rem; letter-spacing:.12em; text-transform:uppercase;
  color:rgba(255,255,255,.4); white-space:nowrap; font-weight:300;
  transition:color .3s;
}}
#orb-wrap.listening #orb-label {{ color:rgba(79,172,254,.9); }}
#orb-wrap.speaking #orb-label {{ color:rgba(240,147,251,.9); }}
#orb-wrap.thinking #orb-label {{ color:rgba(118,75,162,.9); }}
#orb-wrap::after {{
  content:''; position:absolute; inset:0; border-radius:50%;
  border:1px solid rgba(255,255,255,.18); opacity:0; transform:scale(1);
}}
#orb-wrap.listening::after {{ animation:ripple 2s ease-out infinite; }}
@keyframes ripple {{ 0% {{ opacity:.5; transform:scale(1); }} 100% {{ opacity:0; transform:scale(1.9); }} }}

/* ── CONV PANEL ── */
#conv-panel {{
  position:fixed; z-index:10;
  bottom:200px; right:32px;
  width:min(360px, calc(100vw - 64px));
  max-height:calc(100vh - 280px);
  overflow-y:auto; overflow-x:hidden;
  display:flex; flex-direction:column; gap:8px;
  scrollbar-width:thin; scrollbar-color:rgba(255,255,255,.08) transparent;
}}
#conv-panel::-webkit-scrollbar {{ width:3px; }}
#conv-panel::-webkit-scrollbar-thumb {{ background:rgba(255,255,255,.12); border-radius:4px; }}

.msg {{
  max-width:92%; padding:9px 13px; border-radius:14px;
  font-size:.8rem; line-height:1.65; font-weight:300;
  animation:msgIn .28s ease; backdrop-filter:blur(14px);
  position:relative;
}}
@keyframes msgIn {{ from {{ opacity:0; transform:translateY(6px) scale(.97); }} to {{ opacity:1; transform:none; }} }}
.msg.user {{
  align-self:flex-end; margin-left:auto;
  background:rgba(79,172,254,.16); border:1px solid rgba(79,172,254,.28);
  border-bottom-right-radius:4px; color:rgba(255,255,255,.9);
}}
.msg.assistant {{
  align-self:flex-start;
  background:rgba(255,255,255,.07); border:1px solid rgba(255,255,255,.1);
  border-bottom-left-radius:4px; color:rgba(255,255,255,.85);
}}
.msg-footer {{
  display:flex; justify-content:space-between; align-items:center;
  margin-top:5px;
}}
.msg-time {{ font-size:.56rem; color:rgba(255,255,255,.28); font-weight:300; font-family:'DM Mono'; }}
.copy-btn {{
  font-size:.58rem; color:rgba(255,255,255,.2); cursor:pointer;
  background:none; border:none; padding:0 2px; transition:color .2s;
  display:none;
}}
.msg.assistant:hover .copy-btn {{ display:block; color:rgba(255,255,255,.4); }}
.copy-btn:hover {{ color:rgba(79,172,254,.9)!important; }}

/* ── LOGO ── */
#logo {{
  position:fixed; top:26px; left:26px; z-index:10;
  font-family:'DM Mono', monospace; font-size:.85rem; font-weight:300;
  letter-spacing:.3em; color:rgba(255,255,255,.7);
  opacity:0; transition:opacity .8s .3s;
}}
#logo.on {{ opacity:1; }}
#logo span {{ color:var(--blue); }}

/* ── STATUS BAR ── */
#status-bar {{
  position:fixed; bottom:26px; left:26px; z-index:10;
  display:flex; align-items:center; gap:9px;
  opacity:0; transition:opacity .8s .4s;
}}
#status-bar.on {{ opacity:1; }}
#status-dot {{
  width:6px; height:6px; border-radius:50%;
  background:rgba(79,172,254,.7); box-shadow:0 0 7px rgba(79,172,254,.5);
  transition:background .3s, box-shadow .3s;
}}
#status-dot.listening {{ background:#4facfe; box-shadow:0 0 7px #4facfe; animation:dotBlink 1.2s ease-in-out infinite; }}
#status-dot.speaking {{ background:#f093fb; box-shadow:0 0 7px #f093fb; animation:dotBlink .75s ease-in-out infinite; }}
#status-dot.thinking {{ background:#667eea; box-shadow:0 0 7px #667eea; animation:dotBlink 2s ease-in-out infinite; }}
#status-dot.analyzing {{ background:#00c9ff; box-shadow:0 0 7px #00c9ff; animation:dotBlink 1s ease-in-out infinite; }}
#status-dot.sleeping {{ background:rgba(255,255,255,.18); box-shadow:none; animation:none; }}
@keyframes dotBlink {{ 0%,100% {{ opacity:1; }} 50% {{ opacity:.25; }} }}
#status-text {{
  font-size:.67rem; color:rgba(255,255,255,.4); letter-spacing:.07em;
  font-family:'DM Mono'; font-weight:300;
}}

/* ── CONTROLS ── */
#controls {{
  position:fixed; top:20px; right:20px; z-index:10;
  display:flex; gap:8px;
  opacity:0; transition:opacity .8s .5s;
}}
#controls.on {{ opacity:1; }}
.ctrl-btn {{
  width:40px; height:40px; border-radius:12px;
  background:rgba(0,0,0,.5); border:1px solid rgba(255,255,255,.12);
  color:rgba(255,255,255,.65); font-size:.9rem; cursor:pointer;
  display:flex; align-items:center; justify-content:center;
  backdrop-filter:blur(18px); transition:.2s;
}}
.ctrl-btn:hover {{ background:rgba(255,255,255,.16); border-color:rgba(255,255,255,.28); color:#fff; transform:scale(1.07); }}
.ctrl-btn:active {{ transform:scale(.96); }}
.ctrl-btn.active {{ background:rgba(79,172,254,.2); border-color:rgba(79,172,254,.4); color:var(--blue); }}

/* ── TEXT INPUT BAR ── */
#text-bar {{
  position:fixed; z-index:20;
  bottom:26px; left:50%; transform:translateX(-50%);
  width:min(520px, calc(100vw - 180px));
  display:flex; gap:8px; align-items:flex-end;
  opacity:0; transition:opacity .8s .6s;
}}
#text-bar.on {{ opacity:1; }}

#text-input {{
  flex:1; background:rgba(0,0,0,.6); border:1px solid rgba(255,255,255,.14);
  border-radius:14px; padding:10px 14px; color:#fff; font-size:.8rem;
  font-family:'DM Sans'; font-weight:300; outline:none; resize:none;
  backdrop-filter:blur(20px); line-height:1.5; min-height:40px; max-height:96px;
  overflow-y:auto; transition:border-color .2s, background .2s;
  scrollbar-width:none;
}}
#text-input:focus {{
  border-color:rgba(79,172,254,.4);
  background:rgba(0,0,0,.75);
}}
#text-input::placeholder {{ color:rgba(255,255,255,.25); }}
#text-input::-webkit-scrollbar {{ display:none; }}

#send-btn {{
  width:40px; height:40px; border-radius:12px; flex-shrink:0;
  background:linear-gradient(135deg, #4facfe, #667eea);
  border:none; color:#fff; cursor:pointer; font-size:.9rem;
  display:flex; align-items:center; justify-content:center;
  transition:.2s; box-shadow:0 4px 16px rgba(79,172,254,.3);
}}
#send-btn:hover {{ transform:scale(1.08); box-shadow:0 6px 22px rgba(79,172,254,.45); }}
#send-btn:active {{ transform:scale(.95); }}
#send-btn:disabled {{ opacity:.35; cursor:not-allowed; transform:none; }}

/* Upload button */
#upload-btn {{
  width:40px; height:40px; border-radius:12px; flex-shrink:0;
  background:rgba(0,0,0,.5); border:1px solid rgba(255,255,255,.12);
  color:rgba(255,255,255,.55); cursor:pointer; font-size:.9rem;
  display:flex; align-items:center; justify-content:center;
  backdrop-filter:blur(18px); transition:.2s; position:relative;
}}
#upload-btn:hover {{ background:rgba(118,75,162,.25); border-color:rgba(118,75,162,.4); color:#f093fb; }}
#upload-btn.has-files {{ background:rgba(118,75,162,.2); border-color:rgba(118,75,162,.4); color:#f093fb; }}
#file-input {{ display:none; }}
#file-badge {{
  position:absolute; top:-5px; right:-5px; width:16px; height:16px;
  background:linear-gradient(135deg, #667eea, #764ba2); border-radius:50%;
  font-size:.5rem; display:none; align-items:center; justify-content:center;
  color:#fff; font-weight:500; border:1px solid rgba(0,0,0,.4);
}}
#upload-btn.has-files #file-badge {{ display:flex; }}

/* ── QUICK CHIPS ── */
#chips {{
  position:fixed; z-index:15;
  bottom:80px; left:50%; transform:translateX(-50%);
  display:flex; gap:7px; flex-wrap:nowrap;
  opacity:0; transition:opacity .4s;
  pointer-events:none;
}}
#chips.on {{ opacity:1; pointer-events:all; }}
.chip {{
  padding:5px 12px; border-radius:20px; white-space:nowrap;
  background:rgba(0,0,0,.55); border:1px solid rgba(255,255,255,.12);
  font-size:.68rem; color:rgba(255,255,255,.6); cursor:pointer;
  backdrop-filter:blur(16px); transition:.2s; letter-spacing:.03em;
  font-family:'DM Mono';
}}
.chip:hover {{ background:rgba(79,172,254,.15); border-color:rgba(79,172,254,.35); color:rgba(79,172,254,.9); transform:translateY(-2px); }}
.chip:active {{ transform:translateY(0); }}

/* ── FILE PILLS ── */
#file-pills {{
  position:fixed; z-index:15;
  bottom:124px; left:50%; transform:translateX(-50%);
  display:flex; gap:6px; flex-wrap:wrap; justify-content:center;
  max-width:min(520px, calc(100vw - 40px));
  opacity:0; pointer-events:none; transition:opacity .3s;
}}
#file-pills.show {{ opacity:1; pointer-events:all; }}
.file-pill {{
  padding:3px 10px; border-radius:12px;
  background:rgba(118,75,162,.18); border:1px solid rgba(118,75,162,.3);
  font-size:.6rem; color:rgba(240,147,251,.8); cursor:pointer;
  display:flex; align-items:center; gap:5px; transition:.2s;
  font-family:'DM Mono';
}}
.file-pill:hover {{ background:rgba(240,147,251,.15); }}
.file-pill .remove {{ opacity:.5; }}
.file-pill:hover .remove {{ opacity:1; color:#ff6b6b; }}

/* ── SETTINGS ── */
#settings {{
  position:fixed; top:0; right:0; bottom:0; width:300px;
  background:rgba(5,5,9,.97); border-left:1px solid rgba(255,255,255,.06);
  z-index:200; transform:translateX(100%); transition:transform .3s cubic-bezier(.4,0,.2,1);
  padding:22px 18px; overflow-y:auto; backdrop-filter:blur(30px);
}}
#settings.open {{ transform:translateX(0); }}
.s-overlay {{ position:fixed; inset:0; background:rgba(0,0,0,.55); z-index:199; display:none; backdrop-filter:blur(3px); }}
.s-overlay.show {{ display:block; }}
.s-head {{ font-size:.9rem; font-weight:400; margin-bottom:20px; display:flex; justify-content:space-between; align-items:center; color:rgba(255,255,255,.85); }}
.s-close {{ width:28px; height:28px; border-radius:8px; background:rgba(255,255,255,.06); border:none; color:#666; cursor:pointer; font-size:.85rem; display:flex; align-items:center; justify-content:center; }}
.s-close:hover {{ color:#fff; background:rgba(255,255,255,.12); }}
.s-section {{ font-size:.58rem; color:#333; letter-spacing:.12em; text-transform:uppercase; margin:16px 0 5px; }}
.s-input {{ width:100%; background:rgba(255,255,255,.04); border:1px solid rgba(255,255,255,.09); border-radius:10px; padding:8px 11px; color:#fff; font-size:.78rem; outline:none; font-family:'DM Sans'; }}
.s-input:focus {{ border-color:rgba(79,172,254,.35); background:rgba(79,172,254,.04); }}
select.s-input option {{ background:#0a0a12; }}
.s-btn {{ width:100%; padding:9px; border-radius:10px; background:linear-gradient(135deg,#667eea,#764ba2); color:#fff; border:none; font-weight:500; font-size:.8rem; cursor:pointer; margin-top:10px; font-family:'DM Sans'; letter-spacing:.03em; }}
.s-btn:hover {{ opacity:.9; }}
.s-badge {{ font-size:.55rem; color:rgba(79,172,254,.65); background:rgba(79,172,254,.1); padding:2px 6px; border-radius:6px; border:1px solid rgba(79,172,254,.18); font-family:'DM Mono'; }}

/* ── INIT OVERLAY ── */
#init-overlay {{
  position:fixed; inset:0; z-index:100;
  background:radial-gradient(ellipse at 40% 40%, #0a1020 0%, #050507 70%, #000 100%);
  display:flex; flex-direction:column; align-items:center; justify-content:center; gap:0;
  transition:opacity 1s ease;
}}
#init-overlay.fade {{ opacity:0; pointer-events:none; }}
.init-orb {{
  width:80px; height:80px; border-radius:50%; margin-bottom:24px;
  background:radial-gradient(circle at 32% 28%, rgba(200,230,255,.9) 0%, #4facfe 20%, #667eea 50%, #764ba2 72%, #f093fb 100%);
  animation:initPulse 2s ease-in-out infinite;
  box-shadow:0 0 40px rgba(79,172,254,.4), 0 0 80px rgba(102,126,234,.15);
}}
@keyframes initPulse {{ 0%,100% {{ transform:scale(1); }} 50% {{ transform:scale(1.08); }} }}
.init-title {{
  font-family:'DM Mono'; font-size:1.6rem; font-weight:300;
  letter-spacing:.4em; color:rgba(255,255,255,.85); margin-bottom:6px;
}}
.init-sub {{
  font-size:.65rem; color:rgba(255,255,255,.28); letter-spacing:.15em;
  margin-bottom:28px; font-family:'DM Mono';
}}
.init-status {{
  font-size:.7rem; color:rgba(79,172,254,.6); letter-spacing:.08em;
  font-family:'DM Mono'; min-height:20px; transition:opacity .3s;
}}

/* ── TOAST ── */
#toast {{
  position:fixed; top:70px; left:50%; transform:translateX(-50%);
  background:rgba(0,0,0,.85); border:1px solid rgba(255,255,255,.1);
  border-radius:10px; padding:7px 16px; font-size:.72rem; color:rgba(255,255,255,.8);
  z-index:300; opacity:0; transition:opacity .22s; pointer-events:none;
  backdrop-filter:blur(20px); max-width:min(300px,80vw); text-align:center;
  font-family:'DM Mono';
}}
#toast.show {{ opacity:1; }}

/* ── SHORTCUT ── */
#shortcut-hint {{
  position:fixed; top:70px; right:20px; z-index:10;
  font-size:.55rem; color:rgba(255,255,255,.18); text-align:right;
  font-family:'DM Mono'; line-height:2; opacity:0; transition:opacity .5s 1.5s;
}}
#shortcut-hint.on {{ opacity:1; }}
</style>
</head>
<body>

<video id="vid" autoplay playsinline muted></video>
<div class="vignette"></div>
<div class="scan-line" id="scan"></div>
<div class="grad-overlay"></div>

<!-- ══ AUTO-INIT OVERLAY ══ -->
<div id="init-overlay">
  <div class="init-orb"></div>
  <div class="init-title">FRIDAY</div>
  <div class="init-sub">v12 · AI Assistant</div>
  <div class="init-status" id="init-status">Initializing...</div>
</div>

<!-- ══ MAIN UI ══ -->
<div id="logo">FRI<span>DAY</span></div>

<div id="conv-panel"></div>

<!-- Orb -->
<div id="orb-wrap" onclick="manualActivate()">
  <div id="orb-glow"></div>
  <div id="orb"></div>
  <div id="orb-label">Ready</div>
</div>

<!-- Status bar -->
<div id="status-bar">
  <div id="status-dot" class="sleeping"></div>
  <div id="status-text">Initializing</div>
</div>

<!-- Controls -->
<div id="controls">
  <button class="ctrl-btn" onclick="manualCapture()" title="Capture (V)">📸</button>
  <button class="ctrl-btn" onclick="flipCam()" title="Flip Camera">🔄</button>
  <button class="ctrl-btn" id="mute-btn" onclick="toggleMute()" title="Mute (M)">🔊</button>
  <button class="ctrl-btn" id="voice-btn" onclick="toggleVoiceMode()" title="Voice Mode">🎙</button>
  <button class="ctrl-btn" onclick="clearHistory()" title="Clear (C)">🗑</button>
  <button class="ctrl-btn" onclick="openSettings()" title="Settings">⚙</button>
</div>

<div id="shortcut-hint" class="on">
  Space · Voice &nbsp;|&nbsp; V · Camera<br>
  M · Mute &nbsp;|&nbsp; C · Clear<br>
  Enter · Send text
</div>

<!-- Quick Chips -->
<div id="chips">
  <div class="chip" onclick="sendChip('Summarize what you see')">Summarize</div>
  <div class="chip" onclick="sendChip('Translate to Hindi')">Hindi</div>
  <div class="chip" onclick="sendChip('Explain in simple terms')">Explain</div>
  <div class="chip" onclick="sendChip('What time is it and what should I do next?')">What next?</div>
  <div class="chip" onclick="sendChip('Summarize the uploaded documents')">📎 Docs</div>
</div>

<!-- File pills (uploaded RAG files) -->
<div id="file-pills"></div>

<!-- Text Input Bar -->
<div id="text-bar">
  <div id="upload-btn" onclick="document.getElementById('file-input').click()" title="Upload files as knowledge (txt, md, pdf)">
    📎
    <div id="file-badge">0</div>
  </div>
  <input type="file" id="file-input" accept=".txt,.md,.pdf" multiple onchange="handleFileUpload(this)">
  <textarea id="text-input" placeholder="Type a message… or say 'Friday'" rows="1"
    oninput="autoResize(this)" onkeydown="handleTextKey(event)"></textarea>
  <button id="send-btn" onclick="sendTextMessage()" title="Send (Enter)">↑</button>
</div>

<!-- Settings -->
<div class="s-overlay" id="s-overlay" onclick="closeSettings()"></div>
<div id="settings">
  <div class="s-head">
    <span>Settings</span>
    <span class="s-badge">v12</span>
    <button class="s-close" onclick="closeSettings()">✕</button>
  </div>
  <div class="s-section">Chat Model</div>
  <select class="s-input" id="s-model">
    <option value="llama-3.3-70b-versatile">Llama 3.3 70B (best)</option>
    <option value="llama-3.1-70b-versatile">Llama 3.1 70B</option>
    <option value="llama-3.1-8b-instant">Llama 3.1 8B (fast)</option>
    <option value="mixtral-8x7b-32768">Mixtral 8x7B</option>
  </select>
  <div class="s-section">Vision Model</div>
  <select class="s-input" id="s-vision">
    <option value="meta-llama/llama-4-scout-17b-16e-instruct">Llama 4 Scout</option>
    <option value="llama-3.2-11b-vision-preview">Llama 3.2 11B</option>
    <option value="llama-3.2-90b-vision-preview">Llama 3.2 90B</option>
  </select>
  <div class="s-section">Voice</div>
  <select class="s-input" id="s-voice">
    <optgroup label="🇮🇳 Indian English">
      <option value="en-IN-NeerjaNeural">Neerja (Female)</option>
      <option value="en-IN-PrabhatNeural">Prabhat (Male)</option>
    </optgroup>
    <optgroup label="🇺🇸 American">
      <option value="en-US-JennyNeural">Jenny</option>
      <option value="en-US-GuyNeural">Guy</option>
    </optgroup>
    <optgroup label="🇬🇧 British">
      <option value="en-GB-SoniaNeural">Sonia</option>
    </optgroup>
    <optgroup label="🇮🇳 Hindi">
      <option value="hi-IN-SwaraNeural">Swara</option>
    </optgroup>
  </select>
  <div class="s-section">Memory</div>
  <select class="s-input" id="s-memory">
    <option value="10">Last 10 exchanges</option>
    <option value="20" selected>Last 20 exchanges</option>
    <option value="50">Last 50 exchanges</option>
    <option value="0">Full session</option>
  </select>
  <div class="s-section">Personality</div>
  <textarea class="s-input" id="s-prompt" rows="4">{CONFIG['system_prompt']}</textarea>
  <button class="s-btn" onclick="saveSettings()">✓ Save Settings</button>
</div>

<div id="toast"></div>

<script>
// ══ SECURITY ══
const _k = "{CONFIG['groq_api_key']}";
Object.defineProperty(window, '__apiConfig', {{
  value: Object.freeze({{ key: _k }}),
  writable: false, configurable: false
}});

const CONFIG = {{
  chatModel: "{CONFIG['chat_model']}",
  visionModel: "{CONFIG['vision_model']}",
  voice: "{CONFIG['tts_voice']}",
  prompt: `{safe_prompt}`,
  maxTokens: {CONFIG['max_tokens']},
  temperature: {CONFIG['temperature']},
  knowledge: `{safe_knowledge}`,
  memoryLimit: 20
}};

const _origLog = console.log;
console.log = (...args) => {{
  const str = JSON.stringify(args);
  if (str.includes('gsk_') || str.includes('apiKey') || str.includes('__apiConfig')) return;
  _origLog.apply(console, args);
}};

const VISION_TRIGGERS = [
  "what is this","what is that","what's this","what's that","see this","see that",
  "look at this","look at that","look here","identify this","identify that",
  "what am i looking at","tell me what this is","can you see","show me",
  "kya hai","ye kya hai","yeh kya hai","kya hai ye","kya hai yeh","yeh kya","ye kya",
  "kya dikhai de raha","dekh","dekho","dekh lo","dekho ye","dekho yeh","batao kya hai",
  "bata kya hai","yeh dikhao","isme kya hai","is me kya hai","kya chal raha hai","kya ho raha hai",
  "camera dekh","camera se dekho"
];

// ══ STATE ══
const STATE = {{
  history: [],
  savedHistory: [],
  uploadedDocs: [],          // Uploaded file contents for RAG
  camAnalysis: "",
  active: false,
  speaking: false,
  muted: false,
  voiceModeEnabled: true,
  silenceTimer: null,
  lastInteraction: Date.now(),
  lastVisionCapture: 0,
  wakeRecog: null,
  talkRecog: null,
  stream: null,
  facing: "environment",
}};

// ══ AUTO-INIT ══
window.addEventListener('load', () => {{
  setInitStatus("Requesting camera access...");
  setTimeout(() => autoInit(), 400);
}});

async function autoInit() {{
  try {{
    STATE.stream = await navigator.mediaDevices.getUserMedia({{
      video: {{ facingMode: STATE.facing, width:{{ideal:1920}}, height:{{ideal:1080}} }},
      audio: false
    }});
    const vid = document.getElementById("vid");
    vid.srcObject = STATE.stream;
    vid.classList.add("on");
    setInitStatus("Camera ready ✓");
    await sleep(500);
    setInitStatus("Starting voice listener...");
    await sleep(400);
    setInitStatus("Friday is ready");
    await sleep(600);
    // Fade out init overlay
    document.getElementById("init-overlay").classList.add("fade");
    setTimeout(() => {{
      document.getElementById("init-overlay").style.display = "none";
      ["logo","controls","status-bar","shortcut-hint"].forEach(id =>
        document.getElementById(id).classList.add("on")
      );
      document.getElementById("orb-wrap").classList.add("on");
      document.getElementById("text-bar").classList.add("on");
      document.getElementById("chips").classList.add("on");
      startWakeWordListener();
      setOrbState("sleeping");
      toast("Friday ready · Say 'Friday' or type below");
    }}, 900);
  }} catch(e) {{
    setInitStatus("⚠ Camera denied — text chat still available");
    await sleep(1200);
    document.getElementById("init-overlay").classList.add("fade");
    setTimeout(() => {{
      document.getElementById("init-overlay").style.display = "none";
      ["logo","controls","status-bar"].forEach(id =>
        document.getElementById(id).classList.add("on")
      );
      document.getElementById("orb-wrap").classList.add("on");
      document.getElementById("text-bar").classList.add("on");
      document.getElementById("chips").classList.add("on");
      setOrbState("sleeping");
      toast("No camera · Text chat available");
    }}, 900);
  }}
}}

function setInitStatus(msg) {{
  document.getElementById("init-status").textContent = msg;
}}
function sleep(ms) {{ return new Promise(r => setTimeout(r, ms)); }}

// ══ WAKE WORD ══
function startWakeWordListener() {{
  const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (!SR || !STATE.voiceModeEnabled) return;
  STATE.wakeRecog = new SR();
  STATE.wakeRecog.continuous = true;
  STATE.wakeRecog.interimResults = false;
  STATE.wakeRecog.lang = "en-US";
  STATE.wakeRecog.onresult = (e) => {{
    const text = e.results[e.results.length - 1][0].transcript.toLowerCase();
    if (text.includes("friday")) activate();
  }};
  STATE.wakeRecog.onerror = () => {{ setTimeout(() => {{ if (!STATE.active) safeStart(STATE.wakeRecog); }}, 200); }};
  STATE.wakeRecog.onend = () => {{ if (!STATE.active) setTimeout(() => safeStart(STATE.wakeRecog), 150); }};
  safeStart(STATE.wakeRecog);
}}

function safeStart(recog) {{
  try {{ recog.start(); }} catch(e) {{}}
}}

// ══ ACTIVATE ══
function activate() {{
  if (STATE.active || STATE.speaking) return;
  if (STATE.wakeRecog) try {{ STATE.wakeRecog.stop(); }} catch(e) {{}}
  STATE.active = true;
  STATE.lastInteraction = Date.now();
  setOrbState("listening");
  addMessage("assistant", "Haan bolo? 👂");
  startConversationListener();
}}

function manualActivate() {{
  if (STATE.active) {{ deactivate(); return; }}
  activate();
}}

function toggleVoiceMode() {{
  STATE.voiceModeEnabled = !STATE.voiceModeEnabled;
  const btn = document.getElementById("voice-btn");
  btn.classList.toggle("active", STATE.voiceModeEnabled);
  if (!STATE.voiceModeEnabled) {{
    if (STATE.wakeRecog) try {{ STATE.wakeRecog.stop(); }} catch(e) {{}}
    if (STATE.active) deactivate();
    toast("🎙 Voice mode off");
  }} else {{
    startWakeWordListener();
    toast("🎙 Voice mode on");
  }}
}}

// ══ CONVERSATION LISTENER ══
function startConversationListener() {{
  const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (!SR) return;
  STATE.talkRecog = new SR();
  STATE.talkRecog.continuous = true;
  STATE.talkRecog.interimResults = false;
  STATE.talkRecog.lang = "en-US";
  STATE.talkRecog.onresult = (e) => {{
    const text = e.results[e.results.length - 1][0].transcript.trim();
    if (!text) return;
    STATE.lastInteraction = Date.now();
    clearTimeout(STATE.silenceTimer);
    processInput(text);
  }};
  STATE.talkRecog.onerror = () => {{ checkSilence(); }};
  STATE.talkRecog.onend = () => {{
    if (STATE.active && !STATE.speaking) setTimeout(() => safeStart(STATE.talkRecog), 100);
  }};
  safeStart(STATE.talkRecog);
  startSilenceCheck();
}}

function processInput(text) {{
  addMessage("user", text);
  const lower = text.toLowerCase();
  const hasVision = VISION_TRIGGERS.some(t => lower.includes(t));
  if (hasVision && STATE.stream) {{
    const now = Date.now();
    if (now - STATE.lastVisionCapture > 2000) {{
      STATE.lastVisionCapture = now;
      setOrbState("analyzing");
      document.getElementById("scan").classList.add("active");
      autoCapture(text);
    }} else {{ toast("Wait 2s between captures"); }}
  }} else {{
    setOrbState("thinking");
    callGroq(text, false);
  }}
}}

function startSilenceCheck() {{
  clearInterval(STATE.silenceTimer);
  STATE.silenceTimer = setInterval(() => {{
    if (!STATE.active) return;
    if (Date.now() - STATE.lastInteraction > 14000) deactivate();
  }}, 1000);
}}
function checkSilence() {{
  if (Date.now() - STATE.lastInteraction > 14000 && STATE.active) deactivate();
}}
function deactivate() {{
  STATE.active = false;
  if (STATE.talkRecog) try {{ STATE.talkRecog.stop(); }} catch(e) {{}}
  clearInterval(STATE.silenceTimer);
  setOrbState("sleeping");
  addMessage("assistant", "Sleeping 😴 · Say 'Friday' or type below");
  setTimeout(() => {{ if (STATE.voiceModeEnabled) startWakeWordListener(); }}, 2000);
}}

// ══ TEXT CHAT ══
function sendTextMessage() {{
  const input = document.getElementById("text-input");
  const text = input.value.trim();
  if (!text) return;
  input.value = "";
  autoResize(input);
  document.getElementById("send-btn").disabled = true;

  // Wake if sleeping
  if (!STATE.active) {{
    STATE.active = true;
    STATE.lastInteraction = Date.now();
  }}
  setOrbState("thinking");
  processInput(text);
  setTimeout(() => {{ document.getElementById("send-btn").disabled = false; }}, 800);
}}

function sendChip(text) {{
  const input = document.getElementById("text-input");
  input.value = text;
  autoResize(input);
  input.focus();
  sendTextMessage();
}}

function handleTextKey(e) {{
  if (e.key === "Enter" && !e.shiftKey) {{
    e.preventDefault();
    sendTextMessage();
  }}
}}

function autoResize(el) {{
  el.style.height = "auto";
  el.style.height = Math.min(el.scrollHeight, 96) + "px";
}}

// ══ FILE UPLOAD / RAG ══
async function handleFileUpload(input) {{
  const files = Array.from(input.files);
  if (!files.length) return;

  for (const file of files) {{
    try {{
      let content = "";
      if (file.name.endsWith(".pdf")) {{
        content = await extractPdfText(file);
      }} else {{
        content = await file.text();
      }}
      // Trim to 4000 chars per file
      const trimmed = content.slice(0, 4000);
      STATE.uploadedDocs.push({{ name: file.name, content: trimmed }});
      addFilePill(file.name, STATE.uploadedDocs.length - 1);
      toast(`📎 Loaded: ${{file.name}}`);
    }} catch(e) {{
      toast(`Failed to read ${{file.name}}`);
    }}
  }}

  // Update badge
  const count = STATE.uploadedDocs.length;
  const btn = document.getElementById("upload-btn");
  const badge = document.getElementById("file-badge");
  badge.textContent = count;
  btn.classList.toggle("has-files", count > 0);
  input.value = "";
}}

async function extractPdfText(file) {{
  // Simple PDF text extraction using FileReader + basic parsing
  return new Promise((resolve) => {{
    const reader = new FileReader();
    reader.onload = (e) => {{
      const text = e.target.result;
      // Extract readable text from PDF (basic)
      const matches = text.match(/\(([^){{}}\\\\]+)\)/g) || [];
      const extracted = matches.map(m => m.slice(1,-1)).join(" ").slice(0, 4000);
      resolve(extracted || "[PDF content - could not extract text]");
    }};
    reader.readAsBinaryString(file);
  }});
}}

function addFilePill(name, idx) {{
  const pills = document.getElementById("file-pills");
  const pill = document.createElement("div");
  pill.className = "file-pill";
  pill.id = `pill-${{idx}}`;
  pill.innerHTML = `<span>📄 ${{name.length > 18 ? name.slice(0,16)+'…' : name}}</span><span class="remove" onclick="removeFile(${{idx}})">✕</span>`;
  pills.appendChild(pill);
  pills.classList.add("show");
}}

function removeFile(idx) {{
  STATE.uploadedDocs[idx] = null;
  const pill = document.getElementById(`pill-${{idx}}`);
  if (pill) pill.remove();
  const remaining = STATE.uploadedDocs.filter(Boolean).length;
  const btn = document.getElementById("upload-btn");
  const badge = document.getElementById("file-badge");
  badge.textContent = remaining;
  btn.classList.toggle("has-files", remaining > 0);
  if (remaining === 0) document.getElementById("file-pills").classList.remove("show");
  toast("File removed");
}}

function getDocContext() {{
  const docs = STATE.uploadedDocs.filter(Boolean);
  if (!docs.length) return "";
  return docs.map(d => `[File: ${{d.name}}]:\\n${{d.content}}`).join("\\n\\n---\\n\\n");
}}

// ══ VISION ══
async function autoCapture(userQuery) {{
  if (!STATE.stream) {{ callGroq(userQuery, false); return; }}
  const vid = document.getElementById("vid");
  vid.classList.add("analyzing");
  const c = document.createElement("canvas");
  c.width = vid.videoWidth || 1280;
  c.height = vid.videoHeight || 720;
  c.getContext("2d").drawImage(vid, 0, 0);
  const b64 = c.toDataURL("image/jpeg", .85).split(",")[1];
  const desc = await callGroqVision(b64);
  vid.classList.remove("analyzing");
  document.getElementById("scan").classList.remove("active");
  if (!desc) return;
  STATE.camAnalysis = desc;
  setOrbState("thinking");
  callGroq(userQuery, true);
}}

function manualCapture() {{
  if (!STATE.stream) {{ toast("Camera not available"); return; }}
  STATE.lastVisionCapture = Date.now();
  setOrbState("analyzing");
  document.getElementById("scan").classList.add("active");
  autoCapture("Describe what you see in detail.");
}}

async function callGroqVision(b64) {{
  try {{
    const res = await fetch("https://api.groq.com/openai/v1/chat/completions", {{
      method:"POST",
      headers:{{ "Content-Type":"application/json", "Authorization":"Bearer " + window.__apiConfig.key }},
      body: JSON.stringify({{
        model: CONFIG.visionModel,
        messages: [{{
          role:"user",
          content:[
            {{ type:"image_url", image_url:{{ url:"data:image/jpeg;base64,"+b64 }} }},
            {{ type:"text", text:"Describe this image in 2-3 sentences. Objects, text visible, conditions, anything notable." }}
          ]
        }}],
        max_tokens: 350
      }})
    }});
    if (!res.ok) throw new Error(res.status);
    const d = await res.json();
    return d.choices[0].message.content.trim();
  }} catch(e) {{
    speak("Vision error. Try again.");
    return null;
  }}
}}

// ══ GROQ CHAT ══
async function callGroq(userText, includeVision) {{
  const timeStr = new Date().toLocaleString("en-US", {{
    hour:"2-digit", minute:"2-digit", weekday:"short", month:"short", day:"numeric"
  }});

  let systemContent = CONFIG.prompt + "\\n\\nCurrent time: " + timeStr;
  if (includeVision && STATE.camAnalysis) systemContent += "\\n\\n[CAMERA SEES]: " + STATE.camAnalysis;
  if (CONFIG.knowledge) systemContent += "\\n\\n[KNOWLEDGE BASE]:\\n" + CONFIG.knowledge.slice(0, 1200);
  
  // Add uploaded docs context
  const docCtx = getDocContext();
  if (docCtx) systemContent += "\\n\\n[UPLOADED DOCUMENTS]:\\n" + docCtx.slice(0, 3000);

  const memLimit = CONFIG.memoryLimit === 0 ? STATE.savedHistory.length : CONFIG.memoryLimit * 2;
  const historyToSend = STATE.savedHistory.slice(-memLimit);
  const messages = [
    {{ role:"system", content: systemContent }},
    ...historyToSend,
    {{ role:"user", content: userText }}
  ];

  try {{
    const res = await fetch("https://api.groq.com/openai/v1/chat/completions", {{
      method:"POST",
      headers:{{ "Content-Type":"application/json", "Authorization":"Bearer " + window.__apiConfig.key }},
      body: JSON.stringify({{
        model: CONFIG.chatModel,
        messages,
        max_tokens: CONFIG.maxTokens,
        temperature: CONFIG.temperature,
        stream: false
      }})
    }});
    if (!res.ok) {{
      const err = await res.json().catch(() => ({{}}));
      throw new Error(err.error?.message || res.status);
    }}
    const data = await res.json();
    const reply = data.choices[0].message.content.trim();
    STATE.savedHistory.push(
      {{ role:"user", content: userText }},
      {{ role:"assistant", content: reply }}
    );
    if (STATE.savedHistory.length > 200) STATE.savedHistory = STATE.savedHistory.slice(-200);
    speak(reply);
  }} catch(e) {{
    const errMsg = "Network issue: " + (e.message || "please retry");
    addMessage("assistant", "⚠ " + errMsg);
    setOrbState(STATE.active ? "listening" : "sleeping");
  }}
}}

// ══ TTS ══
function speak(text) {{
  addMessage("assistant", text);
  STATE.lastInteraction = Date.now();
  if (STATE.muted) {{
    setOrbState(STATE.active ? "listening" : "sleeping");
    return;
  }}
  setOrbState("speaking");
  STATE.speaking = true;
  speechSynthesis.cancel();
  const utt = new SpeechSynthesisUtterance(text);
  utt.rate = 1.05; utt.pitch = 0.95; utt.volume = 1;
  const voices = speechSynthesis.getVoices();
  const vName = CONFIG.voice.replace("Neural","");
  const pick = voices.find(v => v.name.includes(vName))
             || voices.find(v => v.lang.startsWith("en-IN"))
             || voices[0];
  if (pick) utt.voice = pick;
  utt.onend = () => {{
    STATE.speaking = false;
    STATE.lastInteraction = Date.now();
    setOrbState(STATE.active ? "listening" : "sleeping");
  }};
  utt.onerror = () => {{
    STATE.speaking = false;
    setOrbState(STATE.active ? "listening" : "sleeping");
  }};
  speechSynthesis.speak(utt);
}}

// ══ UI ══
function addMessage(role, text) {{
  const panel = document.getElementById("conv-panel");
  const msg = document.createElement("div");
  msg.className = "msg " + role;
  const timeStr = new Date().toLocaleTimeString([], {{hour:"2-digit", minute:"2-digit"}});
  msg.innerHTML = `
    <div>${{escHtml(text)}}</div>
    <div class="msg-footer">
      <span class="msg-time">${{timeStr}}</span>
      ${{role === 'assistant' ? `<button class="copy-btn" onclick="copyMsg(this)">copy</button>` : ''}}
    </div>
  `;
  panel.appendChild(msg);
  panel.scrollTop = panel.scrollHeight;
  const msgs = panel.querySelectorAll(".msg");
  if (msgs.length > 30) msgs[0].remove();
}}

function escHtml(str) {{
  const d = document.createElement("div"); d.textContent = str; return d.innerHTML;
}}

function copyMsg(btn) {{
  const text = btn.closest(".msg").querySelector("div").textContent;
  navigator.clipboard.writeText(text).then(() => toast("Copied!"));
}}

function clearHistory() {{
  document.getElementById("conv-panel").innerHTML = "";
  STATE.savedHistory = [];
  STATE.camAnalysis = "";
  toast("Conversation cleared");
}}

function setOrbState(state) {{
  const wrap = document.getElementById("orb-wrap");
  wrap.className = "on " + state;
  const labels = {{
    listening:"Listening...", thinking:"Thinking...", speaking:"Speaking...",
    analyzing:"Analyzing...", sleeping:"Tap to wake"
  }};
  document.getElementById("orb-label").textContent = labels[state] || "Ready";
  const dot = document.getElementById("status-dot");
  dot.className = state;
  const statusLabels = {{
    listening:"Sun raha hoon", thinking:"Soch raha hoon",
    speaking:"Bol raha hoon", analyzing:"Dekh raha hoon", sleeping:"Soya hua"
  }};
  document.getElementById("status-text").textContent = statusLabels[state] || "Ready";
}}

// ══ CONTROLS ══
async function flipCam() {{
  STATE.facing = STATE.facing === "environment" ? "user" : "environment";
  if (STATE.stream) STATE.stream.getTracks().forEach(t => t.stop());
  try {{
    STATE.stream = await navigator.mediaDevices.getUserMedia({{
      video: {{ facingMode: STATE.facing }}, audio: false
    }});
    document.getElementById("vid").srcObject = STATE.stream;
    toast("Camera flipped");
  }} catch(e) {{ toast("Camera flip failed"); }}
}}

function toggleMute() {{
  STATE.muted = !STATE.muted;
  document.getElementById("mute-btn").textContent = STATE.muted ? "🔇" : "🔊";
  toast(STATE.muted ? "🔇 Muted" : "🔊 Unmuted");
}}

// ══ KEYBOARD ══
document.addEventListener("keydown", (e) => {{
  if (document.getElementById("init-overlay").style.display !== "none" &&
      !document.getElementById("init-overlay").classList.contains("fade")) return;
  if (document.getElementById("settings").classList.contains("open")) return;
  if (document.activeElement === document.getElementById("text-input")) return;
  switch(e.code) {{
    case "Space": e.preventDefault(); if (STATE.active) deactivate(); else activate(); break;
    case "Escape": if (STATE.active) deactivate(); break;
    case "KeyM": toggleMute(); break;
    case "KeyV": if (STATE.stream) manualCapture(); break;
    case "KeyC": clearHistory(); break;
  }}
}});

// ══ SETTINGS ══
function openSettings() {{
  document.getElementById("s-model").value = CONFIG.chatModel;
  document.getElementById("s-vision").value = CONFIG.visionModel;
  document.getElementById("s-voice").value = CONFIG.voice;
  document.getElementById("s-prompt").value = CONFIG.prompt;
  document.getElementById("s-memory").value = CONFIG.memoryLimit;
  document.getElementById("settings").classList.add("open");
  document.getElementById("s-overlay").classList.add("show");
}}
function closeSettings() {{
  document.getElementById("settings").classList.remove("open");
  document.getElementById("s-overlay").classList.remove("show");
}}
function saveSettings() {{
  CONFIG.chatModel = document.getElementById("s-model").value;
  CONFIG.visionModel = document.getElementById("s-vision").value;
  CONFIG.voice = document.getElementById("s-voice").value;
  CONFIG.prompt = document.getElementById("s-prompt").value;
  CONFIG.memoryLimit = parseInt(document.getElementById("s-memory").value);
  closeSettings();
  toast("✓ Settings saved");
}}

// ══ TOAST ══
let _toastTimer;
function toast(msg, dur=2600) {{
  const el = document.getElementById("toast");
  el.textContent = msg;
  el.classList.add("show");
  clearTimeout(_toastTimer);
  _toastTimer = setTimeout(() => el.classList.remove("show"), dur);
}}

// Init voices
speechSynthesis.onvoiceschanged = () => speechSynthesis.getVoices();
setTimeout(() => speechSynthesis.getVoices(), 100);
</script>
</body>
</html>
"""

st.components.v1.html(HTML, height=800, scrolling=False)
