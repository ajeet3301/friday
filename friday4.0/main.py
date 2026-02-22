"""
FRIDAY AI  v6.0  — Voice + TTS + Always-on Camera
Run: streamlit run main.py
"""

import os, base64, asyncio
from datetime import datetime
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv
load_dotenv()

# ════════════════════════════════════════════════════════
# CONFIG  ← only edit this section
# ════════════════════════════════════════════════════════
GROQ_API_KEY  = os.getenv("GROQ_API_KEY", "")
GROQ_CHAT     = "llama-3.3-70b-versatile"
GROQ_VISION   = "meta-llama/llama-4-scout-17b-16e-instruct"
TTS_VOICE     = "en-IN-NeerjaNeural"   # Friday's voice
# Other voices: "en-US-JennyNeural"  "en-GB-SoniaNeural"  "en-US-GuyNeural"

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

FRIDAY_PROMPT = """You are Friday, an advanced AI assistant like JARVIS from Iron Man.
You can see through the camera in real time.
Be concise and helpful. Occasionally call the user "Boss".
For plants: name them, diagnose issues, give solutions.
For objects: identify and explain.
For problems: diagnose and fix.
Keep answers short unless asked for detail.
Current time: {time}"""

VISION_PROMPT = """Look at this image carefully.
1. What are the main objects or subjects?
2. Are there any problems, damage, or issues? (plant disease, broken things, etc.)
3. What are your practical recommendations?
Be specific. If it is a plant: name it, find the problem, suggest the fix."""

# ════════════════════════════════════════════════════════
# THEMES  ← add or edit here
# ════════════════════════════════════════════════════════
THEMES = {
    "Dark":     {"bg":"#0f0f0f","sf":"#1a1a1a","s2":"#252525","bd":"rgba(255,255,255,.07)","tx":"#e8eaed","mu":"#9aa0a6","ac":"#8ab4f8","ac2":"#81c995"},
    "Midnight": {"bg":"#050810","sf":"#0d1117","s2":"#161b22","bd":"rgba(48,54,61,.8)",    "tx":"#c9d1d9","mu":"#8b949e","ac":"#58a6ff","ac2":"#3fb950"},
    "Slate":    {"bg":"#0f172a","sf":"#1e293b","s2":"#334155","bd":"rgba(148,163,184,.1)", "tx":"#e2e8f0","mu":"#94a3b8","ac":"#818cf8","ac2":"#34d399"},
    "Amoled":   {"bg":"#000000","sf":"#0a0a0a","s2":"#111111","bd":"rgba(255,255,255,.05)","tx":"#ffffff","mu":"#555555","ac":"#00d4ff","ac2":"#00ff88"},
    "Forest":   {"bg":"#0a0f0a","sf":"#111811","s2":"#1a2a1a","bd":"rgba(74,222,128,.08)","tx":"#dcfce7","mu":"#86efac","ac":"#4ade80","ac2":"#a3e635"},
}

# ════════════════════════════════════════════════════════
# DIRS + PAGE
# ════════════════════════════════════════════════════════
Path("uploads").mkdir(exist_ok=True)
Path("knowledge_base").mkdir(exist_ok=True)

st.set_page_config(page_title="Friday", page_icon="✦",
                   layout="wide", initial_sidebar_state="collapsed")

# ════════════════════════════════════════════════════════
# OPTIONAL IMPORTS
# ════════════════════════════════════════════════════════
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

try:
    import edge_tts
    TTS_OK = True
except ImportError:
    TTS_OK = False

# ════════════════════════════════════════════════════════
# SESSION STATE
# ════════════════════════════════════════════════════════
def _init():
    for k, v in {
        "messages":      [],
        "vectorstore":   None,
        "kb_docs":       [],
        "groq_key":      GROQ_API_KEY,
        "chat_model":    GROQ_CHAT,
        "vision_model":  GROQ_VISION,
        "sys_prompt":    FRIDAY_PROMPT,
        "theme":         "Dark",
        "tts_on":        True,
        "cam_analysis":  "",
        "settings_open": False,
    }.items():
        if k not in st.session_state:
            st.session_state[k] = v

_init()

def T(k):
    return THEMES[st.session_state.theme][k]

# ════════════════════════════════════════════════════════
# CSS
# ════════════════════════════════════════════════════════
def inject_css():
    t = THEMES[st.session_state.theme]
    st.markdown(f"""<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;600&family=DM+Mono&display=swap');
:root{{--bg:{t['bg']};--sf:{t['sf']};--s2:{t['s2']};--bd:{t['bd']};
      --tx:{t['tx']};--mu:{t['mu']};--ac:{t['ac']};--ac2:{t['ac2']};
      --sans:'DM Sans',sans-serif;--mono:'DM Mono',monospace;}}
html,body,[class*="css"]{{font-family:var(--sans)!important;background:var(--bg)!important;color:var(--tx)!important;}}
*{{box-sizing:border-box;}}
#MainMenu,footer,header{{visibility:hidden;}}
.block-container{{padding:0!important;max-width:100%!important;}}
::-webkit-scrollbar{{width:3px;}}
::-webkit-scrollbar-thumb{{background:var(--bd);border-radius:2px;}}
.tb{{display:flex;align-items:center;justify-content:space-between;
  padding:11px 20px;background:var(--bg);border-bottom:1px solid var(--bd);position:sticky;top:0;z-index:100;}}
.tb-logo{{font-size:1rem;font-weight:600;color:var(--tx);display:flex;align-items:center;gap:8px;}}
.tb-star{{color:var(--ac);}}
.tb-r{{display:flex;align-items:center;gap:8px;}}
.spill{{display:inline-flex;align-items:center;gap:5px;padding:4px 11px;border-radius:20px;
  border:1px solid var(--bd);font-size:.7rem;color:var(--mu);background:var(--sf);}}
.sdot{{width:5px;height:5px;border-radius:50%;flex-shrink:0;}}
.sg{{background:var(--ac2);box-shadow:0 0 5px var(--ac2);animation:pp 2s infinite;}}
.sr{{background:#444;}}
.sb{{background:var(--ac);box-shadow:0 0 5px var(--ac);animation:pp 2s infinite;}}
@keyframes pp{{0%,100%{{opacity:1}}50%{{opacity:.3}}}}
.mu{{display:flex;justify-content:flex-end;margin:4px 0;}}
.ma{{display:flex;gap:9px;align-items:flex-start;margin:4px 0;}}
.av{{width:25px;height:25px;border-radius:50%;flex-shrink:0;margin-top:2px;
  display:flex;align-items:center;justify-content:center;
  font-size:.65rem;background:var(--s2);border:1px solid var(--bd);color:var(--ac);}}
.bu{{max-width:82%;padding:9px 13px;font-size:.83rem;line-height:1.65;border-radius:16px;}}
.bu-u{{background:var(--s2);border-radius:16px 4px 16px 16px;}}
.bu-a{{background:var(--sf);border-radius:4px 16px 16px 16px;}}
.bm{{font-size:.58rem;color:var(--mu);margin-top:3px;}}
.kb{{display:inline-block;font-size:.56rem;padding:1px 5px;
  background:rgba(138,180,248,.1);border:1px solid rgba(138,180,248,.2);
  border-radius:5px;color:var(--ac);margin-left:4px;vertical-align:middle;}}
.cb2{{display:inline-block;font-size:.56rem;padding:1px 5px;
  background:rgba(129,201,149,.1);border:1px solid rgba(129,201,149,.2);
  border-radius:5px;color:var(--ac2);margin-left:4px;vertical-align:middle;}}
.stTextInput>div>div>input{{background:transparent!important;border:none!important;
  box-shadow:none!important;color:var(--tx)!important;font-family:var(--sans)!important;font-size:.88rem!important;padding:4px 0!important;}}
.stTextInput>label{{display:none!important;}}
.stButton>button{{background:var(--ac)!important;color:#000!important;border:none!important;
  border-radius:20px!important;font-family:var(--sans)!important;font-weight:500!important;
  padding:7px 18px!important;font-size:.78rem!important;transition:.15s!important;}}
.stButton>button:hover{{opacity:.85!important;}}
.stSelectbox>div>div{{background:var(--s2)!important;border:1px solid var(--bd)!important;
  border-radius:8px!important;color:var(--tx)!important;}}
.stTextArea>div>div>textarea{{background:var(--s2)!important;border:1px solid var(--bd)!important;
  border-radius:8px!important;color:var(--tx)!important;font-family:var(--sans)!important;}}
.stFileUploader>div{{background:var(--s2)!important;
  border:2px dashed rgba(138,180,248,.25)!important;border-radius:10px!important;}}
div[data-testid="stSidebar"]{{background:var(--sf)!important;
  border-right:1px solid var(--bd)!important;min-width:290px!important;max-width:290px!important;}}
div[data-testid="stSidebar"] p,div[data-testid="stSidebar"] label{{color:var(--tx)!important;}}
.stExpander summary{{color:var(--mu)!important;font-size:.8rem!important;}}
.stDivider{{border-color:var(--bd)!important;}}
</style>""", unsafe_allow_html=True)

inject_css()

# ════════════════════════════════════════════════════════
# TTS — Friday speaks
# ════════════════════════════════════════════════════════
def speak(text: str):
    """Converts text to speech and auto-plays in browser."""
    if not st.session_state.tts_on or not TTS_OK:
        return
    try:
        async def _gen():
            com  = edge_tts.Communicate(text[:400], TTS_VOICE)
            data = b""
            async for chunk in com.stream():
                if chunk["type"] == "audio":
                    data += chunk["data"]
            return data

        audio = asyncio.run(_gen())
        b64   = base64.b64encode(audio).decode()
        st.markdown(
            f'<audio autoplay style="display:none">'
            f'<source src="data:audio/mp3;base64,{b64}" type="audio/mp3"></audio>',
            unsafe_allow_html=True)
    except Exception:
        pass

# ════════════════════════════════════════════════════════
# VOICE MIC widget (browser Web Speech API)
# ════════════════════════════════════════════════════════
VOICE_HTML = """
<div style="display:flex;align-items:center;gap:10px;padding:4px 0 2px;">
  <button id="mic" onclick="toggleMic()"
    style="width:40px;height:40px;border-radius:50%;border:none;
           background:#8ab4f8;color:#000;font-size:1rem;cursor:pointer;
           display:flex;align-items:center;justify-content:center;flex-shrink:0;transition:.2s;">
    🎤
  </button>
  <div id="lbl" style="font-size:.74rem;color:#9aa0a6;">Press mic → speak → paste result below</div>
</div>
<div id="rbox" style="display:none;margin-top:5px;padding:7px 11px;
  background:rgba(138,180,248,.08);border:1px solid rgba(138,180,248,.18);
  border-radius:9px;font-size:.82rem;color:#e8eaed;"></div>

<script>
let rec=false,r=null;
function toggleMic(){
  if(rec){r.stop();return;}
  const SR=window.SpeechRecognition||window.webkitSpeechRecognition;
  if(!SR){document.getElementById('lbl').textContent='Use Chrome for voice input';return;}
  r=new SR();r.lang='en-US';r.continuous=false;r.interimResults=true;
  r.onstart=()=>{
    rec=true;
    document.getElementById('mic').style.background='#f28b82';
    document.getElementById('mic').textContent='🔴';
    document.getElementById('lbl').textContent='Listening…';
    document.getElementById('rbox').style.display='none';
  };
  r.onend=()=>{
    rec=false;
    document.getElementById('mic').style.background='#8ab4f8';
    document.getElementById('mic').textContent='🎤';
  };
  r.onresult=(e)=>{
    let f='',i='';
    for(let x of e.results){if(x.isFinal)f+=x[0].transcript;else i+=x[0].transcript;}
    const t=f||i;
    document.getElementById('rbox').style.display='block';
    document.getElementById('rbox').textContent=t;
    document.getElementById('lbl').textContent=f?'✓ Copy this and paste in chat box below':'Hearing…';
  };
  r.onerror=(e)=>{
    rec=false;
    document.getElementById('lbl').textContent='Mic error: '+e.error;
    document.getElementById('mic').style.background='#8ab4f8';
    document.getElementById('mic').textContent='🎤';
  };
  r.start();
}
</script>
"""

# ════════════════════════════════════════════════════════
# CAMERA HTML (always-on, browser webcam)
# ════════════════════════════════════════════════════════
def cam_html(accent):
    return f"""<!DOCTYPE html><html><head><style>
*{{margin:0;padding:0;box-sizing:border-box;}}
body{{background:#000;overflow:hidden;font-family:'DM Sans',sans-serif;}}
#w{{position:relative;width:100%;}}
video{{width:100%;height:460px;object-fit:cover;display:block;}}
.corner{{position:absolute;width:15px;height:15px;opacity:.5;}}
.tl{{top:8px;left:8px;border-top:2px solid {accent};border-left:2px solid {accent};}}
.tr{{top:8px;right:8px;border-top:2px solid {accent};border-right:2px solid {accent};}}
.bl{{bottom:50px;left:8px;border-bottom:2px solid {accent};border-left:2px solid {accent};}}
.br{{bottom:50px;right:8px;border-bottom:2px solid {accent};border-right:2px solid {accent};}}
#hud{{position:absolute;top:11px;left:11px;color:rgba(255,255,255,.75);font-size:.7rem;
  display:flex;align-items:center;gap:6px;}}
#ldot{{width:6px;height:6px;border-radius:50%;background:#4ade80;
  box-shadow:0 0 6px #4ade80;animation:pp 2s infinite;display:none;}}
@keyframes pp{{0%,100%{{opacity:1}}50%{{opacity:.3}}}}
#off{{position:absolute;inset:0;display:flex;flex-direction:column;
  align-items:center;justify-content:center;gap:10px;color:#333;}}
#off-i{{font-size:2.5rem;opacity:.25;}}
#bar{{position:absolute;bottom:0;left:0;right:0;padding:8px 12px;
  background:linear-gradient(transparent,rgba(0,0,0,.85));
  display:flex;gap:8px;align-items:center;}}
.cb{{padding:6px 13px;border-radius:17px;font-size:.72rem;cursor:pointer;
  border:1px solid rgba(255,255,255,.15);background:rgba(0,0,0,.5);
  color:rgba(255,255,255,.8);transition:.15s;white-space:nowrap;}}
.cb:hover{{background:rgba(255,255,255,.12);}}
.cp{{background:{accent};color:#000;border:none;font-weight:600;}}
.cp:hover{{opacity:.85;}}
#fl{{position:absolute;inset:0;background:#fff;opacity:0;pointer-events:none;transition:opacity .1s;}}
</style></head><body>
<div id="w">
  <video id="v" autoplay playsinline muted></video>
  <div class="corner tl"></div><div class="corner tr"></div>
  <div class="corner bl"></div><div class="corner br"></div>
  <div id="hud"><div id="ldot"></div><span id="hs">OFFLINE</span></div>
  <div id="off"><div id="off-i">📷</div>
    <div style="font-size:.8rem;">Press Start — uses your device camera</div></div>
  <div id="fl"></div>
  <div id="bar">
    <button class="cb cp" id="bs" onclick="go()">▶ Start</button>
    <button class="cb" id="bsn" onclick="snap()" style="display:none">📸 Capture</button>
    <button class="cb" id="bst" onclick="stp()" style="display:none">■ Stop</button>
    <button class="cb" id="bfl" onclick="flp()" style="display:none">🔄 Flip</button>
  </div>
</div>
<script>
let s=null,f='environment';
async function go(){{
  try{{
    s=await navigator.mediaDevices.getUserMedia({{video:{{facingMode:f,width:{{ideal:1280}},height:{{ideal:720}}}},audio:false}});
    document.getElementById('v').srcObject=s;
    document.getElementById('off').style.display='none';
    document.getElementById('ldot').style.display='block';
    document.getElementById('hs').textContent='LIVE';
    document.getElementById('bs').style.display='none';
    ['bsn','bst','bfl'].forEach(x=>document.getElementById(x).style.display='block');
  }}catch(e){{
    document.getElementById('off').innerHTML='<div style="font-size:.8rem;color:#555;">Camera denied — allow in browser</div>';
  }}
}}
function stp(){{
  if(s){{s.getTracks().forEach(t=>t.stop());s=null;}}
  document.getElementById('v').srcObject=null;
  document.getElementById('off').style.display='flex';
  document.getElementById('ldot').style.display='none';
  document.getElementById('hs').textContent='OFFLINE';
  document.getElementById('bs').style.display='block';
  ['bsn','bst','bfl'].forEach(x=>document.getElementById(x).style.display='none');
}}
async function flp(){{f=f==='environment'?'user':'environment';if(s)s.getTracks().forEach(t=>t.stop());await go();}}
function snap(){{
  const v=document.getElementById('v');
  const c=document.createElement('canvas');
  c.width=v.videoWidth||640;c.height=v.videoHeight||480;
  c.getContext('2d').drawImage(v,0,0);
  document.getElementById('fl').style.opacity='.6';
  setTimeout(()=>document.getElementById('fl').style.opacity='0',100);
  try{{window.parent.postMessage({{type:'friday_snap',data:c.toDataURL('image/jpeg',.85)}},'*');}}catch(e){{}}
}}
</script></body></html>"""

# ════════════════════════════════════════════════════════
# AI FUNCTIONS
# ════════════════════════════════════════════════════════
def ask_ai(query: str, kb_ctx: str = "", cam_ctx: str = "") -> str:
    key = st.session_state.groq_key
    if not key:
        return "Add your Groq API key in Settings (top-right ⚙)."
    if not GROQ_OK:
        return "groq package not installed."
    sys = st.session_state.sys_prompt.format(
        time=datetime.now().strftime("%I:%M %p, %A %d %B %Y"))
    if kb_ctx:
        sys += f"\n\n[Knowledge Base]\n{kb_ctx}"
    if cam_ctx:
        sys += f"\n\n[Camera just saw]\n{cam_ctx[:300]}"
    history = [{"role": m["role"], "content": m["content"]}
               for m in st.session_state.messages[-12:]]
    try:
        r = Groq(api_key=key).chat.completions.create(
            model=st.session_state.chat_model,
            messages=[{"role":"system","content":sys}] + history +
                     [{"role":"user","content":query}],
            max_tokens=500, temperature=0.7)
        return r.choices[0].message.content.strip()
    except Exception as e:
        return f"Error: {e}"

def analyse_image(b64: str, question: str = "") -> str:
    key = st.session_state.groq_key
    if not key:
        return "Add your Groq API key in Settings."
    if "," in b64:
        b64 = b64.split(",", 1)[1]
    try:
        r = Groq(api_key=key).chat.completions.create(
            model=st.session_state.vision_model,
            messages=[{"role":"user","content":[
                {"type":"image_url","image_url":{"url":f"data:image/jpeg;base64,{b64}"}},
                {"type":"text","text": question.strip() or VISION_PROMPT}
            ]}], max_tokens=400)
        result = r.choices[0].message.content.strip()
        st.session_state.cam_analysis = result
        return result
    except Exception as e:
        return f"Vision error: {e}"

# ════════════════════════════════════════════════════════
# RAG FUNCTIONS
# ════════════════════════════════════════════════════════
@st.cache_resource(show_spinner=False)
def load_emb():
    if not RAG_OK:
        return None
    try:
        return HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
    except:
        return None

def rag_q(q: str) -> str:
    vs = st.session_state.vectorstore
    if not vs:
        return ""
    try:
        return "\n\n".join(d.page_content for d in vs.similarity_search(q, k=3))
    except:
        return ""

def ingest_pdf(f) -> dict:
    if not RAG_OK:
        return {"error": "Install: langchain-huggingface faiss-cpu pypdf"}
    p = Path("uploads") / f.name
    p.write_bytes(f.getbuffer())
    try:
        pages = PyPDFLoader(str(p)).load()
        docs  = RecursiveCharacterTextSplitter(
            chunk_size=800, chunk_overlap=100).split_documents(pages)
        emb = load_emb()
        if not emb:
            return {"error": "Embeddings failed"}
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
            chunk_size=800, chunk_overlap=100).split_documents(
            [Document(page_content=text, metadata={"source": name})])
        emb = load_emb()
        if not emb:
            return {"error": "Embeddings failed"}
        if st.session_state.vectorstore is None:
            st.session_state.vectorstore = FAISS.from_documents(docs, emb)
        else:
            st.session_state.vectorstore.add_documents(docs)
        return {"chunks": len(docs)}
    except Exception as e:
        return {"error": str(e)}

def add_msg(role, content, kb=False, cam=False):
    st.session_state.messages.append({
        "role": role, "content": content,
        "time": datetime.now().strftime("%I:%M %p"),
        "kb": kb, "cam": cam})

def send(query: str):
    kb  = rag_q(query)
    cam = st.session_state.cam_analysis
    with st.spinner(""):
        reply = ask_ai(query, kb, cam)
    add_msg("user",      query)
    add_msg("assistant", reply, kb=bool(kb), cam=bool(cam))
    speak(reply)
    st.rerun()

# ════════════════════════════════════════════════════════
# TOP BAR
# ════════════════════════════════════════════════════════
key_ok = bool(st.session_state.groq_key)
kb_cnt = len(st.session_state.kb_docs)

tl, tr = st.columns([7, 2])
with tl:
    kb_pill = (f'<div class="spill"><div class="sdot sb"></div>'
               f'{kb_cnt} doc{"s" if kb_cnt!=1 else ""}</div>') if kb_cnt else ""
    tts_pill = ('<div class="spill"><div class="sdot sg"></div>Voice</div>'
                if TTS_OK and st.session_state.tts_on else "")
    st.markdown(f"""
    <div class="tb" style="border:none;padding:10px 0 6px;">
      <div class="tb-logo"><span class="tb-star">✦</span> Friday</div>
      <div class="tb-r">
        <div class="spill">
          <div class="sdot {'sg' if key_ok else 'sr'}"></div>
          {'AI ready' if key_ok else 'No key'}
        </div>
        {kb_pill}{tts_pill}
      </div>
    </div>""", unsafe_allow_html=True)

with tr:
    st.markdown("<div style='height:4px'></div>", unsafe_allow_html=True)
    if st.button("⚙ Settings"):
        st.session_state.settings_open = not st.session_state.settings_open

st.markdown(f"<hr style='margin:0;border:none;border-top:1px solid {T('bd')};'>",
            unsafe_allow_html=True)

# ════════════════════════════════════════════════════════
# MAIN LAYOUT: camera left | chat right
# ════════════════════════════════════════════════════════
cl, cr = st.columns([11, 10], gap="small")

# ── LEFT: Camera ─────────────────────────────────────────
with cl:
    st.components.v1.html(cam_html(T("ac")), height=472, scrolling=False)

    with st.expander("📁 Upload photo to analyse"):
        uf = st.file_uploader("img", type=["jpg","jpeg","png","webp"],
                               label_visibility="collapsed", key="uf")
        uq = st.text_input("q2", placeholder="What is wrong with this plant?",
                            label_visibility="collapsed", key="uq")
        if uf and st.button("✦ Analyse photo", key="abtn"):
            b64 = base64.b64encode(uf.read()).decode()
            with st.spinner("Analysing…"):
                result = analyse_image(b64, uq)
            add_msg("user",      f"[Photo] {uq or 'Describe this image'}")
            add_msg("assistant", result, cam=True)
            speak(result)
            st.rerun()

# ── RIGHT: Chat ───────────────────────────────────────────
with cr:

    # Welcome screen (no messages yet)
    if not st.session_state.messages:
        st.markdown(f"""
        <div style="padding:26px 12px 10px;text-align:center;">
          <div style="font-size:1.5rem;font-weight:300;letter-spacing:-.02em;margin-bottom:6px;">
            Hello, <b style="color:{T('ac')};font-weight:600;">Boss</b>
          </div>
          <div style="font-size:.82rem;color:{T('mu')};line-height:1.7;
            max-width:255px;margin:0 auto 12px;">
            Start camera → capture → I identify objects, plants, problems and help you.
          </div>
        </div>""", unsafe_allow_html=True)

        sc1, sc2, sc3 = st.columns(3)
        for col, lbl, prompt in [
            (sc1, "🌿 ID plant",    "Identify this plant and tell me how to care for it."),
            (sc2, "⚠️ Find issues", "What problems or damage do you see? How to fix?"),
            (sc3, "💡 Daily tip",   "Give me one practical daily life tip."),
        ]:
            with col:
                if st.button(lbl, key=f"s_{lbl}", use_container_width=True):
                    send(prompt)

    else:
        # Messages list
        chat_box = st.container(height=355)
        with chat_box:
            for m in st.session_state.messages:
                kb_b  = '<span class="kb">KB</span>'   if m.get("kb")  else ""
                cam_b = '<span class="cb2">CAM</span>' if m.get("cam") else ""
                if m["role"] == "user":
                    st.markdown(f"""
                    <div class="mu">
                      <div class="bu bu-u">{m['content']}
                        <div class="bm">{m.get('time','')}</div>
                      </div>
                    </div>""", unsafe_allow_html=True)
                else:
                    st.markdown(f"""
                    <div class="ma">
                      <div class="av">✦</div>
                      <div class="bu bu-a">{m['content']}{kb_b}{cam_b}
                        <div class="bm">{m.get('time','')}</div>
                      </div>
                    </div>""", unsafe_allow_html=True)

    # Voice mic
    st.components.v1.html(VOICE_HTML, height=78, scrolling=False)

    # Text input + send
    with st.form("cf", clear_on_submit=True):
        c1, c2 = st.columns([9, 2])
        with c1:
            msg = st.text_input("m",
                placeholder="Speak above or type here…",
                label_visibility="collapsed")
        with c2:
            sent = st.form_submit_button("Send", use_container_width=True)

    if sent and msg.strip():
        send(msg.strip())

    # Quick buttons row
    q1, q2, q3, q4 = st.columns(4)
    for col, lbl, prompt in [
        (q1, "🕐 Time",    "What time and date is it?"),
        (q2, "🌤 Weather", "What is the weather today?"),
        (q3, "😂 Joke",    "Tell me a funny short joke."),
        (q4, "🗑 Clear",   None),
    ]:
        with col:
            if st.button(lbl, key=f"q_{lbl}", use_container_width=True):
                if prompt:
                    send(prompt)
                else:
                    st.session_state.messages = []
                    st.session_state.cam_analysis = ""
                    st.rerun()

# ════════════════════════════════════════════════════════
# SETTINGS SIDEBAR
# ════════════════════════════════════════════════════════
if st.session_state.settings_open:
    with st.sidebar:
        st.markdown("### ⚙️ Settings")
        st.divider()

        # Theme
        st.markdown("**Theme**")
        tcols = st.columns(len(THEMES))
        for i, (tn, td) in enumerate(THEMES.items()):
            with tcols[i]:
                active = st.session_state.theme == tn
                bdr = f"2px solid {td['ac']}" if active else "2px solid transparent"
                st.markdown(f"""
                <div style="aspect-ratio:1;border-radius:8px;border:{bdr};
                  background:linear-gradient(135deg,{td['bg']},{td['sf']});
                  display:flex;align-items:center;justify-content:center;">
                  <div style="width:7px;height:7px;border-radius:50%;background:{td['ac']};"></div>
                </div>
                <div style="font-size:.57rem;color:{'#fff' if active else '#555'};
                  text-align:center;margin-top:2px;">{tn}</div>""",
                unsafe_allow_html=True)
                if st.button("·", key=f"t_{tn}", use_container_width=True, help=tn):
                    st.session_state.theme = tn
                    st.rerun()

        st.divider()

        # Voice
        st.markdown("**Voice — Friday speaks**")
        st.session_state.tts_on = st.toggle(
            "Speak replies aloud", value=st.session_state.tts_on)
        if not TTS_OK:
            st.caption("Add `edge-tts` to requirements.txt to enable")

        st.divider()

        # API Key
        st.markdown("**Groq API Key**")
        nk = st.text_input("k", value=st.session_state.groq_key,
                            placeholder="gsk_…", type="password",
                            label_visibility="collapsed")
        if nk != st.session_state.groq_key:
            st.session_state.groq_key = nk
            st.success("✓ Key saved")
        st.caption("[Get free key → console.groq.com](https://console.groq.com)")

        st.divider()

        # Models
        st.markdown("**Chat Model**")
        idx = CHAT_MODELS.index(st.session_state.chat_model) \
              if st.session_state.chat_model in CHAT_MODELS else 0
        st.session_state.chat_model = st.selectbox(
            "cm", CHAT_MODELS, index=idx, label_visibility="collapsed")

        st.markdown("**Vision Model**")
        idx2 = VISION_MODELS.index(st.session_state.vision_model) \
               if st.session_state.vision_model in VISION_MODELS else 0
        st.session_state.vision_model = st.selectbox(
            "vm", VISION_MODELS, index=idx2, label_visibility="collapsed")

        st.divider()

        # Knowledge Base
        st.markdown("**Knowledge Base**")
        pdf = st.file_uploader("PDF", type=["pdf"],
                                label_visibility="collapsed", key="pdf_up")
        if pdf and not any(d["name"] == pdf.name for d in st.session_state.kb_docs):
            with st.spinner("Processing…"):
                r = ingest_pdf(pdf)
            if "error" in r:
                st.error(r["error"])
            else:
                st.session_state.kb_docs.append({
                    "name": pdf.name, "type": "pdf", "pages": r["pages"]})
                st.success(f"✓ {r['pages']}p · {r['chunks']} chunks")

        with st.expander("📝 Add text / notes"):
            tt = st.text_input("Title", placeholder="My notes", key="tt")
            tb = st.text_area("Content", placeholder="Paste any text…",
                               height=90, key="tb")
            if st.button("Add to KB", use_container_width=True, key="tadd"):
                if tb.strip():
                    with st.spinner("Adding…"):
                        r = ingest_text(tt or "Notes", tb)
                    if "error" in r:
                        st.error(r["error"])
                    else:
                        st.session_state.kb_docs.append({
                            "name": tt or "Notes", "type": "text",
                            "chunks": r["chunks"]})
                        st.success(f"✓ {r['chunks']} chunks added")

        if st.session_state.kb_docs:
            st.markdown(f"**{len(st.session_state.kb_docs)} documents**")
            for i, d in enumerate(st.session_state.kb_docs):
                c1, c2 = st.columns([5, 1])
                with c1:
                    ico = "📄" if d["type"] == "pdf" else "📝"
                    inf = (f"{d.get('pages','?')}p" if d["type"] == "pdf"
                           else f"{d.get('chunks','?')} chunks")
                    st.markdown(
                        f"<div style='font-size:.74rem;'>{ico} {d['name']}</div>"
                        f"<div style='font-size:.6rem;color:var(--mu);'>{inf}</div>",
                        unsafe_allow_html=True)
                with c2:
                    if st.button("✕", key=f"rm{i}"):
                        st.session_state.kb_docs.pop(i)
                        st.rerun()

        st.divider()

        # Personality
        with st.expander("✏️ Friday's personality"):
            np = st.text_area("p", value=st.session_state.sys_prompt,
                               height=130, label_visibility="collapsed")
            if st.button("Save", key="sp", use_container_width=True):
                st.session_state.sys_prompt = np
                st.success("Saved!")

        st.divider()

        with st.expander("🗑 Reset"):
            if st.button("Clear chat", use_container_width=True, key="cc"):
                st.session_state.messages = []
                st.rerun()
            if st.button("Reset all", use_container_width=True, key="ra"):
                for k in ["messages", "kb_docs"]:
                    st.session_state[k] = []
                st.session_state.vectorstore = None
                st.session_state.cam_analysis = ""
                st.rerun()

        st.markdown(
            f"<div style='font-size:.58rem;color:var(--mu);text-align:center;margin-top:10px;'>"
            f"Friday v6.0 · {st.session_state.theme}</div>",
            unsafe_allow_html=True)
