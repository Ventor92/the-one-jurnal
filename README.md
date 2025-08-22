# The One Jurnal

Aplikacja do prowadzenia dziennika, wspierająca zarządzanie notatkami, zadaniami oraz integrację z Chroma DB.

## Funkcje

- Tworzenie, edycja i usuwanie wpisów dziennika
- Przeglądanie historii notatek
- Integracja z bazą Chroma DB
- API REST z dokumentacją Swagger

## Instalacja

1. Sklonuj repozytorium:
   ```bash
   git clone https://github.com/twoj-uzytkownik/the-one-jurnal.git
   cd the-one-jurnal
   ```
2. Zainstaluj zależności:
   ```bash
   pip install -r requirements.txt
   ```
3. Uruchom aplikację:
   Draft: by main scripts

   Interactive Handbook
   ```
   streamlit run main_rpg_advisor.py
   ```
   or
   ``` 
   streamlit run main_rpg_advisor.py --server.address 0.0.0.0 --server.port 8501
   ```
   <!-- ```bash
   uvicorn main:app --reload
   ``` -->

### Uruchomienie za pomocą Docker Compose

Możesz uruchomić aplikację oraz Chroma DB korzystając z Docker Compose:

```bash
docker compose up -d
```

## Dokumentacja API

1. [API Swagger Chroma DB](http://localhost:8000/docs/#/default/collection_get)

## Technologie

- Python
- Chroma DB

## Kontakt

Autor: [Twoje Imię](mailto:twoj.email@example.com)