import os
import time
import streamlit as st
import torch

from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from pydantic import SecretStr
from langchain_community.embeddings import HuggingFaceEmbeddings
from pdfSplitter_srvc import load_pdf_with_toc, sliding_window_split


# =========================
# Konfiguracja i stałe
# =========================
MODEL_EMBEDDING = "models/embedding-001"
DEFAULT_LLM_MODEL = "gemini-2.5-flash"
PDF_PATH = r"../../data/Jedyny_Pierscien_Gra_Fabularna_v3.1-1.pdf"  # <- podmień w razie potrzeby
FAISS_PATH = r"../../data/faiss_index"

st.set_page_config(page_title="🧙‍♂️ Interaktywny Podręcznik ttRPG", layout="wide")
st.title("🧙‍♂️ Interaktywny Podręcznik ttRPG")

# =========================
# Walidacja środowiska
# =========================
if "GOOGLE_API_KEY" not in os.environ or not os.environ["GOOGLE_API_KEY"]:
    st.error("Brak zmiennej środowiskowej GOOGLE_API_KEY. Ustaw ją w systemie i uruchom ponownie.")
    st.stop()

# =========================
# Sidebar: opcje
# =========================
st.sidebar.header("⚙️ Ustawienia")
llm_model = st.sidebar.selectbox("Model LLM", ["gemini-2.5-flash", "gemini-2.5-pro"], index=0)
temperature = st.sidebar.slider("Temperature", 0.0, 1.0, 0.2, 0.1)
k = st.sidebar.slider("Liczba fragmentów kontekstu (k)", 1, 10, 5, 1)
rebuild = st.sidebar.checkbox("Wymuś przebudowę indeksu", value=False)
show_full_chunks = st.sidebar.checkbox("Pokaż pełne fragmenty kontekstu", value=True)

# =========================
# Lazy inicjalizacja w session_state
# =========================
if "db" not in st.session_state:
    st.session_state.db = None
if "chat" not in st.session_state:
    st.session_state.chat = []  # lista słowników: {"role": "user"/"assistant", "text": "...", "sources": [...]}

# =========================
# Funkcje pomocnicze
# =========================
def build_embeddings():
    # Sprawdzenie dostępności GPU
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"Tworzenie embeddingów na urządzeniu: {device}")
    
    return HuggingFaceEmbeddings(
        model_name="intfloat/multilingual-e5-base",
        model_kwargs={"device": device}
    )
        

def build_llm(model_name: str, temperature: float):
    return ChatGoogleGenerativeAI(
        model=model_name,
        api_key=SecretStr(os.environ["GOOGLE_API_KEY"]),
        temperature=temperature
    )

def ensure_vectorstore(rebuild: bool = False):
    """
    Tworzy lub wczytuje FAISS do st.session_state.db.
    Zapis/wczytanie: FAISS_PATH.
    """
    if rebuild:
        st.session_state.db = None

    if st.session_state.db is not None:
        return

    embeddings = build_embeddings()

    if (not rebuild) and os.path.exists(FAISS_PATH):
        with st.spinner("Wczytywanie istniejącej bazy FAISS..."):
            st.session_state.db = FAISS.load_local(
                FAISS_PATH,
                embeddings,
                allow_dangerous_deserialization=True  # świadomie, bo to nasz własny plik
            )
        return

    # Budowa indeksu od zera
    with st.spinner("Tworzenie bazy FAISS (pierwsze uruchomienie / przebudowa)..."):
        if not os.path.exists(PDF_PATH):
            st.error(f"Nie znaleziono PDF pod ścieżką: {PDF_PATH}")
            st.stop()
        
        # 1. Wczytaj PDF i podziel po nagłówkach (TOC)
        documents = load_pdf_with_toc(PDF_PATH)
        # 2. Zastosuj sliding window
        docs = sliding_window_split(documents, chunk_size=600, chunk_overlap=300)
        
        # loader = PyPDFLoader(PDF_PATH)
        # documents = loader.load()

        # # (opcjonalnie) ograniczenie do stron testowych:
        # # documents = documents[92:105]

        # splitter = RecursiveCharacterTextSplitter(chunk_size=600, chunk_overlap=150)
        # docs = splitter.split_documents(documents)

        st.info(f"Generowanie embeddingów dla {len(docs)} fragmentów...")
        st.session_state.db = FAISS.from_documents(docs, embeddings)
        st.session_state.db.save_local(FAISS_PATH)
        st.success("✅ Baza FAISS zapisana lokalnie.")

def answer_query(query: str, k: int, llm_model: str, temperature: float):
    llm = build_llm(llm_model, temperature)
    retrieved_docs = st.session_state.db.similarity_search(query, k=k)
    context = "\n\n".join([d.page_content for d in retrieved_docs])

    # Prosty, solidny prompt pod reguły TTRPG:
    system = (
        "Jesteś asystentem zasad TTRPG. Odpowiadasz wyłącznie na podstawie dostarczonego kontekstu.\n"
        "Jeśli brakuje informacji w kontekście, powiedz „Nie wiem na podstawie załączonych zasad”.\n"
        "Zachowuj się jak sędzia zasad: bądź precyzyjny, podawaj numery/sekcje jeśli są w tekście."
    )
    prompt = f"{system}\n\n=== KONTEKST ===\n{context}\n\n=== PYTANIE ===\n{query}\n\n=== ODPOWIEDŹ ==="

    start = time.time()
    response = llm.predict(prompt)
    elapsed = time.time() - start

    sources = []
    for d in retrieved_docs:
        meta = d.metadata or {}
        page = meta.get("pages", "—")
        src = meta.get("source", "PDF")
        chapter = meta.get("chapter", "—")
        snippet = d.page_content.replace("\n", " ")
        sources.append(f"{src} {chapter} (strona: {page}) — „{snippet}”")

    return response, sources, elapsed

# =========================
# Inicjalizacja / indeks
# =========================
ensure_vectorstore(rebuild=rebuild)

# =========================
# UI czatu
# =========================
st.subheader("💬 Zapytanie")
user_query = st.text_input("Zadaj pytanie do podręcznika:", placeholder="Np. Jak przeprowadzać atak?")

col1, col2 = st.columns([1, 1])
with col1:
    ask = st.button("✍️ Zapytaj", type="primary", use_container_width=True)
with col2:
    clear = st.button("🧹 Wyczyść historię", use_container_width=True)

if clear:
    st.session_state.chat = []
    st.success("Historia wyczyszczona.")

if ask and user_query.strip():
    try:
        reply, srcs, t = answer_query(user_query.strip(), k=k, llm_model=llm_model, temperature=temperature)
        st.session_state.chat.append({"role": "user", "text": user_query.strip(), "sources": []})
        st.session_state.chat.append({"role": "assistant", "text": reply, "sources": srcs, "time": t})
    except Exception as e:
        st.error(f"Błąd podczas generowania odpowiedzi: {e}")

# =========================
# Render historii czatu
# =========================
st.subheader("🧾 Historia")
if not st.session_state.chat:
    st.info("Zadaj pierwsze pytanie powyżej.")
else:
    for i, turn in enumerate(st.session_state.chat, start=1):
        if turn["role"] == "user":
            st.markdown(f"**🧑 Ty:** {turn['text']}")
        else:
            st.markdown(f"**🤖 Asystent:** {turn['text']}")
            meta = f"_czas generowania: {turn.get('time', 0):.2f}s_"
            with st.expander(f"📚 Źródła (kliknij, by rozwinąć) — {meta}", expanded=False):
                for s in (turn.get("sources") or []):
                    if show_full_chunks:
                        st.write(s)
                    else:
                        st.write(s[:350] + ("..." if len(s) > 350 else ""))

        st.markdown("---")
