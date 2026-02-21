# 🌱 Agri-Friday AI Dashboard

**Smart Agriculture Assistant with Computer Vision, Voice AI, and RAG Knowledge Base**

A futuristic, hackathon-ready web dashboard for your Agri-Friday AI assistant. Features real-time camera feed, voice interaction, and RAG-powered knowledge base for agricultural guidance.

---

## 🚀 Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt --break-system-packages
```

### 2. Run the Dashboard

```bash
streamlit run agri_friday_dashboard.py
```

The dashboard will open automatically in your browser at `http://localhost:8501`

---

## 🎯 Features

### ✅ Core Features
- **📹 Live Camera Feed** - Real-time video with object detection overlay
- **🧠 RAG Knowledge Base** - Upload PDF agricultural manuals for context-aware responses
- **💬 Voice & Text Chat** - Interact with Agri-Friday via typing or voice commands
- **🔍 Object Detection** - Identify crops, pests, diseases from camera feed
- **📊 Status Dashboard** - Real-time monitoring of all system components
- **🎤 Wake Word Detection** - Hands-free activation (optional)

### 🎨 Design Highlights
- **Dark Theme** with vibrant green accents
- **Futuristic UI** inspired by Iron Man's JARVIS interface
- **Responsive Layout** with side-by-side camera and chat
- **Custom Orbitron Font** for that tech-forward look
- **Smooth Animations** and glowing effects

---

## 🔧 Integration Guide

### 📸 Integrate Your Camera/Object Detection

**Location:** `process_frame()` function (Line ~170)

Replace the placeholder with your existing computer vision code:

```python
def process_frame(frame):
    """Your existing CV2/YOLO/MediaPipe code goes here"""
    
    # Example with YOLO:
    from ultralytics import YOLO
    model = YOLO('your_crop_model.pt')
    results = model(frame)
    
    detected_objects = []
    for r in results:
        boxes = r.boxes
        for box in boxes:
            x1, y1, x2, y2 = box.xyxy[0]
            conf = box.conf[0]
            cls = int(box.cls[0])
            label = model.names[cls]
            
            # Draw bounding box
            cv2.rectangle(frame, (int(x1), int(y1)), (int(x2), int(y2)), (0, 255, 136), 2)
            cv2.putText(frame, f"{label} {conf:.2f}", (int(x1), int(y1)-10), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 136), 2)
            detected_objects.append(label)
    
    return frame, detected_objects
```

---

### 🧠 Integrate Your AI Brain (Groq + LangChain RAG)

**Location:** `ask_ai()` function (Line ~198)

Replace the placeholder with your existing Groq + LangChain pipeline:

```python
def ask_ai(query, knowledge_base=None):
    """Your existing Groq LLM + RAG code goes here"""
    
    from groq import Groq
    from langchain_groq import ChatGroq
    from langchain.chains import RetrievalQA
    from langchain_community.vectorstores import Chroma
    from langchain_community.embeddings import HuggingFaceEmbeddings
    
    # Initialize Groq LLM
    llm = ChatGroq(
        temperature=0.7,
        model_name="llama-3.3-70b-versatile",
        groq_api_key=os.getenv("GROQ_API_KEY")
    )
    
    # If knowledge base is available, use RAG
    if knowledge_base:
        # Load your vector store
        embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
        vectorstore = Chroma(persist_directory="./chroma_db", embedding_function=embeddings)
        
        # Create QA chain
        qa_chain = RetrievalQA.from_chain_type(
            llm=llm,
            chain_type="stuff",
            retriever=vectorstore.as_retriever(search_kwargs={"k": 3}),
            return_source_documents=True
        )
        
        result = qa_chain({"query": query})
        response = result["result"]
    else:
        # Direct LLM query without RAG
        response = llm.invoke(f"You are Agri-Friday, an agriculture AI assistant. {query}").content
    
    return response
```

---

### 📚 Integrate Your PDF Processing (RAG)

**Location:** `process_pdf()` function (Line ~232)

Replace with your LangChain document loaders:

```python
def process_pdf(pdf_file):
    """Your PDF processing + vector store code goes here"""
    
    from langchain_community.document_loaders import PyPDFLoader
    from langchain.text_splitter import RecursiveCharacterTextSplitter
    from langchain_community.vectorstores import Chroma
    from langchain_community.embeddings import HuggingFaceEmbeddings
    
    # Save PDF temporarily
    pdf_path = f"temp_{pdf_file.name}"
    with open(pdf_path, "wb") as f:
        f.write(pdf_file.getbuffer())
    
    # Load and split PDF
    loader = PyPDFLoader(pdf_path)
    documents = loader.load()
    
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
        length_function=len
    )
    chunks = text_splitter.split_documents(documents)
    
    # Create/update vector store
    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    vectorstore = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory="./chroma_db"
    )
    vectorstore.persist()
    
    # Clean up
    os.remove(pdf_path)
    
    return True, f"✅ Processed {len(chunks)} chunks from {pdf_file.name}"
```

---

### 🎤 Integrate Your Voice (TTS & STT)

**TTS Location:** `text_to_speech()` function (Line ~260)

```python
def text_to_speech(text):
    """Your edge-tts or pygame TTS code"""
    
    import edge_tts
    import asyncio
    import pygame
    
    async def _speak():
        communicate = edge_tts.Communicate(text, "en-IN-NeerjaNeural", rate="+5%")
        await communicate.save("output.mp3")
    
    asyncio.run(_speak())
    
    # Play audio
    pygame.mixer.init()
    pygame.mixer.music.load("output.mp3")
    pygame.mixer.music.play()
    
    while pygame.mixer.music.get_busy():
        pygame.time.Clock().tick(10)
    
    os.remove("output.mp3")
```

**STT Location:** `speech_to_text()` function (Line ~280)

```python
def speech_to_text():
    """Your speech recognition code"""
    
    import speech_recognition as sr
    
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        recognizer.adjust_for_ambient_noise(source, duration=0.5)
        audio = recognizer.listen(source, timeout=5, phrase_time_limit=10)
    
    try:
        text = recognizer.recognize_google(audio)
        return text
    except sr.UnknownValueError:
        return "Sorry, I couldn't understand that."
    except sr.RequestError:
        return "Speech recognition service unavailable."
```

---

## 📁 Project Structure

```
agri-friday-dashboard/
│
├── agri_friday_dashboard.py   # Main Streamlit app
├── requirements.txt            # Python dependencies
├── README.md                   # This file
│
├── knowledge_base/             # Uploaded PDFs (auto-created)
├── chroma_db/                  # Vector database (auto-created)
│
└── .env                        # API keys (create this)
```

---

## 🔑 Environment Variables

Create a `.env` file in the project root:

```env
# Groq API (Required for AI brain)
GROQ_API_KEY=your_groq_api_key_here

# Optional: OpenAI API
OPENAI_API_KEY=your_openai_key

# Optional: Anthropic Claude
ANTHROPIC_API_KEY=your_anthropic_key

# Optional: Picovoice Wake Word
PICOVOICE_ACCESS_KEY=your_picovoice_key

# Optional: Supabase (for cloud notes)
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_key
USER_EMAIL=your_email
USER_PASSWORD=your_password
```

---

## 🎮 Usage Tips

### Camera Feed
1. Click **"▶️ Start Camera"** to begin live detection
2. The camera will automatically process frames and detect objects
3. Detected items appear in the "Detection Results" box below

### Knowledge Base
1. Upload PDF agricultural manuals via the **sidebar**
2. PDFs are automatically processed and added to RAG
3. Ask questions, and Agri-Friday will reference uploaded documents

### Voice Chat
1. Type questions in the chat input box
2. Or click **"🎤 Voice"** to speak your question
3. Agri-Friday responds with text (and optional TTS audio)

### Quick Questions
Use the three **Quick Question** buttons for common queries:
- 🌾 Identify crop disease
- 💧 Irrigation advice
- 🌱 Planting guide

---

## 🐛 Troubleshooting

### Camera Not Working
```bash
# Check camera permissions
ls /dev/video*

# Test with OpenCV
python -c "import cv2; cap = cv2.VideoCapture(0); print(cap.read())"
```

### Dependencies Failing on Ubuntu/Raspberry Pi
```bash
# Install system packages first
sudo apt-get update
sudo apt-get install -y python3-opencv portaudio19-dev

# Then install Python packages
pip install -r requirements.txt --break-system-packages
```

### PyAudio Installation Issues
```bash
# Ubuntu/Debian
sudo apt-get install portaudio19-dev python3-pyaudio

# macOS
brew install portaudio
pip install pyaudio

# Windows
pip install pipwin
pipwin install pyaudio
```

---

## 🚀 Hackathon Demo Tips

### 1. Pre-load Knowledge Base
Before your demo, upload 2-3 relevant PDFs:
- Crop disease identification guide
- Pest management manual
- Irrigation best practices

### 2. Test Camera Angle
Position your camera to clearly show:
- Plant leaves (for disease detection)
- Soil conditions
- Crop growth stages

### 3. Prepare Demo Questions
Have these ready to showcase RAG:
- "What are the symptoms of tomato blight?" (tests PDF knowledge)
- "How often should I water my crops?" (tests general knowledge)
- "What's in the camera feed right now?" (tests vision integration)

### 4. Highlight Features
Emphasize:
- **Real-time detection** - Show camera identifying objects live
- **RAG knowledge** - Prove it's pulling from uploaded PDFs
- **Voice interaction** - Demo hands-free operation
- **Futuristic UI** - Judges love the Iron Man aesthetic!

---

## 📊 Performance Optimization

### For Faster Inference
```python
# Use quantized models for YOLO
model = YOLO('yolov8n.pt')  # 'n' = nano (fastest)

# Reduce camera resolution
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

# Limit Groq max_tokens
llm = ChatGroq(max_tokens=256)  # Faster responses
```

### For Raspberry Pi
```python
# Use smaller embedding model
embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

# Disable TTS if too slow
tts_enabled = False
```

---

## 🏆 Hackathon Judging Points

This dashboard scores high on:

✅ **Innovation** - RAG + Vision + Voice in agriculture  
✅ **Technical Complexity** - Multi-modal AI integration  
✅ **UI/UX** - Professional, futuristic design  
✅ **Practicality** - Solves real farmer problems  
✅ **Scalability** - Easy to add more features  

---

## 📝 License

MIT License - Feel free to use and modify for your hackathon!

---

## 🤝 Credits

Built with:
- Streamlit (Web Framework)
- OpenCV (Computer Vision)
- Groq LLM (AI Brain)
- LangChain (RAG Pipeline)
- Edge-TTS (Voice Synthesis)

---

## 📞 Support

If you encounter issues during integration:

1. Check the placeholder functions - they have TODO comments
2. Refer to your existing `friday_v3.py` for working examples
3. Test each component individually before combining

**Good luck with your hackathon! 🌱🚀**
