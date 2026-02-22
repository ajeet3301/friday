"""
FRIDAY GEMINI v9.1
- Say "Friday" to wake (background listening)
- Continuous conversation (auto-sleep 10s)
- Settings gear (⚙) for voice/model/personality
- Admin controls everything
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
    "tts_voice": "en-IN-NeerjaNeural",
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
    st.error("❌ API Key not configured")
    st.info("🔧 Admin Panel: streamlit run friday_admin.py --server.port 8503")
    st.stop()

KNOWLEDGE_CONTEXT = ""
if CONFIG['enable_rag'] and os.path.exists("friday_knowledge/"):
    files = [f for f in os.listdir("friday_knowledge/") if f.endswith(('.txt', '.md'))]
    for file in files[:5]:
        try:
            with open(os.path.join("friday_knowledge/", file), 'r', encoding='utf-8') as f:
                KNOWLEDGE_CONTEXT += f"\n{f.read()[:2000]}"
        except:
            pass

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

#vid {{
  position:fixed; inset:0; width:100%; height:100%; object-fit:cover;
  opacity:0; transition:opacity 1s;
}}
#vid.on {{ opacity:1; }}

/* ── ORB ── */
#orb {{
  position:fixed; z-index:5;
  top:50%; left:50%; transform:translate(-50%, -50%);
  width:280px; height:280px; border-radius:50%;
  background: radial-gradient(circle at 30% 30%, #4facfe 0%, #00f2fe 25%, #667eea 50%, #764ba2 75%, #f093fb 100%);
  box-shadow: 0 0 80px rgba(79,172,254,.6), 0 0 120px rgba(102,126,234,.4);
  opacity:0; transition: all .8s;
}}
#orb.on {{ opacity:1; }}
#orb.listening {{ animation: orbPulse 1.2s ease-in-out infinite; }}
#orb.thinking {{ animation: orbRotate 3s linear infinite; filter: blur(2px); }}
#orb.speaking {{ animation: orbWave 1s ease-in-out infinite; }}
@keyframes orbPulse {{
  0%, 100% {{ transform: translate(-50%, -50%) scale(1); }}
  50% {{ transform: translate(-50%, -50%) scale(1.15); }}
}}
@keyframes orbRotate {{
  from {{ transform: translate(-50%, -50%) rotate(0deg); }}
  to {{ transform: translate(-50%, -50%) rotate(360deg); }}
}}
@keyframes orbWave {{
  0%, 100% {{ border-radius: 50%; }}
  25% {{ border-radius: 45% 55% 50% 50%; }}
  50% {{ border-radius: 50% 50% 45% 55%; }}
  75% {{ border-radius: 55% 45% 55% 45%; }}
}}

#ring {{
  position:fixed; z-index:4;
  top:50%; left:50%; transform:translate(-50%, -50%);
  width:340px; height:340px; border-radius:50%;
  background: conic-gradient(from 0deg, #4facfe, #00f2fe, #667eea, #764ba2, #f093fb, #4facfe);
  opacity:0; transition:opacity .8s; filter: blur(30px);
}}
#ring.on {{ opacity:.3; }}

/* ── TEXT ── */
#text {{
  position:fixed; z-index:10; bottom:180px; left:50%; transform:translateX(-50%);
  width:min(600px, 90vw); text-align:center; opacity:0; transition:opacity .5s;
}}
#text.on {{ opacity:1; }}
#text-content {{
  font-size:1rem; font-weight:400; line-height:1.6;
  color:rgba(255,255,255,.9); text-shadow:0 2px 12px rgba(0,0,0,.8);
}}

#status {{
  position:fixed; z-index:10; bottom:140px; left:50%; transform:translateX(-50%);
  font-size:.75rem; color:rgba(255,255,255,.5);
  letter-spacing:.08em; text-transform:uppercase; opacity:0; transition:opacity .5s;
}}
#status.on {{ opacity:1; }}

/* ── LOGO ── */
#logo {{
  position:fixed; top:24px; left:24px; z-index:10;
  font-size:1.1rem; font-weight:500; color:rgba(255,255,255,.7);
  opacity:0; transition:opacity .8s .3s;
}}
#logo.on {{ opacity:1; }}

/* ── CONTROLS ── */
#controls {{
  position:fixed; right:24px; top:50%; transform:translateY(-50%);
  z-index:10; display:flex; flex-direction:column; gap:16px;
  opacity:0; transition:opacity .8s .4s;
}}
#controls.on {{ opacity:1; }}
.ctrl-btn {{
  width:52px; height:52px; border-radius:50%;
  background:rgba(255,255,255,.08); border:1px solid rgba(255,255,255,.15);
  color:rgba(255,255,255,.7); font-size:1.3rem; cursor:pointer;
  display:flex; align-items:center; justify-content:center;
  backdrop-filter:blur(20px); transition:.2s;
}}
.ctrl-btn:hover {{
  background:rgba(255,255,255,.15); border-color:rgba(255,255,255,.3); color:#fff;
}}

/* ── GEAR BUTTON ── */
#gear {{
  position:fixed; top:24px; right:24px; z-index:10;
  width:44px; height:44px; border-radius:50%;
  background:rgba(255,255,255,.08); border:1px solid rgba(255,255,255,.15);
  color:rgba(255,255,255,.6); font-size:1.1rem; cursor:pointer;
  display:flex; align-items:center; justify-content:center;
  backdrop-filter:blur(20px); transition:.2s; opacity:0; transition:opacity .8s .5s;
}}
#gear.on {{ opacity:1; }}
#gear:hover {{ background:rgba(255,255,255,.15); color:#fff; }}

/* ── WAKE INDICATOR ── */
#wake-indicator {{
  position:fixed; bottom:24px; left:50%; transform:translateX(-50%);
  z-index:10; padding:6px 14px; border-radius:20px;
  background:rgba(79,172,254,.15); border:1px solid rgba(79,172,254,.3);
  font-size:.7rem; color:rgba(79,172,254,.9); letter-spacing:.05em;
  backdrop-filter:blur(10px); opacity:0; transition:opacity .5s;
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
  background: radial-gradient(circle at 30% 30%, #4facfe, #00f2fe, #667eea, #764ba2, #f093fb);
  box-shadow: 0 0 60px rgba(79,172,254,.6);
  animation: startPulse 2s ease-in-out infinite;
}}
@keyframes startPulse {{ 0%, 100% {{ transform:scale(1); opacity:.8; }} 50% {{ transform:scale(1.1); opacity:1; }} }}
.start-title {{ font-size:2rem; font-weight:300; letter-spacing:.15em; margin-top:20px; }}
.start-sub {{ font-size:.85rem; color:rgba(255,255,255,.4); max-width:300px; text-align:center; line-height:1.6; }}
#start-btn {{
  margin-top:16px; padding:14px 38px; border-radius:30px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color:#fff; border:none; font-size:.95rem; font-weight:500; cursor:pointer;
}}
#start-btn:hover {{ transform:scale(1.05); }}

/* ── SETTINGS PANEL ── */
#settings {{
  position:fixed; top:0; right:0; bottom:0; width:320px;
  background:rgba(8,8,8,.96); border-left:1px solid rgba(255,255,255,.06);
  z-index:200; transform:translateX(100%); transition:transform .3s;
  padding:24px; overflow-y:auto; backdrop-filter:blur(20px);
}}
#settings.open {{ transform:translateX(0); }}
.s-overlay {{ position:fixed; inset:0; background:rgba(0,0,0,.5); z-index:199; display:none; }}
.s-overlay.show {{ display:block; }}
.s-head {{
  font-size:1rem; font-weight:500; margin-bottom:20px;
  display:flex; justify-content:space-between; align-items:center;
}}
.s-close {{
  width:32px; height:32px; border-radius:50%;
  background:rgba(255,255,255,.06); border:none; color:#888;
  cursor:pointer; font-size:1rem; display:flex; align-items:center; justify-content:center;
}}
.s-close:hover {{ color:#fff; }}
.s-section {{ font-size:.65rem; color:#555; letter-spacing:.1em; text-transform:uppercase; margin:20px 0 8px; }}
.s-input {{
  width:100%; background:rgba(255,255,255,.05); border:1px solid rgba(255,255,255,.08);
  border-radius:10px; padding:10px 14px; color:#fff; font-size:.85rem; outline:none;
}}
.s-input:focus {{ border-color:rgba(138,180,248,.4); }}
select.s-input option {{ background:#111; }}
.s-btn {{
  width:100%; padding:10px; border-radius:12px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color:#fff; border:none; font-weight:500; font-size:.85rem; cursor:pointer; margin-top:10px;
}}
.s-btn:hover {{ opacity:.9; }}
textarea.s-input {{ resize:vertical; font-family:inherit; }}
.s-note {{ font-size:.7rem; color:#444; margin-top:5px; }}

#toast {{
  position:fixed; bottom:100px; left:50%; transform:translateX(-50%);
  background:rgba(0,0,0,.8); border:1px solid rgba(255,255,255,.15);
  border-radius:12px; padding:10px 20px; font-size:.8rem; color:#ccc;
  z-index:300; opacity:0; transition:opacity .3s; pointer-events:none; backdrop-filter:blur(20px);
}}
#toast.show {{ opacity:1; }}
</style>
</head>
<body>

<video id="vid" autoplay playsinline muted></video>

<!-- ══ START ══ -->
<div id="start">
  <div class="start-orb"></div>
  <div class="start-title">FRIDAY</div>
  <div class="start-sub">▶ Press Start → allow camera<br>Say "Friday" to activate • Auto-sleep after 10s</div>
  <button id="start-btn" onclick="launch()">▶ &nbsp; Start</button>
</div>

<!-- ══ MAIN ══ -->
<div id="ring"></div>
<div id="orb"></div>

<div id="logo">FRIDAY</div>
<button id="gear" onclick="openSettings()">⚙</button>
<div id="wake-indicator">🔴 LISTENING FOR "FRIDAY"</div>

<div id="text"><div id="text-content"></div></div>
<div id="status">Ready</div>

<div id="controls">
  <button class="ctrl-btn" onclick="snapAndAnalyse()" title="Capture">📸</button>
  <button class="ctrl-btn" onclick="flipCam()" title="Flip">🔄</button>
  <button class="ctrl-btn" onclick="toggleMute()" title="Mute" id="mute-btn">🔊</button>
</div>

<!-- ══ SETTINGS ══ -->
<div class="s-overlay" id="s-overlay" onclick="closeSettings()"></div>
<div id="settings">
  <div class="s-head">
    <span>Settings</span>
    <button class="s-close" onclick="closeSettings()">✕</button>
  </div>

  <div class="s-section">Chat Model</div>
  <select class="s-input" id="s-model">
    <option value="llama-3.3-70b-versatile">Llama 3.3 70B (best)</option>
    <option value="llama-3.1-8b-instant">Llama 3.1 8B (fast)</option>
    <option value="mixtral-8x7b-32768">Mixtral 8x7B</option>
  </select>

  <div class="s-section">Vision Model</div>
  <select class="s-input" id="s-vision">
    <option value="meta-llama/llama-4-scout-17b-16e-instruct">Llama 4 Scout</option>
    <option value="llama-3.2-11b-vision-preview">Llama 3.2 11B</option>
  </select>

  <div class="s-section">Friday's Voice</div>
  <select class="s-input" id="s-voice">
    <option value="en-IN-NeerjaNeural">🇮🇳 Indian - Neerja</option>
    <option value="en-IN-PrabhatNeural">🇮🇳 Indian - Prabhat</option>
    <option value="en-US-JennyNeural">🇺🇸 US - Jenny</option>
    <option value="en-US-GuyNeural">🇺🇸 US - Guy</option>
    <option value="en-GB-SoniaNeural">🇬🇧 UK - Sonia</option>
    <option value="hi-IN-SwaraNeural">🇮🇳 Hindi - Swara</option>
  </select>

  <div class="s-section">Friday's Personality</div>
  <textarea class="s-input" id="s-prompt" rows="5">{CONFIG['system_prompt']}</textarea>
  <div class="s-note">How Friday behaves and responds</div>

  <button class="s-btn" onclick="saveSettings()">Save Settings</button>

  <div class="s-section" style="margin-top:30px;">Admin Panel</div>
  <div class="s-note">For full control (API keys, theme, knowledge base):<br>streamlit run friday_admin.py --server.port 8503</div>
</div>

<div id="toast"></div>

<script>
const CONFIG = {{
  apiKey: "{CONFIG['groq_api_key']}",
  chatModel: "{CONFIG['chat_model']}",
  visionModel: "{CONFIG['vision_model']}",
  voice: "{CONFIG['tts_voice']}",
  prompt: `{CONFIG['system_prompt']}`,
  maxTokens: {CONFIG['max_tokens']},
  temperature: {CONFIG['temperature']},
  knowledge: `{KNOWLEDGE_CONTEXT.replace('`', '').replace(chr(10), ' ')[:2000]}`
}};

const STATE = {{
  history: [], camAnalysis: "", active: false, speaking: false, muted: false,
  silenceTimer: null, lastInteraction: Date.now(),
  wakeRecog: null, talkRecog: null, stream: null, facing: "environment"
}};

async function launch() {{
  try {{
    STATE.stream = await navigator.mediaDevices.getUserMedia({{
      video: {{ facingMode: STATE.facing, width:{{ideal:1280}}, height:{{ideal:720}} }}, audio: false
    }});
    document.getElementById("vid").srcObject = STATE.stream;
    document.getElementById("vid").classList.add("on");

    document.getElementById("start").classList.add("hide");
    
    setTimeout(() => {{
      ["orb","ring","logo","controls","status","wake-indicator","gear"].forEach(id => 
        document.getElementById(id).classList.add("on")
      );
      startWakeWordListener();
      toast("Say 'Friday' to activate");
    }}, 500);
  }} catch(e) {{
    document.getElementById("start-btn").textContent = "Camera denied - check permissions";
  }}
}}

function startWakeWordListener() {{
  const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (!SR) return;

  STATE.wakeRecog = new SR();
  STATE.wakeRecog.continuous = true;
  STATE.wakeRecog.interimResults = false;
  STATE.wakeRecog.lang = "en-US";

  STATE.wakeRecog.onresult = (e) => {{
    const text = e.results[e.results.length - 1][0].transcript.toLowerCase();
    if (text.includes("friday")) activate();
  }};

  STATE.wakeRecog.onerror = () => {{
    setTimeout(() => {{ if (!STATE.active) STATE.wakeRecog.start(); }}, 100);
  }};

  STATE.wakeRecog.onend = () => {{
    if (!STATE.active) setTimeout(() => STATE.wakeRecog.start(), 100);
  }};

  STATE.wakeRecog.start();
}}

function activate() {{
  if (STATE.active || STATE.speaking) return;
  if (STATE.wakeRecog) STATE.wakeRecog.stop();
  
  STATE.active = true;
  STATE.lastInteraction = Date.now();
  setStatus("listening");
  setText("Yes?");
  document.getElementById("wake-indicator").classList.remove("on");
  startConversationListener();
}}

function startConversationListener() {{
  const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (!SR) return;

  STATE.talkRecog = new SR();
  STATE.talkRecog.continuous = true;
  STATE.talkRecog.interimResults = false;
  STATE.talkRecog.lang = "en-US";

  STATE.talkRecog.onresult = (e) => {{
    const text = e.results[e.results.length - 1][0].transcript;
    STATE.lastInteraction = Date.now();
    clearTimeout(STATE.silenceTimer);
    setText(`"${{text}}"`);
    setStatus("thinking");
    callGroq(text);
  }};

  STATE.talkRecog.onerror = () => {{ checkSilence(); }};
  STATE.talkRecog.onend = () => {{
    if (STATE.active && !STATE.speaking) setTimeout(() => STATE.talkRecog.start(), 100);
  }};

  STATE.talkRecog.start();
  startSilenceCheck();
}}

function startSilenceCheck() {{
  STATE.silenceTimer = setInterval(() => {{
    if (!STATE.active) return;
    if (Date.now() - STATE.lastInteraction > 10000) deactivate();
  }}, 1000);
}}

function checkSilence() {{
  if (Date.now() - STATE.lastInteraction > 10000 && STATE.active) deactivate();
}}

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

async function callGroq(userText) {{
  const sys = CONFIG.prompt + "\\nTime: " + new Date().toLocaleString("en-US", {{hour:"2-digit",minute:"2-digit"}}) +
    (STATE.camAnalysis ? "\\n[Camera: " + STATE.camAnalysis.slice(0,200) + "]" : "") +
    (CONFIG.knowledge ? "\\n[Knowledge: " + CONFIG.knowledge.slice(0,500) + "]" : "");

  const messages = [{{ role:"system", content: sys }}, ...STATE.history.slice(-8), {{ role:"user", content: userText }}];

  try {{
    const res = await fetch("https://api.groq.com/openai/v1/chat/completions", {{
      method: "POST",
      headers: {{ "Content-Type": "application/json", "Authorization": "Bearer " + CONFIG.apiKey }},
      body: JSON.stringify({{
        model: CONFIG.chatModel, messages: messages,
        max_tokens: CONFIG.maxTokens, temperature: CONFIG.temperature
      }})
    }});

    if (!res.ok) throw new Error("API error");

    const data = await res.json();
    const reply = data.choices[0].message.content.trim();

    STATE.history.push({{ role:"user", content: userText }}, {{ role:"assistant", content: reply }});
    if (STATE.history.length > 20) STATE.history = STATE.history.slice(-20);

    speak(reply);
  }} catch(e) {{
    speak("Network error, Boss.");
  }}
}}

function snapAndAnalyse() {{
  if (!STATE.stream) return;
  const c = document.createElement("canvas");
  const vid = document.getElementById("vid");
  c.width = vid.videoWidth || 640;
  c.height = vid.videoHeight || 480;
  c.getContext("2d").drawImage(vid, 0, 0);
  const b64 = c.toDataURL("image/jpeg", .85).split(",")[1];
  
  setStatus("analyzing");
  setText("Let me see...");
  callGroqVision(b64);
}}

async function callGroqVision(b64) {{
  try {{
    const res = await fetch("https://api.groq.com/openai/v1/chat/completions", {{
      method: "POST",
      headers: {{ "Content-Type":"application/json", "Authorization":"Bearer " + CONFIG.apiKey }},
      body: JSON.stringify({{
        model: CONFIG.visionModel,
        messages: [{{ role: "user", content: [
          {{ type:"image_url", image_url:{{ url:"data:image/jpeg;base64," + b64 }} }},
          {{ type:"text", text: "In 2-3 sentences: what do you see? Any issues? Recommendations?" }}
        ]}}],
        max_tokens: 200
      }})
    }});

    if (!res.ok) throw new Error("Vision error");
    const data = await res.json();
    const result = data.choices[0].message.content.trim();
    STATE.camAnalysis = result;
    speak(result);
  }} catch(e) {{
    speak("Couldn't analyze the image.");
  }}
}}

async function flipCam() {{
  STATE.facing = STATE.facing === "environment" ? "user" : "environment";
  if (STATE.stream) STATE.stream.getTracks().forEach(t => t.stop());
  try {{
    STATE.stream = await navigator.mediaDevices.getUserMedia({{ video: {{ facingMode: STATE.facing }}, audio: false }});
    document.getElementById("vid").srcObject = STATE.stream;
  }} catch(e) {{ toast("Couldn't switch camera"); }}
}}

function speak(text) {{
  if (STATE.muted) {{ setText(text); STATE.lastInteraction = Date.now(); return; }}

  setText(text);
  setStatus("speaking");
  STATE.speaking = true;
  STATE.lastInteraction = Date.now();

  speechSynthesis.cancel();
  const utt = new SpeechSynthesisUtterance(text);
  utt.rate = 1.05; utt.pitch = 0.95; utt.lang = "en-IN";

  const voices = speechSynthesis.getVoices();
  const pick = voices.find(v => v.name.includes("Google") || v.name.includes("Neerja")) || voices[0];
  if (pick) utt.voice = pick;

  utt.onend = () => {{
    STATE.speaking = false;
    STATE.lastInteraction = Date.now();
    if (STATE.active) {{ setStatus("listening"); setText(""); }}
  }};

  utt.onerror = () => {{ STATE.speaking = false; setStatus("listening"); }};
  speechSynthesis.speak(utt);
}}

function setStatus(state) {{
  const orb = document.getElementById("orb");
  const status = document.getElementById("status");
  orb.className = state === "listening" ? "on listening" : 
                  state === "thinking" ? "on thinking" : 
                  state === "speaking" ? "on speaking" : "on";
  const labels = {{ listening: "Listening...", thinking: "Thinking...", speaking: "Speaking...", analyzing: "Analyzing...", sleeping: "Sleeping..." }};
  status.textContent = labels[state] || "Ready";
}}

function setText(text) {{
  document.getElementById("text-content").textContent = text;
  document.getElementById("text").classList.toggle("on", !!text);
  document.getElementById("status").classList.toggle("on", !!text);
}}

function toast(msg, duration=2500) {{
  const el = document.getElementById("toast");
  el.textContent = msg;
  el.classList.add("show");
  setTimeout(() => el.classList.remove("show"), duration);
}}

function toggleMute() {{
  STATE.muted = !STATE.muted;
  document.getElementById("mute-btn").textContent = STATE.muted ? "🔇" : "🔊";
  toast(STATE.muted ? "Muted" : "Unmuted");
}}

function openSettings() {{
  document.getElementById("s-model").value = CONFIG.chatModel;
  document.getElementById("s-vision").value = CONFIG.visionModel;
  document.getElementById("s-voice").value = CONFIG.voice;
  document.getElementById("s-prompt").value = CONFIG.prompt;
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
  closeSettings();
  toast("Settings saved ✓");
}}

speechSynthesis.onvoiceschanged = () => {{ speechSynthesis.getVoices(); }};
</script>
</body>
</html>
"""

st.components.v1.html(HTML, height=800, scrolling=False)
