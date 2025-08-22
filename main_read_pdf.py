import fitz  # PyMuPDF
from fitz import Document
def wczytaj_pdf(sciezka):
    """
    Funkcja wczytuje plik PDF i zwraca:
    - metadane
    - spis treści (outline/zakładki)
    - tekst ze stron
    """
    plik = fitz.open(sciezka)

    # 📑 Metadane
    metadane = plik.metadata

    # 📑 Spis treści (zakładki)
    spis_tresci = plik.get_toc()  # lista [ [poziom, tytul, strona], ... ]

    # 📑 Tekst
    strony = []
    for nr, strona in enumerate(plik, start=1):
        strony.append({
            "nr_strony": nr,
            "tekst": strona.get_text()
        })

    plik.close()

    return {
        "metadane": metadane,
        "spis_tresci": spis_tresci,
        "strony": strony
    }

def tekst_rozdzialu(pdf_path, nazwa_rozdzialu):
    plik: Document = fitz.open(pdf_path)
    toc = plik.get_toc()

    start_page = None
    end_page = None
    start_y = None
    end_y = None

    # Szukamy rozdziału i jego końca
    for i, (poziom, tytul, strona) in enumerate(toc):
        if nazwa_rozdzialu.lower() in tytul.lower():
            start_page = strona - 1
            # jeśli istnieje kolejny wpis, jego strona i pozycja będą końcem
            if i + 1 < len(toc):
                end_page = toc[i+1][2] - 1
                next_title = toc[i+1][1]
            else:
                end_page = len(plik) - 1
                next_title = None
            break

    start_idx = None
    poziom_docelowy = None

    # Szukamy wybranego rozdziału
    for i, (poziom, tytul, strona) in enumerate(toc):
        if nazwa_rozdzialu.lower() in tytul.lower():
            start_idx = i
            poziom_docelowy = poziom
            break

    if start_idx is None:
        plik.close()
        return f"❌ Nie znaleziono rozdziału: {nazwa_rozdzialu}"

    # Szukamy indeksu końca rozdziału (następny nagłówek na tym samym lub wyższym poziomie)
    end_idx = len(toc)
    for i in range(start_idx + 1, len(toc)):
        if toc[i][0] <= poziom_docelowy:
            end_idx = i
            break

    start_page = toc[start_idx][2] - 1
    end_page = toc[end_idx][2] - 1 if end_idx < len(toc) else len(plik)

    if start_page is None:
        return f"❌ Nie znaleziono rozdziału: {nazwa_rozdzialu}"

    tekst = ""

    # Sklejanie tekstu ze stron
    tekst = ""
    for nr in range(start_page, end_page):
        tekst += plik[nr].get_text() + "\n"

    tekst += plik[end_page].get_text() + "\n"

    plik.close()
    return tekst

# --- Przykład użycia ---
if __name__ == "__main__":

    pathFile = "G:\RPG\The One Ring\Jedyny_Pierscien_Gra_Fabularna_v3.1-1.pdf"
    dane = wczytaj_pdf(pathFile)
# Metadane
    print("📑 Metadane:")
    for k, v in dane["metadane"].items():
        print(f"{k}: {v}")

    # Spis treści
    print("\n📖 Spis treści:")
    for poziom, tytul, strona in dane["spis_tresci"]:
        print("  " * (poziom - 1) + f"- {tytul} (strona {strona})")

    # Tekst ze stron
    print("\n📄 Tekst pierwszej strony:")
    print(dane["strony"][0]["tekst"])

    sectionName = "Potyczka"
    print(f"📄 Tekst rozdziału '{sectionName}':")
    rozdzial = tekst_rozdzialu(pathFile, sectionName)
    for i in range(0, len(rozdzial), 1000):
        print(rozdzial[i:i+1000])
        print("\n---\n")
