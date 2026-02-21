"""
═══════════════════════════════════════════════════════════════════════════
AGRI-FRIDAY INTEGRATION EXAMPLE
═══════════════════════════════════════════════════════════════════════════

This file shows how to adapt your existing friday_v3.py code components
for use in the Streamlit dashboard. Copy the relevant sections into
agri_friday_dashboard.py placeholder functions.
"""

import os
import cv2
import numpy as np
from dotenv import load_dotenv

load_dotenv()

# ═══════════════════════════════════════════════════════════════════════════
# 1. CAMERA / OBJECT DETECTION INTEGRATION
# ═══════════════════════════════════════════════════════════════════════════

def integrate_vision_from_friday():
    """
    Example: Adapt FridayVision class for Streamlit
    
    In your agri_friday_dashboard.py, replace process_frame() with:
    """
    
    def process_frame(frame):
        """Enhanced version using your existing vision code"""
        
        # Import your existing vision components
        # from friday_v3 import ASLInterpreter, FridayVision
        
        # Option 1: Use MediaPipe for hand gesture detection
        import mediapipe as mp
        
        mp_hands = mp.solutions.hands
        hands = mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=2,
            min_detection_confidence=0.75,
            min_tracking_confidence=0.65
        )
        
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = hands.process(rgb)
        
        detected_objects = []
        
        if results.multi_hand_landmarks:
            for hand_landmarks in results.multi_hand_landmarks:
                # Draw hand landmarks
                mp.solutions.drawing_utils.draw_landmarks(
                    frame, 
                    hand_landmarks, 
                    mp_hands.HAND_CONNECTIONS
                )
                
                # Add to detected objects
                detected_objects.append("Hand Gesture")
        
        # Option 2: Add YOLO for crop/pest detection
        try:
            from ultralytics import YOLO
            model = YOLO('yolov8n.pt')  # Replace with your crop model
            
            results = model(frame, verbose=False)
            
            for r in results:
                boxes = r.boxes
                for box in boxes:
                    x1, y1, x2, y2 = map(int, box.xyxy[0])
                    conf = float(box.conf[0])
                    cls = int(box.cls[0])
                    label = model.names[cls]
                    
                    # Draw bounding box
                    color = (0, 255, 136)  # Green accent
                    cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
                    cv2.putText(
                        frame, 
                        f"{label} {conf:.2f}", 
                        (x1, y1 - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 
                        0.6, 
                        color, 
                        2
                    )
                    
                    detected_objects.append(f"{label} ({conf:.2f})")
        except Exception as e:
            print(f"YOLO error: {e}")
        
        # Add HUD overlay (like your Friday Vision)
        cv2.putText(
            frame, 
            "AGRI-FRIDAY VISION", 
            (10, 30), 
            cv2.FONT_HERSHEY_SIMPLEX, 
            1.0, 
            (0, 255, 136), 
            2
        )
        
        return frame, detected_objects
    
    return process_frame


# ═══════════════════════════════════════════════════════════════════════════
# 2. AI BRAIN (GROQ + RAG) INTEGRATION
# ═══════════════════════════════════════════════════════════════════════════

def integrate_ai_brain_from_friday():
    """
    Example: Adapt Brain class for Streamlit with RAG
    """
    
    def ask_ai(query, knowledge_base=None):
        """Enhanced AI with RAG using your existing Brain logic"""
        
        from groq import Groq
        
        # Initialize Groq client (like your Brain class)
        client = Groq(api_key=os.getenv("GROQ_API_KEY"))
        
        # System prompt (adapted from your Config.SYSTEM_PROMPT)
        system_prompt = """You are Agri-Friday, an advanced AI agriculture assistant.
        You help farmers identify crop diseases, pests, and provide agricultural guidance.
        Be concise, practical, and farmer-friendly. Address the user respectfully.
        Current context will be provided with each query."""
        
        # If RAG knowledge base is available
        if knowledge_base:
            # Use LangChain for RAG
            from langchain_groq import ChatGroq
            from langchain.chains import RetrievalQA
            from langchain_community.vectorstores import Chroma
            from langchain_community.embeddings import HuggingFaceEmbeddings
            
            # Initialize LLM
            llm = ChatGroq(
                temperature=0.7,
                model_name="llama-3.3-70b-versatile",
                groq_api_key=os.getenv("GROQ_API_KEY")
            )
            
            # Load vector store
            embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
            vectorstore = Chroma(
                persist_directory="./chroma_db",
                embedding_function=embeddings
            )
            
            # Create QA chain
            qa_chain = RetrievalQA.from_chain_type(
                llm=llm,
                chain_type="stuff",
                retriever=vectorstore.as_retriever(search_kwargs={"k": 3}),
                return_source_documents=True
            )
            
            # Get response with sources
            result = qa_chain({"query": query})
            response = result["result"]
            
            # Add source references
            if result.get("source_documents"):
                response += "\n\n📚 Sources:\n"
                for i, doc in enumerate(result["source_documents"][:2], 1):
                    source = doc.metadata.get("source", "Unknown")
                    response += f"{i}. {os.path.basename(source)}\n"
        
        else:
            # Direct Groq query without RAG (like your _groq method)
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": query}
            ]
            
            completion = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=messages,
                max_tokens=500,
                temperature=0.7
            )
            
            response = completion.choices[0].message.content.strip()
        
        return response
    
    return ask_ai


# ═══════════════════════════════════════════════════════════════════════════
# 3. RAG PDF PROCESSING INTEGRATION
# ═══════════════════════════════════════════════════════════════════════════

def integrate_rag_from_friday():
    """
    Example: PDF processing and vector store creation
    """
    
    def process_pdf(pdf_file):
        """Process PDF and add to vector database"""
        
        from langchain_community.document_loaders import PyPDFLoader
        from langchain.text_splitter import RecursiveCharacterTextSplitter
        from langchain_community.vectorstores import Chroma
        from langchain_community.embeddings import HuggingFaceEmbeddings
        
        # Create directories
        os.makedirs("knowledge_base", exist_ok=True)
        os.makedirs("chroma_db", exist_ok=True)
        
        # Save PDF temporarily
        pdf_path = f"knowledge_base/{pdf_file.name}"
        with open(pdf_path, "wb") as f:
            f.write(pdf_file.getbuffer())
        
        try:
            # Load PDF
            loader = PyPDFLoader(pdf_path)
            documents = loader.load()
            
            # Split into chunks
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=1000,
                chunk_overlap=200,
                length_function=len,
                separators=["\n\n", "\n", " ", ""]
            )
            chunks = text_splitter.split_documents(documents)
            
            # Create/update vector store
            embeddings = HuggingFaceEmbeddings(
                model_name="all-MiniLM-L6-v2",
                model_kwargs={'device': 'cpu'},
                encode_kwargs={'normalize_embeddings': True}
            )
            
            # Check if vector store exists
            if os.path.exists("chroma_db"):
                # Add to existing
                vectorstore = Chroma(
                    persist_directory="./chroma_db",
                    embedding_function=embeddings
                )
                vectorstore.add_documents(chunks)
            else:
                # Create new
                vectorstore = Chroma.from_documents(
                    documents=chunks,
                    embedding=embeddings,
                    persist_directory="./chroma_db"
                )
            
            vectorstore.persist()
            
            return True, f"✅ Processed {len(chunks)} chunks from {pdf_file.name}"
        
        except Exception as e:
            return False, f"❌ Error processing PDF: {str(e)}"
    
    return process_pdf


# ═══════════════════════════════════════════════════════════════════════════
# 4. VOICE (TTS + STT) INTEGRATION
# ═══════════════════════════════════════════════════════════════════════════

def integrate_voice_from_friday():
    """
    Example: TTS and STT using your existing Speaker and Listener classes
    """
    
    def text_to_speech(text):
        """Convert text to speech (adapted from Speaker class)"""
        
        import edge_tts
        import asyncio
        import pygame
        
        async def _generate_audio():
            communicate = edge_tts.Communicate(
                text, 
                voice="en-IN-NeerjaNeural",  # Indian English
                rate="+5%"
            )
            await communicate.save("temp_tts.mp3")
        
        # Generate audio file
        asyncio.run(_generate_audio())
        
        # Play audio
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init()
            
            pygame.mixer.music.load("temp_tts.mp3")
            pygame.mixer.music.play()
            
            # Wait for playback to finish
            while pygame.mixer.music.get_busy():
                pygame.time.Clock().tick(10)
            
            pygame.mixer.music.unload()
            os.remove("temp_tts.mp3")
        
        except Exception as e:
            print(f"TTS playback error: {e}")
    
    
    def speech_to_text():
        """Convert speech to text (adapted from Listener class)"""
        
        import speech_recognition as sr
        
        recognizer = sr.Recognizer()
        recognizer.energy_threshold = 250
        recognizer.pause_threshold = 0.75
        recognizer.dynamic_energy_threshold = True
        
        try:
            with sr.Microphone() as source:
                print("🎤 Listening...")
                recognizer.adjust_for_ambient_noise(source, duration=0.5)
                
                audio = recognizer.listen(
                    source, 
                    timeout=5, 
                    phrase_time_limit=8
                )
            
            # Try Groq Whisper first (faster & more accurate)
            try:
                import requests
                
                # Save audio to file
                with open("temp_audio.wav", "wb") as f:
                    f.write(audio.get_wav_data())
                
                # Call Groq Whisper API
                with open("temp_audio.wav", "rb") as audio_file:
                    response = requests.post(
                        "https://api.groq.com/openai/v1/audio/transcriptions",
                        headers={"Authorization": f"Bearer {os.getenv('GROQ_API_KEY')}"},
                        files={"file": audio_file},
                        data={"model": "whisper-large-v3-turbo"},
                        timeout=10
                    )
                
                if response.status_code == 200:
                    text = response.json().get("text", "").strip()
                    os.remove("temp_audio.wav")
                    return text
            
            except Exception as e:
                print(f"Groq Whisper error: {e}, falling back to Google")
            
            # Fallback: Google Speech Recognition
            text = recognizer.recognize_google(audio)
            return text.strip()
        
        except sr.WaitTimeoutError:
            return "⏱️ Listening timeout. Please try again."
        
        except sr.UnknownValueError:
            return "❓ Could not understand audio. Please speak clearly."
        
        except Exception as e:
            return f"❌ Speech recognition error: {str(e)}"
    
    return text_to_speech, speech_to_text


# ═══════════════════════════════════════════════════════════════════════════
# 5. COMMAND ROUTER INTEGRATION (Optional)
# ═══════════════════════════════════════════════════════════════════════════

def integrate_command_router_from_friday():
    """
    Example: Smart command routing (adapted from CommandRouter class)
    This adds special handling for common queries
    """
    
    def route_command(query, ask_ai_func):
        """Route commands to appropriate handlers"""
        
        q = query.lower().strip()
        
        # Time/Date queries
        from datetime import datetime
        now = datetime.now()
        
        if any(w in q for w in ["time", "what time"]):
            return f"⏰ Current time: {now.strftime('%I:%M %p')}"
        
        if any(w in q for w in ["date", "today", "what day"]):
            return f"📅 Today is {now.strftime('%A, %B %d, %Y')}"
        
        # Weather queries (use external API)
        if "weather" in q:
            import requests
            try:
                city = "Delhi"  # Default or extract from query
                response = requests.get(f"https://wttr.in/{city}?format=3", timeout=5)
                if response.status_code == 200:
                    return f"🌤️ {response.text.strip()}"
            except:
                pass
        
        # Calculate/Math
        if any(w in q for w in ["calculate", "compute", "what is"]):
            import re
            expr = re.sub(r"[^0-9+\-*/.() ]", "", q)
            try:
                result = eval(expr, {"__builtins__": {}}, {})
                return f"🧮 {expr} = {result}"
            except:
                pass
        
        # Fall through to AI brain
        return ask_ai_func(query)
    
    return route_command


# ═══════════════════════════════════════════════════════════════════════════
# USAGE EXAMPLE
# ═══════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("""
    ╔════════════════════════════════════════════════════════════════╗
    ║          AGRI-FRIDAY INTEGRATION EXAMPLES                      ║
    ╚════════════════════════════════════════════════════════════════╝
    
    This file contains example implementations to integrate your
    existing friday_v3.py code into the Streamlit dashboard.
    
    TO USE:
    1. Copy the relevant function implementations
    2. Replace placeholder functions in agri_friday_dashboard.py
    3. Test each component individually
    4. Combine for full integration
    
    COMPONENTS PROVIDED:
    ✓ Vision/Object Detection (MediaPipe + YOLO)
    ✓ AI Brain (Groq + LangChain RAG)
    ✓ PDF Processing (LangChain + ChromaDB)
    ✓ Voice (TTS with edge-tts, STT with SpeechRecognition)
    ✓ Command Router (Smart query handling)
    """)
    
    print("\n📝 See function docstrings for detailed integration steps.\n")
