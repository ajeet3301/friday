"""
FRIDAY LIVE ADMIN PANEL
Control API keys, models, theme, knowledge base, and voice settings
Run: streamlit run friday_admin.py --server.port 8503
"""

import streamlit as st
import json
import os
from datetime import datetime
import hashlib
load_dotenv() 
# ADMIN CREDENTIALS
ADMIN_USER = os.getenv("ADMIN_USER")
ADMIN_PASS = os.getenv("ADMIN_PASS")

# CONFIG FILES
FRIDAY_CONFIG = "friday_config.json"
THEME_CONFIG = "friday_theme.json"
KNOWLEDGE_BASE = "friday_knowledge/"

# DEFAULTS
DEFAULT_CONFIG = {
    "groq_api_key": "",
    "chat_model": "llama-3.3-70b-versatile",
    "vision_model": "meta-llama/llama-4-scout-17b-16e-instruct",
    "whisper_model": "whisper-large-v3-turbo",
    "tts_voice": "en-IN-NeerjaNeural",
    "system_prompt": """You are Friday, a real-time AI voice assistant like JARVIS.
You can see through the camera.
Always speak in 1-3 short natural sentences.
Never use lists or bullets — just talk naturally.
Say Boss occasionally. Be sharp, helpful, and concise.""",
    "enable_rag": True,
    "max_tokens": 180,
    "temperature": 0.75
}

DEFAULT_THEME = {
    "primary_color": "#8ab4f8",
    "secondary_color": "#81c995",
    "red_color": "#f28b82",
    "background_image": "none",
    "background_blur": "2px",
    "glass_opacity": "0.08",
    "glass_blur": "20px",
    "vignette_intensity": "0.55"
}

def load_config(file, default):
    if os.path.exists(file):
        with open(file, 'r') as f:
            return json.load(f)
    return default.copy()

def save_config(file, config):
    with open(file, 'w') as f:
        json.dump(config, f, indent=2)

def check_login(username, password):
    return username == ADMIN_USER and hashlib.sha256(password.encode()).hexdigest() == hashlib.sha256(ADMIN_PASS.encode()).hexdigest()

def get_knowledge_files():
    if not os.path.exists(KNOWLEDGE_BASE):
        os.makedirs(KNOWLEDGE_BASE)
    files = []
    for f in os.listdir(KNOWLEDGE_BASE):
        if f.endswith(('.pdf', '.txt', '.md')):
            path = os.path.join(KNOWLEDGE_BASE, f)
            size = os.path.getsize(path)
            files.append({
                'name': f,
                'size': f"{size/1024:.1f} KB",
                'path': path,
                'modified': datetime.fromtimestamp(os.path.getmtime(path)).strftime("%Y-%m-%d %H:%M")
            })
    return sorted(files, key=lambda x: x['modified'], reverse=True)

def main():
    st.set_page_config(
        page_title="Friday Live Admin",
        page_icon="⚙️",
        layout="wide"
    )
    
    # Dark theme CSS
    st.markdown("""
    <style>
    .stApp {background: linear-gradient(135deg, #0f0c29 0%, #302b63 50%, #24243e 100%);}
    .block-container {background: rgba(255,255,255,0.05); backdrop-filter: blur(10px); 
                      border-radius: 20px; padding: 2rem !important;}
    h1, h2, h3 {color: #8ab4f8 !important; text-shadow: 0 0 20px rgba(138,180,248,0.5);}
    .stButton>button {background: rgba(138,180,248,0.15) !important; 
                      border: 1px solid rgba(138,180,248,0.3) !important; 
                      color: #8ab4f8 !important; border-radius: 12px !important;}
    .stTextInput>div>div>input, .stTextArea>div>div>textarea, select {
        background: rgba(255,255,255,0.05) !important; 
        border: 1px solid rgba(255,255,255,0.1) !important; 
        border-radius: 12px !important; color: #fff !important;}
    </style>
    """, unsafe_allow_html=True)
    
    # Session state
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False
    
    if 'config' not in st.session_state:
        st.session_state.config = load_config(FRIDAY_CONFIG, DEFAULT_CONFIG)
    
    if 'theme' not in st.session_state:
        st.session_state.theme = load_config(THEME_CONFIG, DEFAULT_THEME)
    
    # Login
    if not st.session_state.logged_in:
        st.markdown("<h1 style='text-align: center;'>🔐 FRIDAY ADMIN</h1>", unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            
            if st.button("Login", use_container_width=True, type="primary"):
                if check_login(username, password):
                    st.session_state.logged_in = True
                    st.rerun()
                else:
                    st.error("Invalid credentials")
            
            st.info("Default: admin / friday123")
        return
    
    # Header
    st.markdown("<h1 style='text-align: center;'>⚙️ FRIDAY LIVE ADMIN</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #8ab4f8;'>Control panel for Friday Live</p>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 6, 1])
    with col3:
        if st.button("🚪 Logout"):
            st.session_state.logged_in = False
            st.rerun()
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Tabs
    tabs = st.tabs(["🔑 API & Models", "🎨 Theme & UI", "📚 Knowledge Base", "🔊 Voice & Prompts"])
    
    # TAB 1: API & MODELS
    with tabs[0]:
        st.markdown("## 🔑 API Keys & Models")
        st.markdown("<br>", unsafe_allow_html=True)
        
        config = st.session_state.config.copy()
        
        # API Key
        st.markdown("### Groq API Key")
        config['groq_api_key'] = st.text_input(
            "API Key",
            value=config['groq_api_key'],
            type="password",
            help="Get free key at console.groq.com"
        )
        
        if config['groq_api_key']:
            st.success("✅ API Key configured")
        else:
            st.error("❌ API Key missing")
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Models
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### Chat Model")
            models = [
                "llama-3.3-70b-versatile",
                "llama-3.1-8b-instant",
                "mixtral-8x7b-32768",
                "gemma2-9b-it"
            ]
            config['chat_model'] = st.selectbox(
                "Select model",
                models,
                index=models.index(config['chat_model']) if config['chat_model'] in models else 0,
                label_visibility="collapsed"
            )
        
        with col2:
            st.markdown("### Vision Model")
            vision_models = [
                "meta-llama/llama-4-scout-17b-16e-instruct",
                "llama-3.2-11b-vision-preview",
                "llama-3.2-90b-vision-preview"
            ]
            config['vision_model'] = st.selectbox(
                "Select vision model",
                vision_models,
                index=vision_models.index(config['vision_model']) if config['vision_model'] in vision_models else 0,
                label_visibility="collapsed"
            )
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Parameters
        st.markdown("### LLM Parameters")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            config['max_tokens'] = st.number_input("Max Tokens", 50, 500, config['max_tokens'])
        
        with col2:
            config['temperature'] = st.slider("Temperature", 0.0, 1.0, config['temperature'], 0.05)
        
        with col3:
            config['enable_rag'] = st.toggle("Enable RAG", value=config['enable_rag'])
        
        st.markdown("<br><br>", unsafe_allow_html=True)
        
        if st.button("💾 Save API & Model Settings", use_container_width=True, type="primary"):
            save_config(FRIDAY_CONFIG, config)
            st.session_state.config = config
            st.success("✅ Saved! Restart Friday Live to apply changes")
    
    # TAB 2: THEME & UI
    with tabs[1]:
        st.markdown("## 🎨 Theme & UI Customization")
        st.markdown("<br>", unsafe_allow_html=True)
        
        theme = st.session_state.theme.copy()
        
        # Colors
        st.markdown("### Colors")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            theme['primary_color'] = st.color_picker("Primary (Blue)", theme['primary_color'])
        
        with col2:
            theme['secondary_color'] = st.color_picker("Secondary (Green)", theme['secondary_color'])
        
        with col3:
            theme['red_color'] = st.color_picker("Red (Recording)", theme['red_color'])
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Background
        st.markdown("### Background")
        
        bg_options = {
            "none": "Dark Gradient (Default)",
            "blur": "Camera Feed (Blurred)",
            "https://images.unsplash.com/photo-1419242902214-272b3f66ee7a?w=1920": "Space Stars",
            "https://images.unsplash.com/photo-1464822759023-fed622ff2c3b?w=1920": "Mountain Peak",
            "https://images.unsplash.com/photo-1558618666-fcd25c85cd64?w=1920": "Forest Path",
            "https://images.unsplash.com/photo-1506905925346-21bda4d32df4?w=1920": "Mountain Lake",
            "https://images.unsplash.com/photo-1534796636912-3b95b3ab5986?w=1920": "City Night",
        }
        
        selected_bg = st.selectbox(
            "Background Image",
            list(bg_options.keys()),
            format_func=lambda x: bg_options[x],
            index=list(bg_options.keys()).index(theme['background_image']) if theme['background_image'] in bg_options else 0
        )
        theme['background_image'] = selected_bg
        
        col1, col2 = st.columns(2)
        
        with col1:
            blur_val = int(theme['background_blur'].replace('px', ''))
            theme['background_blur'] = f"{st.slider('Background Blur (px)', 0, 20, blur_val)}px"
        
        with col2:
            theme['vignette_intensity'] = f"{st.slider('Vignette Intensity', 0.0, 1.0, float(theme['vignette_intensity']))}"
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Glass Effect
        st.markdown("### Glass Effect")
        col1, col2 = st.columns(2)
        
        with col1:
            opacity = float(theme['glass_opacity'])
            theme['glass_opacity'] = f"{st.slider('Glass Opacity', 0.0, 0.3, opacity, 0.01)}"
        
        with col2:
            blur = int(theme['glass_blur'].replace('px', ''))
            theme['glass_blur'] = f"{st.slider('Glass Blur (px)', 0, 40, blur)}px"
        
        st.markdown("<br><br>", unsafe_allow_html=True)
        
        # Preview
        st.markdown("### Preview")
        st.markdown(f"""
        <div style='background: linear-gradient(135deg, {theme['primary_color']}30 0%, {theme['secondary_color']}30 100%);
                    padding: 30px; border-radius: 20px; text-align: center;
                    backdrop-filter: blur({theme['glass_blur']});
                    border: 1px solid {theme['primary_color']}50;'>
            <div style='font-size: 2rem; color: {theme['primary_color']};'>✦</div>
            <div style='font-size: 1.2rem; color: #fff; margin-top: 10px;'>FRIDAY</div>
            <div style='display: inline-block; padding: 5px 15px; border-radius: 20px; margin-top: 10px;
                        background: rgba(255,255,255,{theme['glass_opacity']}); 
                        border: 1px solid {theme['secondary_color']}50;'>
                <span style='color: {theme['secondary_color']};'>● LIVE</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("<br><br>", unsafe_allow_html=True)
        
        if st.button("💾 Save Theme Settings", use_container_width=True, type="primary"):
            save_config(THEME_CONFIG, theme)
            st.session_state.theme = theme
            st.success("✅ Saved! Restart Friday Live to see changes")
    
    # TAB 3: KNOWLEDGE BASE
    with tabs[2]:
        st.markdown("## 📚 Knowledge Base (RAG)")
        st.markdown("<br>", unsafe_allow_html=True)
        
        st.markdown("### Upload Knowledge Files")
        st.info("Upload PDF, TXT, or MD files. Friday will use this knowledge when RAG is enabled.")
        
        uploaded_files = st.file_uploader(
            "Upload files",
            type=['pdf', 'txt', 'md'],
            accept_multiple_files=True,
            label_visibility="collapsed"
        )
        
        if uploaded_files:
            if not os.path.exists(KNOWLEDGE_BASE):
                os.makedirs(KNOWLEDGE_BASE)
            
            for file in uploaded_files:
                path = os.path.join(KNOWLEDGE_BASE, file.name)
                with open(path, 'wb') as f:
                    f.write(file.getbuffer())
                st.success(f"✅ Uploaded: {file.name}")
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Existing files
        st.markdown("### Existing Knowledge Files")
        files = get_knowledge_files()
        
        if files:
            st.markdown(f"**{len(files)} files in knowledge base**")
            st.markdown("<br>", unsafe_allow_html=True)
            
            for file in files:
                col1, col2, col3, col4 = st.columns([4, 2, 2, 1])
                
                with col1:
                    st.markdown(f"**📄 {file['name']}**")
                
                with col2:
                    st.text(file['size'])
                
                with col3:
                    st.text(file['modified'])
                
                with col4:
                    if st.button("🗑️", key=f"del_{file['name']}"):
                        os.remove(file['path'])
                        st.rerun()
                
                st.divider()
        else:
            st.info("No files uploaded yet")
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        if files:
            if st.button("🗑️ Delete All Files", use_container_width=True):
                for file in files:
                    os.remove(file['path'])
                st.success("✅ All files deleted")
                st.rerun()
    
    # TAB 4: VOICE & PROMPTS
    with tabs[3]:
        st.markdown("## 🔊 Voice & System Prompts")
        st.markdown("<br>", unsafe_allow_html=True)
        
        config = st.session_state.config.copy()
        
        # TTS Voice
        st.markdown("### Friday's Voice")
        voices = {
            "en-IN-NeerjaNeural": "🇮🇳 Indian English - Neerja (Female)",
            "en-IN-PrabhatNeural": "🇮🇳 Indian English - Prabhat (Male)",
            "en-US-JennyNeural": "🇺🇸 US English - Jenny (Female)",
            "en-US-GuyNeural": "🇺🇸 US English - Guy (Male)",
            "en-GB-SoniaNeural": "🇬🇧 UK English - Sonia (Female)",
            "en-GB-RyanNeural": "🇬🇧 UK English - Ryan (Male)",
            "hi-IN-SwaraNeural": "🇮🇳 Hindi - Swara (Female)",
            "hi-IN-MadhurNeural": "🇮🇳 Hindi - Madhur (Male)"
        }
        
        config['tts_voice'] = st.selectbox(
            "Select TTS Voice",
            list(voices.keys()),
            format_func=lambda x: voices[x],
            index=list(voices.keys()).index(config['tts_voice']) if config['tts_voice'] in voices else 0
        )
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Whisper Model
        st.markdown("### Speech Recognition Model")
        whisper_models = [
            "whisper-large-v3-turbo",
            "whisper-large-v3"
        ]
        config['whisper_model'] = st.selectbox(
            "Whisper Model",
            whisper_models,
            index=whisper_models.index(config['whisper_model']) if config['whisper_model'] in whisper_models else 0
        )
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # System Prompt
        st.markdown("### System Prompt (Friday's Personality)")
        config['system_prompt'] = st.text_area(
            "System Prompt",
            value=config['system_prompt'],
            height=200,
            label_visibility="collapsed"
        )
        
        st.markdown("<br><br>", unsafe_allow_html=True)
        
        if st.button("💾 Save Voice & Prompt Settings", use_container_width=True, type="primary"):
            save_config(FRIDAY_CONFIG, config)
            st.session_state.config = config
            st.success("✅ Saved! Restart Friday Live to apply changes")

if __name__ == "__main__":
    main()
