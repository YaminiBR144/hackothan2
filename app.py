import streamlit as st
from audio_recorder_streamlit import audio_recorder
from deep_translator import GoogleTranslator
from gtts import gTTS
import speech_recognition as sr
from PIL import Image
import pytesseract
import cv2
import numpy as np
from io import BytesIO
import fitz  # PyMuPDF

# --- CONFIG & HELPERS ---
st.set_page_config(page_title="PragyanAI Studio", layout="wide")
langs_dict = GoogleTranslator().get_supported_languages(as_dict=True)

def translate_and_speak(text, target_code):
    if not text or not text.strip():
        st.warning("No text detected to translate.")
        return
    
    try:
        # Translation
        translated = GoogleTranslator(source='auto', target=target_code).translate(text)
        st.info(f"**Translated:** {translated}")
        
        # Audio Output
        tts = gTTS(text=translated, lang=target_code)
        tts_fp = BytesIO()
        tts.write_to_fp(tts_fp)
        st.audio(tts_fp)
    except Exception as e:
        st.error(f"Translation/TTS Error: {e}")

def extract_text_from_pdf(pdf_bytes):
    text = ""
    with fitz.open(stream=pdf_bytes, filetype="pdf") as doc:
        for page in doc:
            text += page.get_text()
    return text

# --- MAIN APP ---
def main():
    st.title("🌐 PragyanAI Multi-Model Studio")
    
    # Sidebar Configuration
    st.sidebar.header("Settings")
    target_lang = st.sidebar.selectbox("Select Target Language", list(langs_dict.keys()))
    target_code = langs_dict[target_lang]

    # Enhanced Tabs
    tabs = st.tabs(["🎥 Live Vision", "📸 Image/PDF", "🎤 Voice Hub", "📝 Text"])

    # --- TAB 1: LIVE VISION ---
    with tabs[0]:
        st.subheader("Live Camera Translator")
        img_file_buffer = st.camera_input("Take a snapshot of text")
        if img_file_buffer:
            bytes_data = img_file_buffer.getvalue()
            cv2_img = cv2.imdecode(np.frombuffer(bytes_data, np.uint8), cv2.IMREAD_COLOR)
            if st.button("Extract from Snapshot"):
                extracted = pytesseract.image_to_string(cv2_img)
                st.success(f"**Detected:** {extracted}")
                translate_and_speak(extracted, target_code)

    # --- TAB 2: DOCUMENT & IMAGE UPLOAD (PDF Support) ---
    with tabs[1]:
        st.subheader("Image & PDF Translator")
        uploaded_doc = st.file_uploader("Upload Image or PDF", type=['png', 'jpg', 'jpeg', 'pdf'])
        
        if uploaded_doc:
            if uploaded_doc.type == "application/pdf":
                if st.button("Extract from PDF"):
                    pdf_text = extract_text_from_pdf(uploaded_doc.read())
                    st.text_area("Extracted PDF Content", pdf_text, height=200)
                    translate_and_speak(pdf_text, target_code)
            else:
                img = Image.open(uploaded_doc)
                st.image(img, width=300)
                if st.button("Extract from Image"):
                    extracted = pytesseract.image_to_string(img)
                    st.success(f"**Detected:** {extracted}")
                    translate_and_speak(extracted, target_code)

    # --- TAB 3: VOICE HUB (Live & File) ---
    with tabs[2]:
        st.subheader("Audio Translator")
        choice = st.radio("Choose Input", ["Live Record", "Upload Audio File"])
        
        audio_to_process = None
        
        if choice == "Live Record":
            audio_to_process = audio_recorder(text="Click to record")
        else:
            audio_to_process = st.file_uploader("Upload Audio (WAV/FLAC)", type=['wav', 'flac'])

        if audio_to_process:
            # Handle both bytes (recorder) and UploadedFile object
            audio_data_bytes = audio_to_process if isinstance(audio_to_process, bytes) else audio_to_process.read()
            st.audio(audio_data_bytes)
            
            if st.button("Process Audio"):
                with st.spinner("Converting speech to text..."):
                    try:
                        recognizer = sr.Recognizer()
                        with sr.AudioFile(BytesIO(audio_data_bytes)) as source:
                            recorded_audio = recognizer.record(source)
                            text = recognizer.recognize_google(recorded_audio)
                            st.success(f"**Transcription:** {text}")
                            translate_and_speak(text, target_code)
                    except Exception as e:
                        st.error("Audio format not supported or clear. Try WAV files.")

    # --- TAB 4: MANUAL TEXT ---
    with tabs[3]:
        user_text = st.text_area("Type text to translate...", height=150)
        if st.button("Translate Text"):
            translate_and_speak(user_text, target_code)

if __name__ == "__main__":
    main()
