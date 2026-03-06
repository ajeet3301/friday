"""
FRIDAY v13.1 — Upgraded RAG, Markdown Chat, Dynamic Voices
"""

import os, json
from dotenv import load_dotenv
load_dotenv()

import streamlit as st

def load_config(file, default):
    if os.path.exists(file):
        with open(file) as f: return json.load(f)
    return default

CONFIG = load_config("friday_config.json", {
    "groq_api_key": os.getenv("GROQ_API_KEY", ""),
    "chat_model": "llama-3.3-70b-versatile",
    "vision_model": "meta-llama/llama-4-scout-17b-16e-instruct",
    "system_prompt": "You are Friday, a real-time AI voice assistant. Understand English and Hindi/Hinglish. Be very concise. Use markdown for code and lists.",
    "tts_voice": "Google UK English Female", # Will be overridden by dynamic local voices
    "enable_rag": True,
    "max_tokens": 300,
    "temperature": 0.75
})

st.set_page_config(page_title="Friday", page_icon="✦", layout="wide", initial_sidebar_state="collapsed")
st.markdown("<style>*{margin:0;padding:0}html,body,[class*='css']{background:#000!important;overflow:hidden}#MainMenu,footer,header{visibility:hidden}.block-container{padding:0!important;max-width:100%!important}iframe{border:none!important}</style>", unsafe_allow_html=True)

if not CONFIG['groq_api_key']:
    st.error("❌ GROQ_API_KEY missing"); st.stop()

KNOWLEDGE_CONTEXT = ""
if CONFIG['enable_rag'] and os.path.exists("friday_knowledge/"):
    for f in [x for x in os.listdir("friday_knowledge/") if x.endswith(('.txt','.md'))][:5]:
        try:
            with open(f"friday_knowledge/{f}", encoding='utf-8') as fh:
                KNOWLEDGE_CONTEXT += f"\n[{f}]:\n{fh.read()[:2000]}"
        except: pass

safe_k = KNOWLEDGE_CONTEXT.replace('`',"'").replace('\\','\\\\').replace('\n','\\n')[:2500]
safe_p = CONFIG['system_prompt'].replace('`',"'").replace('\\','\\\\').replace('\n','\\n')

HTML = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<meta name="mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
<title>Friday</title>
<script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.min.js"></script>
<script>pdfjsLib.GlobalWorkerOptions.workerSrc = 'https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.worker.min.js';</script>

<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@300;400;500&family=Syne+Mono&display=swap');

:root{{
  --c-blue:#4facfe; --c-purple:#764ba2; --c-pink:#f093fb;
  --c-glass:rgba(255,255,255,.06); --c-border:rgba(255,255,255,.09);
  --safe-b:env(safe-area-inset-bottom,0px);
  --safe-t:env(safe-area-inset-top,0px);
  --bar-h:68px;
}}
*{{margin:0;padding:0;box-sizing:border-box;-webkit-tap-highlight-color:transparent}}
html,body{{
  width:100dvw;height:100dvh;overflow:hidden;
  background:#000;font-family:'Syne',sans-serif;color:#fff;
  user-select:none;-webkit-user-select:none;
}}
/* ── CAMERA ── */
#vid{{
  position:fixed;inset:0;width:100%;height:100%;object-fit:cover;
  opacity:0;transition:opacity 1.2s;
  filter:brightness(.55) saturate(1.1) contrast(1.05);
}}
#vid.on{{opacity:1}}
#vid.scan{{filter:brightness(.5) saturate(1.8) hue-rotate(15deg);transition:filter .35s}}
/* ── OVERLAYS ── */
.vig{{position:fixed;inset:0;z-index:1;pointer-events:none;
  background:radial-gradient(ellipse at 50% 60%,transparent 25%,rgba(0,0,0,.82) 100%)}}
.scanl{{position:fixed;inset:0;z-index:1;pointer-events:none;opacity:0;transition:opacity .3s;
  background:repeating-linear-gradient(0deg,transparent,transparent 2px,rgba(0,255,180,.012) 2px,rgba(0,255,180,.012) 4px)}}
.scanl.on{{opacity:1}}
.grad{{position:fixed;inset:0;z-index:1;pointer-events:none;
  background:linear-gradient(to bottom,rgba(0,0,0,.6) 0%,transparent 22%,transparent 62%,rgba(0,0,0,.95) 100%)}}

/* ══ ORB ══ */
#orb-wrap{{
  position:fixed;z-index:20;
  bottom:calc(var(--bar-h) + 36px + var(--safe-b));
  right:20px;
  width:72px;height:72px;
  opacity:0;transition:opacity .7s;
  cursor:pointer;touch-action:manipulation;
}}
#orb-wrap.on{{opacity:1}}
#orb-glow{{
  position:absolute;inset:-20px;border-radius:50%;
  background:radial-gradient(circle,rgba(79,172,254,.2),transparent 68%);
  opacity:0;transition:opacity .4s;
  animation:gP 3s ease-in-out infinite;
}}
#orb-wrap.listening #orb-glow,#orb-wrap.speaking #orb-glow{{opacity:1}}
@keyframes gP{{0%,100%{{transform:scale(1)}}50%{{transform:scale(1.2)}}}}
#orb{{
  position:absolute;inset:0;border-radius:50%;
  background:radial-gradient(circle at 30% 26%,rgba(220,240,255,.9) 0%,#4facfe 18%,#00c9ff 32%,#667eea 52%,#764ba2 70%,#f093fb 86%,#ff6fd8 100%);
  box-shadow:0 0 28px rgba(79,172,254,.45),0 0 56px rgba(102,126,234,.18),inset 0 0 20px rgba(255,255,255,.07);
  transition:box-shadow .35s;
}}
#orb-wrap.listening #orb{{animation:oP .95s ease-in-out infinite}}
#orb-wrap.thinking #orb{{animation:oS 2.2s linear infinite;filter:blur(.8px) brightness(1.2)}}
#orb-wrap.speaking #orb{{animation:oW .8s ease-in-out infinite}}
#orb-wrap.analyzing #orb{{animation:oA 1.6s ease-in-out infinite}}
#orb-wrap.idle #orb{{opacity:.3;filter:brightness(.5)}}
@keyframes oP{{0%,100%{{transform:scale(1)}}50%{{transform:scale(1.15);box-shadow:0 0 55px rgba(79,172,254,.8)}}}}
@keyframes oS{{from{{transform:rotate(0deg) scale(1.06)}}to{{transform:rotate(360deg) scale(1.06)}}}}
@keyframes oW{{0%,100%{{border-radius:50%;transform:scale(1)}}50%{{transform:scale(1.1)}}}}
@keyframes oA{{0%,100%{{transform:scale(1);box-shadow:0 0 28px rgba(0,200,255,.5)}}50%{{transform:scale(1.1);box-shadow:0 0 60px rgba(0,200,255,1)}}}}
#orb-wrap::after{{
  content:'';position:absolute;inset:0;border-radius:50%;
  border:1px solid rgba(255,255,255,.15);opacity:0;
}}
#orb-wrap.listening::after{{animation:rpl 1.8s ease-out infinite}}
@keyframes rpl{{0%{{opacity:.45;transform:scale(1)}}100%{{opacity:0;transform:scale(1.85)}}}}

/* ── HEADER ── */
#hdr{{
  position:fixed;top:0;left:0;right:0;z-index:10;
  padding:calc(var(--safe-t) + 14px) 16px 10px;
  display:flex;justify-content:space-between;align-items:center;
  opacity:0;transition:opacity .7s .3s;
}}
#hdr.on{{opacity:1}}
#logo{{
  font-family:'Syne Mono',monospace;font-size:.85rem;font-weight:400;
  letter-spacing:.28em;color:rgba(255,255,255,.7);
}}
#logo b{{color:var(--c-blue);font-weight:400}}
#hdr-btns{{display:flex;gap:6px}}
.hbtn{{
  width:36px;height:36px;border-radius:10px;
  background:rgba(0,0,0,.5);border:1px solid var(--c-border);
  color:rgba(255,255,255,.6);font-size:.82rem;cursor:pointer;
  display:flex;align-items:center;justify-content:center;
  backdrop-filter:blur(16px);transition:.18s;
  touch-action:manipulation;
}}
.hbtn:active{{transform:scale(.92);background:rgba(255,255,255,.12)}}
.hbtn.lit{{background:rgba(79,172,254,.18);border-color:rgba(79,172,254,.35);color:var(--c-blue)}}

/* ── CONV PANEL ── */
#conv{{
  position:fixed;z-index:10;
  top:calc(var(--safe-t) + 62px);
  left:0;right:0;
  bottom:calc(var(--bar-h) + var(--safe-b) + 8px);
  overflow-y:auto;overflow-x:hidden;
  display:flex;flex-direction:column;gap:7px;
  padding:8px 14px 12px;
  scrollbar-width:none;
  scroll-behavior: smooth;
}}
#conv::-webkit-scrollbar{{display:none}}
.msg{{
  max-width:85%;padding:10px 14px;border-radius:14px;
  font-size:.85rem;line-height:1.5;font-weight:300;
  animation:mIn .22s ease;backdrop-filter:blur(12px);
  word-wrap:break-word;
}}
/* Markdown Styles inside Messages */
.msg p {{ margin-bottom: 6px; }}
.msg p:last-child {{ margin-bottom: 0; }}
.msg pre {{ background: rgba(0,0,0,0.4); padding: 8px; border-radius: 6px; overflow-x: auto; margin: 6px 0; border: 1px solid rgba(255,255,255,0.1); font-family: 'Syne Mono', monospace; font-size: 0.75rem; }}
.msg code {{ background: rgba(0,0,0,0.3); padding: 2px 4px; border-radius: 4px; font-family: 'Syne Mono', monospace; font-size: 0.75rem; color: #f093fb; }}
.msg ul, .msg ol {{ margin-left: 20px; margin-bottom: 6px; }}
.msg strong {{ font-weight: 500; color: #4facfe; }}

@keyframes mIn{{from{{opacity:0;transform:translateY(5px)}}to{{opacity:1;transform:none}}}}
.msg.u{{
  align-self:flex-end;margin-left:auto;
  background:rgba(79,172,254,.15);border:1px solid rgba(79,172,254,.25);
  border-bottom-right-radius:3px;
}}
.msg.a{{
  align-self:flex-start;
  background:rgba(255,255,255,.07);border:1px solid var(--c-border);
  border-bottom-left-radius:3px;
}}
.msg.typing {{
  color: rgba(255,255,255,0.5); font-style: italic;
}}
.msg-meta{{
  display:flex;justify-content:space-between;align-items:center;
  margin-top:6px;gap:8px; border-top: 1px solid rgba(255,255,255,0.05); padding-top: 4px;
}}
.msg-t{{font-size:.55rem;color:rgba(255,255,255,.25);font-family:'Syne Mono'}}
.cpybtn{{
  font-size:.55rem;color:rgba(255,255,255,.2);
  background:none;border:none;cursor:pointer;padding:0;
  font-family:'Syne Mono';transition:color .2s;
  display:none;
}}
.msg.a:hover .cpybtn,.msg.a:focus-within .cpybtn{{display:block}}
.cpybtn:hover{{color:var(--c-blue)}}

/* ── STATUS DOT ── */
#sdot{{
  position:fixed;z-index:10;
  bottom:calc(var(--bar-h) + var(--safe-b) + 16px);
  left:20px;
  display:flex;align-items:center;gap:7px;
  opacity:0;transition:opacity .7s .4s;
}}
#sdot.on{{opacity:1}}
#dot{{
  width:6px;height:6px;border-radius:50%;
  background:rgba(255,255,255,.2);transition:all .3s;
}}
#dot.listening{{background:#4facfe;box-shadow:0 0 7px #4facfe;animation:db 1.1s ease-in-out infinite}}
#dot.speaking{{background:#f093fb;box-shadow:0 0 7px #f093fb;animation:db .7s ease-in-out infinite}}
#dot.thinking{{background:#667eea;box-shadow:0 0 7px #667eea;animation:db 1.8s ease-in-out infinite}}
#dot.analyzing{{background:#00c9ff;box-shadow:0 0 7px #00c9ff;animation:db .9s ease-in-out infinite}}
@keyframes db{{0%,100%{{opacity:1}}50%{{opacity:.2}}}}
#stxt{{font-size:.62rem;color:rgba(255,255,255,.35);letter-spacing:.06em;font-family:'Syne Mono'}}

/* ══ BOTTOM BAR ══ */
#bar{{
  position:fixed;z-index:20;
  bottom:0;left:0;right:0;
  height:calc(var(--bar-h) + var(--safe-b));
  padding:10px 12px calc(10px + var(--safe-b));
  display:flex;align-items:center;gap:8px;
  background:rgba(0,0,0,.7);
  border-top:1px solid var(--c-border);
  backdrop-filter:blur(24px) saturate(1.4);
  opacity:0;transition:opacity .7s .5s;
}}
#bar.on{{opacity:1}}

/* + RAG button */
#rag-btn{{
  width:44px;height:44px;border-radius:14px;flex-shrink:0;
  background:rgba(118,75,162,.15);border:1px solid rgba(118,75,162,.3);
  color:rgba(240,147,251,.7);font-size:1.2rem;cursor:pointer;
  display:flex;align-items:center;justify-content:center;
  transition:.18s;position:relative;touch-action:manipulation;
  font-weight:300;line-height:1;
}}
#rag-btn:active{{transform:scale(.9)}}
#rag-btn.has{{background:rgba(118,75,162,.3);border-color:rgba(240,147,251,.4);color:#f093fb}}
#rag-badge{{
  position:absolute;top:-4px;right:-4px;
  min-width:16px;height:16px;border-radius:8px;
  background:linear-gradient(135deg,#667eea,#764ba2);
  font-size:.5rem;display:none;align-items:center;justify-content:center;
  color:#fff;font-weight:500;padding:0 3px;
  border:1px solid rgba(0,0,0,.4);font-family:'Syne Mono';
}}
#rag-btn.has #rag-badge{{display:flex}}
#file-input{{display:none}}

/* text input */
#tinput{{
  flex:1;background:rgba(255,255,255,.05);
  border:1px solid var(--c-border);border-radius:14px;
  padding:11px 14px;color:#fff;font-size:.82rem;
  font-family:'Syne';font-weight:300;outline:none;
  resize:none;line-height:1.45;min-height:44px;max-height:88px;
  overflow-y:auto;transition:border-color .2s;
  scrollbar-width:none;
}}
#tinput:focus{{border-color:rgba(79,172,254,.35)}}
#tinput::placeholder{{color:rgba(255,255,255,.22)}}
#tinput::-webkit-scrollbar{{display:none}}

/* send */
#sbtn{{
  width:44px;height:44px;border-radius:14px;flex-shrink:0;
  background:linear-gradient(135deg,#4facfe,#667eea);
  border:none;color:#fff;cursor:pointer;font-size:1rem;
  display:flex;align-items:center;justify-content:center;
  box-shadow:0 3px 14px rgba(79,172,254,.28);
  transition:.18s;touch-action:manipulation;
}}
#sbtn:active{{transform:scale(.9)}}
#sbtn:disabled{{opacity:.3;cursor:not-allowed;transform:none}}

/* ── FILE PILLS ── */
#pills{{
  position:fixed;z-index:15;
  bottom:calc(var(--bar-h) + var(--safe-b) + 4px);
  left:12px;right:12px;
  display:flex;gap:5px;flex-wrap:wrap;
  opacity:0;pointer-events:none;transition:opacity .25s;
  max-height:56px;overflow:hidden;
}}
#pills.on{{opacity:1;pointer-events:all}}
.pill{{
  padding:3px 9px;border-radius:10px;
  background:rgba(118,75,162,.2);border:1px solid rgba(118,75,162,.28);
  font-size:.58rem;color:rgba(240,147,251,.75);
  display:flex;align-items:center;gap:4px;
  font-family:'Syne Mono';cursor:pointer;transition:.18s;
}}
.pill:active{{opacity:.6}}
.pill .x{{opacity:.4;font-size:.6rem}}

/* ── CHIPS ── */
#chips{{
  position:fixed;z-index:15;
  bottom:calc(var(--bar-h) + var(--safe-b) + 8px);
  left:0;right:0;
  display:flex;gap:6px;overflow-x:auto;
  padding:0 14px;
  scrollbar-width:none;pointer-events:none;
  opacity:0;transition:opacity .4s .8s;
}}
#chips::-webkit-scrollbar{{display:none}}
#chips.on{{opacity:1;pointer-events:all}}
.chip{{
  padding:5px 11px;border-radius:20px;white-space:nowrap;flex-shrink:0;
  background:rgba(0,0,0,.55);border:1px solid var(--c-border);
  font-size:.65rem;color:rgba(255,255,255,.5);cursor:pointer;
  backdrop-filter:blur(14px);transition:.18s;
  font-family:'Syne Mono';touch-action:manipulation;
}}
.chip:active{{background:rgba(79,172,254,.18);border-color:rgba(79,172,254,.35);color:rgba(79,172,254,.9)}}

/* ── SETTINGS DRAWER ── */
#sett{{
  position:fixed;bottom:0;left:0;right:0;
  max-height:80dvh;z-index:200;
  background:rgba(5,5,10,.97);
  border-top:1px solid var(--c-border);
  border-radius:20px 20px 0 0;
  padding:0 18px calc(20px + var(--safe-b));
  overflow-y:auto;
  transform:translateY(100%);transition:transform .3s cubic-bezier(.4,0,.2,1);
  backdrop-filter:blur(30px);
}}
#sett.open{{transform:translateY(0)}}
.sett-handle{{
  width:36px;height:4px;border-radius:2px;
  background:rgba(255,255,255,.15);margin:10px auto 18px;
}}
.s-ov{{position:fixed;inset:0;background:rgba(0,0,0,.5);z-index:199;display:none;backdrop-filter:blur(3px)}}
.s-ov.on{{display:block}}
.s-lbl{{font-size:.58rem;color:rgba(255,255,255,.3);letter-spacing:.1em;text-transform:uppercase;margin:14px 0 5px;font-family:'Syne Mono'}}
.s-in{{
  width:100%;background:rgba(255,255,255,.04);border:1px solid var(--c-border);
  border-radius:10px;padding:8px 11px;color:#fff;font-size:.78rem;outline:none;
  font-family:'Syne';
}}
.s-in:focus{{border-color:rgba(79,172,254,.35)}}
select.s-in option{{background:#08080f}}
.s-save{{
  width:100%;padding:11px;border-radius:12px;margin-top:14px;
  background:linear-gradient(135deg,#667eea,#764ba2);
  color:#fff;border:none;font-size:.82rem;cursor:pointer;
  font-family:'Syne';letter-spacing:.03em;font-weight:500;
}}

/* ── INIT ── */
#init{{
  position:fixed;inset:0;z-index:100;
  background:radial-gradient(ellipse at 40% 35%,#0a1022 0%,#040406 70%,#000 100%);
  display:flex;flex-direction:column;align-items:center;justify-content:center;
  transition:opacity .9s;
}}
#init.out{{opacity:0;pointer-events:none}}
.i-orb{{
  width:64px;height:64px;border-radius:50%;margin-bottom:22px;
  background:radial-gradient(circle at 30% 26%,rgba(220,240,255,.9) 0%,#4facfe 18%,#667eea 50%,#764ba2 70%,#f093fb 100%);
  animation:iP 2s ease-in-out infinite;
  box-shadow:0 0 32px rgba(79,172,254,.35),0 0 64px rgba(102,126,234,.12);
}}
@keyframes iP{{0%,100%{{transform:scale(1)}}50%{{transform:scale(1.09)}}}}
.i-name{{font-family:'Syne Mono';font-size:1.4rem;letter-spacing:.4em;color:rgba(255,255,255,.8);margin-bottom:5px}}
.i-ver{{font-size:.58rem;color:rgba(255,255,255,.22);letter-spacing:.15em;margin-bottom:22px;font-family:'Syne Mono'}}
.i-st{{font-size:.68rem;color:rgba(79,172,254,.55);letter-spacing:.07em;font-family:'Syne Mono';min-height:18px}}

/* ── TOAST ── */
#toast{{
  position:fixed;top:calc(var(--safe-t) + 56px);left:50%;transform:translateX(-50%);
  background:rgba(0,0,0,.88);border:1px solid var(--c-border);
  border-radius:10px;padding:7px 16px;font-size:.7rem;color:rgba(255,255,255,.8);
  z-index:300;opacity:0;transition:opacity .2s;pointer-events:none;
  backdrop-filter:blur(18px);max-width:80vw;text-align:center;
  font-family:'Syne Mono';white-space:nowrap;
}}
#toast.on{{opacity:1}}
</style>
</head>
<body>

<video id="vid" autoplay playsinline muted></video>
<div class="vig"></div>
<div class="scanl" id="scanl"></div>
<div class="grad"></div>

<div id="init">
  <div class="i-orb"></div>
  <div class="i-name">FRIDAY</div>
  <div class="i-ver">v13.1</div>
  <div class="i-st" id="ist">System Boot...</div>
</div>

<div id="hdr">
  <div id="logo">FRI<b>DAY</b></div>
  <div id="hdr-btns">
    <button class="hbtn" onclick="flipCam()" title="Flip">🔄</button>
    <button class="hbtn" id="mbtn" onclick="toggleMute()" title="Mute">🔊</button>
    <button class="hbtn" id="vbtn" onclick="toggleVoice()" title="Voice">🎙</button>
    <button class="hbtn" onclick="openSett()" title="Settings">⚙</button>
  </div>
</div>

<div id="conv"></div>

<div id="sdot">
  <div id="dot" class="idle"></div>
  <div id="stxt">—</div>
</div>

<div id="orb-wrap" onclick="manualActivate()">
  <div id="orb-glow"></div>
  <div id="orb"></div>
</div>

<div id="chips">
  <div class="chip" onclick="sendQ('Kya dekh raha hoon?')">👁 Kya hai</div>
  <div class="chip" onclick="sendQ('Summarize uploaded docs')">📎 Docs</div>
  <div class="chip" onclick="sendQ('Hindi mein batao')">🇮🇳 Hindi</div>
  
</div>

<div id="pills"></div>

<div id="bar">
  <button id="rag-btn" onclick="document.getElementById('fi').click()" title="Upload doc">
    +
    <div id="rag-badge">0</div>
  </button>
  
  <textarea id="tinput" placeholder="Message…" rows="1"
    oninput="resize(this)" onkeydown="onKey(event)"></textarea>
  <button id="sbtn" onclick="sendText()">↑</button>
</div>

<div class="s-ov" id="sov" onclick="closeSett()"></div>
<div id="sett">
  <div class="sett-handle"></div>
  <div class="s-lbl">Model</div>
  <select class="s-in" id="sm">
    <option value="llama-3.3-70b-versatile">Llama 3.3 70B</option>
    <option value="llama-3.1-8b-instant">Llama 3.1 8B (fast)</option>
    <option value="mixtral-8x7b-32768">Mixtral 8x7B</option>
  </select>
  <div class="s-lbl">Vision</div>
  <select class="s-in" id="sv">
    <option value="meta-llama/llama-4-scout-17b-16e-instruct">Llama 4 Scout</option>
    <option value="llama-3.2-11b-vision-preview">Llama 3.2 11B</option>
  </select>
  <div class="s-lbl">Voice (Dynamic)</div>
  <select class="s-in" id="svv">
    </select>
  <div class="s-lbl">Memory</div>
  <select class="s-in" id="smem">
    <option value="10">10 turns</option>
    <option value="20" selected>20 turns</option>
    <option value="50">50 turns</option>
    <option value="0">Full</option>
  </select>
  <div class="s-lbl">Persona</div>
  <textarea class="s-in" id="sprompt" rows="3">{CONFIG['system_prompt']}</textarea>
  <button class="s-save" onclick="saveSett()">Save</button>
</div>

<div id="toast"></div>

<script>
// ── Security & Config ──
const _k = "{CONFIG['groq_api_key']}";
Object.defineProperty(window,'__k',{{value:Object.freeze({{k:_k}}),writable:false,configurable:false}});
const _ol=console.log;
console.log=(...a)=>{{if(JSON.stringify(a).includes('gsk_'))return;_ol(...a)}};

const CFG = {{
  model:"{CONFIG['chat_model']}",
  vision:"{CONFIG['vision_model']}",
  voice:"{CONFIG['tts_voice']}",
  prompt:`{safe_p}`,
  maxTok:{CONFIG['max_tokens']},
  temp:{CONFIG['temperature']},
  kb:`{safe_k}`,
  mem:20
}};

const VT = ["what is this","what is that","what's this","what's that","see this","see that",
  "look at this","look here","identify","what am i looking at","can you see","show me",
  "kya hai","ye kya","yeh kya","kya hai ye","kya chal","dekh","dekho","batao kya","camera dekh"];

const S = {{
  hist:[],docs:[],camDesc:"",
  active:false,speaking:false,muted:false,voiceOn:true,
  silT:null,lastT:Date.now(),lastCap:0,
  wakeR:null,talkR:null,stream:null,facing:"environment"
}};

// ── INIT ──
window.addEventListener('load',()=>setTimeout(boot,300));
async function boot(){{
  ist("Requesting camera…");
  try{{
    S.stream=await navigator.mediaDevices.getUserMedia({{video:{{facingMode:S.facing,width:{{ideal:1920}},height:{{ideal:1080}}}},audio:false}});
    const v=document.getElementById("vid");v.srcObject=S.stream;v.classList.add("on");
    ist("Camera ready ✓");await sl(500);ist("Starting AI Engine…");await sl(500);
  }}catch(e){{ist("No camera — text only");await sl(800)}}
  ist("Ready");await sl(500);
  document.getElementById("init").classList.add("out");
  setTimeout(()=>{{
    document.getElementById("init").style.display="none";
    ["hdr","sdot","chips"].forEach(id=>document.getElementById(id).classList.add("on"));
    document.getElementById("orb-wrap").classList.add("on");
    document.getElementById("bar").classList.add("on");
    if(S.voiceOn) startWake();
    setS("idle");
    toast("Friday Online");
  }},850);
}}
function ist(t){{document.getElementById("ist").textContent=t}}
const sl=ms=>new Promise(r=>setTimeout(r,ms));

// ── DYNAMIC VOICE POPULATION ──
function loadVoices() {{
    const vs = speechSynthesis.getVoices();
    const sel = document.getElementById("svv");
    if (vs.length === 0 || sel.options.length > 0) return; 
    
    sel.innerHTML = ""; 
    vs.forEach(v => {{
        const opt = document.createElement("option");
        opt.value = v.name;
        opt.textContent = `${{v.name}} (${{v.lang}})`;
        sel.appendChild(opt);
    }});
    if(CFG.voice) sel.value = CFG.voice;
}}
speechSynthesis.onvoiceschanged = loadVoices;
setTimeout(loadVoices, 500);

// ── WAKE ──
function startWake(){{
  const SR=window.SpeechRecognition||window.webkitSpeechRecognition;
  if(!SR||!S.voiceOn)return;
  S.wakeR=new SR();S.wakeR.continuous=true;S.wakeR.interimResults=false;S.wakeR.lang="en-US";
  S.wakeR.onresult=e=>{{
    const t=e.results[e.results.length-1][0].transcript.toLowerCase();
    if(t.includes("friday"))activate();
  }};
  S.wakeR.onerror=()=>setTimeout(()=>{{if(!S.active)go(S.wakeR)}},200);
  S.wakeR.onend=()=>{{if(!S.active)setTimeout(()=>go(S.wakeR),150)}};
  go(S.wakeR);
}}
function go(r){{try{{r.start()}}catch(e){{}}}}

// ── ACTIVATE ──
function activate(){{
  if(S.active||S.speaking)return;
  try{{S.wakeR&&S.wakeR.stop()}}catch(e){{}}
  S.active=true;S.lastT=Date.now();
  setS("listening");
  startTalk();
}}
function manualActivate(){{
  if(S.active){{deactivate();return}}activate();
}}
function deactivate(){{
  S.active=false;
  try{{S.talkR&&S.talkR.stop()}}catch(e){{}}
  clearInterval(S.silT);setS("idle");
  setTimeout(()=>{{if(S.voiceOn)startWake()}},2000);
}}

// ── TALK ──
function startTalk(){{
  const SR=window.SpeechRecognition||window.webkitSpeechRecognition;
  if(!SR)return;
  S.talkR=new SR();S.talkR.continuous=true;S.talkR.interimResults=false;S.talkR.lang="en-US";
  S.talkR.onresult=e=>{{
    const t=e.results[e.results.length-1][0].transcript.trim();
    if(!t)return;
    S.lastT=Date.now();processIn(t);
  }};
  S.talkR.onerror=()=>chkSil();
  S.talkR.onend=()=>{{if(S.active&&!S.speaking)setTimeout(()=>go(S.talkR),100)}};
  go(S.talkR);
  S.silT=setInterval(()=>{{if(S.active&&Date.now()-S.lastT>14000)deactivate()}},1000);
}}
function chkSil(){{if(Date.now()-S.lastT>14000&&S.active)deactivate()}}

function processIn(text){{
  addMsg("u",text);
  const lo=text.toLowerCase();
  const vis=VT.some(t=>lo.includes(t));
  if(vis&&S.stream){{
    const now=Date.now();
    if(now-S.lastCap>2000){{S.lastCap=now;setS("analyzing");document.getElementById("scanl").classList.add("on");capture(text)}}
    else toast("Wait 2s");
  }}else{{setS("thinking");groq(text,false)}}
}}

// ── TEXT ──
function sendText(){{
  const el=document.getElementById("tinput"),t=el.value.trim();
  if(!t)return;
  el.value="";resize(el);
  document.getElementById("sbtn").disabled=true;
  if(!S.active){{S.active=true;S.lastT=Date.now()}}
  setS("thinking");processIn(t);
  setTimeout(()=>document.getElementById("sbtn").disabled=false,700);
}}
function sendQ(t){{
  document.getElementById("tinput").value=t;sendText();
}}
function onKey(e){{if(e.key==="Enter"&&!e.shiftKey){{e.preventDefault();sendText()}}}}
function resize(el){{el.style.height="auto";el.style.height=Math.min(el.scrollHeight,88)+"px"}}

// ── FILES (UPGRADED RAG) ──
async function loadFiles(inp){{
  for(const f of Array.from(inp.files)){{
    try{{
      let txt = f.name.endsWith(".pdf") ? await pdfTxt(f) : await f.text();
      S.docs.push({{n:f.name,c:txt.slice(0,8000)}});
      addPill(f.name,S.docs.length-1);toast("📎 "+f.name);
    }}catch{{toast("Failed: "+f.name)}}
  }}
  updateBadge();inp.value="";
}}

// ROBUST PDF PARSER USING PDF.JS
async function pdfTxt(f) {{
    return new Promise((resolve, reject) => {{
        const reader = new FileReader();
        reader.onload = async function() {{
            try {{
                const typedarray = new Uint8Array(this.result);
                const pdf = await pdfjsLib.getDocument(typedarray).promise;
                let fullText = "";
                for (let i = 1; i <= pdf.numPages; i++) {{
                    const page = await pdf.getPage(i);
                    const textContent = await page.getTextContent();
                    const pageText = textContent.items.map(item => item.str).join(" ");
                    fullText += pageText + "\\n";
                }}
                resolve(fullText || "[PDF - no text found]");
            }} catch (e) {{
                resolve("[PDF Parsing Error]");
            }}
        }};
        reader.readAsArrayBuffer(f);
    }});
}}

function addPill(name,i){{
  const p=document.createElement("div");
  p.className="pill";p.id="p"+i;
  p.innerHTML=`<span>📄 ${{name.length>16?name.slice(0,14)+"…":name}}</span><span class="x" onclick="rmFile(${{i}})">✕</span>`;
  document.getElementById("pills").appendChild(p);
  document.getElementById("pills").classList.add("on");
}}
function rmFile(i){{
  S.docs[i]=null;
  const p=document.getElementById("p"+i);if(p)p.remove();
  updateBadge();
  if(!S.docs.filter(Boolean).length)document.getElementById("pills").classList.remove("on");
}}
function updateBadge(){{
  const n=S.docs.filter(Boolean).length;
  const btn=document.getElementById("rag-btn");
  document.getElementById("rag-badge").textContent=n;
  btn.classList.toggle("has",n>0);
}}
function docCtx(){{
  const ds=S.docs.filter(Boolean);
  return ds.length?ds.map(d=>"["+d.n+"]:\\n"+d.c).join("\\n---\\n"):"";
}}

// ── VISION ──
async function capture(q){{
  if(!S.stream){{groq(q,false);return}}
  const v=document.getElementById("vid");v.classList.add("scan");
  const c=document.createElement("canvas");
  c.width=v.videoWidth||1280;c.height=v.videoHeight||720;
  c.getContext("2d").drawImage(v,0,0);
  const b=c.toDataURL("image/jpeg",.85).split(",")[1];
  const d=await groqVis(b);
  v.classList.remove("scan");document.getElementById("scanl").classList.remove("on");
  if(!d)return;S.camDesc=d;setS("thinking");groq(q,true);
}}
function manualCapture(){{
  if(!S.stream){{toast("No camera");return}}
  S.lastCap=Date.now();setS("analyzing");
  document.getElementById("scanl").classList.add("on");
  capture("Describe what you see.");
}}
async function groqVis(b64){{
  try{{
    const r=await fetch("https://api.groq.com/openai/v1/chat/completions",{{
      method:"POST",
      headers:{{"Content-Type":"application/json","Authorization":"Bearer "+window.__k.k}},
      body:JSON.stringify({{
        model:CFG.vision,
        messages:[{{role:"user",content:[
          {{type:"image_url",image_url:{{url:"data:image/jpeg;base64,"+b64}}}},
          {{type:"text",text:"Describe in 2-3 sentences: objects, text, conditions."}}
        ]}}],max_tokens:300
      }})
    }});
    if(!r.ok)throw Error(r.status);
    return (await r.json()).choices[0].message.content.trim();
  }}catch{{speak("Vision error.");return null}}
}}

// ── GROQ & TYPING INDICATOR ──
let typingDiv = null;

function showTyping() {{
    const p=document.getElementById("conv");
    typingDiv = document.createElement("div");
    typingDiv.className = "msg a typing";
    typingDiv.textContent = "typing...";
    p.appendChild(typingDiv);
    p.scrollTop=p.scrollHeight;
}}

function removeTyping() {{
    if(typingDiv) {{ typingDiv.remove(); typingDiv = null; }}
}}

async function groq(txt,vis){{
  showTyping();
  const ts=new Date().toLocaleString("en-US",{{hour:"2-digit",minute:"2-digit",weekday:"short",month:"short",day:"numeric"}});
  let sys=CFG.prompt+"\\n\\nTime: "+ts;
  if(vis&&S.camDesc)sys+="\\n\\n[CAMERA]: "+S.camDesc;
  if(CFG.kb)sys+="\\n\\n[KB]:\\n"+CFG.kb.slice(0,1000);
  const dc=docCtx();
  if(dc)sys+="\\n\\n[DOCS]:\\n"+dc.slice(0,5000);
  const lim=CFG.mem===0?S.hist.length:CFG.mem*2;
  const msgs=[{{role:"system",content:sys}},...S.hist.slice(-lim),{{role:"user",content:txt}}];
  
  try{{
    const r=await fetch("https://api.groq.com/openai/v1/chat/completions",{{
      method:"POST",
      headers:{{"Content-Type":"application/json","Authorization":"Bearer "+window.__k.k}},
      body:JSON.stringify({{model:CFG.model,messages:msgs,max_tokens:CFG.maxTok,temperature:CFG.temp,stream:false}})
    }});
    if(!r.ok)throw Error((await r.json().catch(()=>({{}}))).error?.message||r.status);
    const rep=(await r.json()).choices[0].message.content.trim();
    
    removeTyping();
    S.hist.push({{role:"user",content:txt}},{{role:"assistant",content:rep}});
    if(S.hist.length>200)S.hist=S.hist.slice(-200);
    speak(rep);
  }}catch(e){{
    removeTyping();
    addMsg("a","⚠ "+(e.message||"Error"));
    setS(S.active?"listening":"idle");
  }}
}}

// ── TTS (UPGRADED) ──
function speak(txt){{
  addMsg("a",txt);S.lastT=Date.now();
  if(S.muted){{setS(S.active?"listening":"idle");return}}
  setS("speaking");S.speaking=true;
  speechSynthesis.cancel();
  
  // Clean markdown syntax before speaking so it doesn't say "asterisk asterisk"
  const cleanTxt = txt.replace(/\\*\\*|__|`|#/g, '');
  const u=new SpeechSynthesisUtterance(cleanTxt);
  u.rate=1.05;u.pitch=.95;u.volume=1;
  
  const vs=speechSynthesis.getVoices();
  const pk = vs.find(v => v.name === CFG.voice) || vs.find(v => v.lang.startsWith("en-IN")) || vs[0];
  if(pk) u.voice=pk;
  
  u.onend=u.onerror=()=>{{S.speaking=false;setS(S.active?"listening":"idle")}};
  speechSynthesis.speak(u);
}}

// ── UI (MARKDOWN SUPPORT) ──
function addMsg(r,txt){{
  const p=document.getElementById("conv"),m=document.createElement("div");
  m.className="msg "+r;
  const t=new Date().toLocaleTimeString([],{{hour:"2-digit",minute:"2-digit"}});
  
  // Apply Markdown ONLY to assistant messages, escape user messages
  const content = r === "a" ? marked.parse(txt) : esc(txt);

  m.innerHTML=`<div class="msg-content">${{content}}</div>
    <div class="msg-meta">
      <span class="msg-t">${{t}}</span>
      ${{r==="a"?`<button class="cpybtn" onclick="cp(this)">copy</button>`:"" }}
    </div>`;
  p.appendChild(m);
  p.scrollTo({{ top: p.scrollHeight, behavior: 'smooth' }});
  const ms=p.querySelectorAll(".msg:not(.typing)");if(ms.length>30)ms[0].remove();
}}
function esc(s){{const d=document.createElement("div");d.textContent=s;return d.innerHTML}}
function cp(btn){{
  navigator.clipboard.writeText(btn.closest(".msg").querySelector(".msg-content").innerText)
    .then(()=>toast("Copied"));
}}
function clearConv(){{
  document.getElementById("conv").innerHTML="";S.hist=[];S.camDesc="";toast("Cleared");
}}

function setS(st){{
  const w=document.getElementById("orb-wrap");
  w.className="on "+(["listening","thinking","speaking","analyzing","idle"].includes(st)?st:"idle");
  document.getElementById("dot").className=st;
  const stl={{listening:"Sun raha hoon",thinking:"Soch raha hoon",speaking:"Bol raha hoon",analyzing:"Dekh raha hoon",idle:"—"}};
  document.getElementById("stxt").textContent=stl[st]||"—";
  document.getElementById("chips").classList.toggle("on",st==="idle");
}}

// ── CONTROLS ──
async function flipCam(){{
  S.facing=S.facing==="environment"?"user":"environment";
  if(S.stream)S.stream.getTracks().forEach(t=>t.stop());
  try{{
    S.stream=await navigator.mediaDevices.getUserMedia({{video:{{facingMode:S.facing}},audio:false}});
    document.getElementById("vid").srcObject=S.stream;toast("Flipped");
  }}catch{{toast("Failed")}}
}}
function toggleMute(){{
  S.muted=!S.muted;
  document.getElementById("mbtn").textContent=S.muted?"🔇":"🔊";
  toast(S.muted?"Muted":"Unmuted");
}}
function toggleVoice(){{
  S.voiceOn=!S.voiceOn;
  document.getElementById("vbtn").classList.toggle("lit",S.voiceOn);
  if(!S.voiceOn){{
    try{{S.wakeR&&S.wakeR.stop()}}catch(e){{}}
    if(S.active)deactivate();
    toast("Voice off");
  }}else{{startWake();toast("Voice on")}}
}}

// ── KEYBOARD ──
document.addEventListener("keydown",e=>{{
  if(!document.getElementById("init").classList.contains("out"))return;
  if(document.getElementById("sett").classList.contains("open"))return;
  if(document.activeElement===document.getElementById("tinput"))return;
  if(e.code==="Space"){{e.preventDefault();S.active?deactivate():activate()}}
  else if(e.code==="Escape"&&S.active)deactivate();
  else if(e.code==="KeyM")toggleMute();
  else if(e.code==="KeyV"&&S.stream)manualCapture();
  else if(e.code==="KeyC")clearConv();
}});

// ── SETTINGS ──
function openSett(){{
  document.getElementById("sm").value=CFG.model;
  document.getElementById("sv").value=CFG.vision;
  if(CFG.voice) document.getElementById("svv").value=CFG.voice;
  document.getElementById("smem").value=CFG.mem;
  document.getElementById("sprompt").value=CFG.prompt;
  document.getElementById("sett").classList.add("open");
  document.getElementById("sov").classList.add("on");
}}
function closeSett(){{
  document.getElementById("sett").classList.remove("open");
  document.getElementById("sov").classList.remove("on");
}}
function saveSett(){{
  CFG.model=document.getElementById("sm").value;
  CFG.vision=document.getElementById("sv").value;
  CFG.voice=document.getElementById("svv").value;
  CFG.mem=parseInt(document.getElementById("smem").value);
  CFG.prompt=document.getElementById("sprompt").value;
  closeSett();toast("Saved ✓");
}}

// ── TOAST ──
let _tt;
function toast(m,d=2400){{
  const e=document.getElementById("toast");e.textContent=m;e.classList.add("on");
  clearTimeout(_tt);_tt=setTimeout(()=>e.classList.remove("on"),d);
}}
</script>
</body>
</html>
"""

st.components.v1.html(HTML, height=900, scrolling=False)
