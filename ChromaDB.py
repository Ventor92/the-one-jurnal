from typing import Mapping 

# chroma.py
import chromadb
from chromadb.config import Settings
import numpy as np

from utils.singleton import SingletonMeta

from chromadb import Documents, EmbeddingFunction, Embeddings

from google import genai
from google.genai import types

client = genai.Client() 

class GeminiEmbeddingFunction(EmbeddingFunction):
  def __call__(self, input: Documents) -> Embeddings:
    EMBEDDING_MODEL_ID = "gemini-embedding-001"  # @param ["gemini-embedding-001", "text-embedding-004"] {"allow-input": true, "isTemplate": true}
    title = "Custom query"
    response = client.models.embed_content(
        model=EMBEDDING_MODEL_ID,
        contents=input,
        config=types.EmbedContentConfig(
          task_type="retrieval_document",
          title=title
        )
    )

    return response.embeddings[0].values

# class ChromaDB(metaclass=SingletonMeta):
class ChromaDB():
    def __init__(self, collection_name="game_facts", host="http://localhost:8000"):
        """
        Inicjalizacja klienta Chroma i kolekcji.
        """
        # self.client = Client(Settings(
        #     chroma_api_impl="rest",
        #     chroma_server_host=host
        # ))

        self.client = chromadb.HttpClient(host='localhost', port=8000)
        # Tworzymy kolekcję do przechowywania facts

        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            # embedding_function=GeminiEmbeddingFunction()
        )

        # self.client.delete_collection(collection_name)
        # self.collection = self.client.get_or_create_collection(
        #     name=collection_name,
        #     embedding_function=GeminiEmbeddingFunction()
        # )


    def add_entry(self, entry_id: str, embedding: list[float], metadata: Mapping, document: str):
        """
        Dodaje wpis do bazy wektorowej.
        """
        self.collection.add(
            ids=[entry_id],
            embeddings=[embedding],
            metadatas=[metadata],
            documents=[document]
        )

    def search(self, query_embedding: list[float], n_results=3):
        """
        Szuka najbliższych wpisów na podstawie embeddingu.
        """
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results
        )
        # Zwraca listę słowników (metadatas) i dokumentów
        hits = []
        for md, doc in zip(results['metadatas'][0], results['documents'][0]):
            hits.append({
                "metadata": md,
                "document": doc
            })
        return hits

# --- Przykład użycia ---
if __name__ == "__main__":
    db = ChromaDB()
    db.add_entry(
        entry_id="1",
        embedding=[0.1, 0.2, 0.3],
        metadata={"nazwa": "Kompania", "opis": "Podróż", "log": "Start"},
        document="Kompania wyrusza w podróż"
    )
    results = db.search([0.1, 0.2, 0.3])
    print(results)
