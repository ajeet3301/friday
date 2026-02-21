"""
AGRI-FRIDAY - USER APP
Reads configuration from admin panel
Run admin panel: streamlit run admin.py
Setup: pip install -r requirements.txt && echo "GROQ_API_KEY=your_key" > .env
Run user app: streamlit run app_with_admin.py
"""

import streamlit as st
import cv2
import os
import json
from datetime import datetime
from groq import Groq
from langchain_groq import ChatGroq
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain.chains import RetrievalQA
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
import tempfile
import speech_recognition as sr
import edge_tts
import pygame
import asyncio

# Load configs from admin panel
def load_config(file, default):
    if os.path.exists(file):
        with open(file, 'r') as f:
            return json.load(f)
    return default

THEME_CONFIG = load_config("theme_config.json", {
    "primary_color": "#00ff88",
    "background_gradient_start": "#0f0c29",
    "background_gradient_mid": "#302b63",
    "background_gradient_end": "#24243e",
    "glass_opacity": "0.05",
    "glass_blur": "10px",
    "font_family": "Inter",
    "app_name": "AGRI-FRIDAY",
    "app_tagline": "AI Agriculture Assistant"
})

SETTINGS = load_config("settings_config.json", {
    "enable_camera": True,
    "enable_voice": True,
    "enable_rag": True,
    "groq_model": "llama-3.3-70b-versatile",
    "whisper_model": "whisper-large-v3-turbo",
    "max_tokens": 500,
    "temperature": 0.7,
    "chunk_size": 1000,
    "chunk_overlap": 200
})

GROQ_KEY = os.getenv("GROQ_API_KEY", "")
PDF_FOLDER = "knowledge_base"

def init_ai():
    if not GROQ_KEY: return None, None
    client = Groq(api_key=GROQ_KEY)
    embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
    try:
        vectorstore = Chroma(persist_directory="./db", embedding_function=embeddings)
    except:
        vectorstore = None
    return client, vectorstore

def ask_ai(query, client, vectorstore):
    if not client: return "⚠️ Set GROQ_API_KEY"
    
    if SETTINGS['enable_rag'] and vectorstore:
        llm = ChatGroq(
            temperature=SETTINGS['temperature'], 
            model_name=SETTINGS['groq_model'], 
            groq_api_key=GROQ_KEY,
            max_tokens=SETTINGS['max_tokens']
        )
        qa = RetrievalQA.from_chain_type(
            llm=llm, 
            retriever=vectorstore.as_retriever(search_kwargs={"k": 3})
        )
        return qa.run(query)
    else:
        resp = client.chat.completions.create(
            model=SETTINGS['groq_model'],
            messages=[{"role": "user", "content": query}],
            temperature=SETTINGS['temperature'],
            max_tokens=SETTINGS['max_tokens']
        )
        return resp.choices[0].message.content

def speech_to_text():
    if not SETTINGS['enable_voice']: return "Voice disabled"
    
    rec = sr.Recognizer()
    with sr.Microphone() as src:
        rec.adjust_for_ambient_noise(src, duration=0.5)
        audio = rec.listen(src, timeout=5, phrase_time_limit=10)
    
    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
        tmp.write(audio.get_wav_data())
        tmp_path = tmp.name
    
    with open(tmp_path, "rb") as f:
        text = Groq(api_key=GROQ_KEY).audio.transcriptions.create(
            file=f, model=SETTINGS['whisper_model'], response_format="text"
        )
    
    os.unlink(tmp_path)
    return text

def text_to_speech(text):
    if not SETTINGS['enable_voice']: return
    
    async def gen():
        comm = edge_tts.Communicate(text, "en-IN-NeerjaNeural", rate="+10%")
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp:
            tmp_path = tmp.name
        await comm.save(tmp_path)
        return tmp_path
    
    audio = asyncio.run(gen())
    if not pygame.mixer.get_init(): pygame.mixer.init()
    pygame.mixer.music.load(audio)
    pygame.mixer.music.play()
    while pygame.mixer.music.get_busy(): pygame.time.Clock().tick(10)
    pygame.mixer.music.unload()
    os.unlink(audio)

def analyze_frame(frame):
    processed = frame.copy()
    h, w = processed.shape[:2]
    cv2.putText(processed, f"{THEME_CONFIG['app_name']} SCANNING", (10, 40), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 136), 2)
    cv2.rectangle(processed, (0, 0), (w, h), (0, 255, 136), 3)
    return processed

def get_pdfs():
    if not os.path.exists(PDF_FOLDER): return []
    return [f for f in os.listdir(PDF_FOLDER) if f.endswith('.pdf')]

def main():
    st.set_page_config(
        page_title=THEME_CONFIG['app_name'], 
        page_icon="🌱", 
        layout="wide"
    )
    
    # Apply theme from admin panel
    st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family={THEME_CONFIG['font_family'].replace(' ', '+')}:wght@300;400;600;700&display=swap');
    
    .stApp {{
        background: linear-gradient(135deg, 
            {THEME_CONFIG['background_gradient_start']} 0%, 
            {THEME_CONFIG['background_gradient_mid']} 50%, 
            {THEME_CONFIG['background_gradient_end']} 100%);
        font-family: '{THEME_CONFIG['font_family']}', sans-serif;
    }}
    
    .block-container {{
        background: rgba(255, 255, 255, {THEME_CONFIG['glass_opacity']});
        backdrop-filter: blur({THEME_CONFIG['glass_blur']});
        border-radius: 20px;
        padding: 2rem !important;
    }}
    
    h1, h2, h3 {{
        color: {THEME_CONFIG['primary_color']} !important;
        text-shadow: 0 0 20px {THEME_CONFIG['primary_color']}80;
        font-family: '{THEME_CONFIG['font_family']}', sans-serif;
    }}
    
    section[data-testid="stSidebar"] {{
        background: rgba(255, 255, 255, {THEME_CONFIG['glass_opacity']}) !important;
        backdrop-filter: blur(15px) !important;
    }}
    
    section[data-testid="stSidebar"] > div {{background: transparent !important;}}
    
    .stButton>button {{
        background: rgba(0, 255, 136, 0.15) !important;
        backdrop-filter: blur(10px);
        border: 1px solid {THEME_CONFIG['primary_color']}50 !important;
        border-radius: 12px !important;
        color: {THEME_CONFIG['primary_color']} !important;
        font-weight: 600 !important;
    }}
    
    .stButton>button:hover {{
        background: rgba(0, 255, 136, 0.25) !important;
        transform: translateY(-2px);
    }}
    
    .stTextInput>div>div>input {{
        background: rgba(255, 255, 255, 0.05) !important;
        backdrop-filter: blur(10px) !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        border-radius: 12px !important;
        color: #fff !important;
    }}
    
    .chat-user {{
        background: rgba(0, 255, 136, 0.12);
        backdrop-filter: blur(10px);
        border: 1px solid {THEME_CONFIG['primary_color']}50;
        border-radius: 15px;
        padding: 15px;
        margin: 10px 0 10px 20%;
    }}
    
    .chat-ai {{
        background: rgba(100, 100, 255, 0.12);
        backdrop-filter: blur(10px);
        border: 1px solid rgba(100, 100, 255, 0.3);
        border-radius: 15px;
        padding: 15px;
        margin: 10px 20% 10px 0;
    }}
    </style>
    """, unsafe_allow_html=True)
    
    # Session state
    if 'chat' not in st.session_state: st.session_state.chat = []
    if 'client' not in st.session_state: st.session_state.client, st.session_state.vs = init_ai()
    if 'cam' not in st.session_state: st.session_state.cam = False
    
    # Header
    st.markdown(f"<h1 style='text-align: center;'>🌱 {THEME_CONFIG['app_name']}</h1>", 
                unsafe_allow_html=True)
    st.markdown(f"<p style='text-align: center; color: {THEME_CONFIG['primary_color']};'>{THEME_CONFIG['app_tagline']}</p>", 
                unsafe_allow_html=True)
    
    # Sidebar
    with st.sidebar:
        st.markdown("### 📚 Knowledge Base")
        pdfs = get_pdfs()
        if pdfs:
            st.success(f"✅ {len(pdfs)} PDFs loaded")
            with st.expander("View PDFs"):
                for pdf in pdfs:
                    st.text(f"📄 {pdf}")
        else:
            st.info("No PDFs. Use admin panel to upload.")
        
        st.markdown("### ⚙️ Settings")
        if SETTINGS['enable_camera']:
            st.session_state.cam = st.toggle("📹 Camera", value=st.session_state.cam)
        
        st.markdown("### 🔗 Links")
        st.markdown("[⚙️ Admin Panel](http://localhost:8502)")
        
        if st.button("🗑️ Clear Chat"): 
            st.session_state.chat = []
            st.rerun()
    
    # Main columns
    col1, col2 = st.columns([1, 1])
    
    # Camera
    with col1:
        st.markdown("### 📹 Smart Camera")
        cam_ph = st.empty()
        
        if SETTINGS['enable_camera'] and st.session_state.cam:
            try:
                cap = cv2.VideoCapture(0)
                ret, frame = cap.read()
                if ret:
                    processed = analyze_frame(frame)
                    cam_ph.image(cv2.cvtColor(processed, cv2.COLOR_BGR2RGB), use_container_width=True)
                else:
                    cam_ph.error("❌ Camera failed")
                cap.release()
            except Exception as e:
                cam_ph.error(f"❌ {e}")
        else:
            status = "Camera disabled in settings" if not SETTINGS['enable_camera'] else "Camera off"
            cam_ph.info(f"📹 {status}")
    
    # Chat
    with col2:
        st.markdown("### 💬 Chat Assistant")
        
        chat_ph = st.container(height=400)
        with chat_ph:
            if not st.session_state.chat:
                st.markdown(f"<div style='text-align: center; padding: 80px 20px; color: {THEME_CONFIG['primary_color']};'><h3>👋 Hello!</h3><p>Ask me anything</p></div>", 
                           unsafe_allow_html=True)
            else:
                for msg in st.session_state.chat:
                    if msg['role'] == 'user':
                        st.markdown(f"<div class='chat-user'><strong>🧑‍🌾 You:</strong><br>{msg['content']}</div>", 
                                   unsafe_allow_html=True)
                    else:
                        st.markdown(f"<div class='chat-ai'><strong>🌱 AI:</strong><br>{msg['content']}</div>", 
                                   unsafe_allow_html=True)
        
        # Input
        c1, c2 = st.columns([4, 1])
        
        with c2:
            voice_btn = st.button("🎤", use_container_width=True) if SETTINGS['enable_voice'] else None
        
        user_input = st.text_input("Ask...", placeholder="e.g., fertilizer for tomatoes?", 
                                   label_visibility="collapsed")
        send_btn = st.button("📤 Send", use_container_width=True, type="primary")
        
        # Voice
        if voice_btn:
            with st.spinner("🎤 Listening..."):
                try:
                    text = speech_to_text()
                    st.session_state.temp_voice = text
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ {e}")
        
        if 'temp_voice' in st.session_state:
            user_input = st.session_state.temp_voice
            del st.session_state.temp_voice
            send_btn = True
        
        # Send
        if send_btn and user_input:
            st.session_state.chat.append({'role': 'user', 'content': user_input})
            
            with st.spinner("🤔 Thinking..."):
                response = ask_ai(user_input, st.session_state.client, st.session_state.vs)
            
            st.session_state.chat.append({'role': 'assistant', 'content': response})
            
            if SETTINGS['enable_voice']:
                try:
                    text_to_speech(response)
                except:
                    pass
            
            st.rerun()

if __name__ == "__main__":
    main()
