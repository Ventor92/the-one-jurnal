import streamlit as st
from dataclasses import dataclass

@dataclass
class SideBarProps:
    llm_model: str
    temperature: float
    k: int
    rebuild: bool
    show_full_chunks: bool

def setupViewSidebar() -> SideBarProps:
    st.sidebar.header("⚙️ Ustawienia")
    llm_model = st.sidebar.selectbox("Model LLM", ["gemini-2.5-flash", "gemini-2.5-pro"], index=0)
    temperature = st.sidebar.slider("Temperature", 0.0, 1.0, 0.2, 0.1)
    k = st.sidebar.slider("Liczba fragmentów kontekstu (k)", 15, 10, 5, 1)
    rebuild = st.sidebar.checkbox("Wymuś przebudowę indeksu", value=False)
    show_full_chunks = st.sidebar.checkbox("Pokaż pełne fragmenty kontekstu DUPA", value=True)

    # --- Inicjalizacja session_state ---
    if "chat" not in st.session_state:
        st.session_state.chat = []
    if "user_query" not in st.session_state:
        st.session_state.user_query = ""
    if "temperature" not in st.session_state:
        st.session_state.temperature = temperature
    if "k" not in st.session_state:
        st.session_state.k = k
    if "llm_model" not in st.session_state:
        st.session_state.llm_model = llm_model   # ustaw tu swój model LLM, np. ChatGoogleGenerativeAI
    if "rebuild" not in st.session_state:
        st.session_state.rebuild = rebuild

    obj = SideBarProps(
        llm_model=llm_model,
        temperature=temperature,
        k=k,
        rebuild=rebuild,
        show_full_chunks=show_full_chunks
    )

    return obj