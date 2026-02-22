"""
FRIDAY LIVE v9.0 - Gemini Edition
Wake word: "Friday" | Auto-wake after 10s silence | Continuous conversation
Run: streamlit run friday_gemini.py
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
    "system_prompt": "You are Friday, a real-time AI voice assistant.",
    "enable_rag": True,
    "max_tokens": 180,
    "temperature": 0.75
})

st.set_page_config(page_title="Friday", page_icon="✦", layout="wide", initial_sidebar_state="collapsed")

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
    st.error("❌ API Key not configured. Set in Admin Panel (port 8503)")
    st.stop()

KNOWLEDGE_CONTEXT = ""
if CONFIG['enable_rag'] and os.path.exists("friday_knowledge/"):
    files = [f for f in os.listdir("friday_knowledge/") if f.endswith(('.txt', '.md'))]
    for file in files[:5]:
        with open(os.path.join("friday_knowledge/", file), 'r', encoding='utf-8') as f:
            KNOWLEDGE_CONTEXT += f"\n{f.read()[:2000]}"

HTML = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Friday</title>
<style>
* {{ margin:0; padding:0; box-sizing:border-box; }}
html,body {{ width:100vw; height:100vh; overflow:hidden; 
  background: radial-gradient(ellipse at center, #1a1f3a 0%, #000 100%);
  font-family: 'Google Sans', 'Roboto', sans-serif; color:#fff; user-select:none; }}

/* ── ORB (Gemini Style) ── */
#orb {{
  position:fixed; z-index:5;
  top:50%; left:50%; transform:translate(-50%, -50%);
  width:280px; height:280px; border-radius:50%;
  background: radial-gradient(circle at 30% 30%, #4facfe 0%, #00f2fe 25%, #667eea 50%, #764ba2 75%, #f093fb 100%);
  box-shadow: 0 0 80px rgba(79,172,254,.6), 0 0 120px rgba(102,126,234,.4);
  opacity:0; transition: all .8s cubic-bezier(.4,0,.2,1);
  filter: blur(0px);
}}
#orb.on {{ opacity:1; }}
#orb.listening {{
  animation: orbPulse 1.2s ease-in-out infinite;
  box-shadow: 0 0 120px rgba(79,172,254,.9), 0 0 160px rgba(102,126,234,.6);
}}
#orb.thinking {{
  animation: orbRotate 3s linear infinite;
  filter: blur(2px);
}}
#orb.speaking {{
  animation: orbWave 1s ease-in-out infinite;
}}
@keyframes orbPulse {{
  0%, 100% {{ transform: translate(-50%, -50%) scale(1); }}
  50% {{ transform: translate(-50%, -50%) scale(1.15); }}
}}
@keyframes orbRotate {{
  from {{ transform: translate(-50%, -50%) rotate(0deg); }}
  to {{ transform: translate(-50%, -50%) rotate(360deg); }}
}}
@keyframes orbWave {{
  0%, 100% {{ border-radius: 50% 50% 50% 50%; }}
  25% {{ border-radius: 45% 55% 50% 50%; }}
  50% {{ border-radius: 50% 50% 45% 55%; }}
  75% {{ border-radius: 55% 45% 55% 45%; }}
}}

/* ── GRADIENT RING ── */
#ring {{
  position:fixed; z-index:4;
  top:50%; left:50%; transform:translate(-50%, -50%);
  width:340px; height:340px; border-radius:50%;
  background: conic-gradient(from 0deg, #4facfe, #00f2fe, #667eea, #764ba2, #f093fb, #4facfe);
  opacity:0; transition:opacity .8s;
  filter: blur(30px);
}}
#ring.on {{ opacity:.3; }}

/* ── TEXT ── */
#text {{
  position:fixed; z-index:10;
  bottom:180px; left:50%; transform:translateX(-50%);
  width:min(600px, 90vw); text-align:center;
  opacity:0; transition:opacity .5s;
}}
#text.on {{ opacity:1; }}
#text-content {{
  font-size:1rem; font-weight:400; line-height:1.6;
  color:rgba(255,255,255,.9);
  text-shadow:0 2px 12px rgba(0,0,0,.8);
}}

/* ── STATUS ── */
#status {{
  position:fixed; z-index:10;
  bottom:140px; left:50%; transform:translateX(-50%);
  font-size:.75rem; color:rgba(255,255,255,.5);
  letter-spacing:.08em; text-transform:uppercase;
  opacity:0; transition:opacity .5s;
}}
#status.on {{ opacity:1; }}

/* ── LOGO ── */
#logo {{
  position:fixed; top:24px; left:24px; z-index:10;
  font-size:1.1rem; font-weight:500; color:rgba(255,255,255,.7);
  opacity:0; transition:opacity .8s .3s;
}}
#logo.on {{ opacity:1; }}

/* ── BUTTONS ── */
#controls {{
  position:fixed; right:24px; top:50%; transform:translateY(-50%);
  z-index:10; display:flex; flex-direction:column; gap:16px;
  opacity:0; transition:opacity .8s .4s;
}}
#controls.on {{ opacity:1; }}
.ctrl-btn {{
  width:52px; height:52px; border-radius:50%;
  background:rgba(255,255,255,.08);
  border:1px solid rgba(255,255,255,.15);
  color:rgba(255,255,255,.7); font-size:1.3rem; cursor:pointer;
  display:flex; align-items:center; justify-content:center;
  backdrop-filter:blur(20px); transition:.2s;
}}
.ctrl-btn:hover {{
  background:rgba(255,255,255,.15);
  border-color:rgba(255,255,255,.3);
  color:#fff;
}}

/* ── WAKE INDICATOR ── */
#wake-indicator {{
  position:fixed; top:24px; right:24px; z-index:10;
  padding:6px 14px; border-radius:20px;
  background:rgba(79,172,254,.15);
  border:1px solid rgba(79,172,254,.3);
  font-size:.7rem; color:rgba(79,172,254,.9);
  letter-spacing:.05em; backdrop-filter:blur(10px);
  opacity:0; transition:opacity .5s;
}}
#wake-indicator.on {{ opacity:1; }}

/* ── START ── */
#start {{
  position:fixed; inset:0; z-index:100;
  background:radial-gradient(ellipse at center, #1a1f3a 0%, #000 100%);
  display:flex; flex-direction:column; align-items:center; justify-content:center;
  gap:20px; transition:opacity .8s;
}}
#start.hide {{ opacity:0; pointer-events:none; }}
.start-orb {{
  width:160px; height:160px; border-radius:50%;
  background: radial-gradient(circle at 30% 30%, #4facfe 0%, #00f2fe 25%, #667eea 50%, #764ba2 75%, #f093fb 100%);
  box-shadow: 0 0 60px rgba(79,172,254,.6);
  animation: startPulse 2s ease-in-out infinite;
}}
@keyframes startPulse {{
  0%, 100% {{ transform:scale(1); opacity:.8; }}
  50% {{ transform:scale(1.1); opacity:1; }}
}}
.start-title {{
  font-size:2rem; font-weight:300; letter-spacing:.15em;
  color:rgba(255,255,255,.95); margin-top:20px;
}}
.start-sub {{
  font-size:.85rem; color:rgba(255,255,255,.4);
  max-width:280px; text-align:center; line-height:1.6;
}}
#start-btn {{
  margin-top:16px; padding:14px 38px; border-radius:30px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color:#fff; border:none; font-size:.95rem; font-weight:500;
  cursor:pointer; transition:.2s; letter-spacing:.03em;
}}
#start-btn:hover {{ transform:scale(1.05); opacity:.9; }}

/* ── TOAST ── */
#toast {{
  position:fixed; bottom:100px; left:50%; transform:translateX(-50%);
  background:rgba(0,0,0,.8); border:1px solid rgba(255,255,255,.15);
  border-radius:12px; padding:10px 20px; font-size:.8rem; color:#ccc;
  z-index:300; opacity:0; transition:opacity .3s;
  pointer-events:none; backdrop-filter:blur(20px);
}}
#toast.show {{ opacity:1; }}
</style>
</head>
<body>

<!-- ══ START ══ -->
<div id="start">
  <div class="start-orb"></div>
  <div class="start-title">FRIDAY</div>
  <div class="start-sub">Say "Friday" to activate • Continuous conversation mode</div>
  <button id="start-btn" onclick="launch()">Start</button>
</div>

<!-- ══ MAIN UI ══ -->
<div id="ring"></div>
<div id="orb"></div>

<div id="logo">FRIDAY</div>
<div id="wake-indicator">🔴 LISTENING FOR "FRIDAY"</div>

<div id="text">
  <div id="text-content"></div>
</div>

<div id="status">Ready</div>

<div id="controls">
  <button class="ctrl-btn" onclick="snapAndAnalyse()" title="Capture">📸</button>
  <button class="ctrl-btn" onclick="toggleMute()" title="Mute/Unmute" id="mute-btn">🔊</button>
</div>

<div id="toast"></div>

<script>
const CONFIG = {{
  apiKey: "{CONFIG['groq_api_key']}",
  chatModel: "{CONFIG['chat_model']}",
  visionModel: "{CONFIG['vision_model']}",
  prompt: `{CONFIG['system_prompt']}`,
  maxTokens: {CONFIG['max_tokens']},
  temperature: {CONFIG['temperature']},
  knowledge: `{KNOWLEDGE_CONTEXT.replace('`', '').replace(chr(10), ' ')[:2000]}`
}};

const STATE = {{
  history: [],
  camAnalysis: "",
  active: false,
  speaking: false,
  muted: false,
  silenceTimer: null,
  lastInteraction: Date.now(),
  wakeRecog: null,
  talkRecog: null,
  stream: null
}};

// ══════════════════════════════════════
// LAUNCH
// ══════════════════════════════════════
async function launch() {{
  try {{
    STATE.stream = await navigator.mediaDevices.getUserMedia({{
      video: {{ facingMode: "environment", width:{{ideal:1280}}, height:{{ideal:720}} }},
      audio: false
    }});

    document.getElementById("start").classList.add("hide");
    
    setTimeout(() => {{
      ["orb","ring","logo","controls","status","wake-indicator"].forEach(id => 
        document.getElementById(id).classList.add("on")
      );
      startWakeWordListener();
      toast("Say 'Friday' to activate");
    }}, 500);

  }} catch(e) {{
    toast("Camera access denied");
  }}
}}

// ══════════════════════════════════════
// WAKE WORD LISTENER (Always On)
// ══════════════════════════════════════
function startWakeWordListener() {{
  const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (!SR) return;

  STATE.wakeRecog = new SR();
  STATE.wakeRecog.continuous = true;
  STATE.wakeRecog.interimResults = false;
  STATE.wakeRecog.lang = "en-US";

  STATE.wakeRecog.onresult = (e) => {{
    const transcript = e.results[e.results.length - 1][0].transcript.toLowerCase();
    
    if (transcript.includes("friday")) {{
      console.log("Wake word detected:", transcript);
      activate();
    }}
  }};

  STATE.wakeRecog.onerror = (e) => {{
    if (e.error === "no-speech") {{
      // Restart if stops
      setTimeout(() => {{
        if (!STATE.active) STATE.wakeRecog.start();
      }}, 100);
    }}
  }};

  STATE.wakeRecog.onend = () => {{
    // Keep listening if not active
    if (!STATE.active) {{
      setTimeout(() => STATE.wakeRecog.start(), 100);
    }}
  }};

  STATE.wakeRecog.start();
}}

// ══════════════════════════════════════
// ACTIVATE (Wake Word Detected)
// ══════════════════════════════════════
function activate() {{
  if (STATE.active || STATE.speaking) return;
  
  // Stop wake word listener
  if (STATE.wakeRecog) STATE.wakeRecog.stop();
  
  STATE.active = true;
  STATE.lastInteraction = Date.now();
  
  setStatus("listening");
  setText("Yes?");
  
  document.getElementById("wake-indicator").classList.remove("on");
  
  // Start conversation listener
  startConversationListener();
}}

// ══════════════════════════════════════
// CONVERSATION LISTENER (Active Mode)
// ══════════════════════════════════════
function startConversationListener() {{
  const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (!SR) return;

  STATE.talkRecog = new SR();
  STATE.talkRecog.continuous = true;
  STATE.talkRecog.interimResults = false;
  STATE.talkRecog.lang = "en-US";

  STATE.talkRecog.onresult = (e) => {{
    const text = e.results[e.results.length - 1][0].transcript;
    console.log("User said:", text);
    
    STATE.lastInteraction = Date.now();
    clearTimeout(STATE.silenceTimer);
    
    setText(`"${{text}}"`);
    setStatus("thinking");
    
    callGroq(text);
  }};

  STATE.talkRecog.onerror = (e) => {{
    if (e.error === "no-speech") {{
      checkSilence();
    }}
  }};

  STATE.talkRecog.onend = () => {{
    if (STATE.active && !STATE.speaking) {{
      setTimeout(() => STATE.talkRecog.start(), 100);
    }}
  }};

  STATE.talkRecog.start();
  startSilenceCheck();
}}

// ══════════════════════════════════════
// SILENCE CHECK (Auto-sleep after 10s)
// ══════════════════════════════════════
function startSilenceCheck() {{
  STATE.silenceTimer = setInterval(() => {{
    if (!STATE.active) return;
    
    const elapsed = Date.now() - STATE.lastInteraction;
    
    if (elapsed > 10000) {{ // 10 seconds
      console.log("10s silence - going to sleep");
      deactivate();
    }}
  }}, 1000);
}}

function checkSilence() {{
  const elapsed = Date.now() - STATE.lastInteraction;
  if (elapsed > 10000 && STATE.active) {{
    deactivate();
  }}
}}

// ══════════════════════════════════════
// DEACTIVATE (Return to Wake Word)
// ══════════════════════════════════════
function deactivate() {{
  STATE.active = false;
  
  if (STATE.talkRecog) STATE.talkRecog.stop();
  clearTimeout(STATE.silenceTimer);
  
  setStatus("sleeping");
  setText("Say 'Friday' to wake me");
  
  setTimeout(() => {{
    setText("");
    document.getElementById("wake-indicator").classList.add("on");
    startWakeWordListener();
  }}, 2000);
}}

// ══════════════════════════════════════
// GROQ CHAT
// ══════════════════════════════════════
async function callGroq(userText) {{
  const sys = CONFIG.prompt +
    "\\nTime: " + new Date().toLocaleString("en-US", {{hour:"2-digit",minute:"2-digit"}}) +
    (STATE.camAnalysis ? "\\n[Camera: " + STATE.camAnalysis.slice(0,200) + "]" : "") +
    (CONFIG.knowledge ? "\\n[Knowledge: " + CONFIG.knowledge.slice(0,500) + "]" : "");

  const messages = [
    {{ role:"system", content: sys }},
    ...STATE.history.slice(-8),
    {{ role:"user", content: userText }}
  ];

  try {{
    const res = await fetch("https://api.groq.com/openai/v1/chat/completions", {{
      method: "POST",
      headers: {{
        "Content-Type": "application/json",
        "Authorization": "Bearer " + CONFIG.apiKey
      }},
      body: JSON.stringify({{
        model: CONFIG.chatModel,
        messages: messages,
        max_tokens: CONFIG.maxTokens,
        temperature: CONFIG.temperature
      }})
    }});

    if (!res.ok) {{
      const err = await res.json();
      speak("API error: " + (err.error?.message || res.status));
      return;
    }}

    const data = await res.json();
    const reply = data.choices[0].message.content.trim();

    STATE.history.push({{ role:"user", content: userText }});
    STATE.history.push({{ role:"assistant", content: reply }});
    if (STATE.history.length > 20) STATE.history = STATE.history.slice(-20);

    speak(reply);

  }} catch(e) {{
    speak("Network error, Boss.");
  }}
}}

// ══════════════════════════════════════
// VISION
// ══════════════════════════════════════
function snapAndAnalyse() {{
  if (!STATE.stream) return;
  
  const c = document.createElement("canvas");
  const vid = document.createElement("video");
  vid.srcObject = STATE.stream;
  vid.play();
  
  setTimeout(() => {{
    c.width = vid.videoWidth || 640;
    c.height = vid.videoHeight || 480;
    c.getContext("2d").drawImage(vid, 0, 0);
    const b64 = c.toDataURL("image/jpeg", .85).split(",")[1];
    
    setStatus("analyzing");
    setText("Let me see...");
    
    callGroqVision(b64);
  }}, 100);
}}

async function callGroqVision(b64) {{
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
            {{ type:"text", text: "In 2-3 sentences: what do you see? Any issues? Recommendations?" }}
          ]
        }}],
        max_tokens: 200
      }})
    }});

    if (!res.ok) throw new Error("Vision API error");

    const data = await res.json();
    const result = data.choices[0].message.content.trim();
    STATE.camAnalysis = result;
    speak(result);

  }} catch(e) {{
    speak("Couldn't analyze the image.");
  }}
}}

// ══════════════════════════════════════
// TTS
// ══════════════════════════════════════
function speak(text) {{
  if (STATE.muted) {{
    setText(text);
    STATE.lastInteraction = Date.now();
    return;
  }}

  setText(text);
  setStatus("speaking");
  STATE.speaking = true;
  STATE.lastInteraction = Date.now();

  speechSynthesis.cancel();

  const utt = new SpeechSynthesisUtterance(text);
  utt.rate = 1.05;
  utt.pitch = 0.95;
  utt.lang = "en-IN";

  const voices = speechSynthesis.getVoices();
  const pick = voices.find(v => v.name.includes("Google") || v.name.includes("Neerja")) || voices[0];
  if (pick) utt.voice = pick;

  utt.onend = () => {{
    STATE.speaking = false;
    STATE.lastInteraction = Date.now();
    
    if (STATE.active) {{
      setStatus("listening");
      setText("");
    }}
  }};

  utt.onerror = () => {{
    STATE.speaking = false;
    setStatus("listening");
  }};

  speechSynthesis.speak(utt);
}}

// ══════════════════════════════════════
// UI
// ══════════════════════════════════════
function setStatus(state) {{
  const orb = document.getElementById("orb");
  const status = document.getElementById("status");
  
  orb.className = state === "listening" ? "on listening" : 
                  state === "thinking" ? "on thinking" : 
                  state === "speaking" ? "on speaking" : "on";
  
  const labels = {{
    listening: "Listening...",
    thinking: "Thinking...",
    speaking: "Speaking...",
    analyzing: "Analyzing...",
    sleeping: "Sleeping..."
  }};
  
  status.textContent = labels[state] || "Ready";
}}

function setText(text) {{
  const el = document.getElementById("text");
  const content = document.getElementById("text-content");
  content.textContent = text;
  
  if (text) {{
    el.classList.add("on");
  }} else {{
    el.classList.remove("on");
  }}
}}

function toast(msg, duration=2500) {{
  const el = document.getElementById("toast");
  el.textContent = msg;
  el.classList.add("show");
  setTimeout(() => el.classList.remove("show"), duration);
}}

function toggleMute() {{
  STATE.muted = !STATE.muted;
  const btn = document.getElementById("mute-btn");
  btn.textContent = STATE.muted ? "🔇" : "🔊";
  toast(STATE.muted ? "Muted" : "Unmuted");
}}

speechSynthesis.onvoiceschanged = () => {{ speechSynthesis.getVoices(); }};
</script>
</body>
</html>
"""

st.components.v1.html(HTML, height=800, scrolling=False)
