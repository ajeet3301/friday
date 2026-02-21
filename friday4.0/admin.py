"""
AGRI-FRIDAY ADMIN PANEL
Features: Login | PDF Management | Theme Customization | Settings
"""

import streamlit as st
import json
import os
from datetime import datetime
import hashlib
from pathlib import Path

# ADMIN CREDENTIALS (Change these!)
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin123"  # Change this password!

# CONFIG FILES
THEME_CONFIG = "theme_config.json"
SETTINGS_CONFIG = "settings_config.json"
PDF_FOLDER = "knowledge_base"

# Default theme
DEFAULT_THEME = {
    "primary_color": "#00ff88",
    "background_gradient_start": "#0f0c29",
    "background_gradient_mid": "#302b63",
    "background_gradient_end": "#24243e",
    "glass_opacity": "0.05",
    "glass_blur": "10px",
    "font_family": "Inter",
    "app_name": "AGRI-FRIDAY",
    "app_tagline": "AI Agriculture Assistant"
}

# Default settings
DEFAULT_SETTINGS = {
    "enable_camera": True,
    "enable_voice": True,
    "enable_rag": True,
    "max_pdfs": 50,
    "groq_model": "llama-3.3-70b-versatile",
    "whisper_model": "whisper-large-v3-turbo",
    "embedding_model": "sentence-transformers/all-MiniLM-L6-v2",
    "max_tokens": 500,
    "temperature": 0.7,
    "chunk_size": 1000,
    "chunk_overlap": 200
}

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def check_login(username, password):
    return username == ADMIN_USERNAME and hash_password(password) == hash_password(ADMIN_PASSWORD)

def load_config(config_file, default):
    if os.path.exists(config_file):
        with open(config_file, 'r') as f:
            return json.load(f)
    return default.copy()

def save_config(config_file, config):
    with open(config_file, 'w') as f:
        json.dump(config, f, indent=2)

def get_pdf_files():
    if not os.path.exists(PDF_FOLDER):
        os.makedirs(PDF_FOLDER)
    pdfs = []
    for file in os.listdir(PDF_FOLDER):
        if file.endswith('.pdf'):
            path = os.path.join(PDF_FOLDER, file)
            size = os.path.getsize(path)
            modified = datetime.fromtimestamp(os.path.getmtime(path))
            pdfs.append({
                'name': file,
                'size': f"{size/1024:.1f} KB",
                'modified': modified.strftime("%Y-%m-%d %H:%M"),
                'path': path
            })
    return sorted(pdfs, key=lambda x: x['modified'], reverse=True)

def delete_pdf(filename):
    path = os.path.join(PDF_FOLDER, filename)
    if os.path.exists(path):
        os.remove(path)
        return True
    return False

def generate_theme_css(theme):
    return f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family={theme['font_family'].replace(' ', '+')}:wght@300;400;600;700&display=swap');
    
    .stApp {{
        background: linear-gradient(135deg, 
            {theme['background_gradient_start']} 0%, 
            {theme['background_gradient_mid']} 50%, 
            {theme['background_gradient_end']} 100%);
        font-family: '{theme['font_family']}', sans-serif;
    }}
    
    .block-container {{
        background: rgba(255, 255, 255, {theme['glass_opacity']});
        backdrop-filter: blur({theme['glass_blur']});
        border-radius: 20px;
        padding: 2rem !important;
    }}
    
    h1, h2, h3 {{
        color: {theme['primary_color']} !important;
        text-shadow: 0 0 20px {theme['primary_color']}80;
        font-family: '{theme['font_family']}', sans-serif;
    }}
    
    section[data-testid="stSidebar"] {{
        background: rgba(255, 255, 255, {theme['glass_opacity']}) !important;
        backdrop-filter: blur(15px) !important;
    }}
    
    section[data-testid="stSidebar"] > div {{
        background: transparent !important;
    }}
    
    .stButton>button {{
        background: rgba(0, 255, 136, 0.15) !important;
        backdrop-filter: blur(10px);
        border: 1px solid {theme['primary_color']}50 !important;
        border-radius: 12px !important;
        color: {theme['primary_color']} !important;
        font-weight: 600 !important;
        transition: all 0.3s ease !important;
    }}
    
    .stButton>button:hover {{
        background: rgba(0, 255, 136, 0.25) !important;
        border: 1px solid {theme['primary_color']} !important;
        transform: translateY(-2px);
        box-shadow: 0 6px 20px {theme['primary_color']}60 !important;
    }}
    
    .stTextInput>div>div>input, .stTextArea>div>div>textarea {{
        background: rgba(255, 255, 255, 0.05) !important;
        backdrop-filter: blur(10px) !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        border-radius: 12px !important;
        color: #ffffff !important;
    }}
    
    div[data-testid="stMetricValue"] {{
        color: {theme['primary_color']} !important;
    }}
    
    .uploadedFile {{
        background: rgba(0, 255, 136, 0.1) !important;
        backdrop-filter: blur(10px) !important;
        border: 1px solid {theme['primary_color']}30 !important;
        border-radius: 12px !important;
    }}
    </style>
    """

def main():
    st.set_page_config(
        page_title="Agri-Friday Admin",
        page_icon="⚙️",
        layout="wide"
    )
    
    # Initialize session state
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False
    
    if 'theme' not in st.session_state:
        st.session_state.theme = load_config(THEME_CONFIG, DEFAULT_THEME)
    
    if 'settings' not in st.session_state:
        st.session_state.settings = load_config(SETTINGS_CONFIG, DEFAULT_SETTINGS)
    
    # Apply theme
    st.markdown(generate_theme_css(st.session_state.theme), unsafe_allow_html=True)
    
    # Login check
    if not st.session_state.logged_in:
        show_login()
    else:
        show_admin_panel()

def show_login():
    st.markdown("<h1 style='text-align: center;'>🔐 ADMIN LOGIN</h1>", unsafe_allow_html=True)
    st.markdown("<br><br>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("### Enter Credentials")
        username = st.text_input("Username", key="login_username")
        password = st.text_input("Password", type="password", key="login_password")
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        if st.button("🔓 Login", use_container_width=True, type="primary"):
            if check_login(username, password):
                st.session_state.logged_in = True
                st.success("✅ Login successful!")
                st.rerun()
            else:
                st.error("❌ Invalid credentials")
        
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.info("💡 Default: admin / admin123")

def show_admin_panel():
    # Header
    st.markdown(f"<h1 style='text-align: center;'>⚙️ ADMIN PANEL</h1>", unsafe_allow_html=True)
    st.markdown(f"<p style='text-align: center; color: {st.session_state.theme['primary_color']};'>Manage {st.session_state.theme['app_name']}</p>", unsafe_allow_html=True)
    
    # Logout button
    col1, col2, col3 = st.columns([1, 6, 1])
    with col3:
        if st.button("🚪 Logout"):
            st.session_state.logged_in = False
            st.rerun()
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Navigation
    tabs = st.tabs(["📊 Dashboard", "📚 PDF Management", "🎨 Theme", "⚙️ Settings", "🔑 API Keys"])
    
    with tabs[0]:
        show_dashboard()
    
    with tabs[1]:
        show_pdf_management()
    
    with tabs[2]:
        show_theme_customization()
    
    with tabs[3]:
        show_settings()
    
    with tabs[4]:
        show_api_keys()

def show_dashboard():
    st.markdown("## 📊 Dashboard Overview")
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Metrics
    pdfs = get_pdf_files()
    total_size = sum([float(pdf['size'].split()[0]) for pdf in pdfs])
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("📚 Total PDFs", len(pdfs))
    
    with col2:
        st.metric("💾 Storage Used", f"{total_size:.1f} KB")
    
    with col3:
        st.metric("🎨 Theme", "Custom" if os.path.exists(THEME_CONFIG) else "Default")
    
    with col4:
        st.metric("🔑 API Status", "✅ Configured" if os.getenv("GROQ_API_KEY") else "⚠️ Missing")
    
    st.markdown("<br><br>", unsafe_allow_html=True)
    
    # Recent PDFs
    st.markdown("### 📄 Recent Uploads")
    if pdfs:
        for pdf in pdfs[:5]:
            with st.expander(f"📄 {pdf['name']}"):
                col1, col2 = st.columns(2)
                with col1:
                    st.text(f"Size: {pdf['size']}")
                with col2:
                    st.text(f"Modified: {pdf['modified']}")
    else:
        st.info("No PDFs uploaded yet")
    
    st.markdown("<br><br>", unsafe_allow_html=True)
    
    # Quick Actions
    st.markdown("### ⚡ Quick Actions")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📤 Upload PDF", use_container_width=True):
            st.session_state.active_tab = 1
            st.rerun()
    
    with col2:
        if st.button("🎨 Customize Theme", use_container_width=True):
            st.session_state.active_tab = 2
            st.rerun()
    
    with col3:
        if st.button("⚙️ Update Settings", use_container_width=True):
            st.session_state.active_tab = 3
            st.rerun()

def show_pdf_management():
    st.markdown("## 📚 PDF Knowledge Base Management")
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Upload section
    st.markdown("### 📤 Upload New PDFs")
    uploaded_files = st.file_uploader(
        "Drag and drop PDFs here",
        type=['pdf'],
        accept_multiple_files=True,
        help="Upload agricultural manuals, research papers, or any knowledge documents"
    )
    
    if uploaded_files:
        if not os.path.exists(PDF_FOLDER):
            os.makedirs(PDF_FOLDER)
        
        for uploaded_file in uploaded_files:
            file_path = os.path.join(PDF_FOLDER, uploaded_file.name)
            
            if not os.path.exists(file_path):
                with open(file_path, 'wb') as f:
                    f.write(uploaded_file.getbuffer())
                st.success(f"✅ Uploaded: {uploaded_file.name}")
            else:
                st.warning(f"⚠️ File already exists: {uploaded_file.name}")
    
    st.markdown("<br><br>", unsafe_allow_html=True)
    
    # Existing PDFs
    st.markdown("### 📋 Existing PDFs")
    pdfs = get_pdf_files()
    
    if pdfs:
        st.markdown(f"**Total: {len(pdfs)} documents**")
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Search filter
        search = st.text_input("🔍 Search PDFs", placeholder="Search by filename...")
        
        filtered_pdfs = [pdf for pdf in pdfs if search.lower() in pdf['name'].lower()] if search else pdfs
        
        # Display PDFs
        for pdf in filtered_pdfs:
            col1, col2, col3, col4, col5 = st.columns([3, 2, 2, 1, 1])
            
            with col1:
                st.markdown(f"**📄 {pdf['name']}**")
            
            with col2:
                st.text(pdf['size'])
            
            with col3:
                st.text(pdf['modified'])
            
            with col4:
                if st.button("👁️", key=f"view_{pdf['name']}", help="View details"):
                    st.info(f"Path: {pdf['path']}")
            
            with col5:
                if st.button("🗑️", key=f"delete_{pdf['name']}", help="Delete PDF"):
                    if delete_pdf(pdf['name']):
                        st.success(f"✅ Deleted: {pdf['name']}")
                        st.rerun()
                    else:
                        st.error("❌ Delete failed")
            
            st.divider()
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Bulk actions
        st.markdown("### 🔧 Bulk Actions")
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("🗑️ Delete All PDFs", use_container_width=True):
                st.warning("⚠️ This will delete ALL PDFs!")
                if st.button("✅ Confirm Delete All"):
                    for pdf in pdfs:
                        delete_pdf(pdf['name'])
                    st.success("✅ All PDFs deleted")
                    st.rerun()
        
        with col2:
            total_size = sum([float(pdf['size'].split()[0]) for pdf in pdfs])
            st.metric("Total Storage", f"{total_size:.1f} KB")
    
    else:
        st.info("📭 No PDFs uploaded yet. Upload some documents to get started!")

def show_theme_customization():
    st.markdown("## 🎨 Theme Customization")
    st.markdown("<br>", unsafe_allow_html=True)
    
    theme = st.session_state.theme.copy()
    
    # App branding
    st.markdown("### 🏷️ App Branding")
    col1, col2 = st.columns(2)
    
    with col1:
        theme['app_name'] = st.text_input("App Name", value=theme['app_name'])
    
    with col2:
        theme['app_tagline'] = st.text_input("Tagline", value=theme['app_tagline'])
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Colors
    st.markdown("### 🎨 Colors")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        theme['primary_color'] = st.color_picker("Primary Color", value=theme['primary_color'])
    
    with col2:
        theme['background_gradient_start'] = st.color_picker("Background Start", value=theme['background_gradient_start'])
    
    with col3:
        theme['background_gradient_end'] = st.color_picker("Background End", value=theme['background_gradient_end'])
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Glass effect
    st.markdown("### ✨ Glass Effect")
    col1, col2 = st.columns(2)
    
    with col1:
        opacity = st.slider("Glass Opacity", 0.0, 0.2, float(theme['glass_opacity']), 0.01)
        theme['glass_opacity'] = str(opacity)
    
    with col2:
        blur = st.slider("Glass Blur (px)", 0, 30, int(theme['glass_blur'].replace('px', '')))
        theme['glass_blur'] = f"{blur}px"
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Typography
    st.markdown("### 🔤 Typography")
    fonts = ["Inter", "Roboto", "Poppins", "Montserrat", "Open Sans", "Lato", "Raleway", "Nunito"]
    theme['font_family'] = st.selectbox("Font Family", fonts, index=fonts.index(theme['font_family']) if theme['font_family'] in fonts else 0)
    
    st.markdown("<br><br>", unsafe_allow_html=True)
    
    # Preview
    st.markdown("### 👁️ Preview")
    with st.container():
        st.markdown(generate_theme_css(theme), unsafe_allow_html=True)
        st.markdown(f"<h2>{theme['app_name']}</h2>", unsafe_allow_html=True)
        st.markdown(f"<p style='color: {theme['primary_color']};'>{theme['app_tagline']}</p>", unsafe_allow_html=True)
        st.button("Sample Button")
    
    st.markdown("<br><br>", unsafe_allow_html=True)
    
    # Save buttons
    col1, col2, col3 = st.columns([1, 1, 2])
    
    with col1:
        if st.button("💾 Save Theme", use_container_width=True, type="primary"):
            save_config(THEME_CONFIG, theme)
            st.session_state.theme = theme
            st.success("✅ Theme saved!")
            st.rerun()
    
    with col2:
        if st.button("🔄 Reset to Default", use_container_width=True):
            if os.path.exists(THEME_CONFIG):
                os.remove(THEME_CONFIG)
            st.session_state.theme = DEFAULT_THEME.copy()
            st.success("✅ Reset to default theme")
            st.rerun()

def show_settings():
    st.markdown("## ⚙️ Application Settings")
    st.markdown("<br>", unsafe_allow_html=True)
    
    settings = st.session_state.settings.copy()
    
    # Feature toggles
    st.markdown("### 🎛️ Feature Toggles")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        settings['enable_camera'] = st.toggle("📹 Camera", value=settings['enable_camera'])
    
    with col2:
        settings['enable_voice'] = st.toggle("🎤 Voice", value=settings['enable_voice'])
    
    with col3:
        settings['enable_rag'] = st.toggle("📚 RAG", value=settings['enable_rag'])
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # AI Models
    st.markdown("### 🤖 AI Models")
    col1, col2 = st.columns(2)
    
    with col1:
        groq_models = [
            "llama-3.3-70b-versatile",
            "llama-3.1-70b-versatile",
            "mixtral-8x7b-32768",
            "gemma2-9b-it"
        ]
        settings['groq_model'] = st.selectbox("Groq Model", groq_models, index=groq_models.index(settings['groq_model']))
    
    with col2:
        whisper_models = [
            "whisper-large-v3-turbo",
            "whisper-large-v3"
        ]
        settings['whisper_model'] = st.selectbox("Whisper Model", whisper_models, index=whisper_models.index(settings['whisper_model']))
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # LLM parameters
    st.markdown("### 🎚️ LLM Parameters")
    col1, col2 = st.columns(2)
    
    with col1:
        settings['max_tokens'] = st.number_input("Max Tokens", 100, 2000, settings['max_tokens'], 50)
        settings['temperature'] = st.slider("Temperature", 0.0, 1.0, settings['temperature'], 0.1)
    
    with col2:
        settings['chunk_size'] = st.number_input("Chunk Size", 500, 2000, settings['chunk_size'], 100)
        settings['chunk_overlap'] = st.number_input("Chunk Overlap", 0, 500, settings['chunk_overlap'], 50)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Limits
    st.markdown("### 🔢 Limits")
    settings['max_pdfs'] = st.number_input("Max PDFs", 1, 1000, settings['max_pdfs'])
    
    st.markdown("<br><br>", unsafe_allow_html=True)
    
    # Save buttons
    col1, col2, col3 = st.columns([1, 1, 2])
    
    with col1:
        if st.button("💾 Save Settings", use_container_width=True, type="primary"):
            save_config(SETTINGS_CONFIG, settings)
            st.session_state.settings = settings
            st.success("✅ Settings saved!")
    
    with col2:
        if st.button("🔄 Reset to Default", use_container_width=True):
            if os.path.exists(SETTINGS_CONFIG):
                os.remove(SETTINGS_CONFIG)
            st.session_state.settings = DEFAULT_SETTINGS.copy()
            st.success("✅ Reset to default settings")
            st.rerun()

def show_api_keys():
    st.markdown("## 🔑 API Keys Configuration")
    st.markdown("<br>", unsafe_allow_html=True)
    
    st.warning("⚠️ Store API keys in .env file, not here!")
    
    # Check current status
    st.markdown("### 📊 Current Status")
    
    groq_key = os.getenv("GROQ_API_KEY", "")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric("Groq API", "✅ Configured" if groq_key else "❌ Missing")
    
    with col2:
        if groq_key:
            st.text(f"Key: {groq_key[:10]}...{groq_key[-5:]}")
    
    st.markdown("<br><br>", unsafe_allow_html=True)
    
    # Instructions
    st.markdown("### 📝 Setup Instructions")
    
    st.code("""
# Create .env file in project root:
echo "GROQ_API_KEY=gsk_your_key_here" > .env

# Get free key at:
# https://console.groq.com/keys
    """, language="bash")
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    st.info("💡 Restart the app after creating .env file")
    
    st.markdown("<br><br>", unsafe_allow_html=True)
    
    # Test connection
    st.markdown("### 🧪 Test Connection")
    
    if st.button("🔌 Test Groq API", use_container_width=True):
        if groq_key:
            try:
                from groq import Groq
                client = Groq(api_key=groq_key)
                response = client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[{"role": "user", "content": "Hello"}],
                    max_tokens=10
                )
                st.success("✅ Groq API connection successful!")
            except Exception as e:
                st.error(f"❌ Connection failed: {e}")
        else:
            st.error("❌ GROQ_API_KEY not set")

if __name__ == "__main__":
    main()
