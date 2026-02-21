"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                    AGRI-FRIDAY AI ASSISTANT DASHBOARD                        ║
║              Smart Agriculture Assistant with Vision & RAG                   ║
╚══════════════════════════════════════════════════════════════════════════════╝

USAGE:
    streamlit run agri_friday_dashboard.py

FEATURES:
    ✓ Live Vision Feed with Object Detection
    ✓ RAG Knowledge Base (PDF Upload)
    ✓ Voice/Text Chat Interface
    ✓ Status Indicators (Wake Word, Camera, Database)
    ✓ Futuristic Dark Theme with Green Accents
"""

import streamlit as st
import cv2
import numpy as np
from PIL import Image
import time
import os
from datetime import datetime
import json
import base64
from pathlib import Path

# ═══════════════════════════════════════════════════════════════════════════
# PAGE CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════

st.set_page_config(
    page_title="Agri-Friday AI Assistant",
    page_icon="🌱",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ═══════════════════════════════════════════════════════════════════════════
# CUSTOM CSS - FUTURISTIC DARK THEME WITH GREEN ACCENTS
# ═══════════════════════════════════════════════════════════════════════════

def load_custom_css():
    st.markdown("""
    <style>
    /* Import Orbitron font for futuristic look */
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&family=Roboto:wght@300;400;500&display=swap');
    
    /* Main Background */
    .stApp {
        background: linear-gradient(135deg, #0a0e27 0%, #1a1f3a 100%);
        color: #e0e0e0;
    }
    
    /* Headers */
    h1, h2, h3 {
        font-family: 'Orbitron', sans-serif;
        color: #00ff88 !important;
        text-shadow: 0 0 10px rgba(0, 255, 136, 0.5);
    }
    
    /* Status Indicators */
    .status-container {
        background: linear-gradient(135deg, #1a1f3a 0%, #2a2f4a 100%);
        border: 2px solid #00ff88;
        border-radius: 15px;
        padding: 20px;
        margin-bottom: 20px;
        box-shadow: 0 0 20px rgba(0, 255, 136, 0.3);
    }
    
    .status-indicator {
        display: inline-block;
        padding: 10px 20px;
        margin: 5px;
        border-radius: 8px;
        font-family: 'Roboto', sans-serif;
        font-weight: 500;
        border: 1px solid;
    }
    
    .status-active {
        background: rgba(0, 255, 136, 0.2);
        border-color: #00ff88;
        color: #00ff88;
        box-shadow: 0 0 10px rgba(0, 255, 136, 0.4);
    }
    
    .status-inactive {
        background: rgba(255, 68, 68, 0.2);
        border-color: #ff4444;
        color: #ff4444;
    }
    
    .status-warning {
        background: rgba(255, 193, 7, 0.2);
        border-color: #ffc107;
        color: #ffc107;
    }
    
    /* Camera Feed Container */
    .camera-container {
        background: linear-gradient(135deg, #1a1f3a 0%, #2a2f4a 100%);
        border: 2px solid #00ff88;
        border-radius: 15px;
        padding: 15px;
        box-shadow: 0 0 30px rgba(0, 255, 136, 0.3);
    }
    
    /* Chat Container */
    .chat-container {
        background: linear-gradient(135deg, #1a1f3a 0%, #2a2f4a 100%);
        border: 2px solid #00ff88;
        border-radius: 15px;
        padding: 20px;
        min-height: 600px;
        box-shadow: 0 0 30px rgba(0, 255, 136, 0.3);
    }
    
    /* Chat Message Bubbles */
    .user-message {
        background: linear-gradient(135deg, #00ff88 0%, #00cc6a 100%);
        color: #0a0e27;
        padding: 12px 18px;
        border-radius: 18px 18px 5px 18px;
        margin: 10px 0;
        max-width: 80%;
        float: right;
        clear: both;
        font-family: 'Roboto', sans-serif;
        box-shadow: 0 4px 10px rgba(0, 255, 136, 0.3);
    }
    
    .ai-message {
        background: linear-gradient(135deg, #2a2f4a 0%, #3a3f5a 100%);
        color: #00ff88;
        padding: 12px 18px;
        border-radius: 18px 18px 18px 5px;
        margin: 10px 0;
        max-width: 80%;
        float: left;
        clear: both;
        font-family: 'Roboto', sans-serif;
        border: 1px solid #00ff88;
        box-shadow: 0 4px 10px rgba(0, 255, 136, 0.2);
    }
    
    /* Sidebar */
    .css-1d391kg {
        background: linear-gradient(180deg, #1a1f3a 0%, #0a0e27 100%);
    }
    
    /* Buttons */
    .stButton>button {
        background: linear-gradient(135deg, #00ff88 0%, #00cc6a 100%);
        color: #0a0e27;
        border: none;
        border-radius: 10px;
        padding: 12px 24px;
        font-family: 'Orbitron', sans-serif;
        font-weight: bold;
        box-shadow: 0 4px 15px rgba(0, 255, 136, 0.4);
        transition: all 0.3s ease;
    }
    
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(0, 255, 136, 0.6);
    }
    
    /* File Uploader */
    .uploadedFile {
        background: rgba(0, 255, 136, 0.1);
        border: 1px solid #00ff88;
        border-radius: 8px;
    }
    
    /* Text Input */
    .stTextInput>div>div>input {
        background: rgba(42, 47, 74, 0.8);
        color: #e0e0e0;
        border: 2px solid #00ff88;
        border-radius: 10px;
        font-family: 'Roboto', sans-serif;
    }
    
    /* Metrics */
    .metric-container {
        background: rgba(0, 255, 136, 0.1);
        border: 1px solid #00ff88;
        border-radius: 10px;
        padding: 15px;
        text-align: center;
    }
    
    /* Scrollbar */
    ::-webkit-scrollbar {
        width: 10px;
        height: 10px;
    }
    
    ::-webkit-scrollbar-track {
        background: #1a1f3a;
    }
    
    ::-webkit-scrollbar-thumb {
        background: #00ff88;
        border-radius: 5px;
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: #00cc6a;
    }
    
    /* Expander */
    .streamlit-expanderHeader {
        background: rgba(0, 255, 136, 0.1);
        border: 1px solid #00ff88;
        border-radius: 8px;
        color: #00ff88 !important;
        font-family: 'Orbitron', sans-serif;
    }
    
    /* Info boxes */
    .stAlert {
        background: rgba(0, 255, 136, 0.1);
        border: 1px solid #00ff88;
        color: #e0e0e0;
    }
    
    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 10px;
    }
    
    .stTabs [data-baseweb="tab"] {
        background: rgba(42, 47, 74, 0.5);
        border: 1px solid #00ff88;
        border-radius: 8px 8px 0 0;
        color: #00ff88;
        font-family: 'Orbitron', sans-serif;
    }
    
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #00ff88 0%, #00cc6a 100%);
        color: #0a0e27;
    }
    </style>
    """, unsafe_allow_html=True)

load_custom_css()

# ═══════════════════════════════════════════════════════════════════════════
# SESSION STATE INITIALIZATION
# ═══════════════════════════════════════════════════════════════════════════

if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []

if 'wake_word_active' not in st.session_state:
    st.session_state.wake_word_active = False

if 'camera_active' not in st.session_state:
    st.session_state.camera_active = False

if 'detected_object' not in st.session_state:
    st.session_state.detected_object = "None"

if 'knowledge_base' not in st.session_state:
    st.session_state.knowledge_base = []

if 'rag_status' not in st.session_state:
    st.session_state.rag_status = "Not Initialized"

# ═══════════════════════════════════════════════════════════════════════════
# PLACEHOLDER FUNCTIONS - INTEGRATE YOUR EXISTING CODE HERE
# ═══════════════════════════════════════════════════════════════════════════

def process_frame(frame):
    """
    PLACEHOLDER: Object Detection on Camera Frame
    
    TODO: Replace this with your existing cv2/YOLO/MediaPipe detection logic.
    
    Args:
        frame: OpenCV frame (numpy array)
    
    Returns:
        processed_frame: Frame with bounding boxes
        detected_objects: List of detected objects
    """
    # Example placeholder - just add text overlay
    processed = frame.copy()
    
    # Simulate detection (replace with your actual model)
    detected_objects = []
    
    # Example: Add detection text
    cv2.putText(processed, "Agri-Friday Vision Active", 
                (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 
                0.7, (0, 255, 136), 2)
    
    # TODO: Add your object detection code here
    # Example:
    # results = your_model.predict(frame)
    # for result in results:
    #     x1, y1, x2, y2 = result.bbox
    #     label = result.label
    #     cv2.rectangle(processed, (x1, y1), (x2, y2), (0, 255, 136), 2)
    #     cv2.putText(processed, label, (x1, y1-10), ...)
    #     detected_objects.append(label)
    
    return processed, detected_objects


def ask_ai(query, knowledge_base=None):
    """
    PLACEHOLDER: AI Brain Function
    
    TODO: Replace this with your existing Groq + LangChain RAG logic.
    
    Args:
        query: User's question (string)
        knowledge_base: List of uploaded PDF paths (optional)
    
    Returns:
        response: AI's text response (string)
    """
    # Example placeholder response
    response = f"🌱 Agri-Friday AI Response:\n\n"
    response += f"I received your query: '{query}'\n\n"
    
    if knowledge_base:
        response += f"📚 Knowledge Base: {len(knowledge_base)} documents loaded.\n\n"
    
    response += "TODO: Integrate your Groq LLM + LangChain RAG pipeline here."
    
    # TODO: Replace with your actual AI logic
    # Example:
    # from langchain.chains import RetrievalQA
    # from groq import Groq
    # 
    # if knowledge_base:
    #     # Load and process PDFs
    #     docs = load_pdfs(knowledge_base)
    #     vectorstore = create_vectorstore(docs)
    #     qa_chain = RetrievalQA.from_chain_type(llm=groq_llm, retriever=vectorstore.as_retriever())
    #     response = qa_chain.run(query)
    # else:
    #     # Direct LLM query
    #     client = Groq(api_key=your_key)
    #     response = client.chat.completions.create(...)
    
    return response


def process_pdf(pdf_file):
    """
    PLACEHOLDER: PDF Processing for RAG
    
    TODO: Replace with your LangChain PDF loader and chunking logic.
    
    Args:
        pdf_file: Uploaded PDF file object
    
    Returns:
        success: Boolean
        message: Status message
    """
    # Save uploaded PDF
    pdf_path = f"knowledge_base/{pdf_file.name}"
    os.makedirs("knowledge_base", exist_ok=True)
    
    with open(pdf_path, "wb") as f:
        f.write(pdf_file.getbuffer())
    
    # TODO: Add your PDF processing logic here
    # Example:
    # from langchain.document_loaders import PyPDFLoader
    # from langchain.text_splitter import RecursiveCharacterTextSplitter
    # 
    # loader = PyPDFLoader(pdf_path)
    # documents = loader.load()
    # text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    # chunks = text_splitter.split_documents(documents)
    # 
    # # Add to vector database
    # vectorstore.add_documents(chunks)
    
    return True, f"✅ Processed: {pdf_file.name}"


def text_to_speech(text):
    """
    PLACEHOLDER: TTS (Text-to-Speech)
    
    TODO: Integrate your existing edge-tts or pygame audio playback.
    
    Args:
        text: Text to speak (string)
    """
    # TODO: Add your TTS logic here
    # Example:
    # import edge_tts
    # import pygame
    # 
    # async def _speak():
    #     communicate = edge_tts.Communicate(text, voice="en-IN-NeerjaNeural")
    #     await communicate.save("output.mp3")
    #     pygame.mixer.init()
    #     pygame.mixer.music.load("output.mp3")
    #     pygame.mixer.music.play()
    # 
    # asyncio.run(_speak())
    
    st.info("🔊 TTS: Would speak - " + text[:100] + "...")


def speech_to_text():
    """
    PLACEHOLDER: STT (Speech-to-Text)
    
    TODO: Integrate your existing speech recognition logic.
    
    Returns:
        transcribed_text: User's spoken text (string)
    """
    # TODO: Add your STT logic here
    # Example:
    # import speech_recognition as sr
    # 
    # recognizer = sr.Recognizer()
    # with sr.Microphone() as source:
    #     audio = recognizer.listen(source)
    #     text = recognizer.recognize_google(audio)
    #     return text
    
    return "TODO: Integrate speech recognition"

# ═══════════════════════════════════════════════════════════════════════════
# HEADER WITH STATUS INDICATORS
# ═══════════════════════════════════════════════════════════════════════════

st.markdown("""
<div style='text-align: center; padding: 20px 0;'>
    <h1 style='font-size: 3em; margin: 0;'>🌱 AGRI-FRIDAY AI</h1>
    <p style='color: #00ff88; font-family: Orbitron; font-size: 1.2em; margin: 5px 0;'>
        Smart Agriculture Assistant • Vision • Voice • RAG Knowledge Base
    </p>
</div>
""", unsafe_allow_html=True)

# Status Indicators
st.markdown("""
<div class='status-container'>
    <div style='text-align: center;'>
        <span class='status-indicator status-active' id='wake-status'>
            🎤 Wake Word: ACTIVE
        </span>
        <span class='status-indicator status-active' id='camera-status'>
            📹 Camera: ONLINE
        </span>
        <span class='status-indicator status-warning' id='object-status'>
            🔍 Detected: None
        </span>
        <span class='status-indicator status-active' id='rag-status'>
            📚 Knowledge Base: READY
        </span>
    </div>
</div>
""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════
# SIDEBAR - KNOWLEDGE BASE & SETTINGS
# ═══════════════════════════════════════════════════════════════════════════

with st.sidebar:
    st.markdown("### 🌾 AGRI-FRIDAY CONTROL PANEL")
    
    st.markdown("---")
    
    # Knowledge Base Upload
    st.markdown("### 📚 Knowledge Base (RAG)")
    st.markdown("Upload agriculture manuals, crop guides, or research papers:")
    
    uploaded_files = st.file_uploader(
        "Drag & Drop PDFs Here",
        type=['pdf'],
        accept_multiple_files=True,
        help="Upload PDF documents to expand Agri-Friday's knowledge"
    )
    
    if uploaded_files:
        for pdf in uploaded_files:
            if pdf.name not in [doc['name'] for doc in st.session_state.knowledge_base]:
                with st.spinner(f"Processing {pdf.name}..."):
                    success, message = process_pdf(pdf)
                    if success:
                        st.session_state.knowledge_base.append({
                            'name': pdf.name,
                            'size': f"{pdf.size / 1024:.1f} KB",
                            'uploaded': datetime.now().strftime("%Y-%m-%d %H:%M")
                        })
                        st.success(message)
    
    # Display loaded documents
    if st.session_state.knowledge_base:
        st.markdown("#### 📖 Loaded Documents:")
        for doc in st.session_state.knowledge_base:
            with st.expander(f"📄 {doc['name']}"):
                st.write(f"**Size:** {doc['size']}")
                st.write(f"**Uploaded:** {doc['uploaded']}")
                if st.button(f"🗑️ Remove", key=f"remove_{doc['name']}"):
                    st.session_state.knowledge_base.remove(doc)
                    st.rerun()
    else:
        st.info("No documents loaded yet. Upload PDFs to enable RAG.")
    
    st.markdown("---")
    
    # Settings
    st.markdown("### ⚙️ Settings")
    
    wake_word_enabled = st.toggle("🎤 Wake Word Detection", value=True)
    st.session_state.wake_word_active = wake_word_enabled
    
    camera_enabled = st.toggle("📹 Camera Feed", value=True)
    st.session_state.camera_active = camera_enabled
    
    tts_enabled = st.toggle("🔊 Text-to-Speech", value=True)
    
    st.markdown("---")
    
    # System Info
    st.markdown("### 📊 System Stats")
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Chat Messages", len(st.session_state.chat_history))
    with col2:
        st.metric("Documents", len(st.session_state.knowledge_base))
    
    st.markdown("---")
    
    # Clear Chat
    if st.button("🗑️ Clear Chat History", use_container_width=True):
        st.session_state.chat_history = []
        st.rerun()
    
    # About
    with st.expander("ℹ️ About Agri-Friday"):
        st.markdown("""
        **Agri-Friday** is an AI-powered agriculture assistant that combines:
        
        - 🌱 Computer Vision for crop/pest detection
        - 🧠 RAG (Retrieval-Augmented Generation) for knowledge
        - 🎤 Voice interaction for hands-free operation
        - 📱 Real-time guidance and recommendations
        
        Built for farmers, agronomists, and agricultural enthusiasts.
        """)

# ═══════════════════════════════════════════════════════════════════════════
# MAIN AREA - CAMERA FEED & CHAT INTERFACE
# ═══════════════════════════════════════════════════════════════════════════

# Create two columns for layout
col_camera, col_chat = st.columns([1, 1], gap="large")

# ─────────────────────────────────────────────────────────────────────────
# LEFT COLUMN: CAMERA FEED
# ─────────────────────────────────────────────────────────────────────────

with col_camera:
    st.markdown("### 📹 Live Vision Feed")
    st.markdown("*Real-time crop/pest detection and analysis*")
    
    # Camera controls
    col_cam1, col_cam2, col_cam3 = st.columns(3)
    with col_cam1:
        camera_start = st.button("▶️ Start Camera", use_container_width=True)
    with col_cam2:
        camera_stop = st.button("⏸️ Pause", use_container_width=True)
    with col_cam3:
        camera_snapshot = st.button("📸 Snapshot", use_container_width=True)
    
    # Camera feed placeholder
    camera_placeholder = st.empty()
    
    # Detection results
    st.markdown("#### 🔍 Detection Results")
    detection_placeholder = st.empty()
    
    if st.session_state.camera_active:
        # TODO: Replace with your actual camera feed
        # This is a placeholder - you'll integrate your cv2.VideoCapture logic
        
        try:
            # Open camera (replace with your camera initialization)
            cap = cv2.VideoCapture(0)
            ret, frame = cap.read()
            
            if ret:
                # Process frame
                processed_frame, detected_objects = process_frame(frame)
                
                # Convert BGR to RGB for display
                rgb_frame = cv2.cvtColor(processed_frame, cv2.COLOR_BGR2RGB)
                
                # Display in Streamlit
                camera_placeholder.image(rgb_frame, channels="RGB", use_container_width=True)
                
                # Update detected objects
                if detected_objects:
                    st.session_state.detected_object = ", ".join(detected_objects)
                    detection_placeholder.success(f"✅ Detected: {st.session_state.detected_object}")
                else:
                    detection_placeholder.info("👀 Monitoring... No objects detected yet.")
            else:
                camera_placeholder.error("❌ Failed to access camera. Check permissions.")
            
            cap.release()
            
        except Exception as e:
            camera_placeholder.error(f"❌ Camera Error: {str(e)}")
    else:
        camera_placeholder.info("📹 Camera is paused. Click 'Start Camera' to begin.")
        detection_placeholder.info("👀 Waiting for camera activation...")
    
    # Vision statistics
    st.markdown("#### 📊 Vision Stats")
    vis_col1, vis_col2, vis_col3 = st.columns(3)
    with vis_col1:
        st.metric("FPS", "30", delta="Stable")
    with vis_col2:
        st.metric("Confidence", "92%", delta="+5%")
    with vis_col3:
        st.metric("Objects", "2", delta="+1")

# ─────────────────────────────────────────────────────────────────────────
# RIGHT COLUMN: CHAT INTERFACE
# ─────────────────────────────────────────────────────────────────────────

with col_chat:
    st.markdown("### 💬 Agri-Friday Chat Assistant")
    st.markdown("*Ask questions about crops, pests, diseases, and farming practices*")
    
    # Chat display area
    chat_container = st.container(height=500)
    
    with chat_container:
        if not st.session_state.chat_history:
            st.markdown("""
            <div style='text-align: center; padding: 50px 20px; color: #00ff88;'>
                <h3>👋 Hello, Farmer!</h3>
                <p>I'm Agri-Friday, your AI agriculture assistant.</p>
                <p>Ask me anything about:</p>
                <ul style='text-align: left; display: inline-block;'>
                    <li>🌾 Crop diseases and pests</li>
                    <li>💧 Irrigation and soil management</li>
                    <li>🌱 Planting and harvesting tips</li>
                    <li>📊 Agricultural best practices</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)
        else:
            for msg in st.session_state.chat_history:
                if msg['role'] == 'user':
                    st.markdown(f"""
                    <div style='clear: both;'>
                        <div class='user-message'>
                            <strong>🧑‍🌾 You:</strong><br>{msg['content']}
                        </div>
                    </div>
                    <div style='clear: both; margin-bottom: 10px;'></div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown(f"""
                    <div style='clear: both;'>
                        <div class='ai-message'>
                            <strong>🌱 Agri-Friday:</strong><br>{msg['content']}
                        </div>
                    </div>
                    <div style='clear: both; margin-bottom: 10px;'></div>
                    """, unsafe_allow_html=True)
    
    # Input area
    st.markdown("---")
    
    input_col1, input_col2 = st.columns([4, 1])
    
    with input_col1:
        user_input = st.text_input(
            "Type your question...",
            key="user_input",
            placeholder="e.g., What are the signs of tomato blight?",
            label_visibility="collapsed"
        )
    
    with input_col2:
        voice_button = st.button("🎤 Voice", use_container_width=True)
    
    # Send button
    send_col1, send_col2 = st.columns([3, 1])
    with send_col2:
        send_button = st.button("📤 Send", use_container_width=True, type="primary")
    
    # Handle voice input
    if voice_button:
        with st.spinner("🎤 Listening..."):
            voice_text = speech_to_text()
            if voice_text and voice_text != "TODO: Integrate speech recognition":
                user_input = voice_text
                st.rerun()
    
    # Handle send
    if send_button and user_input:
        # Add user message
        st.session_state.chat_history.append({
            'role': 'user',
            'content': user_input,
            'timestamp': datetime.now().strftime("%H:%M")
        })
        
        # Get AI response
        with st.spinner("🤔 Agri-Friday is thinking..."):
            knowledge_docs = [doc['name'] for doc in st.session_state.knowledge_base] if st.session_state.knowledge_base else None
            ai_response = ask_ai(user_input, knowledge_docs)
        
        # Add AI response
        st.session_state.chat_history.append({
            'role': 'assistant',
            'content': ai_response,
            'timestamp': datetime.now().strftime("%H:%M")
        })
        
        # TTS if enabled
        if tts_enabled:
            text_to_speech(ai_response)
        
        st.rerun()
    
    # Quick suggestions
    st.markdown("#### 💡 Quick Questions:")
    quick_col1, quick_col2, quick_col3 = st.columns(3)
    
    with quick_col1:
        if st.button("🌾 Identify crop disease", use_container_width=True):
            st.session_state.chat_history.append({
                'role': 'user',
                'content': "What crop disease is this? (Use camera feed)",
                'timestamp': datetime.now().strftime("%H:%M")
            })
            st.rerun()
    
    with quick_col2:
        if st.button("💧 Irrigation advice", use_container_width=True):
            st.session_state.chat_history.append({
                'role': 'user',
                'content': "Give me irrigation recommendations for my crop",
                'timestamp': datetime.now().strftime("%H:%M")
            })
            st.rerun()
    
    with quick_col3:
        if st.button("🌱 Planting guide", use_container_width=True):
            st.session_state.chat_history.append({
                'role': 'user',
                'content': "What are the best practices for planting season?",
                'timestamp': datetime.now().strftime("%H:%M")
            })
            st.rerun()

# ═══════════════════════════════════════════════════════════════════════════
# FOOTER
# ═══════════════════════════════════════════════════════════════════════════

st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #00ff88; font-family: Orbitron; padding: 20px;'>
    <p>🌱 Agri-Friday AI • Empowering Farmers with Technology • Built with ❤️ for Agriculture</p>
    <p style='font-size: 0.8em; color: #666;'>
        Version 3.0 • Hackathon Edition • Powered by Computer Vision + RAG + Voice AI
    </p>
</div>
""", unsafe_allow_html=True)
