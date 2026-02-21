"""
AGRI-FRIDAY - HACKATHON EDITION
Features: Glass UI | PDF RAG | Voice | Camera
Setup: pip install -r requirements.txt && echo "GROQ_API_KEY=your_key" > .env
Run: streamlit run app.py
"""

import streamlit as st
import cv2
import os
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

# CONFIG
GROQ_KEY = os.getenv("GROQ_API_KEY", "")

def init_ai():
    if not GROQ_KEY: return None, None
    client = Groq(api_key=GROQ_KEY)
    embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
    try:
        vectorstore = Chroma(persist_directory="./db", embedding_function=embeddings)
    except:
        vectorstore = None
    return client, vectorstore

def process_pdf(pdf):
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        tmp.write(pdf.getvalue())
        tmp_path = tmp.name
    
    loader = PyPDFLoader(tmp_path)
    docs = loader.load()
    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    chunks = splitter.split_documents(docs)
    
    embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
    
    if os.path.exists("./db"):
        vs = Chroma(persist_directory="./db", embedding_function=embeddings)
        vs.add_documents(chunks)
    else:
        vs = Chroma.from_documents(chunks, embeddings, persist_directory="./db")
    
    vs.persist()
    os.unlink(tmp_path)
    return len(chunks)

def ask_ai(query, client, vectorstore):
    if not client: return "⚠️ Set GROQ_API_KEY"
    
    if vectorstore:
        llm = ChatGroq(temperature=0.7, model_name="llama-3.3-70b-versatile", groq_api_key=GROQ_KEY)
        qa = RetrievalQA.from_chain_type(llm=llm, retriever=vectorstore.as_retriever(search_kwargs={"k": 3}))
        return qa.run(query)
    else:
        resp = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": query}],
            temperature=0.7,
            max_tokens=300
        )
        return resp.choices[0].message.content

def speech_to_text():
    rec = sr.Recognizer()
    with sr.Microphone() as src:
        rec.adjust_for_ambient_noise(src, duration=0.5)
        audio = rec.listen(src, timeout=5, phrase_time_limit=10)
    
    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
        tmp.write(audio.get_wav_data())
        tmp_path = tmp.name
    
    with open(tmp_path, "rb") as f:
        text = Groq(api_key=GROQ_KEY).audio.transcriptions.create(
            file=f, model="whisper-large-v3-turbo", response_format="text"
        )
    
    os.unlink(tmp_path)
    return text

def text_to_speech(text):
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
    cv2.putText(processed, "AGRI-FRIDAY SCANNING", (10, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 136), 2)
    cv2.rectangle(processed, (0, 0), (w, h), (0, 255, 136), 3)
    return processed

def main():
    st.set_page_config(page_title="Agri-Friday", page_icon="🌱", layout="wide")
    
    # GLASS UI CSS
    st.markdown("""
    <style>
    .stApp {background: linear-gradient(135deg, #0f0c29 0%, #302b63 50%, #24243e 100%);}
    .block-container {background: rgba(255,255,255,0.05); backdrop-filter: blur(10px); border-radius: 20px; padding: 2rem !important;}
    h1, h2, h3 {color: #00ff88 !important; text-shadow: 0 0 20px rgba(0,255,136,0.5);}
    section[data-testid="stSidebar"] {background: rgba(255,255,255,0.05) !important; backdrop-filter: blur(15px) !important;}
    section[data-testid="stSidebar"] > div {background: transparent !important;}
    .stButton>button {background: rgba(0,255,136,0.15) !important; backdrop-filter: blur(10px); border: 1px solid rgba(0,255,136,0.3) !important; 
                      border-radius: 12px !important; color: #00ff88 !important; font-weight: 600 !important;}
    .stTextInput>div>div>input {background: rgba(255,255,255,0.05) !important; backdrop-filter: blur(10px) !important; 
                                 border: 1px solid rgba(255,255,255,0.1) !important; border-radius: 12px !important; color: #fff !important;}
    .chat-user {background: rgba(0,255,136,0.12); backdrop-filter: blur(10px); border: 1px solid rgba(0,255,136,0.3); 
                border-radius: 15px; padding: 15px; margin: 10px 0 10px 20%;}
    .chat-ai {background: rgba(100,100,255,0.12); backdrop-filter: blur(10px); border: 1px solid rgba(100,100,255,0.3); 
              border-radius: 15px; padding: 15px; margin: 10px 20% 10px 0;}
    </style>
    """, unsafe_allow_html=True)
    
    # SESSION STATE
    if 'chat' not in st.session_state: st.session_state.chat = []
    if 'client' not in st.session_state: st.session_state.client, st.session_state.vs = init_ai()
    if 'docs' not in st.session_state: st.session_state.docs = []
    if 'cam' not in st.session_state: st.session_state.cam = False
    
    # HEADER
    st.markdown("<h1 style='text-align: center;'>🌱 AGRI-FRIDAY</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #00ff88;'>AI Agriculture • Glass UI • RAG • Voice • Vision</p>", unsafe_allow_html=True)
    
    # SIDEBAR
    with st.sidebar:
        st.markdown("### 📚 Knowledge Base")
        pdfs = st.file_uploader("Upload PDFs", type=['pdf'], accept_multiple_files=True)
        
        if pdfs:
            for pdf in pdfs:
                if pdf.name not in [d['name'] for d in st.session_state.docs]:
                    with st.spinner(f"Processing {pdf.name}..."):
                        chunks = process_pdf(pdf)
                        st.session_state.docs.append({'name': pdf.name, 'chunks': chunks})
                        st.session_state.client, st.session_state.vs = init_ai()
                        st.success(f"✅ {chunks} chunks")
        
        if st.session_state.docs:
            st.markdown("**Uploaded:**")
            for doc in st.session_state.docs:
                st.text(f"📄 {doc['name']}")
        
        st.markdown("### ⚙️ Settings")
        st.session_state.cam = st.toggle("📹 Camera", value=st.session_state.cam)
        
        if st.button("🗑️ Clear Chat"): 
            st.session_state.chat = []
            st.rerun()
    
    # MAIN - TWO COLUMNS
    col1, col2 = st.columns([1, 1])
    
    # CAMERA
    with col1:
        st.markdown("### 📹 Smart Camera")
        cam_ph = st.empty()
        
        if st.session_state.cam:
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
            cam_ph.info("📹 Camera off")
    
    # CHAT
    with col2:
        st.markdown("### 💬 Chat Assistant")
        
        chat_ph = st.container(height=400)
        with chat_ph:
            if not st.session_state.chat:
                st.markdown("<div style='text-align: center; padding: 80px 20px; color: #00ff88;'><h3>👋 Hello!</h3><p>Upload PDFs or ask questions</p></div>", unsafe_allow_html=True)
            else:
                for msg in st.session_state.chat:
                    if msg['role'] == 'user':
                        st.markdown(f"<div class='chat-user'><strong>🧑‍🌾 You:</strong><br>{msg['content']}</div>", unsafe_allow_html=True)
                    else:
                        st.markdown(f"<div class='chat-ai'><strong>🌱 AI:</strong><br>{msg['content']}</div>", unsafe_allow_html=True)
        
        # INPUT
        c1, c2 = st.columns([4, 1])
        with c2:
            voice_btn = st.button("🎤", use_container_width=True)
        
        user_input = st.text_input("Ask...", placeholder="e.g., fertilizer for tomatoes?", label_visibility="collapsed")
        send_btn = st.button("📤 Send", use_container_width=True, type="primary")
        
        # VOICE
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
        
        # SEND
        if send_btn and user_input:
            st.session_state.chat.append({'role': 'user', 'content': user_input})
            
            with st.spinner("🤔 Thinking..."):
                response = ask_ai(user_input, st.session_state.client, st.session_state.vs)
            
            st.session_state.chat.append({'role': 'assistant', 'content': response})
            
            try:
                text_to_speech(response)
            except:
                pass
            
            st.rerun()

if __name__ == "__main__":
    main()
