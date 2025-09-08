import streamlit as st

st.set_page_config(page_title="RPG Assistant", page_icon="🎲", layout="wide")

st.title("🎲 RPG Assistant")
st.write("Witaj w aplikacji! Skorzystaj z menu po lewej, aby przejść do funkcji:")
st.markdown("""
- 💬 **Q&A Chat** – zadawaj pytania na podstawie podręcznika RPG
- 📂 **Przegląd PDF** – wczytaj i przeglądaj plik podręcznika
- ⚙️ **Ustawienia** – konfiguracja parametrów modelu
""")
