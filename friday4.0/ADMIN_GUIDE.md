# AGRI-FRIDAY WITH ADMIN PANEL

## SETUP

```bash
pip install -r requirements_minimal.txt --break-system-packages
echo "GROQ_API_KEY=your_key_here" > .env
```

## RUN

### Admin Panel (Port 8502)
```bash
streamlit run admin.py --server.port 8502
```

**Login:** admin / admin123

### User App (Port 8501)
```bash
streamlit run app_with_admin.py
```

## ADMIN FEATURES

### 📊 Dashboard
- View metrics (PDFs, storage, API status)
- Recent uploads
- Quick actions

### 📚 PDF Management
- Upload PDFs
- View/delete existing PDFs
- Search PDFs
- Bulk operations

### 🎨 Theme Customization
- App name & tagline
- Colors (primary, background gradient)
- Glass effect (opacity, blur)
- Typography (font family)
- Live preview
- Save/reset

### ⚙️ Settings
- Toggle features (camera, voice, RAG)
- AI models (Groq, Whisper)
- LLM parameters (tokens, temperature)
- RAG settings (chunk size, overlap)
- Limits (max PDFs)

### 🔑 API Keys
- View API status
- Setup instructions
- Test connection

## FILES

- `admin.py` - Admin panel (login, management)
- `app_with_admin.py` - User app (reads admin configs)
- `theme_config.json` - Theme settings (auto-created)
- `settings_config.json` - App settings (auto-created)
- `knowledge_base/` - PDF folder (auto-created)

## HOW IT WORKS

1. Admin customizes theme in admin panel
2. Admin uploads PDFs
3. Admin changes settings
4. User app reads configs automatically
5. User sees customized theme & PDFs

## CHANGE PASSWORD

Edit line 14-15 in `admin.py`:
```python
ADMIN_USERNAME = "your_username"
ADMIN_PASSWORD = "your_password"
```

## PORTS

- User App: http://localhost:8501
- Admin Panel: http://localhost:8502

## DEMO WORKFLOW

1. Open admin panel (8502)
2. Login (admin/admin123)
3. Upload PDFs
4. Customize theme (change colors, name)
5. Save
6. Open user app (8501)
7. See custom theme & uploaded PDFs
