path: str = "G:/Dokumenty/Projectes/The_One_Jurnal/data/"
fileName: str = "Wyp. 01 Zbadać pogłoski o strasznym potworze.md"

from GameFact import GameFact
from FactStore_Service import process_transcript

# --- Przykład użycia ---
if __name__ == "__main__":
    print("Uruchamianie pipeline'u dla fragmentu transkrypcji...")

    frg: str = ""
    with open(path + fileName, "r", encoding="utf-8") as f:
        frg = f.read()

    if not frg or frg.strip() == "":
        print("Brak danych do przetworzenia.")
        exit(0)
    
    extracted_facts: list[GameFact] = process_transcript(frg)
    print("Wyodrębnione i zapisane fakty:")
    for fact in extracted_facts:
        print(fact)
    # print(json.dumps(extracted_facts, indent=2, ensure_ascii=False))