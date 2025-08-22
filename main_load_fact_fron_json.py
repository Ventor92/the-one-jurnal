from FactStore_Service import add_facts_to_db_from_file

# --- Przykład użycia ---
if __name__ == "__main__":
    """Główna funkcja uruchamiająca skrypt.
    """
    print("Dodawanie faktów do bazy danych z pliku JSON...")
    add_facts_to_db_from_file("facts_store.json")

    print("Zakończono dodawanie faktów do bazy danych.")