# pipeline.py
import json
import re
from typing import List, Optional, Mapping

from google import genai
from google.genai import types

from chromadb.api.types import GetResult

# import google.generativeai as genai2

from ChromaDB import ChromaDB
from GameFact import GameFact

MODEL_EMBEDDING = "gemini-embedding-001"
MODEL_TEXT = "gemini-2.5-flash"

base_system_instruction=""" 
        Jesteś asystentem Mistrza Gry – Mistrza Loru,
        w grze fabularnej (ttRPG) The One Ring 2e, opartej na uniwersum Władcy Pierścieni.
        """

promptTask: Mapping = {
    "extract": """Wydobądź z poniższego tekstu informacje o nowych lub istotnych elementach wydarzeniach z sesji ttRPG. 
        Następnie zwróć listę obiektów w formacie JSON zgodnym z klasą GameFact.""",
    "context": """Na podstawie poniższego kontekstu, odpowiedz na pytanie."""

}

db = ChromaDB()
client = genai.Client()

def extract_game_facts(transcript_fragment: str) -> list[GameFact]:
    """
    Wysyła fragment transkrypcji do LLM, aby wydobyć fakty w formacie JSON.
    Zwraca listę słowników gotowych do wrzucenia do FAISS.
    """
    prompt = f"""
    Wydobądź z poniższego tekstu informacje o nowych lub istotnych elementach gry RPG.
    Zwróć listę obiektów w formacie JSON zgodnym z klasą GameFact.
    Tekst:
    {transcript_fragment}
    """

    response = None

    try:
        response = client.models.generate_content(
            model=MODEL_TEXT,
            contents=[prompt],
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=list[GameFact]
            ),
        )

    except Exception as e:
        print(f"Błąd wywołania Gemini: {e}")
        return []
    
    # Jeśli model poprawnie sparsował dane — mamy listę GameFact
    if hasattr(response, "parsed") and response.parsed:
        try:
            return response.parsed
        except Exception as e:
            print(f"Błąd parsowania odpowiedzi: {e}")
            return []
        
    else:
        print("Model nie zwrócił poprawnej odpowiedzi JSON")
        return []

def add_fact_to_db(entry: Mapping):
    """
    Tworzy embedding wpisu i dodaje go do ChromaDB.
    """
    text_repr = f"{entry['nazwa']}. {entry['opis']}. {entry['log']}"
    emb_response = client.models.embed_content(
        model=MODEL_EMBEDDING,
        contents=text_repr)
    
    try: 
        vector = emb_response.embeddings[0].values
    except: 
        print("embeddeng jest pusty")

    if isinstance(vector, list):
        entry_id = entry.get("id", entry['nazwa'])
        db.add_entry(entry_id, vector, entry, text_repr)

    # emb_response = genai.embed_content(model=MODEL_EMBEDDING, content=text_repr)
    # vector = emb_response['embedding']

def save_facts_to_file(facts: List[dict], filename="facts_store.json"):
    """
    Zapisuje wyodrębnione fakty do pliku JSON.
    """
    try:
        # Jeśli plik istnieje, wczytujemy jego zawartość
        with open(filename, "r", encoding="utf-8") as f:
            existing_facts = json.load(f)
    except FileNotFoundError:
        existing_facts = []

    # Dodajemy nowe fakty
    existing_facts.extend(facts)

    # Zapisujemy wszystko z powrotem
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(existing_facts, f, ensure_ascii=False, indent=2)

def process_transcript(fragment: str, save_file: str = "facts_store.json") -> List[GameFact]:
    """
    Główny pipeline: wyodrębnia fakty i zapisuje do pliku.
    """
    # Wyodrębnienie faktów z transkrypcji
    facts = extract_game_facts(fragment)

    # Zapis do pliku JSON
    # save_facts_to_file(facts, save_file)

    # (Opcjonalnie) dodanie do ChromaDB
    for fact in facts:
        fact.data_w_grze = "123 II Ery"
        fact.sesja = 1
        fact_dict = fact.to_metadata()
        add_fact_to_db(fact_dict)

    return facts

def search_context(query: str, k=3):
    """
    Szuka kontekstu do dalszej gry w ChromaDB.
    """
    emb_response = client.models.embed_content(model=MODEL_EMBEDDING, contents=query)

    # vector = emb_response['embedding']
    try: 
        vector = emb_response.embeddings[0].values
    except: 
        print("embeddeng jest pusty")

    if isinstance(vector, list):
        results = db.search(vector, n_results=k)
        return results
        
def ask_gemini(query: str) -> str:
    """
    Wysyła zapytanie do modelu Gemini z opcjonalnym kontekstem.
    """
    context: List[str] = []
    results = search_context(query, 5)

    for result in results:

        metadata: Mapping = result['metadata']
        context.append(GameFact.from_metadata(metadata).toContext())

    context_str = '\n'.join(context) if context else "Brak kontekstu"
    prompt = f"""
    {base_system_instruction}
    {promptTask.get("context")}
    
    Pytanie: {query}
    
    Kontekst: {context_str}
    """

    response = client.models.generate_content(
        model=MODEL_TEXT,
        contents=[prompt],
        config=types.GenerateContentConfig(
            response_mime_type="text/plain"
        )
    )

    return response.text if response.text else "Brak odpowiedzi."


def get_all_facts():
    """
    Pobiera wszystkie fakty z bazy danych.
    """

    number_of_embeddings = db.collection.count()
    print(f"Liczba zapisanych embeddingów: {number_of_embeddings}")

    results:GetResult = db.collection.get()

    for result in results['metadatas']:
        metadata: Mapping = result
        # document = result['documents'][0]
        # entry_id = result['ids'][0]
        # embedding = result['embeddings'][0]

        # Odtwarzamy GameFact z metadanych
        game_fact = GameFact.from_metadata(metadata)
        # game_fact.id = entry_id

        # print(game_fact)
        print(game_fact.model_dump_json(indent=2))

# --- Przykład użycia ---
if __name__ == "__main__":
    from fragment import fragment as frg

    print("Uruchamianie pipeline'u dla fragmentu transkrypcji...")
    extracted_facts: list[GameFact] = process_transcript(frg)
    print("Wyodrębnione i zapisane fakty:")
    for fact in extracted_facts:
        print(fact)
    # print(json.dumps(extracted_facts, indent=2, ensure_ascii=False))
