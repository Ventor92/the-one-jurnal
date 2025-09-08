import os
import time
import streamlit as st
import torch

from utils.singleton import SingletonMeta

from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from pydantic import SecretStr
# from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_huggingface.embeddings import HuggingFaceEmbeddings
from pdfSplitter_srvc import load_pdf_with_toc, sliding_window_split
from langchain.schema import Document
# =========================
# Konfiguracja i stałe
# =========================
MODEL_EMBEDDING = "models/embedding-001"
DEFAULT_LLM_MODEL = "gemini-2.5-flash"
PDF_PATH = r"../../data/Jedyny_Pierscien_Gra_Fabularna_v3.1-1.pdf"  # <- podmień w razie potrzeby
FAISS_PATH = r"../../data/faiss_index"

class DataBase(metaclass=SingletonMeta):
    def __init__(self, rebuild: bool = False):
        self.embeddings = self.build_embeddings()
        self.db: FAISS | None = self.load_db()

    def get_db(self) -> FAISS | None:
        return self.db
    
    def load_db(self) -> FAISS | None:
        try:
            embeddings = self.get_embeddings()
            faiss = FAISS.load_local(
                        FAISS_PATH,
                        embeddings,
                        allow_dangerous_deserialization=True  # świadomie, bo to nasz własny plik
                    )
        except FileNotFoundError: 
            faiss = None
    
        return faiss
    
    def rebuild_db(self):
        self.db = self._rebuild_db()
        self.db.save_local(FAISS_PATH)

    def load_pdf(self, path: str):
        documents = load_pdf_with_toc(PDF_PATH)
        docs = sliding_window_split(documents, chunk_size=1200, chunk_overlap=300)
        return docs
    
    def _rebuild_db(self) -> FAISS:
        docs = self.load_pdf(PDF_PATH)
        embeddings = self.get_embeddings()
        faiss: FAISS = FAISS.from_documents(docs, embeddings)
        return faiss
    
    def build_embeddings(self):
        # Sprawdzenie dostępności GPU
        device = "cuda" if torch.cuda.is_available() else "cpu"
        print(f"Tworzenie embeddingów na urządzeniu: {device}")
        
        return HuggingFaceEmbeddings(
            model_name="intfloat/multilingual-e5-base",
            model_kwargs={"device": device}
        )
    
    def get_embeddings(self):
        return self.embeddings
# =========================
# Funkcje pomocnicze
# =========================    

def build_llm(model_name: str, temperature: float):
    return ChatGoogleGenerativeAI(
        model=model_name,
        api_key=SecretStr(os.environ["GOOGLE_API_KEY"]),
        temperature=temperature
    )

def answer_query(query: str, k: int, llm_model: str, temperature: float):
    llm = build_llm(llm_model, temperature)
    dataBase = DataBase()
    db = dataBase.get_db()
    retrieved_docs = db.similarity_search(query, k=k)
    # retrieved_docs = [Document("PUSTO")]
    context = "\n\n".join([d.page_content for d in retrieved_docs])

    # Prosty, solidny prompt pod reguły TTRPG:
    system = (
        "Jesteś asystentem zasad TTRPG. Odpowiadasz wyłącznie na podstawie dostarczonego kontekstu.\n"
        "Jeśli brakuje informacji w kontekście, powiedz „Nie wiem na podstawie załączonych zasad”.\n"
        "Zachowuj się jak sędzia zasad: bądź precyzyjny, podawaj numery/sekcje jeśli są w tekście."
    )
    prompt = f"{system}\n\n=== KONTEKST ===\n{context}\n\n=== PYTANIE ===\n{query}\n\n=== ODPOWIEDŹ ==="

    start = time.time()
    response = llm.invoke(prompt)
    # response = "llm.invoke(prompt)"
    elapsed = time.time() - start

    sources = []
    for d in retrieved_docs:
        meta = d.metadata or {}
        page = meta.get("pages", "—")
        src = meta.get("source", "PDF")
        chapter = meta.get("chapter", "—")
        snippet = d.page_content.replace("\n", " ")
        obj = {
            "chapter": chapter,
            "page": page,
            "source": src,
            "content": snippet
        }
        # sources.append(f"{src} {chapter} (strona: {page}) — „{snippet}”")
        sources.append(obj)

    return response, sources, elapsed