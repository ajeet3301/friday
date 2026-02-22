"""
FRIDAY LIVE v8.0 - User App
Pure voice interaction controlled by admin panel
Run: streamlit run friday_live.py
Admin: streamlit run friday_admin.py --server.port 8503
"""

import os
import streamlit as st
import json
from dotenv import load_dotenv
load_dotenv()

# Load configs from admin panel
def load_config(file, default):
    if os.path.exists(file):
        with open(file, 'r') as f:
            return json.load(f)
    return default

CONFIG = load_config("friday_config.json", {
    "groq_api_key": os.getenv("GROQ_API_KEY", ""),
    "chat_model": "llama-3.3-70b-versatile",
    "vision_model": "meta-llama/llama-4-scout-17b-16e-instruct",
    "whisper_model": "whisper-large-v3-turbo",
    "tts_voice": "en-IN-NeerjaNeural",
    "system_prompt": "You are Friday, a real-time AI voice assistant like JARVIS.",
    "enable_rag": True,
    "max_tokens": 180,
    "temperature": 0.75
})

THEME = load_config("friday_theme.json", {
    "primary_color": "#8ab4f8",
    "secondary_color": "#81c995",
    "red_color": "#f28b82",
    "background_image": "none",
    "background_blur": "2px",
    "glass_opacity": "0.08",
    "glass_blur": "20px",
    "vignette_intensity": "0.55"
})

st.set_page_config(
    page_title="Friday Live",
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

# Check API key
if not CONFIG['groq_api_key']:
    st.error("❌ API Key not configured. Please set it in Admin Panel (port 8503)")
    st.code("streamlit run friday_admin.py --server.port 8503")
    st.stop()

# Load knowledge base if RAG enabled
KNOWLEDGE_CONTEXT = ""
if CONFIG['enable_rag'] and os.path.exists("friday_knowledge/"):
    files = [f for f in os.listdir("friday_knowledge/") if f.endswith(('.txt', '.md'))]
    for file in files[:5]:  # Max 5 files
        with open(os.path.join("friday_knowledge/", file), 'r', encoding='utf-8') as f:
            content = f.read()[:2000]  # First 2000 chars per file
            KNOWLEDGE_CONTEXT += f"\n\n[Knowledge from {file}]:\n{content}"

# Generate background style
bg_style = ""
if THEME['background_image'] == "blur":
    bg_style = ""  # Use camera feed
elif THEME['background_image'] != "none":
    bg_style = f"background-image: url('{THEME['background_image']}'); background-size: cover; background-position: center;"

HTML = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1,maximum-scale=1">
<title>Friday Live</title>
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@200;300;400;500&display=swap');

:root {{
  --ac:  {THEME['primary_color']};
  --ac2: {THEME['secondary_color']};
  --red: {THEME['red_color']};
}}

* {{ margin:0; padding:0; box-sizing:border-box; }}
html,body {{ width:100vw; height:100vh; overflow:hidden; background:#000;
  font-family:'DM Sans',sans-serif; color:#fff; user-select:none; }}

/* ── VIDEO/BG ── */
#vid {{
  position:fixed; inset:0; width:100%; height:100%; object-fit:cover;
  transition: filter .5s;
  {bg_style}
}}
#vid.blur {{ filter: brightness(.35) blur({THEME['background_blur']}); }}

.vignette {{
  position:fixed; inset:0; z-index:1; pointer-events:none;
  background: radial-gradient(ellipse at center, transparent 50%, rgba(0,0,0,{THEME['vignette_intensity']}) 100%);
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
  background:rgba(255,255,255,{THEME['glass_opacity']});
  border:1.5px solid rgba(255,255,255,.2);
  color:#fff; font-size:1.65rem; cursor:pointer;
  display:flex; align-items:center; justify-content:center;
  backdrop-filter:blur({THEME['glass_blur']});
  transition:all .2s;
  box-shadow:0 8px 32px rgba(0,0,0,.5);
  -webkit-tap-highlight-color:transparent;
  position:relative;
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

<!-- ══ FRIDAY'S REPLY ══ -->
<div id="reply-area">
  <div id="reply-text"></div>
  <div id="waveform">
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
  <button class="side-btn" onclick="flipCam()" title="Flip camera">🔄</button>
</div>

<!-- ══ STATUS CHIPS ══ -->
<div id="status-chips">
  <div class="chip" id="chip-cam">CAM OFF</div>
  <div class="chip" id="chip-voice">TAP TO TALK</div>
  <div class="chip" id="chip-ai">AI READY</div>
</div>

<!-- ══ TOAST ══ -->
<div id="toast"></div>

<script>
// ══════════════════════════════════════
// CONFIG FROM ADMIN PANEL
// ══════════════════════════════════════
const CONFIG = {{
  apiKey:       "{CONFIG['groq_api_key']}",
  chatModel:    "{CONFIG['chat_model']}",
  visionModel:  "{CONFIG['vision_model']}",
  voice:        "{CONFIG['tts_voice']}",
  prompt:       `{CONFIG['system_prompt']}`,
  maxTokens:    {CONFIG['max_tokens']},
  temperature:  {CONFIG['temperature']},
  enableRAG:    {str(CONFIG['enable_rag']).lower()},
  knowledge:    `{KNOWLEDGE_CONTEXT.replace('`', '').replace(chr(10), ' ')[:2000]}`
}};

const STATE = {{
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
      document.getElementById("mic-ring").classList.add("on");
      document.getElementById("mic-label").classList.add("on");
      document.getElementById("cam-btns").classList.add("on");
      document.getElementById("status-chips").classList.add("on");
    }}, 400);

    document.getElementById("chip-cam").textContent = "CAM ON";
    STATE.launched = true;

    setTimeout(() => {{
      fridaySpeak("Friday online. Camera active. Talk to me, Boss.");
    }}, 800);

  }} catch(e) {{
    document.getElementById("start-btn").textContent = "Camera denied — check permissions";
  }}
}}

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
  if (STATE.speaking) return;
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
// SNAP + VISION
// ══════════════════════════════════════
function snapAndAnalyse() {{
  if (!STATE.stream) {{ toast("Start camera first"); return; }}
  const vid = document.getElementById("vid");
  const c   = document.createElement("canvas");
  c.width   = vid.videoWidth  || 640;
  c.height  = vid.videoHeight || 480;
  c.getContext("2d").drawImage(vid, 0, 0);

  const fl = document.getElementById("flash");
  fl.style.opacity = ".65";
  setTimeout(() => fl.style.opacity = "0", 110);

  const b64 = c.toDataURL("image/jpeg", .85).split(",")[1];
  setMicState("thinking");
  showReply("Let me look at this…");
  callGroqVision(b64);
}}

// ══════════════════════════════════════
// GROQ CHAT
// ══════════════════════════════════════
async function callGroq(userText) {{
  const sys = CONFIG.prompt +
    "\\nCurrent time: " + new Date().toLocaleTimeString("en-US",{{hour:"2-digit",minute:"2-digit"}}) +
    ", " + new Date().toLocaleDateString("en-US",{{weekday:"long",day:"numeric",month:"long",year:"numeric"}}) +
    (STATE.camAnalysis ? "\\n\\n[Camera: " + STATE.camAnalysis.slice(0,200) + "]" : "") +
    (CONFIG.enableRAG && CONFIG.knowledge ? "\\n\\n[Knowledge: " + CONFIG.knowledge.slice(0,500) + "]" : "");

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
        "Authorization": "Bearer " + CONFIG.apiKey
      }},
      body: JSON.stringify({{
        model:       CONFIG.chatModel,
        messages:    messages,
        max_tokens:  CONFIG.maxTokens,
        temperature: CONFIG.temperature
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
// GROQ VISION
// ══════════════════════════════════════
async function callGroqVision(b64) {{
  const visionPrompt = "Look at this image. In 2-3 sentences: what do you see? Any problems? Quick recommendation? Talk naturally, no lists.";

  try {{
    const res = await fetch("https://api.groq.com/openai/v1/chat/completions", {{
      method: "POST",
      headers: {{
        "Content-Type":"application/json",
        "Authorization":"Bearer " + CONFIG.apiKey
      }},
      body: JSON.stringify({{
        model: CONFIG.visionModel,
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
// TTS — Web Speech API
// ══════════════════════════════════════
function fridaySpeak(text) {{
  showReply(text);
  setMicState("speaking");
  updateChip("chip-voice", "SPEAKING…");
  document.getElementById("waveform").classList.add("on");

  speechSynthesis.cancel();

  const utt = new SpeechSynthesisUtterance(text);
  utt.rate = 1.05;
  utt.pitch = 0.95;
  utt.volume = 1;
  utt.lang = "en-IN";

  const voices = speechSynthesis.getVoices();
  const pick = voices.find(v => v.name.includes("Google") || v.name.includes("Neerja")) || voices[0];
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

// Space bar = mic
document.addEventListener("keydown", (e) => {{
  if (e.code === "Space" && !e.target.matches("input,textarea,select")) {{
    e.preventDefault();
    toggleMic();
  }}
}});

speechSynthesis.onvoiceschanged = () => {{ speechSynthesis.getVoices(); }};
</script>
</body>
</html>
"""

st.components.v1.html(HTML, height=800, scrolling=False)
