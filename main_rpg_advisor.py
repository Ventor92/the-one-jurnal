from langchain.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores import FAISS
from langchain_community.chat_models import ChatOpenAI
from langchain.schema import Document

from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings

from main_read_pdf import tekst_rozdzialu

from pydantic import SecretStr

import fitz  # PyMuPDF

MODEL_EMBEDDING = "models/embedding-001"
MODEL_TEXT = "gemini-2.5-flash"

# Pliki
PDF_PATH = r"G:\RPG\The One Ring\Jedyny_Pierscien_Gra_Fabularna_v3.1-1.pdf"
FAISS_PATH = r"../../data/faiss_index"

import os

import streamlit as st

st.set_page_config(page_title="TTRPG RAG Assistant", layout="wide")
st.title("🧙‍♂️ TTRPG RAG Assistant (Gemini + FAISS)")

# Slider: liczba fragmentów do wyszukania
st.sidebar.header("Opcje")
k = st.sidebar.slider("Liczba fragmentów kontekstu do wyszukania (k)", min_value=1, max_value=20, value=10)

# Embeddingi Gemini
embeddings = GoogleGenerativeAIEmbeddings(
    model=MODEL_EMBEDDING,
    google_api_key=SecretStr(os.environ["GOOGLE_API_KEY"])
)

# 1. Wczytaj lub stwórz bazę FAISS
if os.path.exists(FAISS_PATH):
    st.info("🔹 Wczytywanie istniejącej bazy FAISS...")
    db = FAISS.load_local(FAISS_PATH, embeddings, allow_dangerous_deserialization=True)
else:
    st.info("⚡ Tworzenie bazy FAISS i generowanie embeddingów (pierwsze uruchomienie)...")
    loader = PyPDFLoader(PDF_PATH)
    documents = loader.load()
    documents = documents[92:105]  # fragment testowy

    splitter = RecursiveCharacterTextSplitter(chunk_size=600, chunk_overlap=150)
    docs = splitter.split_documents(documents)

    db = FAISS.from_documents(docs, embeddings)
    db.save_local(FAISS_PATH)
    st.success("✅ Baza FAISS została utworzona i zapisana.")


# 2. Model LLM Gemini
llm = ChatGoogleGenerativeAI(
    model=MODEL_TEXT, 
    api_key=SecretStr(os.environ["GOOGLE_API_KEY"]), 
    temperature=0.2
    )


# 3. Pole do wpisywania pytań
query = st.text_input("Zadaj pytanie do podręcznika TTRPG:", "")

if query:
    retrieved_docs = db.similarity_search(query, k=k)
    context = "\n".join([d.page_content for d in retrieved_docs])

    prompt = f"Odpowiedz na pytanie na podstawie zasad:\n\n{context}\n\nPytanie: {query}"
    response = llm.predict(prompt)

    st.subheader("📄 Kontekst (wybrane fragmenty podręcznika):")
    for i, d in enumerate(retrieved_docs, 1):
        st.markdown(f"**Fragment {i}:** {d.page_content}...")  # skrót 300 znaków

    st.subheader("💬 Odpowiedź LLM:")
    st.write(response)