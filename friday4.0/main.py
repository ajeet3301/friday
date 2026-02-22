"""
FRIDAY LIVE  v9.0 — Full Screen Camera + Gemini Orb + Wake Word
Say "Friday" to activate | Camera always on behind everything
Run: streamlit run friday_live.py
"""

import os, json
import streamlit as st
from dotenv import load_dotenv
load_dotenv()

def load_config(file, default):
    if os.path.exists(file):
        with open(file, "r") as f:
            return {**default, **json.load(f)}
    return default.copy()

CONFIG = load_config("friday_config.json", {
    "groq_api_key": os.getenv("GROQ_API_KEY", ""),
    "chat_model":   "llama-3.3-70b-versatile",
    "vision_model": "meta-llama/llama-4-scout-17b-16e-instruct",
    "system_prompt": "You are Friday, a real-time AI voice assistant like JARVIS. Speak in 1-3 short natural sentences. Never use lists or bullets. Say Boss occasionally. Be sharp and concise.",
    "max_tokens":   180,
    "temperature":  0.75,
    "enable_rag":   True,
})

THEME = load_config("friday_theme.json", {
    "primary":   "#8ab4f8",
    "secondary": "#81c995",
    "orb_start": "#4facfe",
    "orb_mid":   "#667eea",
    "orb_end":   "#f093fb",
})

# Load knowledge base text files
KB_TEXT = ""
if CONFIG["enable_rag"] and os.path.exists("friday_knowledge/"):
    for f in os.listdir("friday_knowledge/")[:5]:
        if f.endswith((".txt", ".md")):
            try:
                with open(f"friday_knowledge/{f}", "r", encoding="utf-8") as fh:
                    KB_TEXT += fh.read()[:1500] + "\n"
            except: pass

st.set_page_config(page_title="Friday", page_icon="✦",
                   layout="wide", initial_sidebar_state="collapsed")

st.markdown("""<style>
* { margin:0; padding:0; }
html,body,[class*="css"] { background:#000!important; overflow:hidden; }
#MainMenu,footer,header,.stDeployButton { visibility:hidden; }
.block-container { padding:0!important; max-width:100%!important; }
iframe { border:none!important; display:block; }
</style>""", unsafe_allow_html=True)

if not CONFIG["groq_api_key"]:
    st.markdown("""
    <div style="display:flex;flex-direction:column;align-items:center;justify-content:center;
                height:100vh;background:#000;gap:16px;font-family:sans-serif;">
      <div style="font-size:2rem;color:#8ab4f8;">✦</div>
      <div style="font-size:1.2rem;color:#fff;">No API Key</div>
      <div style="font-size:.85rem;color:#666;text-align:center;max-width:300px;">
        Set GROQ_API_KEY in Streamlit secrets or run the Admin Panel:<br>
        <code style="color:#8ab4f8;">streamlit run friday_admin.py --server.port 8503</code>
      </div>
    </div>""", unsafe_allow_html=True)
    st.stop()

# Escape for JS
kb_safe     = KB_TEXT.replace("`","").replace("\\","\\\\").replace("\n"," ")[:2000]
prompt_safe = CONFIG["system_prompt"].replace("`","").replace("\\","\\\\").replace("\n"," ")

HTML = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1,maximum-scale=1">
<title>Friday</title>
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@200;300;400;500&display=swap');
*{{margin:0;padding:0;box-sizing:border-box;}}
html,body{{width:100vw;height:100vh;overflow:hidden;background:#000;
  font-family:'DM Sans',sans-serif;color:#fff;user-select:none;}}

/* ══ FULL SCREEN CAMERA — always behind everything ══ */
#cam-video{{
  position:fixed;inset:0;width:100%;height:100%;
  object-fit:cover;z-index:0;
  transition:filter .6s ease;
}}
#cam-video.dimmed{{ filter:brightness(.28) blur(1px); }}

/* ══ CAMERA OFF FALLBACK ══ */
#cam-off{{
  position:fixed;inset:0;z-index:0;
  background:radial-gradient(ellipse at 30% 40%, #1a1f3a 0%, #0a0a12 60%, #000 100%);
  display:flex;align-items:center;justify-content:center;
}}

/* ══ VIGNETTE ══ */
.vig{{
  position:fixed;inset:0;z-index:1;pointer-events:none;
  background:radial-gradient(ellipse at center, transparent 45%, rgba(0,0,0,.7) 100%);
}}
#grad-top{{position:fixed;top:0;left:0;right:0;height:180px;z-index:1;
  background:linear-gradient(to bottom,rgba(0,0,0,.75),transparent);pointer-events:none;}}
#grad-bot{{position:fixed;bottom:0;left:0;right:0;height:320px;z-index:1;
  background:linear-gradient(to top,rgba(0,0,0,.9) 0%,rgba(0,0,0,.5) 50%,transparent 100%);
  pointer-events:none;}}

/* ══ SCAN CORNERS (camera HUD) ══ */
.sc{{position:fixed;width:20px;height:20px;z-index:5;opacity:0;transition:opacity .5s;}}
.sc.on{{opacity:.4;}}
.sc-tl{{top:14px;left:14px;border-top:1.5px solid {THEME['primary']};border-left:1.5px solid {THEME['primary']};}}
.sc-tr{{top:14px;right:14px;border-top:1.5px solid {THEME['primary']};border-right:1.5px solid {THEME['primary']};}}
.sc-bl{{bottom:210px;left:14px;border-bottom:1.5px solid {THEME['primary']};border-left:1.5px solid {THEME['primary']};}}
.sc-br{{bottom:210px;right:14px;border-bottom:1.5px solid {THEME['primary']};border-right:1.5px solid {THEME['primary']};}}

/* ══ GEMINI ORB — floats over camera ══ */
#orb-wrap{{
  position:fixed;z-index:6;
  top:50%;left:50%;transform:translate(-50%,-60%);
  display:flex;align-items:center;justify-content:center;
  opacity:0;transition:opacity .8s;
}}
#orb-wrap.on{{opacity:1;}}
#orb-glow{{
  position:absolute;
  width:300px;height:300px;border-radius:50%;
  background:conic-gradient(from 0deg,{THEME['orb_start']},{THEME['orb_mid']},{THEME['orb_end']},{THEME['orb_start']});
  filter:blur(40px);opacity:.35;transition:opacity .5s;
}}
#orb{{
  width:220px;height:220px;border-radius:50%;position:relative;z-index:1;
  background:radial-gradient(circle at 32% 28%,
    {THEME['orb_start']} 0%,#00f2fe 20%,{THEME['orb_mid']} 50%,#764ba2 75%,{THEME['orb_end']} 100%);
  box-shadow:0 0 60px rgba(79,172,254,.5),0 0 100px rgba(102,126,234,.3);
  transition:all .4s;
}}
/* Orb states */
#orb.idle{{animation:orbFloat 4s ease-in-out infinite;}}
#orb.listening{{animation:orbPulse 1.1s ease-in-out infinite;
  box-shadow:0 0 90px rgba(242,139,130,.7),0 0 140px rgba(242,139,130,.4);
  background:radial-gradient(circle at 32% 28%,#ff6b6b,#f28b82,#ff4757,#c0392b,#e84393);}}
#orb.thinking{{animation:orbSpin 2.5s linear infinite;filter:blur(1px);
  box-shadow:0 0 80px rgba(138,180,248,.8);}}
#orb.speaking{{animation:orbMorph 1.2s ease-in-out infinite;
  box-shadow:0 0 80px rgba(129,201,149,.7),0 0 120px rgba(129,201,149,.3);
  background:radial-gradient(circle at 32% 28%,#00f2fe,{THEME['secondary']},#11998e,#38ef7d,#00b09b);}}
@keyframes orbFloat{{0%,100%{{transform:translateY(0) scale(1)}}50%{{transform:translateY(-12px) scale(1.02)}}}}
@keyframes orbPulse{{0%,100%{{transform:scale(1)}}50%{{transform:scale(1.12)}}}}
@keyframes orbSpin{{from{{filter:blur(1px) hue-rotate(0deg)}}to{{filter:blur(1px) hue-rotate(360deg)}}}}
@keyframes orbMorph{{
  0%,100%{{border-radius:50%}}
  25%{{border-radius:45% 55% 50% 50%}}
  50%{{border-radius:50% 50% 45% 55%}}
  75%{{border-radius:55% 45% 55% 45%}}
}}

/* ══ REPLY TEXT ══ */
#reply-area{{
  position:fixed;z-index:8;
  left:50%;transform:translateX(-50%);
  bottom:200px;
  width:min(600px,88vw);text-align:center;
  opacity:0;transition:opacity .4s;
}}
#reply-area.on{{opacity:1;}}
#reply-text{{
  font-size:1.05rem;font-weight:300;line-height:1.7;
  color:rgba(255,255,255,.95);
  text-shadow:0 2px 16px rgba(0,0,0,.9);
}}

/* ══ WAVEFORM (speaking) ══ */
#waveform{{
  display:flex;align-items:center;justify-content:center;
  gap:3px;height:26px;margin-top:10px;
  opacity:0;transition:opacity .3s;
}}
#waveform.on{{opacity:1;}}
.wb{{width:3px;border-radius:2px;background:{THEME['primary']};
  animation:wb .7s ease-in-out infinite;}}
.wb:nth-child(1){{height:4px; animation-delay:0s;}}
.wb:nth-child(2){{height:10px;animation-delay:.07s;}}
.wb:nth-child(3){{height:18px;animation-delay:.14s;}}
.wb:nth-child(4){{height:24px;animation-delay:.21s;}}
.wb:nth-child(5){{height:18px;animation-delay:.14s;}}
.wb:nth-child(6){{height:10px;animation-delay:.07s;}}
.wb:nth-child(7){{height:4px; animation-delay:0s;}}
@keyframes wb{{0%,100%{{transform:scaleY(1);opacity:.5}}50%{{transform:scaleY(1.6);opacity:1}}}}

/* ══ STATUS ══ */
#status{{
  position:fixed;z-index:8;
  bottom:165px;left:50%;transform:translateX(-50%);
  font-size:.7rem;color:rgba(255,255,255,.45);
  letter-spacing:.1em;text-transform:uppercase;
  opacity:0;transition:opacity .5s;white-space:nowrap;
}}
#status.on{{opacity:1;}}

/* ══ LOGO ══ */
#logo{{
  position:fixed;top:20px;left:20px;z-index:10;
  display:flex;align-items:center;gap:8px;
  opacity:0;transition:opacity .6s .3s;
}}
#logo.on{{opacity:1;}}
#logo-mark{{font-size:.9rem;color:{THEME['primary']};}}
#logo-name{{font-size:.82rem;font-weight:500;color:rgba(255,255,255,.8);letter-spacing:.08em;}}
#live-pill{{
  display:flex;align-items:center;gap:5px;
  padding:3px 9px;border-radius:12px;
  background:rgba(0,0,0,.45);border:1px solid rgba(255,255,255,.1);
  font-size:.6rem;color:rgba(255,255,255,.5);letter-spacing:.05em;
}}
#live-led{{width:6px;height:6px;border-radius:50%;
  background:{THEME['secondary']};box-shadow:0 0 6px {THEME['secondary']};
  animation:led 2s infinite;}}
@keyframes led{{0%,100%{{opacity:1}}50%{{opacity:.2}}}}

/* ══ WAKE INDICATOR ══ */
#wake-badge{{
  position:fixed;top:20px;right:66px;z-index:10;
  padding:5px 12px;border-radius:14px;
  background:rgba(0,0,0,.45);
  border:1px solid rgba(138,180,248,.2);
  font-size:.62rem;color:rgba(138,180,248,.7);
  letter-spacing:.06em;backdrop-filter:blur(10px);
  opacity:0;transition:opacity .5s;
}}
#wake-badge.on{{opacity:1;}}

/* ══ SETTINGS GEAR ══ */
#gear{{
  position:fixed;top:16px;right:16px;z-index:10;
  width:38px;height:38px;border-radius:50%;
  background:rgba(0,0,0,.4);border:1px solid rgba(255,255,255,.1);
  color:rgba(255,255,255,.5);font-size:.9rem;cursor:pointer;
  display:flex;align-items:center;justify-content:center;
  backdrop-filter:blur(12px);opacity:0;transition:opacity .5s .4s;
}}
#gear.on{{opacity:1;}}
#gear:hover{{background:rgba(255,255,255,.12);color:#fff;}}

/* ══ SIDE BUTTONS ══ */
#side-btns{{
  position:fixed;right:18px;z-index:10;
  top:50%;transform:translateY(-50%);
  display:flex;flex-direction:column;gap:12px;
  opacity:0;transition:opacity .5s .5s;
}}
#side-btns.on{{opacity:1;}}
.sBtn{{
  width:48px;height:48px;border-radius:50%;
  background:rgba(0,0,0,.45);border:1px solid rgba(255,255,255,.1);
  color:rgba(255,255,255,.6);font-size:1.05rem;cursor:pointer;
  display:flex;align-items:center;justify-content:center;
  backdrop-filter:blur(10px);transition:.2s;
}}
.sBtn:hover{{background:rgba(255,255,255,.1);color:#fff;border-color:rgba(255,255,255,.25);}}

/* ══ FLIP BTN (left side of camera) ══ */
#flip-btn{{
  position:fixed;left:18px;bottom:88px;z-index:10;
  width:44px;height:44px;border-radius:50%;
  background:rgba(0,0,0,.4);border:1px solid rgba(255,255,255,.09);
  color:rgba(255,255,255,.55);font-size:.95rem;cursor:pointer;
  display:flex;align-items:center;justify-content:center;
  backdrop-filter:blur(10px);
  opacity:0;transition:opacity .5s .5s;
}}
#flip-btn.on{{opacity:1;}}
#flip-btn:hover{{background:rgba(255,255,255,.1);color:#fff;}}

/* ══ STATUS CHIPS ══ */
#chips{{
  position:fixed;bottom:24px;left:50%;transform:translateX(-50%);
  z-index:9;display:flex;gap:6px;
  opacity:0;transition:opacity .5s .6s;
}}
#chips.on{{opacity:1;}}
.chip{{
  padding:4px 11px;border-radius:14px;
  background:rgba(0,0,0,.5);border:1px solid rgba(255,255,255,.07);
  font-size:.62rem;color:rgba(255,255,255,.35);
  letter-spacing:.05em;backdrop-filter:blur(8px);
}}

/* ══ FLASH ══ */
#flash{{
  position:fixed;inset:0;background:#fff;
  opacity:0;z-index:50;pointer-events:none;transition:opacity .08s;
}}

/* ══ START SCREEN ══ */
#start{{
  position:fixed;inset:0;z-index:100;background:#000;
  display:flex;flex-direction:column;align-items:center;justify-content:center;
  gap:16px;transition:opacity .7s;
}}
#start.hide{{opacity:0;pointer-events:none;}}
.st-orb{{
  width:140px;height:140px;border-radius:50%;
  background:radial-gradient(circle at 32% 28%,{THEME['orb_start']},#00f2fe,{THEME['orb_mid']},#764ba2,{THEME['orb_end']});
  box-shadow:0 0 60px rgba(79,172,254,.5);
  animation:orbFloat 3s ease-in-out infinite;
}}
.st-title{{font-size:1.8rem;font-weight:200;letter-spacing:.12em;color:rgba(255,255,255,.9);}}
.st-sub{{font-size:.82rem;color:rgba(255,255,255,.35);max-width:250px;text-align:center;line-height:1.65;}}
#startBtn{{
  margin-top:12px;padding:13px 40px;border-radius:30px;
  background:linear-gradient(135deg,{THEME['orb_mid']} 0%,#764ba2 100%);
  color:#fff;border:none;font-size:.9rem;font-weight:500;
  cursor:pointer;transition:.2s;letter-spacing:.03em;
  font-family:'DM Sans',sans-serif;
}}
#startBtn:hover{{transform:scale(1.04);opacity:.9;}}

/* ══ SETTINGS PANEL ══ */
#s-overlay{{
  position:fixed;inset:0;background:rgba(0,0,0,.5);
  z-index:198;display:none;backdrop-filter:blur(4px);
}}
#s-overlay.on{{display:block;}}
#settings{{
  position:fixed;top:0;right:0;bottom:0;width:290px;
  background:rgba(8,8,10,.97);border-left:1px solid rgba(255,255,255,.07);
  z-index:199;overflow-y:auto;padding:22px;
  transform:translateX(100%);transition:transform .3s cubic-bezier(.4,0,.2,1);
}}
#settings.on{{transform:translateX(0);}}
.sh{{font-size:.95rem;font-weight:500;margin-bottom:18px;
  display:flex;align-items:center;justify-content:space-between;color:#fff;}}
.sc-btn{{width:28px;height:28px;border-radius:50%;
  background:rgba(255,255,255,.07);border:none;color:#666;
  cursor:pointer;font-size:.85rem;display:flex;align-items:center;justify-content:center;}}
.sc-btn:hover{{color:#fff;}}
.sl{{font-size:.65rem;color:#444;letter-spacing:.1em;text-transform:uppercase;margin:14px 0 6px;}}
.si{{width:100%;background:rgba(255,255,255,.05);border:1px solid rgba(255,255,255,.08);
  border-radius:8px;padding:8px 11px;color:#fff;font-size:.82rem;
  font-family:'DM Sans',sans-serif;outline:none;}}
.si:focus{{border-color:rgba(138,180,248,.4);}}
select.si option{{background:#111;}}
.sb2{{width:100%;padding:9px;border-radius:10px;background:{THEME['primary']};
  color:#000;border:none;font-weight:600;font-size:.82rem;cursor:pointer;
  font-family:'DM Sans',sans-serif;transition:.15s;margin-top:8px;}}
.sb2:hover{{opacity:.88;}}
.ghost{{background:rgba(255,255,255,.06)!important;color:#777!important;
  border:1px solid rgba(255,255,255,.08)!important;font-weight:400!important;}}
.ghost:hover{{background:rgba(255,255,255,.12)!important;color:#fff!important;}}
hr.sd{{border:none;border-top:1px solid rgba(255,255,255,.05);margin:12px 0;}}

/* ══ TOAST ══ */
#toast{{
  position:fixed;bottom:120px;left:50%;transform:translateX(-50%);
  background:rgba(0,0,0,.75);border:1px solid rgba(255,255,255,.1);
  border-radius:12px;padding:9px 20px;font-size:.78rem;color:#ccc;
  z-index:300;opacity:0;transition:opacity .3s;pointer-events:none;
  backdrop-filter:blur(16px);white-space:nowrap;
}}
#toast.on{{opacity:1;}}
</style>
</head>
<body>

<!-- ══ FULL SCREEN CAMERA (z-index 0, always visible) ══ -->
<video id="cam-video" autoplay playsinline muted></video>
<div id="cam-off"></div>

<!-- ══ OVERLAYS ══ -->
<div class="vig"></div>
<div id="grad-top"></div>
<div id="grad-bot"></div>

<!-- ══ SCAN CORNERS ══ -->
<div class="sc sc-tl" id="c0"></div>
<div class="sc sc-tr" id="c1"></div>
<div class="sc sc-bl" id="c2"></div>
<div class="sc sc-br" id="c3"></div>

<!-- ══ FLASH ══ -->
<div id="flash"></div>

<!-- ══ ORB ══ -->
<div id="orb-wrap">
  <div id="orb-glow"></div>
  <div id="orb" class="idle"></div>
</div>

<!-- ══ TEXT & WAVE ══ -->
<div id="reply-area">
  <div id="reply-text"></div>
  <div id="waveform">
    <div class="wb"></div><div class="wb"></div><div class="wb"></div>
    <div class="wb"></div><div class="wb"></div><div class="wb"></div>
    <div class="wb"></div>
  </div>
</div>
<div id="status"></div>

<!-- ══ TOP BAR ══ -->
<div id="logo">
  <div id="logo-mark">✦</div>
  <div id="logo-name">FRIDAY</div>
  <div id="live-pill"><div id="live-led"></div>LIVE</div>
</div>
<div id="wake-badge">🔴 SAY "FRIDAY"</div>
<button id="gear" onclick="openS()">⚙</button>

<!-- ══ SIDE BUTTONS ══ -->
<div id="side-btns">
  <button class="sBtn" onclick="snapAndAsk()" title="Capture & analyse">📸</button>
  <button class="sBtn" onclick="toggleMute()" id="mute-btn" title="Mute">🔊</button>
</div>
<button id="flip-btn" onclick="flipCam()">🔄</button>

<!-- ══ STATUS CHIPS ══ -->
<div id="chips">
  <div class="chip" id="chip-cam">CAM OFF</div>
  <div class="chip" id="chip-voice">SAY "FRIDAY"</div>
</div>

<!-- ══ TOAST ══ -->
<div id="toast"></div>

<!-- ══ SETTINGS ══ -->
<div id="s-overlay" onclick="closeS()"></div>
<div id="settings">
  <div class="sh">
    <span>⚙ Settings</span>
    <button class="sc-btn" onclick="closeS()">✕</button>
  </div>

  <div class="sl">Groq API Key</div>
  <input class="si" id="s-key" type="password" placeholder="gsk_…" value="{CONFIG['groq_api_key']}">

  <hr class="sd">
  <div class="sl">Chat Model</div>
  <select class="si" id="s-model">
    <option value="llama-3.3-70b-versatile" {"selected" if CONFIG["chat_model"]=="llama-3.3-70b-versatile" else ""}>Llama 3.3 70B</option>
    <option value="llama-3.1-8b-instant"    {"selected" if CONFIG["chat_model"]=="llama-3.1-8b-instant"    else ""}>Llama 3.1 8B (fast)</option>
    <option value="mixtral-8x7b-32768"      {"selected" if CONFIG["chat_model"]=="mixtral-8x7b-32768"      else ""}>Mixtral 8x7B</option>
  </select>

  <div class="sl">Vision Model</div>
  <select class="si" id="s-vision">
    <option value="meta-llama/llama-4-scout-17b-16e-instruct">Llama 4 Scout</option>
    <option value="llama-3.2-11b-vision-preview">Llama 3.2 11B</option>
  </select>

  <hr class="sd">
  <div class="sl">Voice</div>
  <select class="si" id="s-voice">
    <option value="en-IN">Indian English</option>
    <option value="en-US">US English</option>
    <option value="en-GB">UK English</option>
    <option value="hi-IN">Hindi</option>
  </select>

  <hr class="sd">
  <div class="sl">Personality</div>
  <textarea class="si" id="s-prompt" rows="5" style="resize:vertical;">{CONFIG['system_prompt']}</textarea>

  <hr class="sd">
  <button class="sb2" onclick="saveS()">Save Settings</button>
  <button class="sb2 ghost" style="margin-top:6px;" onclick="clearH()">Clear History</button>
  <div style="font-size:.58rem;color:#333;text-align:center;margin-top:14px;">Friday v9.0</div>
</div>

<!-- ══ START SCREEN ══ -->
<div id="start">
  <div class="st-orb"></div>
  <div class="st-title">FRIDAY</div>
  <div class="st-sub">Full-screen camera · Say "Friday" to activate · Talks back</div>
  <button id="startBtn" onclick="boot()">▶ &nbsp;Start</button>
</div>

<script>
// ══════════════════════════════════
// CONFIG & STATE
// ══════════════════════════════════
const CFG = {{
  apiKey:      document.getElementById("s-key")?.value || "{CONFIG['groq_api_key']}",
  chatModel:   "{CONFIG['chat_model']}",
  visionModel: "{CONFIG['vision_model']}",
  prompt:      `{prompt_safe}`,
  maxTokens:   {CONFIG['max_tokens']},
  temperature: {CONFIG['temperature']},
  knowledge:   `{kb_safe}`,
  voiceLang:   "en-IN",
}};

const S = {{
  history:      [],
  camAnalysis:  "",
  active:       false,
  speaking:     false,
  muted:        false,
  stream:       null,
  facing:       "environment",
  wakeRecog:    null,
  talkRecog:    null,
  silenceTimer: null,
  lastTalk:     Date.now(),
  launched:     false,
}};

// ══════════════════════════════════
// BOOT — camera on first, then UI
// ══════════════════════════════════
async function boot() {{
  // 1. Start camera — full screen
  try {{
    S.stream = await navigator.mediaDevices.getUserMedia({{
      video: {{ facingMode: S.facing, width:{{ideal:1920}}, height:{{ideal:1080}} }},
      audio: false
    }});
    const vid = document.getElementById("cam-video");
    vid.srcObject = S.stream;
    vid.onloadedmetadata = () => vid.play();
    document.getElementById("cam-off").style.display = "none";
    document.getElementById("chip-cam").textContent = "CAM ON";
  }} catch(e) {{
    toast("Camera denied — mic only mode");
  }}

  // 2. Fade out start screen
  const start = document.getElementById("start");
  start.classList.add("hide");

  // 3. Show UI elements with staggered animation
  setTimeout(() => {{
    ["c0","c1","c2","c3"].forEach(id => document.getElementById(id).classList.add("on"));
    document.getElementById("orb-wrap").classList.add("on");
    document.getElementById("logo").classList.add("on");
    document.getElementById("gear").classList.add("on");
    document.getElementById("side-btns").classList.add("on");
    document.getElementById("flip-btn").classList.add("on");
    document.getElementById("chips").classList.add("on");
    document.getElementById("wake-badge").classList.add("on");
    S.launched = true;
  }}, 500);

  // 4. Dim camera slightly so orb pops
  setTimeout(() => {{
    document.getElementById("cam-video").classList.add("dimmed");
  }}, 600);

  // 5. Start wake word listener
  setTimeout(() => {{
    startWake();
    fridaySpeak("Friday online. Say my name to talk, Boss.");
  }}, 1000);
}}

// ══════════════════════════════════
// FLIP CAMERA
// ══════════════════════════════════
async function flipCam() {{
  S.facing = S.facing === "environment" ? "user" : "environment";
  if (S.stream) S.stream.getTracks().forEach(t => t.stop());
  try {{
    S.stream = await navigator.mediaDevices.getUserMedia({{
      video: {{ facingMode: S.facing }}, audio:false
    }});
    document.getElementById("cam-video").srcObject = S.stream;
  }} catch(e) {{ toast("Couldn't flip camera"); }}
}}

// ══════════════════════════════════
// WAKE WORD — always listening
// ══════════════════════════════════
function startWake() {{
  const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (!SR) {{ toast("Use Chrome for voice features"); return; }}

  S.wakeRecog = new SR();
  S.wakeRecog.lang = "en-US";
  S.wakeRecog.continuous = true;
  S.wakeRecog.interimResults = false;

  S.wakeRecog.onresult = e => {{
    const t = e.results[e.results.length-1][0].transcript.toLowerCase();
    if (t.includes("friday")) activate();
  }};
  S.wakeRecog.onerror = e => {{
    if (e.error === "no-speech") restart_wake();
  }};
  S.wakeRecog.onend = () => {{
    if (!S.active) restart_wake();
  }};
  S.wakeRecog.start();
}}

function restart_wake() {{
  if (!S.active) setTimeout(() => {{ try{{ S.wakeRecog.start(); }}catch(e){{}} }}, 200);
}}

// ══════════════════════════════════
// ACTIVATE after wake word
// ══════════════════════════════════
function activate() {{
  if (S.active || S.speaking) return;
  try{{ S.wakeRecog.stop(); }}catch(e){{}}
  S.active = true;
  S.lastTalk = Date.now();

  document.getElementById("wake-badge").classList.remove("on");
  document.getElementById("chip-voice").textContent = "LISTENING";
  setOrb("listening");
  setText("Yes?");
  setStatus("listening");

  setTimeout(startTalk, 300);
}}

// ══════════════════════════════════
// CONVERSATION LISTENER
// ══════════════════════════════════
function startTalk() {{
  const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (!SR) return;

  S.talkRecog = new SR();
  S.talkRecog.lang = "en-US";
  S.talkRecog.continuous = true;
  S.talkRecog.interimResults = false;

  S.talkRecog.onresult = e => {{
    const text = e.results[e.results.length-1][0].transcript;
    S.lastTalk = Date.now();
    clearTimeout(S.silenceTimer);
    setText('"' + text + '"');
    setOrb("thinking");
    setStatus("thinking");
    document.getElementById("chip-voice").textContent = "THINKING";
    callGroq(text);
  }};

  S.talkRecog.onerror = e => {{
    if (e.error !== "aborted") checkSilence();
  }};

  S.talkRecog.onend = () => {{
    if (S.active && !S.speaking)
      setTimeout(() => {{ try{{ S.talkRecog.start(); }}catch(e){{}} }}, 150);
  }};

  S.talkRecog.start();
  startSilenceWatch();
}}

function startSilenceWatch() {{
  S.silenceTimer = setInterval(() => {{
    if (!S.active) return;
    if (Date.now() - S.lastTalk > 12000) sleep();
  }}, 1000);
}}

function checkSilence() {{
  if (Date.now() - S.lastTalk > 12000 && S.active) sleep();
}}

function sleep() {{
  S.active = false;
  try{{ S.talkRecog.stop(); }}catch(e){{}}
  clearInterval(S.silenceTimer);

  setOrb("idle");
  setStatus("");
  setText("Say 'Friday' to wake me...");
  document.getElementById("chip-voice").textContent = "SAY \"FRIDAY\"";

  setTimeout(() => {{
    setText("");
    document.getElementById("wake-badge").classList.add("on");
    startWake();
  }}, 2500);
}}

// ══════════════════════════════════
// SNAPSHOT & VISION
// ══════════════════════════════════
function snapAndAsk() {{
  if (!S.stream) {{ toast("Camera not started"); return; }}
  const vid = document.getElementById("cam-video");
  const c = document.createElement("canvas");
  c.width = vid.videoWidth || 640;
  c.height = vid.videoHeight || 480;
  c.getContext("2d").drawImage(vid,0,0);

  const fl = document.getElementById("flash");
  fl.style.opacity = ".6";
  setTimeout(() => fl.style.opacity="0", 110);

  const b64 = c.toDataURL("image/jpeg",.85).split(",")[1];
  setOrb("thinking");
  setStatus("analyzing");
  setText("Analysing...");
  callVision(b64);
}}

async function callVision(b64) {{
  const key = document.getElementById("s-key").value || CFG.apiKey;
  try {{
    const res = await fetch("https://api.groq.com/openai/v1/chat/completions", {{
      method:"POST",
      headers:{{"Content-Type":"application/json","Authorization":"Bearer "+key}},
      body:JSON.stringify({{
        model: document.getElementById("s-vision").value || CFG.visionModel,
        messages:[{{role:"user",content:[
          {{type:"image_url",image_url:{{url:"data:image/jpeg;base64,"+b64}}}},
          {{type:"text",text:"In 2-3 sentences: what do you see? Any problems? Quick recommendation. No lists, just talk naturally."}}
        ]}}],
        max_tokens:200
      }})
    }});
    const d = await res.json();
    const result = d.choices[0].message.content.trim();
    S.camAnalysis = result;
    fridaySpeak(result);
  }} catch(e) {{
    fridaySpeak("Couldn't read the image, Boss.");
  }}
}}

// ══════════════════════════════════
// GROQ CHAT (direct from browser)
// ══════════════════════════════════
async function callGroq(text) {{
  const key = document.getElementById("s-key").value || CFG.apiKey;
  const sys = (document.getElementById("s-prompt")?.value || CFG.prompt) +
    "\\nTime: " + new Date().toLocaleTimeString("en-US",{{hour:"2-digit",minute:"2-digit"}}) +
    (S.camAnalysis ? "\\n[Camera shows: " + S.camAnalysis.slice(0,200) + "]" : "") +
    (CFG.knowledge ? "\\n[Knowledge: " + CFG.knowledge.slice(0,500) + "]" : "");

  const msgs = [
    {{role:"system", content:sys}},
    ...S.history.slice(-8),
    {{role:"user", content:text}}
  ];

  try {{
    const res = await fetch("https://api.groq.com/openai/v1/chat/completions", {{
      method:"POST",
      headers:{{"Content-Type":"application/json","Authorization":"Bearer "+key}},
      body:JSON.stringify({{
        model: document.getElementById("s-model").value || CFG.chatModel,
        messages: msgs,
        max_tokens: CFG.maxTokens,
        temperature: CFG.temperature
      }})
    }});
    if (!res.ok) {{
      const e = await res.json();
      fridaySpeak("API error: " + (e.error?.message || res.status));
      return;
    }}
    const d = await res.json();
    const reply = d.choices[0].message.content.trim();
    S.history.push({{role:"user",content:text}});
    S.history.push({{role:"assistant",content:reply}});
    if (S.history.length > 20) S.history = S.history.slice(-20);
    fridaySpeak(reply);
  }} catch(e) {{
    fridaySpeak("Network error, Boss.");
  }}
}}

// ══════════════════════════════════
// SPEAK (browser TTS)
// ══════════════════════════════════
function fridaySpeak(text) {{
  S.lastTalk = Date.now();
  setText(text);
  setOrb("speaking");
  setStatus("speaking");
  document.getElementById("waveform").classList.add("on");
  document.getElementById("chip-voice").textContent = "SPEAKING";

  if (S.muted) {{
    setTimeout(afterSpeak, 100);
    return;
  }}

  speechSynthesis.cancel();
  const u = new SpeechSynthesisUtterance(text);
  u.rate  = 1.05; u.pitch = 0.95; u.volume = 1;

  const lang = document.getElementById("s-voice")?.value || CFG.voiceLang;
  u.lang  = lang;

  const vv = speechSynthesis.getVoices();
  const pick = vv.find(v => v.name.includes("Google") && v.lang.startsWith(lang.split("-")[0]))
            || vv.find(v => v.lang === lang)
            || vv.find(v => v.lang.startsWith("en"))
            || vv[0];
  if (pick) u.voice = pick;

  S.speaking = true;
  u.onend = u.onerror = () => afterSpeak();
  speechSynthesis.speak(u);
}}

function afterSpeak() {{
  S.speaking = false;
  S.lastTalk  = Date.now();
  document.getElementById("waveform").classList.remove("on");
  if (S.active) {{
    setOrb("listening");
    setStatus("listening");
    setText("");
    document.getElementById("chip-voice").textContent = "LISTENING";
  }} else {{
    setOrb("idle");
    setStatus("");
  }}
}}

// ══════════════════════════════════
// UI HELPERS
// ══════════════════════════════════
function setOrb(state) {{
  const o = document.getElementById("orb");
  o.className = state;
}}

function setText(t) {{
  document.getElementById("reply-text").textContent = t;
  document.getElementById("reply-area").classList.toggle("on", !!t);
}}

function setStatus(t) {{
  const el = document.getElementById("status");
  el.textContent = t;
  el.classList.toggle("on", !!t);
}}

function toast(msg, ms=2500) {{
  const el = document.getElementById("toast");
  el.textContent = msg;
  el.classList.add("on");
  setTimeout(() => el.classList.remove("on"), ms);
}}

function toggleMute() {{
  S.muted = !S.muted;
  document.getElementById("mute-btn").textContent = S.muted ? "🔇" : "🔊";
  toast(S.muted ? "Muted" : "Unmuted");
}}

// ══════════════════════════════════
// SETTINGS PANEL
// ══════════════════════════════════
function openS()  {{ document.getElementById("settings").classList.add("on"); document.getElementById("s-overlay").classList.add("on"); }}
function closeS() {{ document.getElementById("settings").classList.remove("on"); document.getElementById("s-overlay").classList.remove("on"); }}
function saveS()  {{ closeS(); toast("Settings saved ✓"); }}
function clearH() {{ S.history=[]; S.camAnalysis=""; setText(""); closeS(); toast("History cleared"); }}

// Load voices
speechSynthesis.onvoiceschanged = () => speechSynthesis.getVoices();

// Space bar = snap
document.addEventListener("keydown", e => {{
  if (e.code === "Space" && !e.target.matches("input,textarea,select")) {{
    e.preventDefault(); snapAndAsk();
  }}
}});
</script>
</body>
</html>"""

st.components.v1.html(HTML, height=800, scrolling=False)
