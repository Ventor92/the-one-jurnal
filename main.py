import json
import faiss
import numpy as np

import json
import re

from google import genai
from google.genai import types

import google.generativeai as genai2

from typing import List, Literal, Optional
from pydantic import BaseModel, Field


from fragment import fragment as frg 
from ChromaDB import ChromaDB
from GameFact import GameFact

from FactStore_Service import search_context, ask_gemini

MODEL_EMBEDDING = "models/text-embedding-004"
MODEL_TEXT = "gemini-2.5-flash"

# Klucz API
client = genai.Client()
# Inicjalizacja bazy Chroma
db = ChromaDB()

# Inicjalizacja FAISS z odpowiednim wymiarem embeddingu
metadata_store = []

# Pobierz wymiar embeddingów z modelu
test_emb = genai2.embed_content(model=MODEL_EMBEDDING, content="Test")['embedding']
embedding_dim = len(test_emb)
index = faiss.IndexFlatL2(embedding_dim)

metadata_store = []  # Równoległa lista metadanych

base_model: str = "gemini-2.5-flash"
base_system_instruction="You are the creative assistance of Game Master - Lore Master, " \
    "in ttRPG The One Ring 2e based on Lord of the Ring universe." \
    "The Response provide in polish language"

import threading
import time
import sys

done: list[bool] = [False]

# Loader w osobnym wątku
def loader():
    spinner = ["|", "/", "-", "\\"]
    i = 0
    while not done[0]:
        sys.stdout.write(f"\rŁadowanie {spinner[i % len(spinner)]}")
        sys.stdout.flush()
        i += 1
        time.sleep(0.1)
    sys.stdout.write("\rGotowe!      \n")

# --- Przykład działania ---
if __name__ == "__main__":

    done = [False]  # flaga zakończenia pracy loadera


    # Szukanie kontekstu do dalszej gry
    query = "Czy Veig jest z Marsa?"

    t = threading.Thread(target=loader)
    t.start()
    print("Pobieranie kontekstu...")
    results = search_context(query)
    print("Wyniki wyszukiwania:")
    print(json.dumps(results, indent=2, ensure_ascii=False))

    answer: str = ask_gemini(query)

    done[0] = True
    t.join()

    print("Odpowiedź modelu:")
    print(answer)
