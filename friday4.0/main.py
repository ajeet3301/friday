"""
FRIDAY v10.1 - Full Screen Edition
- Full-screen camera background
- Smaller orb (180px)
- Hindi/Hinglish support (kya chal raha hai, etc.)
- Intent-based vision
- 20+ voices
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
    "system_prompt": "You are Friday, a real-time AI voice assistant. You understand both English and Hindi (written in Roman script/Hinglish).",
    "tts_voice": "en-IN-NeerjaNeural",
    "enable_rag": True,
    "max_tokens": 250,
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
    st.info("🔧 Admin: streamlit run friday_admin.py --server.port 8503")
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

HTML = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Friday</title>
<style>
* {{ margin:0; padding:0; box-sizing:border-box; }}
html,body {{ width:100vw; height:100vh; overflow:hidden; 
  background:#000; font-family:'Google Sans','Roboto',sans-serif; color:#fff; user-select:none; }}

/* ── FULL SCREEN CAMERA ── */
#vid {{
  position:fixed; inset:0; width:100%; height:100%; object-fit:cover;
  opacity:0; transition:opacity 1s; filter: brightness(.7);
}}
#vid.on {{ opacity:1; }}
#vid.analyzing {{ filter: brightness(.7) saturate(1.3); }}

/* ── VIGNETTE ── */
.vignette {{
  position:fixed; inset:0; z-index:1; pointer-events:none;
  background: radial-gradient(ellipse at center, transparent 40%, rgba(0,0,0,.7) 100%);
}}
.grad-overlay {{
  position:fixed; inset:0; z-index:1; pointer-events:none;
  background: linear-gradient(to bottom, rgba(0,0,0,.4) 0%, transparent 20%, transparent 80%, rgba(0,0,0,.6) 100%);
}}

/* ── SMALLER ORB (180px) ── */
#orb {{
  position:fixed; z-index:5; top:50%; left:50%; transform:translate(-50%, -50%);
  width:180px; height:180px; border-radius:50%;
  background: radial-gradient(circle at 30% 30%, #4facfe 0%, #00f2fe 25%, #667eea 50%, #764ba2 75%, #f093fb 100%);
  box-shadow: 0 0 60px rgba(79,172,254,.5), 0 0 100px rgba(102,126,234,.3);
  opacity:0; transition: all .8s;
}}
#orb.on {{ opacity:1; }}
#orb.listening {{ animation: orbPulse 1.2s ease-in-out infinite; }}
#orb.thinking {{ animation: orbRotate 3s linear infinite; filter: blur(2px); }}
#orb.speaking {{ animation: orbWave 1s ease-in-out infinite; }}
#orb.analyzing {{ animation: orbScan 2s ease-in-out infinite; filter: blur(1px); }}
@keyframes orbPulse {{ 0%, 100% {{ transform: translate(-50%, -50%) scale(1); }} 50% {{ transform: translate(-50%, -50%) scale(1.15); }} }}
@keyframes orbRotate {{ from {{ transform: translate(-50%, -50%) rotate(0deg); }} to {{ transform: translate(-50%, -50%) rotate(360deg); }} }}
@keyframes orbWave {{ 0%, 100% {{ border-radius: 50%; }} 25% {{ border-radius: 45% 55% 50% 50%; }} 50% {{ border-radius: 50% 50% 45% 55%; }} 75% {{ border-radius: 55% 45% 55% 45%; }} }}
@keyframes orbScan {{ 0%, 100% {{ transform: translate(-50%, -50%) scale(1); box-shadow: 0 0 60px rgba(79,172,254,.8); }} 50% {{ transform: translate(-50%, -50%) scale(1.1); box-shadow: 0 0 100px rgba(79,172,254,1); }} }}

#ring {{
  position:fixed; z-index:4; top:50%; left:50%; transform:translate(-50%, -50%);
  width:240px; height:240px; border-radius:50%;
  background: conic-gradient(from 0deg, #4facfe, #00f2fe, #667eea, #764ba2, #f093fb, #4facfe);
  opacity:0; transition:opacity .8s; filter: blur(25px);
}}
#ring.on {{ opacity:.25; }}

/* ── TEXT ── */
#text {{
  position:fixed; z-index:10; bottom:200px; left:50%; transform:translateX(-50%);
  width:min(700px, 90vw); text-align:center; opacity:0; transition:opacity .5s;
}}
#text.on {{ opacity:1; }}
#text-content {{ font-size:1.05rem; font-weight:400; line-height:1.7; color:rgba(255,255,255,.95); text-shadow:0 2px 16px rgba(0,0,0,.9); }}

#status {{
  position:fixed; z-index:10; bottom:160px; left:50%; transform:translateX(-50%);
  font-size:.75rem; color:rgba(255,255,255,.6); letter-spacing:.1em; text-transform:uppercase;
  opacity:0; transition:opacity .5s; text-shadow:0 2px 8px rgba(0,0,0,.8);
}}
#status.on {{ opacity:1; }}

/* ── LOGO ── */
#logo {{
  position:fixed; top:24px; left:24px; z-index:10; font-size:1.1rem; font-weight:500;
  color:rgba(255,255,255,.8); opacity:0; transition:opacity .8s .3s; text-shadow:0 2px 8px rgba(0,0,0,.6);
}}
#logo.on {{ opacity:1; }}

/* ── CONTROLS ── */
#controls {{
  position:fixed; right:24px; top:50%; transform:translateY(-50%); z-index:10;
  display:flex; flex-direction:column; gap:16px; opacity:0; transition:opacity .8s .4s;
}}
#controls.on {{ opacity:1; }}
.ctrl-btn {{
  width:52px; height:52px; border-radius:50%; background:rgba(0,0,0,.4); border:1.5px solid rgba(255,255,255,.2);
  color:rgba(255,255,255,.8); font-size:1.3rem; cursor:pointer; display:flex; align-items:center; justify-content:center;
  backdrop-filter:blur(20px); transition:.2s; box-shadow:0 4px 16px rgba(0,0,0,.4);
}}
.ctrl-btn:hover {{ background:rgba(255,255,255,.2); border-color:rgba(255,255,255,.4); color:#fff; transform:scale(1.05); }}

/* ── GEAR ── */
#gear {{
  position:fixed; top:24px; right:24px; z-index:10; width:44px; height:44px; border-radius:50%;
  background:rgba(0,0,0,.4); border:1.5px solid rgba(255,255,255,.2); color:rgba(255,255,255,.7);
  font-size:1.1rem; cursor:pointer; display:flex; align-items:center; justify-content:center;
  backdrop-filter:blur(20px); transition:.2s; opacity:0; transition:opacity .8s .5s;
  box-shadow:0 4px 16px rgba(0,0,0,.4);
}}
#gear.on {{ opacity:1; }}
#gear:hover {{ background:rgba(255,255,255,.2); color:#fff; }}

/* ── WAKE INDICATOR ── */
#wake-indicator {{
  position:fixed; bottom:24px; left:50%; transform:translateX(-50%); z-index:10;
  padding:8px 16px; border-radius:24px; background:rgba(79,172,254,.15); border:1.5px solid rgba(79,172,254,.4);
  font-size:.7rem; color:rgba(79,172,254,1); letter-spacing:.06em; backdrop-filter:blur(15px);
  opacity:0; transition:opacity .5s; box-shadow:0 4px 20px rgba(79,172,254,.3);
}}
#wake-indicator.on {{ opacity:1; }}

/* ── START ── */
#start {{
  position:fixed; inset:0; z-index:100; background:radial-gradient(ellipse at center, #1a1f3a 0%, #000 100%);
  display:flex; flex-direction:column; align-items:center; justify-content:center; gap:20px; transition:opacity .8s;
}}
#start.hide {{ opacity:0; pointer-events:none; }}
.start-orb {{
  width:140px; height:140px; border-radius:50%;
  background: radial-gradient(circle at 30% 30%, #4facfe, #00f2fe, #667eea, #764ba2, #f093fb);
  box-shadow: 0 0 50px rgba(79,172,254,.6); animation: startPulse 2s ease-in-out infinite;
}}
@keyframes startPulse {{ 0%, 100% {{ transform:scale(1); opacity:.8; }} 50% {{ transform:scale(1.08); opacity:1; }} }}
.start-title {{ font-size:2rem; font-weight:300; letter-spacing:.15em; margin-top:20px; }}
.start-sub {{ font-size:.85rem; color:rgba(255,255,255,.4); max-width:360px; text-align:center; line-height:1.6; }}
#start-btn {{
  margin-top:16px; padding:14px 40px; border-radius:30px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color:#fff; border:none; font-size:.95rem; font-weight:500; cursor:pointer; letter-spacing:.02em;
}}
#start-btn:hover {{ transform:scale(1.05); opacity:.95; }}

/* ── SETTINGS ── */
#settings {{
  position:fixed; top:0; right:0; bottom:0; width:340px; background:rgba(8,8,8,.97); border-left:1.5px solid rgba(255,255,255,.08);
  z-index:200; transform:translateX(100%); transition:transform .3s; padding:24px; overflow-y:auto; backdrop-filter:blur(20px);
}}
#settings.open {{ transform:translateX(0); }}
.s-overlay {{ position:fixed; inset:0; background:rgba(0,0,0,.7); z-index:199; display:none; backdrop-filter:blur(4px); }}
.s-overlay.show {{ display:block; }}
.s-head {{ font-size:1rem; font-weight:500; margin-bottom:20px; display:flex; justify-content:space-between; align-items:center; }}
.s-close {{
  width:32px; height:32px; border-radius:50%; background:rgba(255,255,255,.06); border:none; color:#888;
  cursor:pointer; font-size:1rem; display:flex; align-items:center; justify-content:center;
}}
.s-close:hover {{ color:#fff; background:rgba(255,255,255,.12); }}
.s-section {{ font-size:.65rem; color:#555; letter-spacing:.1em; text-transform:uppercase; margin:20px 0 8px; }}
.s-input {{
  width:100%; background:rgba(255,255,255,.05); border:1px solid rgba(255,255,255,.1);
  border-radius:10px; padding:10px 14px; color:#fff; font-size:.85rem; outline:none;
}}
.s-input:focus {{ border-color:rgba(138,180,248,.5); }}
select.s-input option {{ background:#111; }}
.s-btn {{
  width:100%; padding:11px; border-radius:12px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color:#fff; border:none; font-weight:500; font-size:.85rem; cursor:pointer; margin-top:10px;
}}
.s-btn:hover {{ opacity:.92; }}
textarea.s-input {{ resize:vertical; font-family:inherit; }}
.s-note {{ font-size:.7rem; color:#444; margin-top:5px; line-height:1.5; }}

#toast {{
  position:fixed; bottom:100px; left:50%; transform:translateX(-50%); background:rgba(0,0,0,.9); border:1.5px solid rgba(255,255,255,.15);
  border-radius:12px; padding:10px 20px; font-size:.8rem; color:#ddd; z-index:300; opacity:0; transition:opacity .3s;
  pointer-events:none; backdrop-filter:blur(20px); box-shadow:0 4px 20px rgba(0,0,0,.6);
}}
#toast.show {{ opacity:1; }}
</style>
</head>
<body>

<video id="vid" autoplay playsinline muted></video>
<div class="vignette"></div>
<div class="grad-overlay"></div>

<!-- ══ START ══ -->
<div id="start">
  <div class="start-orb"></div>
  <div class="start-title">FRIDAY</div>
  <div class="start-sub">Full-screen camera • Smaller orb<br>Say "Friday" → Talk in Hindi/Hinglish<br>"kya hai" → Auto-vision</div>
  <button id="start-btn" onclick="launch()">▶ &nbsp; Start</button>
</div>

<!-- ══ MAIN ══ -->
<div id="ring"></div>
<div id="orb"></div>
<div id="logo">FRIDAY</div>
<button id="gear" onclick="openSettings()">⚙</button>
<div id="wake-indicator">🔴 SAY "FRIDAY"</div>
<div id="text"><div id="text-content"></div></div>
<div id="status">Ready</div>

<div id="controls">
  <button class="ctrl-btn" onclick="manualCapture()" title="Capture">📸</button>
  <button class="ctrl-btn" onclick="flipCam()" title="Flip">🔄</button>
  <button class="ctrl-btn" onclick="toggleMute()" title="Mute" id="mute-btn">🔊</button>
</div>

<!-- ══ SETTINGS ══ -->
<div class="s-overlay" id="s-overlay" onclick="closeSettings()"></div>
<div id="settings">
  <div class="s-head"><span>Settings</span><button class="s-close" onclick="closeSettings()">✕</button></div>

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

  <div class="s-section">Voice (20+ Options)</div>
  <select class="s-input" id="s-voice">
    <optgroup label="🇮🇳 Indian">
      <option value="en-IN-NeerjaNeural">Neerja (Female)</option>
      <option value="en-IN-PrabhatNeural">Prabhat (Male)</option>
    </optgroup>
    <optgroup label="🇺🇸 US">
      <option value="en-US-JennyNeural">Jenny</option>
      <option value="en-US-GuyNeural">Guy</option>
      <option value="en-US-AriaNeural">Aria</option>
      <option value="en-US-AmberNeural">Amber</option>
    </optgroup>
    <optgroup label="🇬🇧 UK">
      <option value="en-GB-SoniaNeural">Sonia</option>
      <option value="en-GB-RyanNeural">Ryan</option>
    </optgroup>
    <optgroup label="🇮🇳 Hindi">
      <option value="hi-IN-SwaraNeural">Swara</option>
      <option value="hi-IN-MadhurNeural">Madhur</option>
    </optgroup>
  </select>

  <div class="s-section">Personality</div>
  <textarea class="s-input" id="s-prompt" rows="5">{CONFIG['system_prompt']}</textarea>

  <button class="s-btn" onclick="saveSettings()">Save Settings</button>
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
  knowledge: `{KNOWLEDGE_CONTEXT.replace('`', '').replace(chr(10), ' ')[:3000]}`
}};

// VISION TRIGGERS (English + Hindi/Hinglish)
const VISION_TRIGGERS = [
  // English
  "what is this", "what is that", "what's this", "what's that",
  "see this", "see that", "look at this", "look at that", "look here",
  "identify this", "identify that", "what am i looking at",
  "tell me what this is", "can you see this", "show me",
  
  // Hindi/Hinglish
  "kya hai", "ye kya hai", "yeh kya hai", "kya hai ye", "kya hai yeh",
  "yeh kya", "ye kya", "kya dikhai de raha",
  "dekh", "dekho", "dekh lo", "dekho ye", "dekho yeh", "dekh ye",
  "batao kya hai", "bata kya hai", "yeh dikhao",
  "isme kya hai", "is me kya hai",
  "kya chal raha hai", "kya ho raha hai"
];

const STATE = {{
  history: [], camAnalysis: "", active: false, speaking: false, muted: false,
  silenceTimer: null, lastInteraction: Date.now(), lastVisionCapture: 0,
  wakeRecog: null, talkRecog: null, stream: null, facing: "environment"
}};

async function launch() {{
  try {{
    STATE.stream = await navigator.mediaDevices.getUserMedia({{
      video: {{ facingMode: STATE.facing, width:{{ideal:1920}}, height:{{ideal:1080}} }}, audio: false
    }});
    document.getElementById("vid").srcObject = STATE.stream;
    document.getElementById("vid").classList.add("on");
    document.getElementById("start").classList.add("hide");
    
    setTimeout(() => {{
      ["orb","ring","logo","controls","status","wake-indicator","gear"].forEach(id => 
        document.getElementById(id).classList.add("on")
      );
      startWakeWordListener();
      toast("Full screen ready • Say 'Friday'");
    }}, 500);
  }} catch(e) {{
    document.getElementById("start-btn").textContent = "Camera denied";
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

  STATE.wakeRecog.onerror = () => {{ setTimeout(() => {{ if (!STATE.active) STATE.wakeRecog.start(); }}, 100); }};
  STATE.wakeRecog.onend = () => {{ if (!STATE.active) setTimeout(() => STATE.wakeRecog.start(), 100); }};
  STATE.wakeRecog.start();
}}

function activate() {{
  if (STATE.active || STATE.speaking) return;
  if (STATE.wakeRecog) STATE.wakeRecog.stop();
  STATE.active = true;
  STATE.lastInteraction = Date.now();
  setStatus("listening");
  setText("Haan bolo?");
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
    
    // CHECK VISION INTENT
    const lowerText = text.toLowerCase();
    const hasVisionIntent = VISION_TRIGGERS.some(trigger => lowerText.includes(trigger));
    
    if (hasVisionIntent) {{
      const now = Date.now();
      if (now - STATE.lastVisionCapture > 2000) {{
        STATE.lastVisionCapture = now;
        setStatus("analyzing");
        autoCapture(text);
      }} else {{
        toast("2 second wait");
        setStatus("listening");
      }}
    }} else {{
      setStatus("thinking");
      callGroq(text, false);
    }}
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
  setText("'Friday' bolo");
  setTimeout(() => {{
    setText("");
    document.getElementById("wake-indicator").classList.add("on");
    startWakeWordListener();
  }}, 2000);
}}

async function autoCapture(userQuery) {{
  if (!STATE.stream) {{ speak("Camera nahi hai"); return; }}
  
  const vid = document.getElementById("vid");
  vid.classList.add("analyzing");
  
  const c = document.createElement("canvas");
  c.width = vid.videoWidth || 1280;
  c.height = vid.videoHeight || 720;
  c.getContext("2d").drawImage(vid, 0, 0);
  const b64 = c.toDataURL("image/jpeg", .90).split(",")[1];
  
  const visionDesc = await callGroqVision(b64);
  vid.classList.remove("analyzing");
  
  if (!visionDesc) return;
  
  STATE.camAnalysis = visionDesc;
  setStatus("thinking");
  callGroq(userQuery, true);
}}

function manualCapture() {{
  if (!STATE.active) {{ toast("Pehle 'Friday' bolo"); return; }}
  STATE.lastVisionCapture = Date.now();
  setStatus("analyzing");
  autoCapture("Isme kya hai?");
}}

async function callGroqVision(b64) {{
  try {{
    const res = await fetch("https://api.groq.com/openai/v1/chat/completions", {{
      method: "POST",
      headers: {{ "Content-Type":"application/json", "Authorization":"Bearer " + CONFIG.apiKey }},
      body: JSON.stringify({{
        model: CONFIG.visionModel,
        messages: [{{
          role: "user",
          content: [
            {{ type:"image_url", image_url:{{ url:"data:image/jpeg;base64," + b64 }} }},
            {{ type:"text", text: "Describe what you see in this image in detail (2-3 sentences). Focus on objects, text, conditions, problems, and recommendations." }}
          ]
        }}],
        max_tokens: 300
      }})
    }});

    if (!res.ok) throw new Error("Vision error");
    const data = await res.json();
    return data.choices[0].message.content.trim();
  }} catch(e) {{
    speak("Vision kaam nahi kar raha");
    return null;
  }}
}}

async function callGroq(userText, includeVision) {{
  const sys = CONFIG.prompt + 
    "\\n\\nTime: " + new Date().toLocaleString("en-US", {{hour:"2-digit",minute:"2-digit",weekday:"long"}});
  
  let ctx = "";
  if (includeVision && STATE.camAnalysis) ctx += "\\n\\n[CAMERA]: " + STATE.camAnalysis;
  if (CONFIG.knowledge) ctx += "\\n\\n[KNOWLEDGE]: " + CONFIG.knowledge.slice(0, 900);
  
  const messages = [
    {{ role:"system", content: sys + ctx }},
    ...STATE.history.slice(-8),
    {{ role:"user", content: userText }}
  ];

  try {{
    const res = await fetch("https://api.groq.com/openai/v1/chat/completions", {{
      method: "POST",
      headers: {{ "Content-Type": "application/json", "Authorization": "Bearer " + CONFIG.apiKey }},
      body: JSON.stringify({{
        model: CONFIG.chatModel,
        messages: messages,
        max_tokens: CONFIG.maxTokens,
        temperature: CONFIG.temperature
      }})
    }});

    if (!res.ok) throw new Error("API error");
    const data = await res.json();
    const reply = data.choices[0].message.content.trim();

    STATE.history.push({{ role:"user", content: userText }}, {{ role:"assistant", content: reply }});
    if (STATE.history.length > 20) STATE.history = STATE.history.slice(-20);

    speak(reply);
  }} catch(e) {{
    speak("Network problem hai");
  }}
}}

async function flipCam() {{
  STATE.facing = STATE.facing === "environment" ? "user" : "environment";
  if (STATE.stream) STATE.stream.getTracks().forEach(t => t.stop());
  try {{
    STATE.stream = await navigator.mediaDevices.getUserMedia({{ video: {{ facingMode: STATE.facing }}, audio: false }});
    document.getElementById("vid").srcObject = STATE.stream;
  }} catch(e) {{ toast("Camera flip nahi hua"); }}
}}

function speak(text) {{
  if (STATE.muted) {{ setText(text); STATE.lastInteraction = Date.now(); return; }}

  setText(text);
  setStatus("speaking");
  STATE.speaking = true;
  STATE.lastInteraction = Date.now();

  speechSynthesis.cancel();
  const utt = new SpeechSynthesisUtterance(text);
  utt.rate = 1.05;
  utt.pitch = 0.95;
  utt.volume = 1;
  
  const voices = speechSynthesis.getVoices();
  const voiceName = CONFIG.voice.replace("Neural", "");
  const pick = voices.find(v => v.name.includes(voiceName)) || 
               voices.find(v => v.lang.startsWith("en-IN")) ||
               voices.find(v => v.lang.startsWith("hi-IN")) ||
               voices[0];
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
                  state === "speaking" ? "on speaking" :
                  state === "analyzing" ? "on analyzing" : "on";
  const labels = {{ listening: "Sun raha hoon...", thinking: "Soch raha hoon...", speaking: "Bol raha hoon...", analyzing: "Dekh raha hoon...", sleeping: "So gaya..." }};
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
  toast(STATE.muted ? "Mute hai" : "Unmute hai");
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
  toast("Settings save ho gayi");
}}

speechSynthesis.onvoiceschanged = () => {{ speechSynthesis.getVoices(); }};
setTimeout(() => speechSynthesis.getVoices(), 100);
</script>
</body>
</html>
"""

st.components.v1.html(HTML, height=800, scrolling=False)
