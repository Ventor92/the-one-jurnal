import streamlit as st
import fitz  # PyMuPDF
import os

st.set_page_config(page_title="📂 Przegląd PDF", layout="wide")
st.title("📂 Przegląd PDF")

# =========================
# Funkcje pomocnicze
# =========================
def load_pdf(path):
    try:
        return fitz.open(path)
    except Exception as e:
        st.error(f"Nie udało się wczytać PDF: {e}")
        return None

def extract_toc(doc):
    toc = doc.get_toc(simple=True)  # lista: [ [level, title, page], ... ]
    return toc

def extract_section(doc, start_page, end_page=None):
    """Wyciąga tekst z PDF od start_page do end_page (exclusive)."""
    text = ""
    last = end_page if end_page else len(doc)
    for page_num in range(start_page-1, last-1):  # PyMuPDF numeruje od 0
        text += doc[page_num].get_text("text") + "\n"
    return text.strip()

# =========================
# Upload pliku
# =========================
uploaded_file = st.file_uploader("Wgraj plik PDF", type="pdf")

if uploaded_file is not None:
    # Zapisz plik tymczasowo
    pdf_path = os.path.join("temp_uploaded.pdf")
    with open(pdf_path, "wb") as f:
        f.write(uploaded_file.getvalue())
else:
    pdf_path = r"../../data/Jedyny_Pierscien_Gra_Fabularna_v3.1-1.pdf"

doc = load_pdf(pdf_path)

if doc:
    # =========================
    # TOC
    # =========================
    toc = extract_toc(doc)

    if not toc:
        st.warning("Ten PDF nie ma spisu treści (TOC).")
    else:
        st.subheader("📑 Spis treści")

        # Tworzymy listę rozdziałów do wyboru
        chapters = [f"{t[0]*'  '}{t[1]} (str. {t[2]})" for t in toc]
        selected = st.selectbox("Wybierz rozdział:", chapters)

        # Znajdź stronę początkową i następną
        idx = chapters.index(selected)
        start_page = toc[idx][2]
        if idx + 1 < len(toc):
            end_page = toc[idx+1][2]
        else:
            end_page = None

        # =========================
        # Treść rozdziału
        # =========================
        st.subheader(f"📖 {toc[idx][1]}")
        section_text = extract_section(doc, start_page, end_page)
        st.text_area(
            "Treść rozdziału:",
            value=section_text,
            height=500
        )
