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
from docx import Document
import tempfile
import os

# -----------------------------------
# PAGE CONFIG
# -----------------------------------
st.set_page_config(page_title="PragyanAI Studio", layout="wide")

langs_dict = GoogleTranslator().get_supported_languages(as_dict=True)

# For Windows use this if needed:
# pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'


# -----------------------------------
# HELPER FUNCTIONS
# -----------------------------------

def translate_text(text, target_code):
    if not text.strip():
        return ""
    translated = GoogleTranslator(
        source='auto',
        target=target_code
    ).translate(text)
    return translated


def text_to_audio(text, lang):
    tts = gTTS(text=text, lang=lang)

    audio_fp = BytesIO()
    tts.write_to_fp(audio_fp)

    return audio_fp


# DOCX translation preserving structure
def translate_docx(uploaded_file, target_code):

    doc = Document(uploaded_file)
    new_doc = Document()

    # paragraphs
    for para in doc.paragraphs:
        translated = translate_text(para.text, target_code)
        new_doc.add_paragraph(translated)

    # tables
    for table in doc.tables:
        new_table = new_doc.add_table(
            rows=len(table.rows),
            cols=len(table.columns)
        )

        for i, row in enumerate(table.rows):
            for j, cell in enumerate(row.cells):

                translated = translate_text(
                    cell.text,
                    target_code
                )

                new_table.cell(i, j).text = translated

    output = BytesIO()
    new_doc.save(output)
    output.seek(0)

    return output


# OCR image
def extract_text_from_image(image):
    text = pytesseract.image_to_string(image)
    return text


# -----------------------------------
# MAIN APP
# -----------------------------------

def main():

    st.title("🌐 PragyanAI Multi-Modal Translator")

    target_lang = st.sidebar.selectbox(
        "Select Target Language",
        list(langs_dict.keys())
    )

    target_code = langs_dict[target_lang]

    tabs = st.tabs([
        "📄 DOCX",
        "🖼 Image",
        "🎤 Audio",
        "⌨ Text"
    ])

    # -----------------------------------
    # TAB 1 DOCX
    # -----------------------------------
    with tabs[0]:

        st.subheader("Upload DOCX")

        doc_file = st.file_uploader(
            "Upload Word file",
            type=["docx"]
        )

        if doc_file:

            if st.button("Translate DOCX"):

                translated_doc = translate_docx(
                    doc_file,
                    target_code
                )

                st.success("Translation complete")

                st.download_button(
                    "Download translated DOCX",
                    translated_doc,
                    file_name="translated.docx"
                )

    # -----------------------------------
    # TAB 2 IMAGE
    # -----------------------------------
    with tabs[1]:

        image_file = st.file_uploader(
            "Upload image",
            type=["png", "jpg", "jpeg"]
        )

        if image_file:

            image = Image.open(image_file)

            st.image(image, width=300)

            if st.button("Translate Image"):

                extracted = extract_text_from_image(image)

                translated = translate_text(
                    extracted,
                    target_code
                )

                st.write("Detected Text:")
                st.success(extracted)

                st.write("Translated:")
                st.info(translated)

                # save to docx
                doc = Document()
                doc.add_picture(image_file, width=None)
                doc.add_paragraph(translated)

                output = BytesIO()
                doc.save(output)
                output.seek(0)

                st.download_button(
                    "Download as DOCX",
                    output,
                    file_name="translated_image.docx"
                )

    # -----------------------------------
    # TAB 3 AUDIO
    # -----------------------------------
    with tabs[2]:

        st.subheader("Record or Upload Audio")

        # record
        audio_bytes = audio_recorder(
            text="Click to record"
        )

        # upload
        audio_upload = st.file_uploader(
            "Upload audio",
            type=["wav", "mp3"]
        )

        selected_audio = None

        if audio_bytes:
            selected_audio = audio_bytes

        elif audio_upload:
            selected_audio = audio_upload.read()

        if selected_audio:

            st.audio(selected_audio)

            if st.button("Translate Audio"):

                recognizer = sr.Recognizer()

                with tempfile.NamedTemporaryFile(
                    delete=False,
                    suffix=".wav"
                ) as temp_audio:

                    temp_audio.write(selected_audio)
                    temp_path = temp_audio.name

                with sr.AudioFile(temp_path) as source:

                    audio_data = recognizer.record(source)

                    original_text = recognizer.recognize_google(
                        audio_data
                    )

                translated = translate_text(
                    original_text,
                    target_code
                )

                st.success(original_text)

                st.info(translated)

                translated_audio = text_to_audio(
                    translated,
                    target_code
                )

                st.audio(translated_audio)

                os.remove(temp_path)

    # -----------------------------------
    # TAB 4 TEXT
    # -----------------------------------
    with tabs[3]:

        text = st.text_area(
            "Type your text"
        )

        if st.button("Translate Text"):

            translated = translate_text(
                text,
                target_code
            )

            st.info(translated)

            # save as docx
            doc = Document()
            doc.add_paragraph(translated)

            output = BytesIO()
            doc.save(output)
            output.seek(0)

            st.download_button(
                "Download DOCX",
                output,
                file_name="translated_text.docx"
            )


if __name__ == "__main__":
    main()
