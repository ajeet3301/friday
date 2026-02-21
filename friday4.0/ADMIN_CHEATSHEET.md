# ADMIN PANEL QUICK REFERENCE

## START

```bash
# Admin Panel
streamlit run admin.py --server.port 8502

# User App  
streamlit run app_with_admin.py

# Login: admin / admin123
```

## FEATURES

### 📊 Dashboard
- Metrics: PDFs, storage, API status
- Recent uploads list
- Quick action buttons

### 📚 PDF Management
**Upload:** Drag-drop PDFs  
**Delete:** Click 🗑️ button  
**Search:** Filter by name  
**Bulk:** Delete all option

### 🎨 Theme
**Colors:**
- Primary color
- Background gradients (start/mid/end)

**Glass:**
- Opacity (0.0 - 0.2)
- Blur (0 - 30px)

**Typography:**
- Font family (Inter, Roboto, etc.)

**Branding:**
- App name
- Tagline

**Actions:**
- 💾 Save theme
- 🔄 Reset to default
- 👁️ Live preview

### ⚙️ Settings
**Features:**
- Camera on/off
- Voice on/off
- RAG on/off

**Models:**
- Groq: llama-3.3-70b-versatile
- Whisper: whisper-large-v3-turbo

**Parameters:**
- Max tokens: 100-2000
- Temperature: 0.0-1.0
- Chunk size: 500-2000
- Chunk overlap: 0-500

**Limits:**
- Max PDFs: 1-1000

### 🔑 API Keys
**Check:**
- View status (✅/❌)
- Test connection

**Setup:**
```bash
echo "GROQ_API_KEY=gsk_key" > .env
```

## FILE STRUCTURE

```
project/
├── admin.py              # Admin panel
├── app_with_admin.py     # User app
├── .env                  # API key
├── theme_config.json     # Theme (auto)
├── settings_config.json  # Settings (auto)
└── knowledge_base/       # PDFs (auto)
```

## WORKFLOW

1. Login to admin (8502)
2. Upload PDFs
3. Customize theme
4. Change settings
5. Save
6. Open user app (8501)
7. Changes applied!

## CHANGE PASSWORD

**admin.py line 14-15:**
```python
ADMIN_USERNAME = "new_user"
ADMIN_PASSWORD = "new_pass"
```

## PORTS

| App | URL |
|-----|-----|
| User | http://localhost:8501 |
| Admin | http://localhost:8502 |

## TIPS

✅ Save theme after changes  
✅ Test API before using  
✅ Upload PDFs before testing RAG  
✅ Restart user app after config changes  
✅ Use different browsers for admin/user  

## KEYBOARD SHORTCUTS

| Key | Action |
|-----|--------|
| Ctrl+R | Reload app |
| Ctrl+K | Clear screen |
| Ctrl+C | Stop server |
