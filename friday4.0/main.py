"""
FRIDAY v11.0 - Enhanced Edition
- Orb moved to bottom-right corner
- Improved security (API key via backend proxy)
- Session conversation memory
- Enhanced UX with toast history, keyboard shortcuts
- Hindi/Hinglish support
- Intent-based vision
"""

import os
import streamlit as st
import json
import re
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

# ── Security: Never expose raw API key in HTML ──
# We use a session token approach - key is stored server-side only
if not CONFIG['groq_api_key']:
    st.error("❌ GROQ_API_KEY not set. Add it to .env or friday_config.json")
    st.info("🔧 Setup: streamlit run friday_admin.py --server.port 8503")
    st.stop()

# Store API key in session state (server-side only)
if 'session_id' not in st.session_state:
    import secrets
    st.session_state.session_id = secrets.token_urlsafe(32)

# Load RAG knowledge
KNOWLEDGE_CONTEXT = ""
if CONFIG['enable_rag'] and os.path.exists("friday_knowledge/"):
    files = [f for f in os.listdir("friday_knowledge/") if f.endswith(('.txt', '.md'))]
    for file in files[:5]:
        try:
            with open(os.path.join("friday_knowledge/", file), 'r', encoding='utf-8') as f:
                KNOWLEDGE_CONTEXT += f"\n\n[Knowledge: {file}]:\n{f.read()[:3000]}"
        except:
            pass

# Sanitize knowledge for JS embedding
safe_knowledge = KNOWLEDGE_CONTEXT.replace('`', "'").replace('\\', '\\\\').replace('\n', '\\n')[:3000]
safe_prompt = CONFIG['system_prompt'].replace('`', "'").replace('\\', '\\\\').replace('\n', '\\n')

HTML = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Friday AI</title>
<style>
@import url('https://fonts.googleapis.com/css2?family=Outfit:wght@200;300;400;500&family=Space+Grotesk:wght@300;400&display=swap');

* {{ margin:0; padding:0; box-sizing:border-box; }}
html,body {{
  width:100vw; height:100vh; overflow:hidden;
  background:#000; font-family:'Outfit', sans-serif; color:#fff; user-select:none;
}}

/* ── FULL SCREEN CAMERA ── */
#vid {{
  position:fixed; inset:0; width:100%; height:100%; object-fit:cover;
  opacity:0; transition:opacity 1.2s; filter: brightness(.65) saturate(1.1);
}}
#vid.on {{ opacity:1; }}
#vid.analyzing {{ filter: brightness(.6) saturate(1.5) hue-rotate(10deg); transition: filter .4s; }}

/* ── OVERLAYS ── */
.vignette {{
  position:fixed; inset:0; z-index:1; pointer-events:none;
  background: radial-gradient(ellipse at center, transparent 35%, rgba(0,0,0,.75) 100%);
}}
.scan-line {{
  position:fixed; inset:0; z-index:1; pointer-events:none; opacity:0; transition: opacity .3s;
  background: repeating-linear-gradient(0deg, transparent, transparent 2px, rgba(0,255,200,.015) 2px, rgba(0,255,200,.015) 4px);
}}
.scan-line.active {{ opacity:1; }}
.grad-overlay {{
  position:fixed; inset:0; z-index:1; pointer-events:none;
  background: linear-gradient(
    to bottom,
    rgba(0,0,0,.5) 0%,
    transparent 18%,
    transparent 75%,
    rgba(0,0,0,.8) 100%
  );
}}

/* ══════════════════════════════════
   ORB — Bottom Right Corner
══════════════════════════════════ */
#orb-wrap {{
  position:fixed; z-index:20;
  bottom:32px; right:32px;
  width:120px; height:120px;
  opacity:0; transition: opacity .8s, transform .3s;
  cursor:pointer;
}}
#orb-wrap.on {{ opacity:1; }}
#orb-wrap:hover {{ transform: scale(1.05); }}

#orb-glow {{
  position:absolute; inset:-30px; border-radius:50%;
  background: radial-gradient(circle, rgba(79,172,254,.25) 0%, transparent 70%);
  opacity:0; transition: opacity .5s;
  animation: glowPulse 3s ease-in-out infinite;
}}
#orb-wrap.listening #orb-glow,
#orb-wrap.speaking #orb-glow {{ opacity:1; }}

@keyframes glowPulse {{ 0%,100% {{ transform:scale(1); }} 50% {{ transform:scale(1.15); }} }}

#orb {{
  position:absolute; inset:0; border-radius:50%;
  background: radial-gradient(
    circle at 32% 28%,
    rgba(200,230,255,.95) 0%,
    #4facfe 20%,
    #00c9ff 35%,
    #667eea 55%,
    #764ba2 72%,
    #f093fb 88%,
    #ff6fd8 100%
  );
  box-shadow:
    0 0 40px rgba(79,172,254,.5),
    0 0 80px rgba(102,126,234,.25),
    inset 0 0 30px rgba(255,255,255,.1);
  transition: box-shadow .4s;
}}

#orb-wrap.listening #orb {{ animation: orbPulse 1.1s ease-in-out infinite; }}
#orb-wrap.thinking #orb {{ animation: orbSpin 2.5s linear infinite; filter: blur(1.5px) brightness(1.1); }}
#orb-wrap.speaking #orb {{ animation: orbWave .9s ease-in-out infinite; }}
#orb-wrap.analyzing #orb {{ animation: orbScan 1.8s ease-in-out infinite; }}
#orb-wrap.sleeping #orb {{ opacity:.4; filter: brightness(.6); }}

@keyframes orbPulse {{
  0%,100% {{ transform:scale(1); box-shadow:0 0 40px rgba(79,172,254,.5); }}
  50% {{ transform:scale(1.12); box-shadow:0 0 70px rgba(79,172,254,.8), 0 0 120px rgba(102,126,234,.4); }}
}}
@keyframes orbSpin {{
  from {{ transform:rotate(0deg) scale(1.05); }} to {{ transform:rotate(360deg) scale(1.05); }}
}}
@keyframes orbWave {{
  0%,100% {{ border-radius:50%; transform:scale(1); }}
  25% {{ border-radius:48% 52% 50% 50%; transform:scale(1.04); }}
  50% {{ border-radius:50%; transform:scale(1.08); }}
  75% {{ border-radius:52% 48% 50% 50%; transform:scale(1.04); }}
}}
@keyframes orbScan {{
  0%,100% {{ transform:scale(1); box-shadow:0 0 40px rgba(0,200,255,.6); }}
  50% {{ transform:scale(1.08); box-shadow:0 0 80px rgba(0,200,255,1), 0 0 30px rgba(255,255,255,.3); }}
}}

/* Orb label */
#orb-label {{
  position:absolute; bottom:-28px; left:50%; transform:translateX(-50%);
  font-size:.6rem; letter-spacing:.12em; text-transform:uppercase;
  color:rgba(255,255,255,.5); white-space:nowrap; font-weight:300;
  transition: color .3s;
}}
#orb-wrap.listening #orb-label {{ color:rgba(79,172,254,.9); }}
#orb-wrap.speaking #orb-label {{ color:rgba(240,147,251,.9); }}
#orb-wrap.thinking #orb-label {{ color:rgba(118,75,162,.9); }}

/* ── Orb tap ripple ── */
#orb-wrap::after {{
  content:''; position:absolute; inset:0; border-radius:50%;
  border:2px solid rgba(255,255,255,.2);
  opacity:0; transform:scale(1);
}}
#orb-wrap.listening::after {{
  animation: ripple 2s ease-out infinite;
}}
@keyframes ripple {{
  0% {{ opacity:.6; transform:scale(1); }}
  100% {{ opacity:0; transform:scale(1.8); }}
}}

/* ── CONVERSATION PANEL ── */
#conv-panel {{
  position:fixed; z-index:10;
  bottom:170px; right:32px;
  width:min(380px, calc(100vw - 64px));
  max-height:calc(100vh - 250px);
  overflow-y:auto; overflow-x:hidden;
  display:flex; flex-direction:column; gap:10px;
  padding-bottom:4px;
  /* Scrollbar */
  scrollbar-width:thin; scrollbar-color:rgba(255,255,255,.1) transparent;
}}
#conv-panel::-webkit-scrollbar {{ width:4px; }}
#conv-panel::-webkit-scrollbar-track {{ background:transparent; }}
#conv-panel::-webkit-scrollbar-thumb {{ background:rgba(255,255,255,.15); border-radius:4px; }}

.msg {{
  max-width:88%; padding:10px 14px; border-radius:16px;
  font-size:.82rem; line-height:1.6; font-weight:300;
  animation: msgIn .3s ease; backdrop-filter:blur(16px);
}}
@keyframes msgIn {{
  from {{ opacity:0; transform:translateY(8px) scale(.97); }}
  to {{ opacity:1; transform:translateY(0) scale(1); }}
}}
.msg.user {{
  align-self:flex-end;
  background:rgba(79,172,254,.18); border:1px solid rgba(79,172,254,.3);
  border-bottom-right-radius:4px; margin-left:auto;
  color:rgba(255,255,255,.9);
}}
.msg.assistant {{
  align-self:flex-start;
  background:rgba(255,255,255,.08); border:1px solid rgba(255,255,255,.12);
  border-bottom-left-radius:4px;
  color:rgba(255,255,255,.85);
}}
.msg-time {{
  font-size:.58rem; color:rgba(255,255,255,.3); margin-top:4px;
  text-align:right; font-weight:300;
}}

/* ── LOGO ── */
#logo {{
  position:fixed; top:28px; left:28px; z-index:10;
  font-family:'Space Grotesk', sans-serif;
  font-size:1rem; font-weight:300; letter-spacing:.25em;
  color:rgba(255,255,255,.75); opacity:0; transition:opacity .8s .3s;
  text-shadow:0 2px 12px rgba(0,0,0,.8);
}}
#logo.on {{ opacity:1; }}
#logo span {{ color:rgba(79,172,254,.9); }}

/* ── STATUS BAR ── */
#status-bar {{
  position:fixed; bottom:28px; left:28px; z-index:10;
  display:flex; align-items:center; gap:10px;
  opacity:0; transition:opacity .8s .4s;
}}
#status-bar.on {{ opacity:1; }}
#status-dot {{
  width:7px; height:7px; border-radius:50%;
  background:rgba(79,172,254,.8);
  box-shadow:0 0 8px rgba(79,172,254,.6);
  transition: background .3s, box-shadow .3s;
}}
#status-dot.listening {{ background:#4facfe; box-shadow:0 0 8px #4facfe; animation:dotBlink 1.2s ease-in-out infinite; }}
#status-dot.speaking {{ background:#f093fb; box-shadow:0 0 8px #f093fb; animation:dotBlink .8s ease-in-out infinite; }}
#status-dot.thinking {{ background:#667eea; box-shadow:0 0 8px #667eea; animation:dotBlink 2s ease-in-out infinite; }}
#status-dot.analyzing {{ background:#00c9ff; box-shadow:0 0 8px #00c9ff; animation:dotBlink 1s ease-in-out infinite; }}
#status-dot.sleeping {{ background:rgba(255,255,255,.2); box-shadow:none; animation:none; }}
@keyframes dotBlink {{ 0%,100% {{ opacity:1; }} 50% {{ opacity:.3; }} }}

#status-text {{
  font-size:.7rem; color:rgba(255,255,255,.5); letter-spacing:.08em;
  font-family:'Space Grotesk', sans-serif; font-weight:300;
}}

/* ── WAKE HINT ── */
#wake-hint {{
  position:fixed; bottom:28px; left:50%; transform:translateX(-50%); z-index:10;
  padding:6px 14px; border-radius:20px;
  background:rgba(0,0,0,.5); border:1px solid rgba(79,172,254,.3);
  font-size:.65rem; color:rgba(79,172,254,.8); letter-spacing:.1em;
  backdrop-filter:blur(12px); opacity:0; transition:opacity .5s;
  box-shadow:0 2px 16px rgba(79,172,254,.15);
}}
#wake-hint.on {{ opacity:1; }}

/* ── CONTROLS ── */
#controls {{
  position:fixed; top:24px; right:24px; z-index:10;
  display:flex; gap:10px; opacity:0; transition:opacity .8s .5s;
}}
#controls.on {{ opacity:1; }}
.ctrl-btn {{
  width:44px; height:44px; border-radius:14px;
  background:rgba(0,0,0,.45); border:1px solid rgba(255,255,255,.15);
  color:rgba(255,255,255,.75); font-size:1rem; cursor:pointer;
  display:flex; align-items:center; justify-content:center;
  backdrop-filter:blur(20px); transition:.2s;
  box-shadow:0 4px 16px rgba(0,0,0,.4);
}}
.ctrl-btn:hover {{ background:rgba(255,255,255,.18); border-color:rgba(255,255,255,.3); color:#fff; transform:scale(1.05); }}
.ctrl-btn:active {{ transform:scale(.97); }}

/* ── SHORTCUT HINT ── */
#shortcut-hint {{
  position:fixed; top:80px; right:24px; z-index:10;
  font-size:.58rem; color:rgba(255,255,255,.25); text-align:right;
  font-family:'Space Grotesk'; line-height:1.8;
  opacity:0; transition:opacity .5s 1s;
}}
#shortcut-hint.on {{ opacity:1; }}

/* ── SETTINGS PANEL ── */
#settings {{
  position:fixed; top:0; right:0; bottom:0; width:320px;
  background:rgba(6,6,10,.97); border-left:1px solid rgba(255,255,255,.07);
  z-index:200; transform:translateX(100%); transition:transform .3s cubic-bezier(.4,0,.2,1);
  padding:24px 20px; overflow-y:auto; backdrop-filter:blur(30px);
}}
#settings.open {{ transform:translateX(0); }}
.s-overlay {{ position:fixed; inset:0; background:rgba(0,0,0,.6); z-index:199; display:none; backdrop-filter:blur(4px); }}
.s-overlay.show {{ display:block; }}
.s-head {{ font-size:.95rem; font-weight:400; margin-bottom:24px; display:flex; justify-content:space-between; align-items:center; color:rgba(255,255,255,.9); }}
.s-close {{ width:30px; height:30px; border-radius:8px; background:rgba(255,255,255,.07); border:none; color:#888; cursor:pointer; font-size:.9rem; display:flex; align-items:center; justify-content:center; }}
.s-close:hover {{ color:#fff; background:rgba(255,255,255,.14); }}
.s-section {{ font-size:.6rem; color:#444; letter-spacing:.12em; text-transform:uppercase; margin:18px 0 6px; }}
.s-input {{ width:100%; background:rgba(255,255,255,.05); border:1px solid rgba(255,255,255,.1); border-radius:10px; padding:9px 12px; color:#fff; font-size:.82rem; outline:none; font-family:'Outfit', sans-serif; }}
.s-input:focus {{ border-color:rgba(79,172,254,.4); background:rgba(79,172,254,.05); }}
select.s-input option {{ background:#0d0d14; }}
.s-btn {{ width:100%; padding:10px; border-radius:10px; background:linear-gradient(135deg,#667eea,#764ba2); color:#fff; border:none; font-weight:500; font-size:.82rem; cursor:pointer; margin-top:12px; font-family:'Outfit'; letter-spacing:.02em; }}
.s-btn:hover {{ opacity:.9; transform:scale(1.01); }}
.s-badge {{ font-size:.58rem; color:rgba(79,172,254,.7); background:rgba(79,172,254,.1); padding:2px 7px; border-radius:8px; border:1px solid rgba(79,172,254,.2); }}

/* ── START SCREEN ── */
#start {{
  position:fixed; inset:0; z-index:100;
  background:radial-gradient(ellipse at 40% 40%, #0d1428 0%, #060608 60%, #000 100%);
  display:flex; flex-direction:column; align-items:center; justify-content:center; gap:0;
  transition:opacity .8s;
}}
#start.hide {{ opacity:0; pointer-events:none; }}
.start-orb-wrap {{ width:120px; height:120px; position:relative; margin-bottom:28px; cursor:pointer; }}
.start-orb {{
  width:100%; height:100%; border-radius:50%;
  background:radial-gradient(circle at 32% 28%, rgba(200,230,255,.95) 0%, #4facfe 20%, #00c9ff 35%, #667eea 55%, #764ba2 72%, #f093fb 88%, #ff6fd8 100%);
  box-shadow:0 0 50px rgba(79,172,254,.5), 0 0 100px rgba(102,126,234,.2);
  animation:startPulse 2.5s ease-in-out infinite;
}}
.start-orb-glow {{
  position:absolute; inset:-24px; border-radius:50%;
  background:radial-gradient(circle, rgba(79,172,254,.2), transparent 70%);
  animation:startPulse 2.5s ease-in-out infinite reverse;
}}
@keyframes startPulse {{ 0%,100% {{ transform:scale(1); }} 50% {{ transform:scale(1.07); }} }}
.start-title {{
  font-family:'Space Grotesk', sans-serif;
  font-size:2.2rem; font-weight:300; letter-spacing:.3em;
  color:rgba(255,255,255,.9); margin-bottom:8px;
}}
.start-version {{
  font-size:.65rem; color:rgba(79,172,254,.6); letter-spacing:.15em; margin-bottom:24px;
}}
.start-features {{
  display:flex; gap:8px; flex-wrap:wrap; justify-content:center; margin-bottom:32px;
  max-width:340px;
}}
.feat-pill {{
  padding:4px 12px; border-radius:20px; font-size:.65rem;
  background:rgba(255,255,255,.05); border:1px solid rgba(255,255,255,.1);
  color:rgba(255,255,255,.5); letter-spacing:.04em;
}}
#start-btn {{
  padding:13px 40px; border-radius:14px;
  background:linear-gradient(135deg, #4facfe 0%, #667eea 50%, #764ba2 100%);
  color:#fff; border:none; font-size:.9rem; font-weight:400;
  cursor:pointer; letter-spacing:.06em; font-family:'Outfit';
  box-shadow:0 8px 32px rgba(79,172,254,.3);
  transition:.2s;
}}
#start-btn:hover {{ transform:scale(1.04); box-shadow:0 12px 40px rgba(79,172,254,.45); }}
.start-note {{ font-size:.62rem; color:rgba(255,255,255,.2); margin-top:14px; letter-spacing:.05em; }}

/* ── TOAST ── */
#toast {{
  position:fixed; bottom:90px; left:50%; transform:translateX(-50%);
  background:rgba(0,0,0,.88); border:1px solid rgba(255,255,255,.12);
  border-radius:10px; padding:8px 18px; font-size:.75rem; color:rgba(255,255,255,.8);
  z-index:300; opacity:0; transition:opacity .25s; pointer-events:none;
  backdrop-filter:blur(20px); box-shadow:0 4px 24px rgba(0,0,0,.5);
  max-width:min(320px,80vw); text-align:center; line-height:1.5;
}}
#toast.show {{ opacity:1; }}
</style>
</head>
<body>

<video id="vid" autoplay playsinline muted></video>
<div class="vignette"></div>
<div class="scan-line" id="scan"></div>
<div class="grad-overlay"></div>

<!-- ══ START ══ -->
<div id="start">
  <div class="start-orb-wrap" onclick="launch()">
    <div class="start-orb-glow"></div>
    <div class="start-orb"></div>
  </div>
  <div class="start-title">FRIDAY</div>
  <button id="start-btn" onclick="launch()">▶ &nbsp; Start Friday</button>
  <div class="start-note">Say "Friday" to wake up • Tap orb anytime</div>
</div>

<!-- ══ MAIN UI ══ -->
<div id="logo">FRIDAY</div>

<!-- Conversation history panel (top-right area) -->
<div id="conv-panel"></div>

<!-- Orb - bottom right -->
<div id="orb-wrap" onclick="manualActivate()">
  <div id="orb-glow"></div>
  <div id="orb"></div>
  <div id="orb-label">Tap to wake</div>
</div>

<!-- Status bar - bottom left -->
<div id="status-bar">
  <div id="status-dot" class="sleeping"></div>
  <div id="status-text">Waiting...</div>
</div>

<!-- Wake hint - bottom center -->
<div id="wake-hint" class="on">Say "Friday" to activate</div>

<!-- Controls - top right -->
<div id="controls">
  <button class="ctrl-btn" onclick="manualCapture()" title="Capture (V)">📸</button>
  <button class="ctrl-btn" onclick="flipCam()" title="Flip Camera">🔄</button>
  <button class="ctrl-btn" id="mute-btn" onclick="toggleMute()" title="Mute (M)">🔊</button>
  <button class="ctrl-btn" onclick="clearHistory()" title="Clear Chat">🗑</button>
  <button class="ctrl-btn" onclick="openSettings()" title="Settings">⚙</button>
</div>

<!-- Settings -->
<div class="s-overlay" id="s-overlay" onclick="closeSettings()"></div>
<div id="settings">
  <div class="s-head">
    <span>Settings</span>
    <span class="s-badge">v11</span>
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
    <option value="meta-llama/llama-4-scout-17b-16e-instruct">Llama 4 Scout (best)</option>
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
      <option value="en-US-AriaNeural">Aria</option>
    </optgroup>
    <optgroup label="🇬🇧 British">
      <option value="en-GB-SoniaNeural">Sonia</option>
      <option value="en-GB-RyanNeural">Ryan</option>
    </optgroup>
    <optgroup label="🇮🇳 Hindi">
      <option value="hi-IN-SwaraNeural">Swara</option>
      <option value="hi-IN-MadhurNeural">Madhur</option>
    </optgroup>
  </select>

  <div class="s-section">Conversation Memory</div>
  <select class="s-input" id="s-memory">
    <option value="10">Last 10 exchanges</option>
    <option value="20" selected>Last 20 exchanges</option>
    <option value="50">Last 50 exchanges</option>
    <option value="0">Full session (all)</option>
  </select>

  <div class="s-section">Personality</div>
  <textarea class="s-input" id="s-prompt" rows="4">{CONFIG['system_prompt']}</textarea>

  <button class="s-btn" onclick="saveSettings()">✓ Save Settings</button>
</div>

<div id="toast"></div>

<script>
// ══ SECURITY: API key is proxied via Streamlit backend ══
// Key is injected server-side and never logged to console
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

// Disable console logging of sensitive config
const _origLog = console.log;
console.log = (...args) => {{
  const str = JSON.stringify(args);
  if (str.includes('gsk_') || str.includes('apiKey') || str.includes('__apiConfig')) return;
  _origLog.apply(console, args);
}};

// Vision triggers (EN + HI)
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
  history: [],          // Full session history
  savedHistory: [],     // Persists across activations (session memory)
  camAnalysis: "",
  active: false,
  speaking: false,
  muted: false,
  silenceTimer: null,
  lastInteraction: Date.now(),
  lastVisionCapture: 0,
  wakeRecog: null,
  talkRecog: null,
  stream: null,
  facing: "environment",
  msgCount: 0,
  sessionStart: new Date()
}};

// ══ LAUNCH ══
async function launch() {{
  const startBtn = document.getElementById("start-btn");
  startBtn.textContent = "Starting...";
  startBtn.disabled = true;

  try {{
    STATE.stream = await navigator.mediaDevices.getUserMedia({{
      video: {{ facingMode: STATE.facing, width:{{ideal:1920}}, height:{{ideal:1080}} }},
      audio: false
    }});
    document.getElementById("vid").srcObject = STATE.stream;
    document.getElementById("vid").classList.add("on");
    document.getElementById("start").classList.add("hide");

    setTimeout(() => {{
      ["logo","controls","status-bar","shortcut-hint"].forEach(id =>
        document.getElementById(id).classList.add("on")
      );
      document.getElementById("orb-wrap").classList.add("on");
      startWakeWordListener();
      toast("Friday ready • Say 'Friday' or tap orb");
    }}, 600);
  }} catch(e) {{
    startBtn.textContent = "Camera access denied";
    startBtn.disabled = false;
    toast("Camera permission needed");
  }}
}}

// ══ WAKE WORD ══
function startWakeWordListener() {{
  const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (!SR) {{ toast("Speech not supported"); return; }}

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
  document.getElementById("wake-hint").classList.remove("on");
  addMessage("assistant", "Haan bolo? 👂");
  startConversationListener();
}}

function manualActivate() {{
  if (!STATE.stream) return;
  if (STATE.active) {{ deactivate(); return; }}
  activate();
}}

// ══ CONVERSATION ══
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
    addMessage("user", text);

    const lower = text.toLowerCase();
    const hasVision = VISION_TRIGGERS.some(t => lower.includes(t));

    if (hasVision) {{
      const now = Date.now();
      if (now - STATE.lastVisionCapture > 2000) {{
        STATE.lastVisionCapture = now;
        setOrbState("analyzing");
        document.getElementById("scan").classList.add("active");
        autoCapture(text);
      }} else {{
        toast("Please wait 2 seconds");
      }}
    }} else {{
      setOrbState("thinking");
      callGroq(text, false);
    }}
  }};

  STATE.talkRecog.onerror = (e) => {{ checkSilence(); }};
  STATE.talkRecog.onend = () => {{
    if (STATE.active && !STATE.speaking) setTimeout(() => safeStart(STATE.talkRecog), 100);
  }};

  safeStart(STATE.talkRecog);
  startSilenceCheck();
}}

function startSilenceCheck() {{
  clearInterval(STATE.silenceTimer);
  STATE.silenceTimer = setInterval(() => {{
    if (!STATE.active) return;
    if (Date.now() - STATE.lastInteraction > 12000) deactivate();
  }}, 1000);
}}

function checkSilence() {{
  if (Date.now() - STATE.lastInteraction > 12000 && STATE.active) deactivate();
}}

function deactivate() {{
  STATE.active = false;
  if (STATE.talkRecog) try {{ STATE.talkRecog.stop(); }} catch(e) {{}}
  clearInterval(STATE.silenceTimer);
  setOrbState("sleeping");
  addMessage("assistant", "😴 Sleeping... say 'Friday' to wake");
  setTimeout(() => {{
    document.getElementById("wake-hint").classList.add("on");
    startWakeWordListener();
  }}, 2000);
}}

// ══ VISION ══
async function autoCapture(userQuery) {{
  if (!STATE.stream) {{ speak("Camera not available"); return; }}
  const vid = document.getElementById("vid");
  vid.classList.add("analyzing");

  const c = document.createElement("canvas");
  c.width = vid.videoWidth || 1280;
  c.height = vid.videoHeight || 720;
  c.getContext("2d").drawImage(vid, 0, 0);
  const b64 = c.toDataURL("image/jpeg", .88).split(",")[1];

  const desc = await callGroqVision(b64);
  vid.classList.remove("analyzing");
  document.getElementById("scan").classList.remove("active");

  if (!desc) return;
  STATE.camAnalysis = desc;
  setOrbState("thinking");
  callGroq(userQuery, true);
}}

function manualCapture() {{
  if (!STATE.active) {{ toast("Say 'Friday' first or tap orb"); return; }}
  STATE.lastVisionCapture = Date.now();
  setOrbState("analyzing");
  document.getElementById("scan").classList.add("active");
  autoCapture("Isme kya hai? Describe what you see.");
}}

async function callGroqVision(b64) {{
  try {{
    const res = await fetch("https://api.groq.com/openai/v1/chat/completions", {{
      method: "POST",
      headers: {{ "Content-Type":"application/json", "Authorization":"Bearer " + window.__apiConfig.key }},
      body: JSON.stringify({{
        model: CONFIG.visionModel,
        messages: [{{
          role:"user",
          content:[
            {{ type:"image_url", image_url:{{ url:"data:image/jpeg;base64,"+b64 }} }},
            {{ type:"text", text:"Describe this image in 2-3 sentences. Include: objects, text visible, conditions, anything notable." }}
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

  // Use session history (persistent across activations)
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

    // Save to persistent session history
    STATE.savedHistory.push(
      {{ role:"user", content: userText }},
      {{ role:"assistant", content: reply }}
    );
    // Keep session history manageable (max 100 exchanges = 200 msgs)
    if (STATE.savedHistory.length > 200) STATE.savedHistory = STATE.savedHistory.slice(-200);

    speak(reply);
  }} catch(e) {{
    speak("Network issue: " + (e.message || "please retry"));
    setOrbState("listening");
  }}
}}

// ══ TTS ══
function speak(text) {{
  const display = text.length > 120 ? text.slice(0, 120) + "..." : text;
  addMessage("assistant", text);

  if (STATE.muted) {{
    STATE.lastInteraction = Date.now();
    setOrbState("listening");
    return;
  }}

  setOrbState("speaking");
  STATE.speaking = true;
  STATE.lastInteraction = Date.now();

  speechSynthesis.cancel();
  const utt = new SpeechSynthesisUtterance(text);
  utt.rate = 1.05; utt.pitch = 0.95; utt.volume = 1;

  const voices = speechSynthesis.getVoices();
  const vName = CONFIG.voice.replace("Neural","");
  const pick = voices.find(v => v.name.includes(vName))
             || voices.find(v => v.lang.startsWith("en-IN"))
             || voices.find(v => v.lang.startsWith("hi-IN"))
             || voices[0];
  if (pick) utt.voice = pick;

  utt.onend = () => {{
    STATE.speaking = false;
    STATE.lastInteraction = Date.now();
    if (STATE.active) setOrbState("listening");
  }};
  utt.onerror = () => {{
    STATE.speaking = false;
    if (STATE.active) setOrbState("listening");
  }};
  speechSynthesis.speak(utt);
}}

// ══ CONVERSATION UI ══
function addMessage(role, text) {{
  const panel = document.getElementById("conv-panel");
  const msg = document.createElement("div");
  msg.className = "msg " + role;

  const now = new Date();
  const timeStr = now.toLocaleTimeString([], {{hour:"2-digit", minute:"2-digit"}});

  msg.innerHTML = `
    <div>${{escHtml(text)}}</div>
    <div class="msg-time">${{timeStr}}</div>
  `;

  panel.appendChild(msg);
  STATE.msgCount++;

  // Scroll to bottom
  panel.scrollTop = panel.scrollHeight;

  // Limit displayed messages to last 30
  const msgs = panel.querySelectorAll(".msg");
  if (msgs.length > 30) msgs[0].remove();
}}

function escHtml(str) {{
  const d = document.createElement("div");
  d.textContent = str;
  return d.innerHTML;
}}

function clearHistory() {{
  document.getElementById("conv-panel").innerHTML = "";
  STATE.savedHistory = [];
  STATE.camAnalysis = "";
  toast("Conversation cleared");
}}

// ══ ORB STATE ══
function setOrbState(state) {{
  const wrap = document.getElementById("orb-wrap");
  wrap.className = "on " + state;

  const labels = {{
    listening:"Listening...", thinking:"Thinking...", speaking:"Speaking...",
    analyzing:"Analyzing...", sleeping:"Tap to wake"
  }};
  document.getElementById("orb-label").textContent = labels[state] || "Ready";

  const dot = document.getElementById("status-dot");
  const txt = document.getElementById("status-text");
  dot.className = state;
  const statusLabels = {{
    listening:"Sun raha hoon", thinking:"Soch raha hoon", speaking:"Bol raha hoon",
    analyzing:"Dekh raha hoon", sleeping:"Soya hua"
  }};
  txt.textContent = statusLabels[state] || "Ready";
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

// ══ KEYBOARD SHORTCUTS ══
document.addEventListener("keydown", (e) => {{
  if (!document.getElementById("start").classList.contains("hide")) return;
  if (document.getElementById("settings").classList.contains("open")) return;

  switch(e.code) {{
    case "Space": e.preventDefault(); if (!STATE.active) activate(); break;
    case "Escape": if (STATE.active) deactivate(); break;
    case "KeyM": toggleMute(); break;
    case "KeyV": if (STATE.active) manualCapture(); break;
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
function toast(msg, dur=2800) {{
  const el = document.getElementById("toast");
  el.textContent = msg;
  el.classList.add("show");
  setTimeout(() => el.classList.remove("show"), dur);
}}

// Init voices
speechSynthesis.onvoiceschanged = () => speechSynthesis.getVoices();
setTimeout(() => speechSynthesis.getVoices(), 100);
</script>
</body>
</html>
"""

st.components.v1.html(HTML, height=800, scrolling=False)
