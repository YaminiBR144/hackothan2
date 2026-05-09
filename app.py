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
import fitz
from docx import Document
import tempfile
import os

# ---------------------------- #
# CONFIG
# ---------------------------- #
st.set_page_config(
    page_title="PragyanAI Studio",
    layout="wide"
)

# Fetch supported languages once
try:
    langs_dict = GoogleTranslator().get_supported_languages(as_dict=True)
except Exception:
    # Fallback if there's a connection issue
    langs_dict = {"english": "en", "hindi": "hi", "spanish": "es"}

# ---------------------------- #
# HELPERS
# ---------------------------- #
def translate_text(text, target_code):
    if not text.strip():
        return ""
    translated = GoogleTranslator(
        source="auto",
        target=target_code
    ).translate(text)
    return translated

def create_audio(text, lang):
    tts = gTTS(text=text, lang=lang)
    audio_fp = BytesIO()
    tts.write_to_fp(audio_fp)
    audio_fp.seek(0)
    return audio_fp

def extract_text_from_pdf(pdf_bytes):
    text = ""
    with fitz.open(stream=pdf_bytes, filetype="pdf") as doc:
        for page in doc:
            text += page.get_text()
    return text

# ---------------------------- #
# MAIN
# ---------------------------- #
def main():
    st.title("🌐 PragyanAI Multi-Modal Studio")
    
    # Sidebar for language selection
    target_lang = st.sidebar.selectbox(
        "Target Language", 
        list(langs_dict.keys()),
        index=list(langs_dict.keys()).index("english") if "english" in langs_dict else 0
    )
    target_code = langs_dict[target_lang]

    # Tabs definition - DOCX replaced by Capture
    tabs = st.tabs([
        "📸 Capture & Translate", 
        "🖼️ Upload Image/PDF", 
        "🎤 Audio", 
        "📝 Text"
    ])

    # ---------------- TAB 0: CAPTURE & TRANSLATE
    with tabs[0]:
        st.header("Live Camera Capture")
        # Use camera input instead of file uploader
        img_file_buffer = st.camera_input("Take a photo of text to translate")

        if img_file_buffer:
            img = Image.open(img_file_buffer)
            
            if st.button("Extract & Translate Capture"):
                with st.spinner("Processing..."):
                    # OCR processing
                    extracted = pytesseract.image_to_string(img)
                    
                    if extracted.strip():
                        translated = translate_text(extracted, target_code)
                        
                        st.subheader("Results")
                        col1, col2 = st.columns(2)
                        with col1:
                            st.info(f"**Original Text:**\n{extracted}")
                        with col2:
                            st.success(f"**Translated ({target_lang}):**\n{translated}")
                        
                        # Save to DOCX for download
                        doc = Document()
                        doc.add_heading('Captured Translation', 0)
                        doc.add_picture(img_file_buffer, width=fitz.utils.inches(4))
                        doc.add_paragraph(f"Translated Text: {translated}")
                        
                        output = BytesIO()
                        doc.save(output)
                        output.seek(0)
                        st.download_button("Download DOCX", output, file_name="captured_text.docx")
                    else:
                        st.warning("No text found in the image. Try a clearer shot!")

    # ---------------- TAB 1: IMAGE/PDF UPLOAD
    with tabs[1]:
        uploaded_file = st.file_uploader("Upload Image or PDF", type=["png", "jpg", "jpeg", "pdf"])
        if uploaded_file:
            if uploaded_file.type == "application/pdf":
                if st.button("Translate PDF"):
                    extracted = extract_text_from_pdf(uploaded_file.read())
                    translated = translate_text(extracted, target_code)
                    st.success(translated)
            else:
                img = Image.open(uploaded_file)
                st.image(img, width=300)
                if st.button("Translate Uploaded Image"):
                    extracted = pytesseract.image_to_string(img)
                    translated = translate_text(extracted, target_code)
                    st.success(translated)

    # ---------------- TAB 2: AUDIO
    with tabs[2]:
        choice = st.radio("Input type", ["Record", "Upload"])
        audio_bytes = None
        if choice == "Record":
            audio_bytes = audio_recorder(text="Click to Record")
        else:
            uploaded_audio = st.file_uploader("Upload audio", type=["wav", "flac"])
            if uploaded_audio:
                audio_bytes = uploaded_audio.read()
        
        if audio_bytes:
            st.audio(audio_bytes)
            if st.button("Translate Audio"):
                recognizer = sr.Recognizer()
                with sr.AudioFile(BytesIO(audio_bytes)) as source:
                    audio_data = recognizer.record(source)
                try:
                    text = recognizer.recognize_google(audio_data)
                    translated = translate_text(text, target_code)
                    st.success(translated)
                    st.audio(create_audio(translated, target_code))
                except Exception as e:
                    st.error(f"Error: {e}")

    # ---------------- TAB 3: TEXT
    with tabs[3]:
        text_input = st.text_area("Type text here")
        if st.button("Translate Text"):
            if text_input:
                translated = translate_text(text_input, target_code)
                st.success(translated)
            else:
                st.warning("Please enter some text.")

if __name__ == "__main__":
    main()
