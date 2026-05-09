import streamlit as st
from audio_recorder_streamlit import audio_recorder
from deep_translator import GoogleTranslator
from gtts import gTTS
import speech_recognition as sr
from PIL import Image
import pytesseract
from io import BytesIO
import fitz
from docx import Document
from pydub import AudioSegment  # Required for MP3 processing

# ---------------------------- #
# CONFIG & HELPERS
# ---------------------------- #
st.set_page_config(page_title="PragyanAI Studio", layout="wide")

try:
    langs_dict = GoogleTranslator().get_supported_languages(as_dict=True)
except:
    langs_dict = {"english": "en", "hindi": "hi"}

def translate_text(text, target_code):
    return GoogleTranslator(source="auto", target=target_code).translate(text) if text.strip() else ""

def create_audio(text, lang):
    tts = gTTS(text=text, lang=lang)
    audio_fp = BytesIO()
    tts.write_to_fp(audio_fp)
    audio_fp.seek(0)
    return audio_fp

# ---------------------------- #
# MAIN
# ---------------------------- #
def main():
    st.title("🌐 PragyanAI Multi-Modal Studio")
    target_lang = st.sidebar.selectbox("Target Language", list(langs_dict.keys()))
    target_code = langs_dict[target_lang]

    tabs = st.tabs(["📸 Capture", "🖼️ Upload Image/PDF", "🎤 Audio", "📝 Text"])

    # --- TAB 0: CAPTURE ---
    with tabs[0]:
        img_file = st.camera_input("Capture text")
        if img_file and st.button("Translate Capture"):
            img = Image.open(img_file)
            text = pytesseract.image_to_string(img)
            translated = translate_text(text, target_code)
            st.success(translated)

    # --- TAB 1: IMAGE/PDF ---
    with tabs[1]:
        uploaded_file = st.file_uploader("Upload Image/PDF", type=["png", "jpg", "pdf"])
        if uploaded_file and st.button("Translate Upload"):
            # Simple extraction logic (OCR for image, fitz for PDF)
            pass 

    # --- TAB 2: AUDIO (MP3 & DOWNLOAD) ---
    with tabs[2]:
        choice = st.radio("Input", ["Record", "Upload MP3/WAV"])
        audio_data = None
        
        if choice == "Record":
            audio_data = audio_recorder()
        else:
            uploaded_audio = st.file_uploader("Upload Song", type=["mp3", "wav"])
            if uploaded_audio:
                # Convert MP3 to WAV in-memory for SpeechRecognition
                if uploaded_audio.name.endswith(".mp3"):
                    audio = AudioSegment.from_file(uploaded_audio, format="mp3")
                    wav_io = BytesIO()
                    audio.export(wav_io, format="wav")
                    audio_data = wav_io.getvalue()
                else:
                    audio_data = uploaded_audio.read()

        if audio_data:
            st.audio(audio_data)
            if st.button("Translate Audio"):
                recognizer = sr.Recognizer()
                with sr.AudioFile(BytesIO(audio_data)) as source:
                    audio_recorded = recognizer.record(source)
                
                try:
                    text = recognizer.recognize_google(audio_recorded)
                    translated = translate_text(text, target_code)
                    st.subheader("Translated Lyrics:")
                    st.write(translated)
                    
                    # Generate Translated Audio
                    translated_audio = create_audio(translated, target_code)
                    st.audio(translated_audio)
                    
                    # DOWNLOAD OPTION
                    st.download_button(
                        label="🎵 Download Translated Song (MP3)",
                        data=translated_audio,
                        file_name="translated_song.mp3",
                        mime="audio/mp3"
                    )
                except Exception as e:
                    st.error(f"Could not process audio: {e}")

    # --- TAB 3: TEXT ---
    with tabs[3]:
        text_input = st.text_area("Type text")
        if st.button("Translate"):
            st.success(translate_text(text_input, target_code))

if __name__ == "__main__":
    main()
