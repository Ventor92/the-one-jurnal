import os
import streamlit as st
import torch
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_google_genai import ChatGoogleGenerativeAI
from pdfSplitter_srvc import load_pdf_with_toc, sliding_window_split
from ai_svrc import answer_query, DataBase

# =========================
# Konfiguracja i stałe
# =========================
MODEL_EMBEDDING = "models/embedding-001"
DEFAULT_LLM_MODEL = "gemini-2.5-flash"
PDF_PATH = r"../../data/Jedyny_Pierscien_Gra_Fabularna_v3.1-1.pdf"
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
# Inicjalizacja session_state
# =========================
for key, default in [
    ("chat", []),
    ("temperature", 0.2),
    ("k", 5),
    ("llm_model", DEFAULT_LLM_MODEL),
    ("user_query", ""),
    ("db", None)
]:
    if key not in st.session_state:
        st.session_state[key] = default

# =========================
# Sidebar: ustawienia
# =========================
st.sidebar.header("⚙️ Ustawienia")
st.session_state.llm_model = st.sidebar.selectbox(
    "Model LLM",
    ["gemini-2.5-flash", "gemini-2.5-pro"],
    index=0
)
st.session_state.temperature = st.sidebar.slider(
    "Temperature", 0.0, 1.0, st.session_state.temperature, 0.1
)
st.session_state.k = st.sidebar.slider(
    "Liczba fragmentów kontekstu (k)", 1, 10, st.session_state.k
)

if "rebuild" not in st.session_state:
    st.session_state.rebuild = False

if st.sidebar.button("🔄 Przebuduj indeks"):
    st.session_state.rebuild = True
else:
    # resetujemy flagę po użyciu, żeby rebuild nie odpalał się w kółko
    if st.session_state.rebuild:
        st.session_state.rebuild = False

show_full_chunks = st.sidebar.checkbox("Pokaż pełne fragmenty kontekstu", value=True)

st.write(f"Aktualne parametry: temperature={st.session_state.temperature}, k={st.session_state.k}")

# =========================
# Funkcja inicjalizacji FAISS
# =========================
def ensure_vectorstore(rebuild: bool = False):
    """
    Tworzy lub wczytuje FAISS do st.session_state.db.
    Zapis/wczytanie: FAISS_PATH.
    """

    if rebuild:
        st.session_state.db = None

    if st.session_state.db is not None:
        return
    
    dataBase = DataBase()
    if rebuild or (dataBase.get_db() is None):
        try:
            with st.spinner("Tworzenie bazy FAISS (pierwsze uruchomienie / przebudowa)..."):
                dataBase.rebuild_db()
                st.success("✅ Baza FAISS stworzona i zapisana lokalnie.")
        except any as e:
            st.error(f"Błąd podczas (prze)budowy bazy FAISS: {e}")
            st.stop()
    
    st.session_state.db = dataBase.get_db()

# =========================
# Lazy load FAISS
# =========================
ensure_vectorstore(rebuild=st.session_state.rebuild)

# =========================
# Q&A Chat – Historia i input
# =========================
st.title("💬 RPG Assistant - Q&A Chat")

history_container = st.container()
with history_container:
    st.subheader("🧾 Historia")
    if not st.session_state.chat:
        st.info("Zadaj pierwsze pytanie poniżej.")
    else:
        for turn in st.session_state.chat:
            if turn["role"] == "user":
                st.markdown(f"**🧑 Ty:** {turn['text']}")
            else:
                st.markdown(f"**🤖 Asystent:** {turn['text']}")
                with st.expander("📚 Źródła", expanded=False):
                    for s in (turn.get("sources") or []):
                        st.write(s)
                        # st.info(type(s))
                        # st.write((f"{s.src} {s.chapter} ({s.page}) — „{s.content}”"))
                        # st.write(f"{s.get('chapter')} ({s.get('page')}) — „{s.get('content')}”")
            st.markdown("---")

def _handle_submit():
    q = st.session_state.user_query.strip()
    if not q:
        return
    reply, srcs, t = answer_query(
        q,
        k=st.session_state.k,
        llm_model=st.session_state.llm_model,
        temperature=st.session_state.temperature
    )
    st.session_state.chat.append({"role": "user", "text": q, "sources": []})
    st.session_state.chat.append({"role": "assistant", "text": reply.content, "sources": srcs, "time": t})
    # st.session_state.user_query = ""
    st.rerun()

# ===== Input =====
st.text_input(
    "Twoje pytanie:",
    key="user_query",
    placeholder="Np. Jak przeprowadzać atak?",
    label_visibility="collapsed",
    on_change=_handle_submit,
)

col1, col2 = st.columns([1, 1])
with col1:
    if st.button("✍️ Zapytaj", type="primary", use_container_width=True):
        _handle_submit()
        # st.rerun()
with col2:
    if st.button("🧹 Wyczyść historię", use_container_width=True):
        st.session_state.chat = []
        st.rerun()
