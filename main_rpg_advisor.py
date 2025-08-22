from langchain.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores import FAISS
from langchain_community.chat_models import ChatOpenAI
from langchain.schema import Document

from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings

from main_read_pdf import tekst_rozdzialu

import fitz  # PyMuPDF

MODEL_EMBEDDING = "models/embedding-001"
MODEL_TEXT = "gemini-2.5-flash"

import os


# 1. Wczytaj podręcznik
pathFile = r"G:\RPG\The One Ring\Jedyny_Pierscien_Gra_Fabularna_v3.1-1.pdf"
loader = PyPDFLoader(pathFile)
documents = loader.load()

documents = documents[92:105]  # Testowo bierzemy tylko dwa dokumenty

for doc in documents:
	print(doc)

# sectionName = "Potyczka"
# print(f"📄 Tekst rozdziału '{sectionName}':")
# rozdzial = tekst_rozdzialu(pathFile, sectionName)
# documents = [Document(page_content=rozdzial, metadata={})]

# 2. Podziel na fragmenty
splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
docs = splitter.split_documents(documents)

# 3. Stwórz embeddingi i bazę FAISS
# embeddings = OpenAIEmbeddings(model="text-embedding-3-small")

# 3. Stwórz embeddingi Gemini
from pydantic import SecretStr

embeddings = GoogleGenerativeAIEmbeddings(
	model=MODEL_EMBEDDING,
	google_api_key=SecretStr(os.environ["GOOGLE_API_KEY"])
)

db = FAISS.from_documents(docs, embeddings)

# 4. Model LLM
# llm = ChatOpenAI(model="gpt-4")

llm = ChatGoogleGenerativeAI(model=MODEL_TEXT, api_key=SecretStr(os.environ["GOOGLE_API_KEY"]), temperature=0.2)

# 5. Zadawanie pytań z kontekstem
while True:
    query = input("Twoje pytanie: ")
    if query.lower() in ["exit", "quit"]:
        print("Koniec sesji.")
        break

    # Pobierz kontekst z FAISS
    retrieved_docs = db.similarity_search(query, k=10)
    context = "\n".join([d.page_content for d in retrieved_docs])

    # Prompt dla modelu
    prompt = f"Odpowiedz na pytanie na podstawie zasad:\n\n{context}\n\nPytanie: {query}"
    
    # Generuj odpowiedź
    response = llm.predict(prompt)
    
    print("\n📄 Kontekst (fragmenty podręcznika):")
    print(context)
    print("\n💬 Odpowiedź:")
    print(response)
    print("\n" + "="*60 + "\n")