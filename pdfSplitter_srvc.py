import fitz  # PyMuPDF
from langchain.schema import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter

def load_pdf_with_toc(pdf_path):
    """
    Wczytuje PDF i zwraca listę Document (LangChain) z metadata zawierającą nagłówek/rozdział.
    """
    doc = fitz.open(pdf_path)
    documents = []

    # Pobierz TOC: lista [poziom, tytuł, strona]
    toc = doc.get_toc(simple=False)  # simple=True zwraca tylko (poziom, tytuł, strona)

    # Jeśli brak TOC, traktuj cały PDF jako jeden rozdział
    if not toc:
        full_text = ""
        for page in doc:
            full_text += page.get_text()
        documents.append(Document(page_content=full_text, metadata={"chapter": "cały dokument"}))
        return documents

    # Iteruj po TOC i zbierz tekst dla każdego nagłówka
    for i, entry in enumerate(toc):
        level, title, page_num = entry[:3]  # bierzemy tylko pierwsze 3 wartości
        start_page = page_num - 1
        end_page = toc[i + 1][2] - 1 if i + 1 < len(toc) else len(doc)
        
        chapter_text = ""
        for p in range(start_page, end_page):
            chapter_text += doc[p].get_text()
        
        documents.append(Document(page_content=chapter_text, metadata={"chapter": title, "pages": f"{start_page}-{end_page}", "source": pdf_path}))

    return documents


def sliding_window_split(documents, chunk_size=500, chunk_overlap=100):
    """
    Dzieli dokumenty po nagłówkach na fragmenty o określonym chunk_size + chunk_overlap
    """
    splitter = RecursiveCharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    all_chunks = []
    for doc in documents:
        chunks = splitter.split_documents([doc])
        # Dodaj info o rozdziale do każdego chunk
        for c in chunks:
            c.metadata["chapter"] = doc.metadata.get("chapter", "brak")
        all_chunks.extend(chunks)
    return all_chunks


# ==========================
# Przykład użycia
# ==========================

if __name__ == "__main__":
    pdf_path = "G:\\RPG\\The One Ring\\Jedyny_Pierscien_Gra_Fabularna_v3.1-1.pdf"

    # 1. Wczytaj PDF i podziel po nagłówkach (TOC)
    documents = load_pdf_with_toc(pdf_path)

    # 2. Zastosuj sliding window
    chunks = sliding_window_split(documents, chunk_size=500, chunk_overlap=100)

    # 3. Sprawdź wynik
    for i, c in enumerate(chunks[:5], 1):
        print(f"Chunk {i} | Chapter: {c.metadata['chapter']} | Length: {len(c.page_content)}")
        print(c.page_content[:200], "...\n")
