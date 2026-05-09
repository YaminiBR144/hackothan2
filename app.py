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
import pdfplumber
from fpdf import FPDF
from pydub import AudioSegment

# --- CONFIG & HELPERS ---
st.set_page_config(page_title="PragyanAI Studio Pro", layout="wide")
langs_dict = GoogleTranslator().get_supported_languages(as_dict=True)

def translate_text(text, target_code):
    if not text or not text.strip():
        return None
    return GoogleTranslator(source='auto', target=target_code).translate(text)

def create_pdf(text):
    pdf = FPDF()
    pdf.add_page()
    # Using Arial as a standard font; note: for non-Latin scripts, 
    # you'd need to link a Unicode-compatible .ttf font.
    pdf.set_font("Arial", size=12)
    pdf.multi_cell(0, 10, txt=text)
    return pdf.output(dest='S').encode('latin-1', errors='replace')

# --- MAIN APP ---
def main():
    st.title("🌐 PragyanAI Multi-Model Studio Pro")
    
    target_lang = st.sidebar.selectbox("Select Target Language", list(langs_dict.keys()))
    target_code = langs_dict[target_lang]

    tab1, tab2, tab3, tab4 = st.tabs(["🎥 Live Vision", "📂 Documents/Images", "🎤 Voice/Audio", "📝 Text"])

    # --- TAB 1: LIVE VISION ---
    with tab1:
        st.subheader("Live Camera Translator")
        img_file_buffer = st.camera_input("Take a photo of text")
        if img_file_buffer:
            bytes_data = img_file_buffer.getvalue()
            cv2_img = cv2.imdecode(np.frombuffer(bytes_data, np.uint8), cv2.IMREAD_COLOR)
            if st.button("Extract & Translate Camera"):
                extracted = pytesseract.image_to_string(cv2_img)
                translated = translate_text(extracted, target_code)
                if translated:
                    st.success(f"**Translated:** {translated}")

    # --- TAB 2: DOCUMENT & IMAGE UPLOAD ---
    with tab2:
        st.subheader("Upload Image or PDF")
        uploaded_file = st.file_uploader("Choose a file", type=['png', 'jpg', 'jpeg', 'pdf'])
        
        if uploaded_file:
            extracted_text = ""
            if uploaded_file.type == "application/pdf":
                with pdfplumber.open(uploaded_file) as pdf:
                    extracted_text = "\n".join([page.extract_text() for page in pdf.pages if page.extract_text()])
            else:
                img = Image.open(uploaded_file)
                st.image(img, width=300)
                extracted_text = pytesseract.image_to_string(img)

            if st.button("Process Document"):
                translated_text = translate_text(extracted_text, target_code)
                if translated_text:
                    st.info(f"**Translation:**\n{translated_text}")
                    
                    # PDF Download Logic
                    pdf_bytes = create_pdf(translated_text)
                    st.download_button(
                        label="📥 Download Translated PDF",
                        data=pdf_bytes,
                        file_name="translated_document.pdf",
                        mime="application/pdf"
                    )

    # --- TAB 3: VOICE & AUDIO FILE ---
    with tab3:
        st.subheader("Audio Translation")
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("Record Live:")
            recorded_audio = audio_recorder()
        
        with col2:
            st.write("Or Upload File:")
            uploaded_audio = st.file_uploader("Upload Audio", type=['wav', 'mp3', 'm4a'])

        final_audio_bytes = recorded_audio if recorded_audio else (uploaded_audio.read() if uploaded_audio else None)

        if final_audio_bytes:
            if st.button("Transcribe & Translate Audio"):
                recognizer = sr.Recognizer()
                # Convert to WAV for speech_recognition compatibility
                audio_seg = AudioSegment.from_file(BytesIO(final_audio_bytes))
                wav_io = BytesIO()
                audio_seg.export(wav_io, format="wav")
                wav_io.seek(0)

                with sr.AudioFile(wav_io) as source:
                    audio_data = recognizer.record(source)
                    try:
                        raw_text = recognizer.recognize_google(audio_data)
                        translated = translate_text(raw_text, target_code)
                        st.success(f"**Original:** {raw_text}")
                        st.success(f"**Translated:** {translated}")

                        # TTS and Download
                        tts = gTTS(text=translated, lang=target_code)
                        tts_io = BytesIO()
                        tts.write_to_fp(tts_io)
                        st.audio(tts_io)
                        st.download_button("📥 Download Translated Audio", tts_io.getvalue(), "translated_voice.mp3", "audio/mp3")
                    except Exception as e:
                        st.error(f"Speech Error: {e}")

    # --- TAB 4: MANUAL TEXT ---
    with tab4:
        st.subheader("Manual Text Input")
        user_text = st.text_area("Paste text or scripts here...")
        if st.button("Translate & Download"):
            translated = translate_text(user_text, target_code)
            if translated:
                st.write(translated)
                pdf_bytes = create_pdf(translated)
                st.download_button("📥 Download PDF", pdf_bytes, "text_translation.pdf", "application/pdf")

if __name__ == "__main__":
    main()
