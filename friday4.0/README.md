# FRIDAY LIVE WITH ADMIN PANEL

## SETUP

```bash
pip install streamlit python-dotenv
```

## RUN

### Admin Panel (Port 8503)
```bash
streamlit run friday_admin.py --server.port 8503
```
**Login:** admin / friday123

### Friday Live (Port 8501)
```bash
streamlit run friday_live.py
```

## FEATURES

### ADMIN PANEL (8503)
**🔑 API & Models**
- Groq API key configuration
- Chat model selection
- Vision model selection
- Whisper model selection
- LLM parameters (tokens, temperature)
- Enable/disable RAG

**🎨 Theme & UI**
- Primary/secondary/red colors
- Background image selection
  - Dark gradient (default)
  - Camera blur
  - Space stars
  - Mountains
  - Forest
  - City night
- Background blur control
- Vignette intensity
- Glass effect (opacity, blur)
- Live preview

**📚 Knowledge Base**
- Upload PDF/TXT/MD files
- View all files
- Delete files
- Files used for RAG when enabled

**🔊 Voice & Prompts**
- TTS voice selection (8 voices)
  - 🇮🇳 Indian English (Neerja, Prabhat)
  - 🇺🇸 US English (Jenny, Guy)
  - 🇬🇧 UK English (Sonia, Ryan)
  - 🇮🇳 Hindi (Swara, Madhur)
- Whisper model
- System prompt (personality)

### USER APP (8501)
- Full-screen camera view
- Tap mic to talk
- Voice responses
- Camera analysis (📸 button)
- Flip camera (🔄 button)
- No settings (all controlled by admin)

## WORKFLOW

1. **Admin** configures settings (port 8503)
   - Set API key
   - Choose models
   - Upload knowledge files
   - Customize theme
   - Set voice

2. **Save** configurations

3. **Restart** Friday Live (port 8501)

4. **Users** access Friday Live
   - Just tap mic and talk
   - Can't change settings
   - Clean, simple interface

## FILES

```
project/
├── friday_admin.py          # Admin panel
├── friday_live.py           # User app
├── friday_config.json       # Config (auto-created)
├── friday_theme.json        # Theme (auto-created)
└── friday_knowledge/        # Knowledge files (auto-created)
```

## CHANGE ADMIN PASSWORD

**friday_admin.py lines 16-17:**
```python
ADMIN_USER = "your_username"
ADMIN_PASS = "your_password"
```

## PORTS

| App | URL |
|-----|-----|
| Friday Live | http://localhost:8501 |
| Admin | http://localhost:8503 |

## MOBILE ACCESS

Users can access Friday Live on their phones:

```bash
# Find your local IP
# Linux/Mac: ifconfig | grep "inet "
# Windows: ipconfig

# Run Friday Live with network access
streamlit run friday_live.py --server.address 0.0.0.0

# Users open on phone:
# http://YOUR_IP:8501
```

## QUICK START

```bash
# Terminal 1 - Admin
streamlit run friday_admin.py --server.port 8503

# Terminal 2 - User App
streamlit run friday_live.py

# Open browser:
# Admin: localhost:8503
# User: localhost:8501
```

## FEATURES CHECKLIST

✅ API key hidden from users  
✅ Model selection (admin only)  
✅ Theme customization (7 themes)  
✅ Wallpaper selection  
✅ Blur control  
✅ RAG knowledge base  
✅ PDF/TXT upload  
✅ Voice selection (8 voices)  
✅ System prompt control  
✅ Mobile-friendly  
✅ No user settings panel  

## DONE
