"""
FRIDAY LIVE  v7.0
Pure voice interaction — full screen, Gemini Live style.
This serves a single HTML file that does everything in the browser.
Run: streamlit run main.py
"""

import os
import streamlit as st
from dotenv import load_dotenv
load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")

st.set_page_config(page_title="Friday Live", page_icon="✦", layout="wide",
                   initial_sidebar_state="collapsed")

st.markdown("""
<style>
* { margin:0; padding:0; }
html,body,[class*="css"] { background:#000!important; overflow:hidden; }
#MainMenu,footer,header { visibility:hidden; }
.block-container { padding:0!important; max-width:100%!important; }
iframe { border:none!important; }
</style>
""", unsafe_allow_html=True)

# ─── Get API key from user if not set ────────────────────────────────────────
api_key = st.session_state.get("groq_key", GROQ_API_KEY)

if not api_key:
    with st.form("key_form"):
        st.markdown("""
        <div style='text-align:center;padding:60px 20px;'>
          <div style='font-size:2.5rem;color:#8ab4f8;margin-bottom:12px;'>✦</div>
          <div style='font-size:1.4rem;font-weight:300;color:#fff;margin-bottom:8px;'>FRIDAY</div>
          <div style='font-size:.85rem;color:#666;margin-bottom:24px;'>Enter your Groq API key to start</div>
        </div>
        """, unsafe_allow_html=True)
        k = st.text_input("Groq API Key", placeholder="gsk_…", type="password")
        if st.form_submit_button("Start Friday →"):
            st.session_state.groq_key = k
            st.rerun()
    st.stop()

api_key = st.session_state.get("groq_key", GROQ_API_KEY)

# ─── THE ENTIRE APP IS ONE HTML FILE ─────────────────────────────────────────
# All AI calls go directly from browser JS → Groq API (no Python in the loop)
# This gives true real-time interaction

HTML = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1,maximum-scale=1">
<title>Friday Live</title>
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@200;300;400;500&display=swap');

:root {{
  --ac:  #8ab4f8;
  --ac2: #81c995;
  --red: #f28b82;
}}

* {{ margin:0; padding:0; box-sizing:border-box; }}
html,body {{ width:100vw; height:100vh; overflow:hidden; background:#000;
  font-family:'DM Sans',sans-serif; color:#fff; user-select:none; }}

/* ── VIDEO BG ── */
#vid {{
  position:fixed; inset:0;
  width:100%; height:100%;
  object-fit:cover;
  transition: filter .5s;
}}
#vid.blur {{ filter: brightness(.35) blur(2px); }}

/* ── VIGNETTE ── */
.vignette {{
  position:fixed; inset:0; z-index:1; pointer-events:none;
  background: radial-gradient(ellipse at center, transparent 50%, rgba(0,0,0,.55) 100%);
}}
#grad-top {{
  position:fixed; top:0; left:0; right:0; height:160px; z-index:1;
  background: linear-gradient(to bottom, rgba(0,0,0,.65), transparent);
  pointer-events:none;
}}
#grad-bot {{
  position:fixed; bottom:0; left:0; right:0; height:300px; z-index:1;
  background: linear-gradient(to top, rgba(0,0,0,.9) 0%, rgba(0,0,0,.4) 60%, transparent 100%);
  pointer-events:none;
}}

/* ── HUD CORNERS ── */
.hud-corner {{
  position:fixed; width:20px; height:20px; z-index:5;
  opacity:0; transition:opacity .5s;
}}
.hud-corner.on {{ opacity:.45; }}
.hc-tl {{ top:14px; left:14px; border-top:1.5px solid var(--ac); border-left:1.5px solid var(--ac); }}
.hc-tr {{ top:14px; right:14px; border-top:1.5px solid var(--ac); border-right:1.5px solid var(--ac); }}
.hc-bl {{ bottom:220px; left:14px; border-bottom:1.5px solid var(--ac); border-left:1.5px solid var(--ac); }}
.hc-br {{ bottom:220px; right:14px; border-bottom:1.5px solid var(--ac); border-right:1.5px solid var(--ac); }}

/* ── LOGO ── */
#logo {{
  position:fixed; top:18px; left:18px; z-index:10;
  display:flex; align-items:center; gap:8px;
  opacity:0; transform:translateY(-8px);
  transition: opacity .5s .2s, transform .5s .2s;
}}
#logo.on {{ opacity:1; transform:translateY(0); }}
#logo-mark {{ font-size:.95rem; color:var(--ac); }}
#logo-name {{ font-size:.82rem; font-weight:500; color:rgba(255,255,255,.8); letter-spacing:.08em; }}
#live-pill {{
  display:flex; align-items:center; gap:5px;
  padding:3px 9px; border-radius:12px;
  background:rgba(0,0,0,.4); border:1px solid rgba(255,255,255,.1);
  font-size:.6rem; color:rgba(255,255,255,.5); letter-spacing:.05em;
}}
#live-led {{
  width:6px; height:6px; border-radius:50%;
  background:var(--ac2); box-shadow:0 0 6px var(--ac2);
  animation:led 2s infinite;
}}
@keyframes led {{ 0%,100%{{opacity:1}} 50%{{opacity:.2}} }}

/* ── SETTINGS BTN ── */
#gear-btn {{
  position:fixed; top:16px; right:16px; z-index:10;
  width:36px; height:36px; border-radius:50%;
  background:rgba(0,0,0,.4); border:1px solid rgba(255,255,255,.1);
  color:rgba(255,255,255,.5); font-size:.9rem; cursor:pointer;
  display:flex; align-items:center; justify-content:center;
  backdrop-filter:blur(12px);
  opacity:0; transition:opacity .5s .3s;
}}
#gear-btn.on {{ opacity:1; }}
#gear-btn:hover {{ background:rgba(255,255,255,.12); color:#fff; }}

/* ── REPLY TEXT CENTER ── */
#reply-area {{
  position:fixed; z-index:8;
  left:50%; transform:translateX(-50%);
  bottom:210px;
  width:min(580px,90vw);
  text-align:center;
  opacity:0; transition:opacity .35s;
}}
#reply-area.on {{ opacity:1; }}

#reply-text {{
  font-size:1.1rem; font-weight:300; line-height:1.7;
  color:rgba(255,255,255,.95);
  text-shadow:0 2px 12px rgba(0,0,0,.9);
  letter-spacing:.005em;
}}

/* ── WAVEFORM ── */
#waveform {{
  display:flex; align-items:center; justify-content:center;
  gap:3px; height:28px; margin-top:10px;
  opacity:0; transition:opacity .3s;
}}
#waveform.on {{ opacity:1; }}
.wb {{
  width:3px; border-radius:2px;
  background:var(--ac);
  animation:wbounce .7s ease-in-out infinite;
}}
.wb:nth-child(1){{height:5px;  animation-delay:0s;   }}
.wb:nth-child(2){{height:12px; animation-delay:.07s; }}
.wb:nth-child(3){{height:20px; animation-delay:.14s; }}
.wb:nth-child(4){{height:26px; animation-delay:.21s; }}
.wb:nth-child(5){{height:20px; animation-delay:.14s; }}
.wb:nth-child(6){{height:12px; animation-delay:.07s; }}
.wb:nth-child(7){{height:5px;  animation-delay:0s;   }}
@keyframes wbounce {{
  0%,100% {{ transform:scaleY(1); opacity:.5; }}
  50%      {{ transform:scaleY(1.5); opacity:1; }}
}}

/* ── MIC BUTTON ── */
#mic-ring {{
  position:fixed; z-index:10;
  bottom:68px; left:50%; transform:translateX(-50%);
  width:80px; height:80px; border-radius:50%;
  display:flex; align-items:center; justify-content:center;
  opacity:0; transition:opacity .5s .4s;
}}
#mic-ring.on {{ opacity:1; }}

#mic-btn {{
  width:80px; height:80px; border-radius:50%;
  background:rgba(255,255,255,.08);
  border:1.5px solid rgba(255,255,255,.2);
  color:#fff; font-size:1.65rem; cursor:pointer;
  display:flex; align-items:center; justify-content:center;
  backdrop-filter:blur(20px);
  transition:all .2s;
  box-shadow:0 8px 32px rgba(0,0,0,.5);
  -webkit-tap-highlight-color:transparent;
  position:relative;
}}
#mic-btn::before {{
  content:'';
  position:absolute; inset:-4px; border-radius:50%;
  border:1px solid transparent;
  transition:all .3s;
}}
#mic-btn:hover {{
  background:rgba(255,255,255,.14);
  border-color:rgba(255,255,255,.35);
  transform:scale(1.04);
}}
#mic-btn.listening {{
  background:rgba(242,139,130,.15);
  border-color:var(--red);
  animation:mring 1.2s ease-in-out infinite;
}}
#mic-btn.thinking {{
  background:rgba(138,180,248,.12);
  border-color:var(--ac);
}}
#mic-btn.speaking {{
  background:rgba(129,201,149,.12);
  border-color:var(--ac2);
}}
@keyframes mring {{
  0%   {{ box-shadow:0 0 0 0 rgba(242,139,130,.5); }}
  70%  {{ box-shadow:0 0 0 20px rgba(242,139,130,0); }}
  100% {{ box-shadow:0 0 0 0 rgba(242,139,130,0); }}
}}

#mic-label {{
  position:fixed; z-index:10;
  bottom:46px; left:50%; transform:translateX(-50%);
  font-size:.68rem; color:rgba(255,255,255,.4);
  letter-spacing:.1em; text-transform:uppercase;
  white-space:nowrap;
  opacity:0; transition:opacity .5s .5s;
}}
#mic-label.on {{ opacity:1; }}

/* ── SIDE BUTTONS ── */
#cam-btns {{
  position:fixed; z-index:10;
  bottom:78px;
  display:flex; gap:14px; align-items:center;
  right:20px;
  flex-direction:column;
  opacity:0; transition:opacity .5s .3s;
}}
#cam-btns.on {{ opacity:1; }}
.side-btn {{
  width:46px; height:46px; border-radius:50%;
  background:rgba(0,0,0,.45);
  border:1px solid rgba(255,255,255,.1);
  color:rgba(255,255,255,.6); font-size:1rem; cursor:pointer;
  display:flex; align-items:center; justify-content:center;
  backdrop-filter:blur(10px); transition:.2s;
}}
.side-btn:hover {{ background:rgba(255,255,255,.1); color:#fff; }}

/* ── SNAP FLASH ── */
#flash {{
  position:fixed; inset:0; background:#fff;
  opacity:0; z-index:50; pointer-events:none;
  transition:opacity .08s;
}}

/* ── START SCREEN ── */
#start {{
  position:fixed; inset:0; z-index:100;
  background:#000;
  display:flex; flex-direction:column;
  align-items:center; justify-content:center;
  gap:14px;
  transition:opacity .6s;
}}
#start.hide {{ opacity:0; pointer-events:none; }}
.s-star {{ font-size:2.8rem; color:var(--ac); }}
.s-title {{ font-size:1.5rem; font-weight:200; letter-spacing:.1em; color:rgba(255,255,255,.9); }}
.s-sub {{
  font-size:.82rem; color:rgba(255,255,255,.3); max-width:220px;
  text-align:center; line-height:1.65;
}}
#start-btn {{
  margin-top:10px; padding:13px 40px; border-radius:30px;
  background:var(--ac); color:#000; border:none;
  font-size:.9rem; font-weight:600; cursor:pointer;
  font-family:'DM Sans',sans-serif; transition:.2s;
  letter-spacing:.02em;
}}
#start-btn:hover {{ opacity:.88; transform:scale(1.02); }}

/* ── SETTINGS PANEL ── */
#settings {{
  position:fixed; top:0; right:0; bottom:0; width:300px;
  background:rgba(8,8,8,.96); border-left:1px solid rgba(255,255,255,.06);
  z-index:200; overflow-y:auto;
  transform:translateX(100%);
  transition:transform .3s cubic-bezier(.4,0,.2,1);
  padding:20px;
  backdrop-filter:blur(20px);
}}
#settings.open {{ transform:translateX(0); }}
.s-overlay {{
  position:fixed; inset:0; background:rgba(0,0,0,.4);
  z-index:199; display:none;
}}
.s-overlay.show {{ display:block; }}
.s-head {{
  font-size:.95rem; font-weight:500; margin-bottom:16px;
  display:flex; align-items:center; justify-content:space-between;
  color:#fff;
}}
.s-close {{
  width:28px; height:28px; border-radius:50%;
  background:rgba(255,255,255,.06); border:none; color:#888;
  cursor:pointer; font-size:.9rem;
  display:flex; align-items:center; justify-content:center;
}}
.s-close:hover {{ color:#fff; }}
.s-section {{
  font-size:.65rem; color:#555; letter-spacing:.1em;
  text-transform:uppercase; margin:14px 0 7px;
}}
.s-input {{
  width:100%; background:rgba(255,255,255,.05);
  border:1px solid rgba(255,255,255,.08); border-radius:8px;
  padding:9px 12px; color:#fff; font-size:.82rem;
  font-family:'DM Sans',sans-serif; outline:none;
}}
.s-input:focus {{ border-color:rgba(138,180,248,.4); }}
select.s-input option {{ background:#111; }}
.s-btn {{
  width:100%; padding:9px; border-radius:10px;
  background:var(--ac); color:#000; border:none;
  font-weight:600; font-size:.82rem; cursor:pointer;
  font-family:'DM Sans',sans-serif; transition:.15s; margin-top:8px;
}}
.s-btn:hover {{ opacity:.88; }}
.s-btn.ghost {{
  background:rgba(255,255,255,.05); color:#888;
  border:1px solid rgba(255,255,255,.08);
}}
.s-btn.ghost:hover {{ background:rgba(255,255,255,.1); color:#fff; }}
.s-label {{ font-size:.78rem; color:#888; margin-bottom:5px; display:block; }}
.s-note {{ font-size:.68rem; color:#444; margin-top:4px; }}
.s-divider {{ border:none; border-top:1px solid rgba(255,255,255,.05); margin:12px 0; }}
.theme-row {{ display:grid; grid-template-columns:repeat(5,1fr); gap:6px; margin-top:4px; }}
.theme-swatch {{
  aspect-ratio:1; border-radius:8px; cursor:pointer;
  border:2px solid transparent; transition:.15s;
  display:flex; align-items:center; justify-content:center;
}}
.theme-swatch:hover {{ transform:scale(1.08); }}
.theme-swatch.active {{ border-color:var(--ac); }}

/* ── TOAST ── */
#toast {{
  position:fixed; bottom:140px; left:50%; transform:translateX(-50%);
  background:rgba(0,0,0,.7); border:1px solid rgba(255,255,255,.1);
  border-radius:10px; padding:8px 18px;
  font-size:.75rem; color:#ccc;
  z-index:300; opacity:0; transition:opacity .3s;
  pointer-events:none; white-space:nowrap;
}}
#toast.show {{ opacity:1; }}

/* ── STATUS CHIPS ── */
#status-chips {{
  position:fixed; left:50%; transform:translateX(-50%);
  bottom:24px; z-index:9;
  display:flex; gap:6px; align-items:center;
  opacity:0; transition:opacity .5s .6s;
}}
#status-chips.on {{ opacity:1; }}
.chip {{
  padding:3px 10px; border-radius:14px;
  background:rgba(0,0,0,.5); border:1px solid rgba(255,255,255,.06);
  font-size:.62rem; color:rgba(255,255,255,.35); letter-spacing:.05em;
  backdrop-filter:blur(8px);
}}
</style>
</head>
<body>

<!-- Full screen camera feed -->
<video id="vid" autoplay playsinline muted></video>

<!-- Visual overlays -->
<div class="vignette"></div>
<div id="grad-top"></div>
<div id="grad-bot"></div>

<!-- HUD corners -->
<div class="hud-corner hc-tl" id="c0"></div>
<div class="hud-corner hc-tr" id="c1"></div>
<div class="hud-corner hc-bl" id="c2"></div>
<div class="hud-corner hc-br" id="c3"></div>

<!-- Flash -->
<div id="flash"></div>

<!-- ══ START SCREEN ══ -->
<div id="start">
  <div class="s-star">✦</div>
  <div class="s-title">FRIDAY</div>
  <div class="s-sub">Full-screen live AI — camera on, voice in, voice out</div>
  <button id="start-btn" onclick="launch()">▶ &nbsp; Start</button>
</div>

<!-- ══ LOGO ══ -->
<div id="logo">
  <div id="logo-mark">✦</div>
  <div id="logo-name">FRIDAY</div>
  <div id="live-pill"><div id="live-led"></div>LIVE</div>
</div>

<!-- ══ SETTINGS GEAR ══ -->
<button id="gear-btn" onclick="openSettings()">⚙</button>

<!-- ══ FRIDAY'S REPLY ══ -->
<div id="reply-area">
  <div id="reply-text"></div>
  <div id="waveform" id="wave">
    <div class="wb"></div><div class="wb"></div><div class="wb"></div>
    <div class="wb"></div><div class="wb"></div><div class="wb"></div>
    <div class="wb"></div>
  </div>
</div>

<!-- ══ MIC BUTTON ══ -->
<div id="mic-ring">
  <button id="mic-btn" onclick="toggleMic()">🎤</button>
</div>
<div id="mic-label">Tap to talk</div>

<!-- ══ SIDE BUTTONS ══ -->
<div id="cam-btns">
  <button class="side-btn" onclick="snapAndAnalyse()" title="Capture & analyse">📸</button>
  <button class="side-btn" onclick="flipCam()"         title="Flip camera">🔄</button>
</div>

<!-- ══ STATUS CHIPS ══ -->
<div id="status-chips">
  <div class="chip" id="chip-cam">CAM OFF</div>
  <div class="chip" id="chip-voice">TAP TO TALK</div>
  <div class="chip" id="chip-ai">AI READY</div>
</div>

<!-- ══ TOAST ══ -->
<div id="toast"></div>

<!-- ══ SETTINGS OVERLAY + PANEL ══ -->
<div class="s-overlay" id="s-overlay" onclick="closeSettings()"></div>
<div id="settings">
  <div class="s-head">
    <span>Settings</span>
    <button class="s-close" onclick="closeSettings()">✕</button>
  </div>

  <div class="s-section">Groq API Key</div>
  <input class="s-input" id="s-key" type="password" placeholder="gsk_…" value="{api_key}">
  <div class="s-note">console.groq.com — free key</div>

  <hr class="s-divider">

  <div class="s-section">Chat Model</div>
  <select class="s-input" id="s-model">
    <option value="llama-3.3-70b-versatile">Llama 3.3 70B (best)</option>
    <option value="llama-3.1-8b-instant">Llama 3.1 8B (fast)</option>
    <option value="mixtral-8x7b-32768">Mixtral 8x7B</option>
  </select>

  <div class="s-section">Vision Model</div>
  <select class="s-input" id="s-vision">
    <option value="meta-llama/llama-4-scout-17b-16e-instruct">Llama 4 Scout (best)</option>
    <option value="llama-3.2-11b-vision-preview">Llama 3.2 11B Vision</option>
  </select>

  <hr class="s-divider">

  <div class="s-section">Friday's Voice</div>
  <select class="s-input" id="s-voice">
    <option value="en-IN-NeerjaNeural">Indian English — Neerja</option>
    <option value="en-US-JennyNeural">US English — Jenny</option>
    <option value="en-GB-SoniaNeural">UK English — Sonia</option>
    <option value="en-US-GuyNeural">US Male — Guy</option>
    <option value="hi-IN-SwaraNeural">Hindi — Swara</option>
  </select>

  <hr class="s-divider">

  <div class="s-section">Friday's Personality</div>
  <textarea class="s-input" id="s-prompt" rows="5" style="resize:vertical;">You are Friday, a real-time AI voice assistant like JARVIS.
You can see through the camera.
Always speak in 1-3 short natural sentences.
Never use lists or bullets — just talk naturally.
Say Boss occasionally. Be sharp, helpful, and concise.</textarea>

  <hr class="s-divider">

  <button class="s-btn" onclick="saveSettings()">Save Settings</button>
  <button class="s-btn ghost" style="margin-top:6px;" onclick="clearHistory()">Clear Conversation</button>

  <div style="font-size:.58rem;color:#333;text-align:center;margin-top:14px;">Friday Live v7.0</div>
</div>

<script>
// ══════════════════════════════════════
// STATE
// ══════════════════════════════════════
const STATE = {{
  apiKey:       "{api_key}",
  chatModel:    "llama-3.3-70b-versatile",
  visionModel:  "meta-llama/llama-4-scout-17b-16e-instruct",
  voice:        "en-IN-NeerjaNeural",
  prompt:       `You are Friday, a real-time AI voice assistant like JARVIS.
You can see through the camera.
Always speak in 1-3 short natural sentences.
Never use lists or bullets — just talk naturally.
Say Boss occasionally. Be sharp, helpful, and concise.`,
  history:      [],
  camAnalysis:  "",
  recognizing:  false,
  speaking:     false,
  launched:     false,
  facing:       "environment",
  stream:       null,
}};

// ══════════════════════════════════════
// LAUNCH
// ══════════════════════════════════════
async function launch() {{
  try {{
    STATE.stream = await navigator.mediaDevices.getUserMedia({{
      video: {{ facingMode: STATE.facing, width:{{ideal:1280}}, height:{{ideal:720}} }},
      audio: false
    }});
    document.getElementById("vid").srcObject = STATE.stream;

    document.getElementById("start").classList.add("hide");
    setTimeout(() => {{
      ["c0","c1","c2","c3"].forEach(id => document.getElementById(id).classList.add("on"));
      document.getElementById("logo").classList.add("on");
      document.getElementById("gear-btn").classList.add("on");
      document.getElementById("mic-ring").classList.add("on");
      document.getElementById("mic-label").classList.add("on");
      document.getElementById("cam-btns").classList.add("on");
      document.getElementById("status-chips").classList.add("on");
    }}, 400);

    document.getElementById("chip-cam").textContent = "CAM ON";
    STATE.launched = true;

    // Welcome
    setTimeout(() => {{
      fridaySpeak("Friday online. Camera active. Talk to me, Boss.");
    }}, 800);

  }} catch(e) {{
    document.getElementById("start-btn").textContent = "Camera denied — check permissions";
  }}
}}

// ══════════════════════════════════════
// FLIP CAMERA
// ══════════════════════════════════════
async function flipCam() {{
  STATE.facing = STATE.facing === "environment" ? "user" : "environment";
  if (STATE.stream) STATE.stream.getTracks().forEach(t => t.stop());
  try {{
    STATE.stream = await navigator.mediaDevices.getUserMedia({{
      video: {{ facingMode: STATE.facing }}, audio: false
    }});
    document.getElementById("vid").srcObject = STATE.stream;
  }} catch(e) {{ toast("Couldn't switch camera"); }}
}}

// ══════════════════════════════════════
// MIC — Web Speech API
// ══════════════════════════════════════
let recog = null;

function toggleMic() {{
  if (!STATE.launched) return;
  if (STATE.speaking)  return;  // don't interrupt Friday speaking
  if (STATE.recognizing) {{ recog && recog.stop(); return; }}

  const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (!SR) {{
    fridaySpeak("Voice recognition needs Chrome browser, Boss.");
    return;
  }}

  recog = new SR();
  recog.lang = "en-US";
  recog.continuous = false;
  recog.interimResults = false;
  recog.maxAlternatives = 1;

  recog.onstart = () => {{
    STATE.recognizing = true;
    setMicState("listening");
    updateChip("chip-voice", "LISTENING…");
  }};

  recog.onresult = (e) => {{
    const text = e.results[0][0].transcript;
    STATE.recognizing = false;
    setMicState("thinking");
    updateChip("chip-voice", "THINKING…");
    showReply('"' + text + '"');
    callGroq(text);
  }};

  recog.onerror = (e) => {{
    STATE.recognizing = false;
    setMicState("idle");
    updateChip("chip-voice", "TAP TO TALK");
    if (e.error !== "no-speech" && e.error !== "aborted")
      toast("Mic error: " + e.error);
  }};

  recog.onend = () => {{
    STATE.recognizing = false;
    if (document.getElementById("mic-btn").classList.contains("listening")) {{
      setMicState("idle");
      updateChip("chip-voice","TAP TO TALK");
    }}
  }};

  recog.start();
}}

// ══════════════════════════════════════
// SNAP + ASK FRIDAY WHAT IT SEES
// ══════════════════════════════════════
function snapAndAnalyse() {{
  if (!STATE.stream) {{ toast("Start camera first"); return; }}
  const vid = document.getElementById("vid");
  const c   = document.createElement("canvas");
  c.width   = vid.videoWidth  || 640;
  c.height  = vid.videoHeight || 480;
  c.getContext("2d").drawImage(vid, 0, 0);

  // Flash
  const fl = document.getElementById("flash");
  fl.style.opacity = ".65";
  setTimeout(() => fl.style.opacity = "0", 110);

  const b64 = c.toDataURL("image/jpeg", .85).split(",")[1];
  setMicState("thinking");
  showReply("Let me look at this…");
  callGroqVision(b64);
}}

// ══════════════════════════════════════
// GROQ CHAT API  (direct from browser)
// ══════════════════════════════════════
async function callGroq(userText) {{
  const key = STATE.apiKey;
  if (!key) {{ fridaySpeak("Please add your Groq API key in settings."); return; }}

  const sys = STATE.prompt +
    "\\nCurrent time: " + new Date().toLocaleTimeString("en-US",{{hour:"2-digit",minute:"2-digit"}}) +
    ", " + new Date().toLocaleDateString("en-US",{{weekday:"long",day:"numeric",month:"long",year:"numeric"}}) +
    (STATE.camAnalysis ? "\\n\\n[Camera just saw: " + STATE.camAnalysis.slice(0,200) + "]" : "");

  const messages = [
    {{ role:"system", content: sys }},
    ...STATE.history.slice(-8),
    {{ role:"user",   content: userText }}
  ];

  try {{
    const res = await fetch("https://api.groq.com/openai/v1/chat/completions", {{
      method: "POST",
      headers: {{
        "Content-Type": "application/json",
        "Authorization": "Bearer " + key
      }},
      body: JSON.stringify({{
        model:       STATE.chatModel,
        messages:    messages,
        max_tokens:  180,
        temperature: 0.75
      }})
    }});

    if (!res.ok) {{
      const err = await res.json();
      fridaySpeak("API error: " + (err.error?.message || res.status));
      return;
    }}

    const data  = await res.json();
    const reply = data.choices[0].message.content.trim();

    STATE.history.push({{ role:"user",      content: userText }});
    STATE.history.push({{ role:"assistant", content: reply    }});
    if (STATE.history.length > 20) STATE.history = STATE.history.slice(-20);

    fridaySpeak(reply);

  }} catch(e) {{
    fridaySpeak("Network error. Check your connection, Boss.");
  }}
}}

// ══════════════════════════════════════
// GROQ VISION API  (direct from browser)
// ══════════════════════════════════════
async function callGroqVision(b64) {{
  const key = STATE.apiKey;
  if (!key) {{ fridaySpeak("Please add your Groq API key in settings."); return; }}

  const visionPrompt = "Look at this image. In 2-3 sentences: what do you see? Any problems? Quick recommendation? Talk naturally, no lists.";

  try {{
    const res = await fetch("https://api.groq.com/openai/v1/chat/completions", {{
      method: "POST",
      headers: {{
        "Content-Type":"application/json",
        "Authorization":"Bearer " + key
      }},
      body: JSON.stringify({{
        model: STATE.visionModel,
        messages: [{{
          role: "user",
          content: [
            {{ type:"image_url", image_url:{{ url:"data:image/jpeg;base64," + b64 }} }},
            {{ type:"text", text: visionPrompt }}
          ]
        }}],
        max_tokens: 200
      }})
    }});

    if (!res.ok) {{
      const err = await res.json();
      fridaySpeak("Vision error: " + (err.error?.message || res.status));
      return;
    }}

    const data   = await res.json();
    const result = data.choices[0].message.content.trim();
    STATE.camAnalysis = result;
    fridaySpeak(result);

  }} catch(e) {{
    fridaySpeak("Couldn't analyse the image. Try again, Boss.");
  }}
}}

// ══════════════════════════════════════
// TEXT-TO-SPEECH  (Web Speech API)
// Uses browser's built-in TTS — no edge-tts needed
// ══════════════════════════════════════
function fridaySpeak(text) {{
  // Show text
  showReply(text);
  setMicState("speaking");
  updateChip("chip-voice", "SPEAKING…");
  document.getElementById("waveform").classList.add("on");

  // Cancel any ongoing speech
  speechSynthesis.cancel();

  const utt  = new SpeechSynthesisUtterance(text);
  utt.rate   = 1.05;
  utt.pitch  = 0.95;
  utt.volume = 1;
  utt.lang   = "en-IN";

  // Try to find a good voice
  const voices = speechSynthesis.getVoices();
  const pick = voices.find(v =>
    v.name.includes("Google") ||
    v.name.includes("Neerja")  ||
    v.name.includes("Samantha") ||
    v.name.includes("Karen")
  ) || voices.find(v => v.lang === "en-IN")
    || voices.find(v => v.lang.startsWith("en"))
    || voices[0];
  if (pick) utt.voice = pick;

  STATE.speaking = true;

  utt.onend = () => {{
    STATE.speaking = false;
    setMicState("idle");
    updateChip("chip-voice","TAP TO TALK");
    document.getElementById("waveform").classList.remove("on");
  }};

  utt.onerror = () => {{
    STATE.speaking = false;
    setMicState("idle");
    updateChip("chip-voice","TAP TO TALK");
    document.getElementById("waveform").classList.remove("on");
  }};

  speechSynthesis.speak(utt);
}}

// ══════════════════════════════════════
// UI HELPERS
// ══════════════════════════════════════
function showReply(text) {{
  document.getElementById("reply-text").textContent = text;
  document.getElementById("reply-area").classList.add("on");
}}

function clearReply() {{
  document.getElementById("reply-area").classList.remove("on");
}}

function setMicState(state) {{
  const btn = document.getElementById("mic-btn");
  btn.classList.remove("listening","thinking","speaking");
  const icons = {{ idle:"🎤", listening:"🔴", thinking:"⏳", speaking:"🔊" }};
  btn.textContent = icons[state] || "🎤";
  if (state !== "idle") btn.classList.add(state);
}}

function updateChip(id, text) {{
  const el = document.getElementById(id);
  if (el) el.textContent = text;
}}

function toast(msg, duration=2500) {{
  const el = document.getElementById("toast");
  el.textContent = msg;
  el.classList.add("show");
  setTimeout(() => el.classList.remove("show"), duration);
}}

// ══════════════════════════════════════
// SETTINGS PANEL
// ══════════════════════════════════════
function openSettings() {{
  document.getElementById("settings").classList.add("open");
  document.getElementById("s-overlay").classList.add("show");
}}
function closeSettings() {{
  document.getElementById("settings").classList.remove("open");
  document.getElementById("s-overlay").classList.remove("show");
}}
function saveSettings() {{
  STATE.apiKey     = document.getElementById("s-key").value.trim();
  STATE.chatModel  = document.getElementById("s-model").value;
  STATE.visionModel= document.getElementById("s-vision").value;
  STATE.voice      = document.getElementById("s-voice").value;
  STATE.prompt     = document.getElementById("s-prompt").value;
  closeSettings();
  toast("Settings saved ✓");
}}
function clearHistory() {{
  STATE.history = [];
  STATE.camAnalysis = "";
  clearReply();
  toast("Conversation cleared");
  closeSettings();
}}

// ══════════════════════════════════════
// KEYBOARD SHORTCUT — Space bar = mic
// ══════════════════════════════════════
document.addEventListener("keydown", (e) => {{
  if (e.code === "Space" && !e.target.matches("input,textarea,select")) {{
    e.preventDefault();
    toggleMic();
  }}
}});

// Load voices (async in some browsers)
speechSynthesis.onvoiceschanged = () => {{ speechSynthesis.getVoices(); }};
</script>
</body>
</html>
"""

st.components.v1.html(HTML, height=800, scrolling=False)
