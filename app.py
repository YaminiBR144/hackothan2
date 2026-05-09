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
import fitz  # PyMuPDF for PDF handling
from docx import Document # python-docx for Word files
from pydub import AudioSegment # for MP3 to WAV conversion

# --- CONFIG & HELPERS ---
st.set_page_config(page_title="PragyanAI Studio Pro", layout="wide")
langs_dict = GoogleTranslator().get_supported_languages(as_dict=True)

def translate_and_get_tts(text, target_code):
    if not text.strip():
        return None, None
    translated = GoogleTranslator(source='auto', target=target_code).translate(text)
    tts = gTTS(text=translated, lang=target_code)
    tts_fp = BytesIO()
    tts.write_to_fp(tts_fp)
    return translated, tts_fp

# --- MAIN APP ---
def main():
    st.title("🌐 PragyanAI Multi-Model Studio Pro")
    
    target_lang = st.sidebar.selectbox("Select Target Language", list(langs_dict.keys()))
    target_code = langs_dict[target_lang]

    tab1, tab2, tab3, tab4 = st.tabs(["🎥 Live Vision", "📸 Image/PDF", "🎤 Voice/MP3", "📝 Text/Docx"])

    # --- TAB 1: LIVE VISION (Unchanged) ---
    with tab1:
        img_file_buffer = st.camera_input("Take a photo to translate")
        if img_file_buffer:
            cv2_img = cv2.imdecode(np.frombuffer(img_file_buffer.getvalue(), np.uint8), cv2.IMREAD_COLOR)
            if st.button("Extract & Translate Camera"):
                text = pytesseract.image_to_string(cv2_img)
                trans, audio = translate_and_get_tts(text, target_code)
                st.success(f"**Detected:** {text}\n\n**Translated:** {trans}")
                st.audio(audio)

    # --- TAB 2: IMAGE & PDF UPLOAD ---
    with tab2:
        up_file = st.file_uploader("Upload Image or PDF", type=['png', 'jpg', 'jpeg', 'pdf'])
        if up_file:
            if up_file.type == "application/pdf":
                doc = fitz.open(stream=up_file.read(), filetype="pdf")
                full_text = "".join([page.get_text() for page in doc])
                st.text_area("Extracted PDF Text", full_text, height=200)
                if st.button("Translate PDF"):
                    trans, audio = translate_and_get_tts(full_text, target_code)
                    st.info(f"**Translated:** {trans}")
                    st.download_button("Download Translation (TXT)", trans, file_name="translated_pdf.txt")
            else:
                img = Image.open(up_file)
                st.image(img, width=300)
                if st.button("Process Image"):
                    text = pytesseract.image_to_string(img)
                    trans, _ = translate_and_get_tts(text, target_code)
                    st.success(f"**Translated:** {trans}")
                    st.download_button("Download Translation", trans, file_name="translated_img.txt")

    # --- TAB 3: VOICE & MP3 ---
    with tab3:
        st.subheader("Record or Upload Audio")
        audio_rec = audio_recorder(text="Click to record")
        audio_up = st.file_uploader("Or Upload MP3", type=['mp3', 'wav'])
        
        final_audio = audio_rec if audio_rec else (audio_up.read() if audio_up else None)
        
        if final_audio:
            # Convert MP3 to WAV for SpeechRecognition if needed
            audio_bio = BytesIO(final_audio)
            if audio_up and audio_up.type == "audio/mpeg":
                sound = AudioSegment.from_file(audio_bio, format="mp3")
                audio_bio = BytesIO()
                sound.export(audio_bio, format="wav")
            
            if st.button("Transcribe & Translate Audio"):
                r = sr.Recognizer()
                with sr.AudioFile(audio_bio) as source:
                    audio_data = r.record(source)
                    text = r.recognize_google(audio_data)
                    trans, tts_audio = translate_and_get_tts(text, target_code)
                    st.success(f"**Original:** {text}\n\n**Translated:** {trans}")
                    st.audio(tts_audio)
                    st.download_button("Download Transcript", trans, file_name="audio_trans.txt")

    # --- TAB 4: MANUAL TEXT & DOCX (With Image Preservation) ---
    with tab4:
        st.subheader("Text or Word Document")
        user_text = st.text_area("Manual Input")
        docx_file = st.file_uploader("Upload Docx", type=['docx'])

        if docx_file:
            doc = Document(docx_file)
            if st.button("Translate Docx"):
                # Logic: Iterate paragraphs, translate text, keep images
                for para in doc.paragraphs:
                    if para.text.strip():
                        para.text = GoogleTranslator(source='auto', target=target_code).translate(para.text)
                
                # Save modified doc to buffer
                out_bio = BytesIO()
                doc.save(out_bio)
                st.success("Docx Translated! (Images preserved)")
                st.download_button("Download Translated Docx", out_bio.getvalue(), 
                                   file_name="translated.docx", 
                                   mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document")

        if st.button("Translate Manual Text") and user_text:
            trans, _ = translate_and_get_tts(user_text, target_code)
            st.info(trans)
            st.download_button("Download Text", trans, file_name="manual_trans.txt")

if __name__ == "__main__":
    main()
